#!/usr/bin/env python
"""SENTINEL on MongoDB Atlas: customers and transactions.

Script version of sentinel_mongodb.ipynb (same steps, same order).
Run:  python sentinel_mongodb.py      (reads MONGODB_URI from .env or the environment)
"""
import os
from pathlib import Path
# Resolve .env and data/ relative to this file, whatever the current directory is.
os.chdir(Path(__file__).resolve().parent)

import pandas as pd
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)
pd.set_option("display.max_colwidth", 60)


# ==============================================================================
# ## 0. Configuration and connection
# ==============================================================================
print()
print("=" * 80, "0. Configuration and connection", "=" * 80, sep=chr(10))
import os, glob, json, time, pprint
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pandas as pd
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import BulkWriteError

# Minimal .env reader (KEY=VALUE lines) so python-dotenv isn't required.
env_file = Path(".env")
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

MONGODB_URI   = os.environ["MONGODB_URI"]                       # mongodb+srv://user:pass@cluster.xxxxx.mongodb.net/
DB_NAME       = os.environ.get("SENTINEL_DB", "sentinel")
DATA_DIR      = Path(os.environ.get("SENTINEL_DATA", "data")) / "tables"
# Number of customers to load. 2000 (about 77k transactions, about 60 MB) fits an M0 free cluster.
# Set SAMPLE_CUSTOMERS=all to load all 25,000 customers (about 1M transactions; needs M10 or larger).
SAMPLE_CUSTOMERS = os.environ.get("SAMPLE_CUSTOMERS", "2000")
SAMPLE_CUSTOMERS = None if SAMPLE_CUSTOMERS.lower() == "all" else int(SAMPLE_CUSTOMERS)
# Holdout is the blind evaluation window, so it stays off the cluster by default.
LOAD_SPLITS   = ["warmup", "train", "validation"]
BATCH_SIZE    = 5_000

client = MongoClient(MONGODB_URI, appname="sentinel-notebook", tz_aware=True)
print("Server version:", client.server_info()["version"])
db = client[DB_NAME]


# ==============================================================================
# ## 1. Read the source tables
#
# Only the `*.csv.gz` parts are read. Some folders also hold stray uncompressed copies (`part-00003.csv/`, `.zip`), which would double-count rows.
# ==============================================================================
print()
print("=" * 80, "1. Read the source tables", "=" * 80, sep=chr(10))
def read_table(name, split="all", **kw):
    files = sorted(glob.glob(str(DATA_DIR / name / split / "*.csv.gz")))
    assert files, f"no files for {name}/{split} under {DATA_DIR}"
    return pd.concat((pd.read_csv(f, **kw) for f in files), ignore_index=True)

customers_df = read_table("customers")
devices_df   = read_table("devices")
merchants_df = read_table("merchants")
tx_df  = pd.concat([read_table("transactions", s) for s in LOAD_SPLITS], ignore_index=True)
lbl_df = pd.concat([read_table("labels", s, usecols=["transaction_id", "fraud_label", "label_source", "label_available_at"])
                    for s in LOAD_SPLITS], ignore_index=True)

if SAMPLE_CUSTOMERS:
    keep = customers_df.sample(n=SAMPLE_CUSTOMERS, random_state=42).customer_id
    customers_df = customers_df[customers_df.customer_id.isin(keep)]
    tx_df = tx_df[tx_df.customer_id.isin(keep)]

tx_df = tx_df.merge(lbl_df, on="transaction_id", how="left")
print(f"customers={len(customers_df):,}  devices={len(devices_df):,}  merchants={len(merchants_df):,}  transactions={len(tx_df):,}")
print(tx_df.head(3))


