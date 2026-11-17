"""
Load a sample of SENTINEL transactions into Neo4j.

Graph model
    (:Customer)-[:USED_DEVICE]->(:Device)
    (:Customer)-[:PAID {transaction_id, amount, time, fraud_label, device_id}]->(:Merchant)

Every write uses MERGE, so running this script twice gives the same graph.
"""
import glob
import json
import os

import pandas as pd
from neo4j import GraphDatabase

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tables")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "sentinel123")

# We load a continuous time window instead of random rows. A random sample
# would cut most devices off from the other customers using them, and the
# shared-device pattern would disappear. 14 days of train data is ~32k payments.
SAMPLE_SPLIT = "train"
SAMPLE_START = "2025-03-01"
SAMPLE_DAYS = 14

BATCH_SIZE = 2000


# ---------------------------------------------------------------- reading data

# read_table
# Opens one data table (for example "customers" or "transactions") from the
# data folder. Each table is split into many small zipped CSV files, so this
# reads all of them and joins them into one big table.
#   table   - which table to read
#   split   - which sub-folder (e.g. "train"); "all" for tables with no split
#   columns - only read these columns, to save memory
def read_table(table, split="all", columns=None):
    files = sorted(glob.glob(os.path.join(DATA_DIR, table, split, "*.csv.gz")))
    if not files:
        raise FileNotFoundError(f"No files for {table}/{split} under {DATA_DIR}")
    return pd.concat([pd.read_csv(f, usecols=columns) for f in files], ignore_index=True)


# read_sample
# Picks the payments we will put into the graph.
#   1. Reads all payments from the chosen split (default: train).
#   2. Keeps only payments inside the date window (default: 14 days from 1 March 2025).
#   3. Adds the fraud label (1 = fraud, 0 = not fraud) to each payment from the
#      labels table. Payments with no label are treated as 0.
# Returns the payments sorted from oldest to newest.
def read_sample(split=SAMPLE_SPLIT, start=SAMPLE_START, days=SAMPLE_DAYS):
    tx = read_table("transactions", split, [
        "transaction_id", "customer_id", "merchant_id", "device_id",
        "transaction_amount", "payment_channel", "transaction_time",
    ])
    labels = read_table("labels", split, ["transaction_id", "fraud_label"])

    tx["transaction_time"] = pd.to_datetime(tx["transaction_time"], utc=True)
    window_start = pd.Timestamp(start, tz="UTC")
    window_end = window_start + pd.Timedelta(days=days)
    tx = tx[(tx["transaction_time"] >= window_start) & (tx["transaction_time"] < window_end)]

    tx = tx.merge(labels, on="transaction_id", how="left")
    tx["fraud_label"] = tx["fraud_label"].fillna(0).astype(int)
    return tx.sort_values("transaction_time").reset_index(drop=True)


# to_records
# Converts a table into a list of simple records (one per row) that can be
# sent to Neo4j. Empty cells are sent as "null" so Neo4j knows the value is missing.
def to_records(df):
    # pandas uses NaN for missing values; Neo4j should get null instead
    return df.astype(object).where(df.notna(), None).to_dict("records")


# build_rows
# Prepares everything the graph needs, using the sampled payments:
#   customers - details (age, city, region) of every customer in the sample
#   devices   - type (mobile, browser, ...) of every device in the sample
#   merchants - name, category and city of every merchant in the sample
#   usage     - one row per customer + device pair: when it was first and
#               last used, how many payments, and on which days
#   payments  - one row per payment: amount, time, channel, device and fraud label
# Only customers, devices and merchants that appear in the sample are kept.
def build_rows(tx):
    customers = read_table("customers", columns=["customer_id", "customer_age", "home_city", "region"])
    customers = customers[customers["customer_id"].isin(tx["customer_id"])]

    devices = read_table("devices", columns=["device_id", "device_kind"])
    devices = devices[devices["device_id"].isin(tx["device_id"])].drop_duplicates("device_id")

    merchants = read_table("merchants", columns=["merchant_id", "synthetic_name",
                                                 "merchant_category", "merchant_location"])
    merchants = merchants[merchants["merchant_id"].isin(tx["merchant_id"])].copy()
    merchants["city"] = merchants["merchant_location"].map(lambda s: json.loads(s)["city"])
    merchants = merchants.drop(columns="merchant_location")

    # A few payments have no device_id; they still get a PAID edge but no USED_DEVICE.
    # One USED_DEVICE edge per customer/device pair. We keep the list of days
    # the pair was active so the 7-day sharing query can work on dates.
    tx = tx.assign(day=tx["transaction_time"].dt.strftime("%Y-%m-%d"))
    usage = (tx.groupby(["customer_id", "device_id"])
               .agg(first_seen=("transaction_time", "min"),
                    last_seen=("transaction_time", "max"),
                    tx_count=("transaction_id", "count"),
                    days=("day", lambda d: sorted(set(d))))
               .reset_index())
    usage["first_seen"] = usage["first_seen"].map(lambda t: t.isoformat())
    usage["last_seen"] = usage["last_seen"].map(lambda t: t.isoformat())

    payments = tx[["transaction_id", "customer_id", "merchant_id", "device_id",
                   "transaction_amount", "payment_channel", "transaction_time", "fraud_label"]].copy()
    payments["transaction_time"] = payments["transaction_time"].map(lambda t: t.isoformat())

    return {
        "customers": to_records(customers),
        "devices": to_records(devices),
        "merchants": to_records(merchants),
        "usage": to_records(usage),
        "payments": to_records(payments),
    }


