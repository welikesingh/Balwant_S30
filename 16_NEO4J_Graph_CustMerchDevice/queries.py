"""
Pattern queries on the SENTINEL graph. Run graph_loader.py first.
"""
import pandas as pd

from graph_loader import connect

# 1. Devices shared by 3 or more customers within any 7-day window.
#    Every day a device was used is tried as the start of a window; we keep
#    the busiest window per device.
SHARED_DEVICES_7D = """
MATCH (:Customer)-[u:USED_DEVICE]->(d:Device)
UNWIND u.days AS day
WITH d, collect(DISTINCT day) AS start_days
UNWIND start_days AS window_start
MATCH (c:Customer)-[u:USED_DEVICE]->(d)
WHERE any(day IN u.days WHERE window_start <= day < window_start + duration({days: 7}))
WITH d, window_start, collect(DISTINCT c.customer_id) AS customers
WHERE size(customers) >= $min_customers
ORDER BY size(customers) DESC, window_start
WITH d, collect({start: window_start, customers: customers})[0] AS busiest
RETURN d.device_id               AS device_id,
       d.kind                    AS device_kind,
       busiest.start             AS window_start,
       size(busiest.customers)   AS customers_in_7d,
       busiest.customers         AS customer_ids
ORDER BY customers_in_7d DESC, device_id
"""

# 2. Customers within 2 hops of a fraud-labelled payment.
#    Start from the customer who made the fraud payment and walk up to two
#    hops over USED_DEVICE or PAID. Two hops reach another customer either
#    through a shared device or through a shared merchant.
NEAR_FRAUD_CUSTOMERS = """
MATCH (fraudster:Customer)-[:PAID {fraud_label: 1}]->(:Merchant)
WITH DISTINCT fraudster
MATCH (fraudster)-[:USED_DEVICE|PAID]-(link)-[:USED_DEVICE|PAID]-(c:Customer)
WHERE c <> fraudster
WITH c,
     collect(DISTINCT fraudster.customer_id)                            AS fraud_customers,
     collect(DISTINCT CASE WHEN link:Device THEN link.device_id END)     AS via_devices,
     collect(DISTINCT CASE WHEN link:Merchant THEN link.merchant_id END) AS via_merchants
OPTIONAL MATCH (c)-[own:PAID {fraud_label: 1}]->()
RETURN c.customer_id         AS customer_id,
       size(fraud_customers) AS linked_fraud_customers,
       size(via_devices)     AS shared_devices,
       size(via_merchants)   AS shared_merchants,
       count(own) > 0        AS has_own_fraud,
       via_devices
ORDER BY shared_devices DESC, linked_fraud_customers DESC, customer_id
"""

# 3. Merchants most often paid from shared devices
#    (a shared device = used by 3+ customers in the loaded sample).
MERCHANTS_FROM_SHARED_DEVICES = """
MATCH (c:Customer)-[:USED_DEVICE]->(d:Device)
WITH d, count(DISTINCT c) AS n_customers
WHERE n_customers >= $min_customers
WITH collect(d.device_id) AS shared_device_ids
MATCH (:Customer)-[p:PAID]->(m:Merchant)
WHERE p.device_id IN shared_device_ids
RETURN m.merchant_id                AS merchant_id,
       m.name                       AS merchant_name,
       m.category                   AS category,
       count(p)                     AS payments_from_shared,
       count(DISTINCT p.device_id)  AS shared_devices,
       sum(p.fraud_label)           AS fraud_payments,
       round(sum(p.amount), 2)      AS total_amount
ORDER BY payments_from_shared DESC
LIMIT $top_n
"""


def run(driver, cypher, **params):
    records, _, _ = driver.execute_query(cypher, **params)
    return pd.DataFrame([r.data() for r in records])


def shared_devices_7d(driver, min_customers=3):
    return run(driver, SHARED_DEVICES_7D, min_customers=min_customers)


def customers_near_fraud(driver):
    return run(driver, NEAR_FRAUD_CUSTOMERS)


def merchants_from_shared_devices(driver, min_customers=3, top_n=15):
    return run(driver, MERCHANTS_FROM_SHARED_DEVICES, min_customers=min_customers, top_n=top_n)


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    pd.set_option("display.max_colwidth", 60)

    with connect() as driver:
        shared = shared_devices_7d(driver)
        print(f"\n1) Devices shared by 3+ customers in 7 days: {len(shared)}")
        print(shared.drop(columns="customer_ids").head(10).to_string(index=False))

        near = customers_near_fraud(driver)
        print(f"\n2) Customers within 2 hops of a fraud payment: {len(near)} "
              f"({(near['shared_devices'] > 0).sum()} of them through a shared device)")
        print(near.drop(columns="via_devices").head(10).to_string(index=False))

        top = merchants_from_shared_devices(driver)
        print("\n3) Merchants most often paid from shared devices")
        print(top.to_string(index=False))