# ==============================================================================
# ## 2. Shape the documents
#
# **customers**: one document per payer, `_id = customer_id`, with a `devices` array **embedded**. The source `devices` table has no owner column, so the customer-to-device link comes from the transactions. Each array entry carries the device kind plus usage stats (`first_seen_at`, `last_seen_at`, `txn_count`).
#
# **transactions**: one document per payment attempt, `_id = transaction_id`. It **references** `customer_id` and `device_id`. The merchant category and location are copied in, because every fraud query filters on them. The fraud label is joined in as well.
# ==============================================================================
print()
print("=" * 80, "2. Shape the documents", "=" * 80, sep=chr(10))
_loc_cache = {}
def parse_loc(s):
    # '{"city":"Indore","lat":22.72,"lon":75.86}' -> {city, geo: GeoJSON Point}
    if not isinstance(s, str):
        return None
    if s not in _loc_cache:
        d = json.loads(s)
        _loc_cache[s] = {"city": d["city"], "geo": {"type": "Point", "coordinates": [d["lon"], d["lat"]]}}
    return _loc_cache[s]

def ts(col):
    return pd.to_datetime(col, utc=True, format="ISO8601")

tx_df["transaction_time"] = ts(tx_df["transaction_time"])
tx_df["label_available_at"] = ts(tx_df["label_available_at"])

# ---- embedded device summaries, derived from transactions ----
dev_usage = (tx_df.dropna(subset=["device_id"])
             .groupby(["customer_id", "device_id"])
             .agg(first_seen_at=("transaction_time", "min"),
                  last_seen_at=("transaction_time", "max"),
                  txn_count=("transaction_id", "count"))
             .reset_index()
             .merge(devices_df[["device_id", "device_kind"]], on="device_id", how="left"))
devices_by_customer = {
    cid: [{**d, "first_seen_at": d["first_seen_at"].to_pydatetime(), "last_seen_at": d["last_seen_at"].to_pydatetime()}
          for d in g.drop(columns="customer_id").sort_values("last_seen_at", ascending=False).to_dict("records")]
    for cid, g in dev_usage.groupby("customer_id")
}
print("max devices on one customer:", max(len(v) for v in devices_by_customer.values()))

customer_docs = [
    {
        "_id": r.customer_id,
        "created_at": pd.Timestamp(r.created_at).to_pydatetime(),
        "age": int(r.customer_age),
        "home_city": r.home_city,
        "region": r.region,
        "devices": devices_by_customer.get(r.customer_id, []),
        "is_synthetic": bool(r.is_synthetic),
    }
    for r in customers_df.itertuples(index=False)
]

def tx_doc(r):
    doc = {
        "_id": r["transaction_id"],
        "customer_id": r["customer_id"],
        "device_id": r["device_id"] if isinstance(r["device_id"], str) else None,
        "merchant_id": r["merchant_id"],
        "merchant_category": r["merchant_category"],
        "merchant_location": parse_loc(r["merchant_location"]),
        "customer_location": parse_loc(r["customer_location"]),
        "amount_paise": int(r["amount_paise"]),            # integer paise is authoritative
        "payment_channel": r["payment_channel"],
        "transaction_time": r["transaction_time"].to_pydatetime(),
        "snapshot": {                                      # customer features at event time
            "customer_age": int(r["customer_age"]),
            "account_age_days": int(r["account_age"]),
            "previous_transactions": int(r["previous_transactions"]),
            "average_transaction_value": float(r["average_transaction_value"]),
            "failed_transactions": int(r["failed_transactions"]),
        },
        "label": None if pd.isna(r["fraud_label"]) else {
            "fraud": bool(r["fraud_label"]),
            "source": r["label_source"],
            "available_at": r["label_available_at"].to_pydatetime(),
        },
        "split": r["split"],
        "is_synthetic": bool(r["is_synthetic"]),
    }
    return doc

transaction_docs = [tx_doc(r) for r in tx_df.to_dict("records")]
pprint.pprint(customer_docs[0], sort_dicts=False)
pprint.pprint(transaction_docs[0], sort_dicts=False)