# ---------------------------------------------------------------- neo4j

# connect
# Opens a connection to the Neo4j database and checks that it really works
# (verify_connectivity). If Neo4j is not running or the password is wrong,
# this stops with an error straight away.
def connect(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    return driver


# Uniqueness rules: Neo4j will refuse to store two customers, devices or
# merchants with the same id, or two payments with the same transaction id.
CONSTRAINTS = [
    "CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.customer_id IS UNIQUE",
    "CREATE CONSTRAINT device_id IF NOT EXISTS FOR (d:Device) REQUIRE d.device_id IS UNIQUE",
    "CREATE CONSTRAINT merchant_id IF NOT EXISTS FOR (m:Merchant) REQUIRE m.merchant_id IS UNIQUE",
    # one PAID edge per transaction (relationship constraints need Neo4j 5.7+)
    "CREATE CONSTRAINT paid_tx_id IF NOT EXISTS FOR ()-[p:PAID]-() REQUIRE p.transaction_id IS UNIQUE",
]

# The Cypher statements below write data into Neo4j.
# MERGE means "find it if it already exists, otherwise create it", so running
# the load again updates the same items instead of making copies.
# SET fills in or refreshes the details.

# Add Customer nodes.
MERGE_CUSTOMERS = """
UNWIND $rows AS row
MERGE (c:Customer {customer_id: row.customer_id})
SET c.age = row.customer_age, c.home_city = row.home_city, c.region = row.region
"""

# Add Device nodes.
MERGE_DEVICES = """
UNWIND $rows AS row
MERGE (d:Device {device_id: row.device_id})
SET d.kind = row.device_kind
"""

# Add Merchant nodes.
MERGE_MERCHANTS = """
UNWIND $rows AS row
MERGE (m:Merchant {merchant_id: row.merchant_id})
SET m.name = row.synthetic_name, m.category = row.merchant_category, m.city = row.city
"""

# Link each customer to each device they used (Customer -USED_DEVICE-> Device).
MERGE_USED_DEVICE = """
UNWIND $rows AS row
MATCH (c:Customer {customer_id: row.customer_id})
MATCH (d:Device {device_id: row.device_id})
MERGE (c)-[u:USED_DEVICE]->(d)
SET u.first_seen = datetime(row.first_seen),
    u.last_seen  = datetime(row.last_seen),
    u.tx_count   = row.tx_count,
    u.days       = [day IN row.days | date(day)]
"""

# Add one payment link per transaction (Customer -PAID-> Merchant) with the
# amount, time, channel, device and fraud label stored on the link.
MERGE_PAID = """
UNWIND $rows AS row
MATCH (c:Customer {customer_id: row.customer_id})
MATCH (m:Merchant {merchant_id: row.merchant_id})
MERGE (c)-[p:PAID {transaction_id: row.transaction_id}]->(m)
SET p.amount      = row.transaction_amount,
    p.time        = datetime(row.transaction_time),
    p.fraud_label = row.fraud_label,
    p.channel     = row.payment_channel,
    p.device_id   = row.device_id
"""


# create_constraints
# Applies the uniqueness rules above. Safe to run many times: a rule that
# already exists is skipped.
def create_constraints(driver):
    for statement in CONSTRAINTS:
        driver.execute_query(statement)


# write_in_batches
# Sends records to Neo4j in groups of BATCH_SIZE (2,000) instead of all at
# once or one by one. This keeps each request small and the load fast.
def write_in_batches(driver, cypher, rows):
    for i in range(0, len(rows), BATCH_SIZE):
        driver.execute_query(cypher, rows=rows[i:i + BATCH_SIZE])


# load_graph
# Writes the whole sample into Neo4j: first the customers, devices and
# merchants, then the links between them (a link needs both ends to exist).
def load_graph(driver, rows):
    write_in_batches(driver, MERGE_CUSTOMERS, rows["customers"])
    write_in_batches(driver, MERGE_DEVICES, rows["devices"])
    write_in_batches(driver, MERGE_MERCHANTS, rows["merchants"])
    write_in_batches(driver, MERGE_USED_DEVICE, rows["usage"])
    write_in_batches(driver, MERGE_PAID, rows["payments"])


# graph_counts
# Counts what is in the database: customers, devices, merchants, device links,
# payments and fraud payments. Useful to check the load, and to confirm that a
# second run did not create duplicates (the numbers should stay the same).
def graph_counts(driver):
    records, _, _ = driver.execute_query("""
        CALL () { MATCH (n:Customer) RETURN count(n) AS customers }
        CALL () { MATCH (n:Device)   RETURN count(n) AS devices }
        CALL () { MATCH (n:Merchant) RETURN count(n) AS merchants }
        CALL () { MATCH ()-[r:USED_DEVICE]->() RETURN count(r) AS used_device }
        CALL () { MATCH ()-[r:PAID]->() RETURN count(r) AS paid, sum(r.fraud_label) AS fraud_paid }
        RETURN customers, devices, merchants, used_device, paid, fraud_paid
    """)
    return records[0].data()


# Runs when you type "python graph_loader.py":
# pick the sample, prepare it, connect to Neo4j, add the rules, load, and print the counts.
if __name__ == "__main__":
    tx = read_sample()
    print(f"Sample: {len(tx):,} transactions, {tx['fraud_label'].sum()} labelled fraud, "
          f"{tx['transaction_time'].min()} -> {tx['transaction_time'].max()}")
    rows = build_rows(tx)

    with connect() as driver:
        create_constraints(driver)
        load_graph(driver, rows)
        print("Graph now has:", graph_counts(driver))
