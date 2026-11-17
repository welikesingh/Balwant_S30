<!-- 
Load SENTINEL entities into Neo4j and find patterns that are hard to see in tables.

WHAT TO BUILD
1. Run Neo4j locally with Docker (ports 7474 and 7687) or on Aura, and connect from Python with the neo4j driver (verify_connectivity).

2 Create Customer, Device and Merchant nodes and 
the relationships USED_DEVICE and PAID (with amount, time and fraud_label on the PAID edge) from a sample of at least 5,000 transactions. Use the SENTINEL data from data dir. A sample of a few thousand rows is enough where the task says so.

3 Use MERGE, not CREATE, so the load can run twice without duplicates. Add uniqueness constraints on the ids.

4 Write Cypher for: devices shared by 3 or more customers in 7 days; customers within 2 hops of a fraud-labelled payment; and the merchants most often paid from shared devices.


Try to write code as human understandable instead of AI generated. Also create a ipynb file so that demonstration can be easy. create a readme file with objective of project and donot add unwanted details in this. Keep it simple and concise
 -->



# SENTINEL Graph: Customers, Devices and Merchants in Neo4j

## Objective

Load SENTINEL payment data into Neo4j as a graph and find fraud patterns that are hard to see in tables:

- devices shared by 3 or more customers within 7 days
- customers within 2 hops of a fraud-labelled payment
- merchants most often paid from shared devices

## Graph model

```
(:Customer)-[:USED_DEVICE]->(:Device)
(:Customer)-[:PAID {transaction_id, amount, time, fraud_label}]->(:Merchant)
```

The load uses `MERGE`, so you can run it again without creating duplicates. Uniqueness constraints are set on `customer_id`, `device_id`, `merchant_id` and `PAID.transaction_id`.

## Data

The data comes from `data/tables/` (customers, devices, merchants, transactions and labels). The sample is a continuous 14-day window of train transactions, from 2025-03-01 to 2025-03-14 (31,937 payments, 190 of them fraud). A random sample would split up the customers who share a device, so the sample uses a time window instead.

## Files

| File | Purpose |
|---|---|
| `docker-compose.yml` | Neo4j 5 on ports 7474 (browser) and 7687 (bolt) |
| `graph_loader.py` | Reads the sample, creates constraints, loads nodes and edges |
| `queries.py` | The three pattern queries in Cypher |
| `sentinel_graph_demo.ipynb` | Step-by-step demo with results |

## Neo4j login

| Setting | Value |
|---|---|
| Browser | http://localhost:7474 |
| Bolt URI | `bolt://localhost:7687` |
| User | `neo4j` |
| Password | `sentinel123` |

The password is set in `docker-compose.yml` (`NEO4J_AUTH`) and used as the default in `graph_loader.py`. If you change it in one place, change it in the other too, or set the `NEO4J_PASSWORD` environment variable.

## How to run

```bash
docker compose up -d              # Neo4j at http://localhost:7474 (neo4j / sentinel123)
pip install -r requirements.txt
python graph_loader.py            # load the graph (safe to run twice)
python queries.py                 # print the query results
```

Or open `sentinel_graph_demo.ipynb` and run all cells.

To use Neo4j Aura instead, set `NEO4J_URI`, `NEO4J_USER` and `NEO4J_PASSWORD`.