# ==============================================================================
# ## 3. Create the collections (with schema validation) and load them with `insert_many`
#
# Both collections are dropped and recreated so the notebook can be re-run. Only the `_id` index exists at this point. The secondary indexes come in section 5, so that the "before" `explain()` there is a real collection scan.
# ==============================================================================
print()
print("=" * 80, "3. Create the collections (with schema validation) and load them with `insert_many`", "=" * 80, sep=chr(10))
customers_schema = {"$jsonSchema": {
    "bsonType": "object",
    "required": ["_id", "created_at", "region", "devices"],
    "properties": {
        "_id": {"bsonType": "string", "pattern": "^C_"},
        "created_at": {"bsonType": "date"},
        "age": {"bsonType": "int", "minimum": 0},
        "region": {"bsonType": "string"},
        "devices": {"bsonType": "array", "maxItems": 50, "items": {
            "bsonType": "object", "required": ["device_id"],
            "properties": {"device_id": {"bsonType": "string", "pattern": "^D_"},
                           "txn_count": {"bsonType": ["int", "long"]}}}},
    }}}
transactions_schema = {"$jsonSchema": {
    "bsonType": "object",
    "required": ["_id", "customer_id", "amount_paise", "transaction_time", "merchant_category"],
    "properties": {
        "_id": {"bsonType": "string"},
        "customer_id": {"bsonType": "string", "pattern": "^C_"},
        "device_id": {"bsonType": ["string", "null"]},
        "amount_paise": {"bsonType": ["int", "long"], "minimum": 0},
        "transaction_time": {"bsonType": "date"},
        "split": {"enum": LOAD_SPLITS + ["demo"]},     # holdout is rejected at write time
    }}}

for name, schema in [("customers", customers_schema), ("transactions", transactions_schema)]:
    db.drop_collection(name)
    db.create_collection(name, validator=schema, validationLevel="strict")

customers, transactions = db.customers, db.transactions

def load(coll, docs):
    t0 = time.perf_counter()
    for i in range(0, len(docs), BATCH_SIZE):
        coll.insert_many(docs[i:i + BATCH_SIZE], ordered=False)
    print(f"{coll.name}: {coll.estimated_document_count():,} docs in {time.perf_counter() - t0:.1f}s")

load(customers, customer_docs)
load(transactions, transaction_docs)


# ==============================================================================
# ## 4. CRUD operations
# ==============================================================================
print()
print("=" * 80, "4. CRUD operations", "=" * 80, sep=chr(10))

# ==============================================================================
# ### 4.1 `insert_one`: a new customer with one embedded device
# ==============================================================================
print()
print("=" * 80, "4.1 `insert_one`: a new customer with one embedded device", "=" * 80, sep=chr(10))
DEMO_CID, DEMO_DEV = "C_demo000000000001", "D_demo000000000001"
now = datetime.now(timezone.utc).replace(microsecond=0)

res = customers.insert_one({
    "_id": DEMO_CID,
    "created_at": now - timedelta(days=30),
    "age": 29, "home_city": "Pune", "region": "west",
    "devices": [{"device_id": DEMO_DEV, "device_kind": "mobile",
                 "first_seen_at": now - timedelta(days=2), "last_seen_at": now, "txn_count": 4}],
    "is_synthetic": True,
})
print("inserted_id:", res.inserted_id)


# ==============================================================================
# ### 4.2 `insert_many`: four transactions for that customer
# ==============================================================================
print()
print("=" * 80, "4.2 `insert_many`: four transactions for that customer", "=" * 80, sep=chr(10))
pune = {"city": "Pune", "geo": {"type": "Point", "coordinates": [73.86, 18.52]}}
demo_tx = [
    {"_id": f"TX_demo_{i}", "customer_id": DEMO_CID, "device_id": DEMO_DEV, "merchant_id": "M_demo",
     "merchant_category": cat, "merchant_location": pune, "customer_location": pune,
     "amount_paise": amt, "payment_channel": "UPI", "transaction_time": now - timedelta(hours=h),
     "label": None, "split": "demo", "is_synthetic": True}
    for i, (cat, amt, h) in enumerate([("grocery", 45_000, 40), ("gift_cards", 1_500_000, 3),
                                       ("gift_cards", 1_900_000, 2), ("gaming", 800_000, 1)], start=1)
]
res = transactions.insert_many(demo_tx)
print("inserted_ids:", res.inserted_ids)


# ==============================================================================
# ### 4.3 `find` with filters and projection
#
# **(a)** High-value (₹10,000 or more) UPI transactions in the `gift_cards` and `gaming` categories that were labelled fraud. The projection returns only the fields an analyst needs.
# ==============================================================================
print()
print("=" * 80, "4.3 `find` with filters and projection", "=" * 80, sep=chr(10))
query = {
    "merchant_category": {"$in": ["gift_cards", "gaming"]},
    "payment_channel": "UPI",
    "amount_paise": {"$gte": 1_000_000},
    "label.fraud": True,
}
projection = {"_id": 1, "customer_id": 1, "merchant_category": 1, "amount_paise": 1,
              "transaction_time": 1, "merchant_location.city": 1}

print("matching:", transactions.count_documents(query))
print(pd.DataFrame(transactions.find(query, projection).sort("amount_paise", DESCENDING).limit(10)))


# ==============================================================================
# **(b)** Customers in the `south` region with more than one device. The filter is on the embedded array, and the projection returns only the device IDs.
# ==============================================================================
cur = customers.find(
    {"region": "south", "devices.1": {"$exists": True}},      # array has at least 2 elements
    {"home_city": 1, "devices.device_id": 1, "devices.device_kind": 1},
).limit(5)
for c in cur:
    print(c)


# ==============================================================================
# ### 4.4 `update_many`
#
# Investigators confirm that the demo customer's gift-card burst was fraud. One `update_many` sets the label on every matching transaction.
# ==============================================================================
print()
print("=" * 80, "4.4 `update_many`", "=" * 80, sep=chr(10))
res = transactions.update_many(
    {"customer_id": DEMO_CID, "merchant_category": "gift_cards"},
    {"$set": {"label": {"fraud": True, "source": "demo_investigator_confirmed", "available_at": now}}},
)
print(f"matched={res.matched_count} modified={res.modified_count}")
pprint.pprint(list(transactions.find({"customer_id": DEMO_CID}, {"merchant_category": 1, "amount_paise": 1, "label.fraud": 1})))


# ==============================================================================
# ### 4.5 `delete_one`: remove the grocery transaction that was entered by mistake
# ==============================================================================
print()
print("=" * 80, "4.5 `delete_one`: remove the grocery transaction that was entered by mistake", "=" * 80, sep=chr(10))
res = transactions.delete_one({"customer_id": DEMO_CID, "merchant_category": "grocery"})
print("deleted_count:", res.deleted_count)
print("remaining demo txns:", transactions.count_documents({"customer_id": DEMO_CID}))


# ==============================================================================
# ## 5. Indexes and `explain()`: before and after
#
# **Query under test:** *"this customer's transactions in the last 30 days of their history, newest first"*. This is the history lookup a fraud scorer runs on every payment.
# ==============================================================================
print()
print("=" * 80, "5. Indexes and `explain()`: before and after", "=" * 80, sep=chr(10))
# Pick a busy real customer and the window ending at their latest transaction.
busy = next(transactions.aggregate([
    {"$match": {"split": {"$ne": "demo"}}},
    {"$group": {"_id": "$customer_id", "n": {"$sum": 1}, "last": {"$max": "$transaction_time"}}},
    {"$sort": {"n": -1}}, {"$limit": 1}]))
CID, SINCE = busy["_id"], busy["last"] - timedelta(days=30)
print(f"customer {CID}: {busy['n']} txns, window since {SINCE:%Y-%m-%d %H:%M}")

def run_query():
    return (transactions.find({"customer_id": CID, "transaction_time": {"$gte": SINCE}},
                              {"amount_paise": 1, "transaction_time": 1, "merchant_category": 1})
                        .sort("transaction_time", DESCENDING))

def plan_stages(node):
    # Flatten the winning plan tree into e.g. 'PROJECTION_SIMPLE <- SORT <- COLLSCAN'
    out = []
    while node:
        s = node["stage"]
        if "indexName" in node:
            s += f"({node['indexName']})"
        out.append(s)
        node = node.get("inputStage") or (node.get("inputStages") or [None])[0]
    return " <- ".join(out)

def explain_summary(label):
    ex = run_query().explain()
    st = ex["executionStats"]
    qp = ex["queryPlanner"]["winningPlan"]
    qp = qp.get("queryPlan", qp)                    # SBE engine nests the plan under queryPlan
    row = {"case": label, "winning_plan": plan_stages(qp), "nReturned": st["nReturned"],
           "totalKeysExamined": st["totalKeysExamined"], "totalDocsExamined": st["totalDocsExamined"],
           "executionTimeMillis": st["executionTimeMillis"]}
    pprint.pprint(row, sort_dicts=False)
    return row

print("indexes now:", list(transactions.index_information()))
results = [explain_summary("BEFORE: no secondary indexes")]


# ==============================================================================
# Now create the two indexes the task asks for: one on `customer_id` and one on `transaction_time`.
# ==============================================================================
transactions.create_index([("customer_id", ASCENDING)], name="customer_id_1")
transactions.create_index([("transaction_time", ASCENDING)], name="transaction_time_1")
# customers._id *is* customer_id, so that collection already has its customer_id index.
print("indexes now:", list(transactions.index_information()))
results.append(explain_summary("AFTER: customer_id_1 + transaction_time_1"))


# ==============================================================================
# With two single-field indexes, the planner chooses `customer_id_1`, because equality on a customer is far more selective than a 30-day time range. It still has to filter on time and run an in-memory `SORT`. A **compound** index following the ESR rule (Equality, then Sort/Range: `{customer_id: 1, transaction_time: -1}`) serves the equality, the range and the sort from a single index scan.
# ==============================================================================
transactions.create_index([("customer_id", ASCENDING), ("transaction_time", DESCENDING)],
                          name="customer_id_1_transaction_time_-1")
results.append(explain_summary("AFTER: + compound customer_id_1_transaction_time_-1"))
print(pd.DataFrame(results).set_index("case"))


# ==============================================================================
# The full `explain()` document for the final plan, trimmed to the planner section:
# ==============================================================================
pprint.pprint(run_query().explain()["queryPlanner"]["winningPlan"], width=110)


# ==============================================================================
# ## 6. Aggregation pipelines
#
# ### 6.1 Fraud rate per `merchant_category`
#
# Only transactions with a label are counted. The rate is `fraud / labelled`.
# ==============================================================================
print()
print("=" * 80, "6. Aggregation pipelines", "=" * 80, sep=chr(10))
print()
print("=" * 80, "6.1 Fraud rate per `merchant_category`", "=" * 80, sep=chr(10))
fraud_rate_pipeline = [
    {"$match": {"label": {"$ne": None}}},
    {"$group": {
        "_id": "$merchant_category",
        "transactions": {"$sum": 1},
        "fraud": {"$sum": {"$cond": ["$label.fraud", 1, 0]}},
        "fraud_amount_paise": {"$sum": {"$cond": ["$label.fraud", "$amount_paise", 0]}},
    }},
    {"$project": {
        "_id": 0, "merchant_category": "$_id", "transactions": 1, "fraud": 1,
        "fraud_rate_pct": {"$round": [{"$multiply": [{"$divide": ["$fraud", "$transactions"]}, 100]}, 3]},
        "fraud_amount_inr": {"$round": [{"$divide": ["$fraud_amount_paise", 100]}, 2]},
    }},
    {"$sort": {"fraud_rate_pct": -1}},
]
print(pd.DataFrame(transactions.aggregate(fraud_rate_pipeline)))


# ==============================================================================
# ### 6.2 Top 10 customers by amount in their last 24 hours of activity
#
# "Last 24 hours of activity" is a different window for each customer: the 24 hours ending at **that customer's** most recent transaction. A single global "now minus 24h" would not work here, because the loaded splits end in December 2025 and most customers are idle at the very end.
#
# 1. `$group` finds each customer's `last_txn_at`.
# 2. `$lookup` (with a sub-pipeline) fetches that customer's transactions in `[last_txn_at − 24h, last_txn_at]`. It uses the compound `customer_id_1_transaction_time_-1` index from section 5.
# 3. Sum, sort, keep the top 10, and join the customer profile.
# ==============================================================================
print()
print("=" * 80, "6.2 Top 10 customers by amount in their last 24 hours of activity", "=" * 80, sep=chr(10))
top_24h_pipeline = [
    {"$group": {"_id": "$customer_id", "last_txn_at": {"$max": "$transaction_time"}}},
    {"$lookup": {
        "from": "transactions",
        "let": {"cid": "$_id", "end": "$last_txn_at",
                "start": {"$dateSubtract": {"startDate": "$last_txn_at", "unit": "hour", "amount": 24}}},
        "pipeline": [
            {"$match": {"$expr": {"$and": [
                {"$eq": ["$customer_id", "$$cid"]},
                {"$gte": ["$transaction_time", "$$start"]},
                {"$lte": ["$transaction_time", "$$end"]}]}}},
            {"$group": {"_id": None, "amount_paise": {"$sum": "$amount_paise"}, "txns": {"$sum": 1},
                        "categories": {"$addToSet": "$merchant_category"}}},
        ],
        "as": "w",
    }},
    {"$unwind": "$w"},
    {"$sort": {"w.amount_paise": -1}},
    {"$limit": 10},
    {"$lookup": {"from": "customers", "localField": "_id", "foreignField": "_id", "as": "c"}},
    {"$unwind": {"path": "$c", "preserveNullAndEmptyArrays": True}},
    {"$project": {
        "_id": 0, "customer_id": "$_id", "home_city": "$c.home_city", "region": "$c.region",
        "window_start": {"$dateSubtract": {"startDate": "$last_txn_at", "unit": "hour", "amount": 24}},
        "last_txn_at": 1, "txns_24h": "$w.txns",
        "amount_24h_inr": {"$round": [{"$divide": ["$w.amount_paise", 100]}, 2]},
        "categories": "$w.categories",
    }},
]
t0 = time.perf_counter()
top10 = pd.DataFrame(transactions.aggregate(top_24h_pipeline, allowDiskUse=True))
top10 = top10[["customer_id", "home_city", "region", "window_start", "last_txn_at", "txns_24h", "amount_24h_inr", "categories"]]
print(f"{time.perf_counter() - t0:.1f}s")
print(top10)


# ==============================================================================
# ## 7. Clean up the demo documents (optional)
# ==============================================================================
print()
print("=" * 80, "7. Clean up the demo documents (optional)", "=" * 80, sep=chr(10))
print("customers deleted:", customers.delete_many({"_id": DEMO_CID}).deleted_count)
print("transactions deleted:", transactions.delete_many({"customer_id": DEMO_CID}).deleted_count)
for name in ("customers", "transactions"):
    s = db.command("collStats", name)
    print(f"{name:13s} docs={s['count']:>9,}  data={s['size']/1e6:7.1f} MB  "
          f"storage={s['storageSize']/1e6:6.1f} MB  indexes={s['totalIndexSize']/1e6:5.1f} MB")


# ==============================================================================
# ## 8. Drop the database (optional, irreversible)
#
# This deletes the whole `SENTINEL_DB` database (`sentinel` by default): both collections, their indexes and their validators. Use it to free space on the cluster when you are finished. It cannot be undone, but the data can be rebuilt at any time by running the notebook again.
#
# As a safety guard, the cell does nothing unless `DROP_DATABASE=true` is set in `.env` or in the environment. Then **Run All** never wipes the data by accident. You can also set `DROP_DATABASE = True` in the cell below and run just that cell.
# ==============================================================================
print()
print("=" * 80, "8. Drop the database (optional, irreversible)", "=" * 80, sep=chr(10))
#DROP_DATABASE = os.environ.get("DROP_DATABASE", "false").strip().lower() in ("1", "true", "yes")
DROP_DATABASE = os.environ.get("DROP_DATABASE", "false").strip().lower() in ("1", "true", "yes")
print(f"database '{DB_NAME}' collections:", db.list_collection_names())
if DROP_DATABASE:
    client.drop_database(DB_NAME)
    print(f"dropped database '{DB_NAME}'")
    print(f"'{DB_NAME}' still exists:", DB_NAME in client.list_database_names())
else:
    print("DROP_DATABASE is not set, so the database was kept. Set DROP_DATABASE=true to drop it.")

