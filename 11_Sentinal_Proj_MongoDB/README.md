# SENTINEL on MongoDB Atlas: `customers` and `transactions`

`sentinel_mongodb.ipynb` loads the SENTINEL synthetic dataset from the local `data/` folder into two MongoDB collections. It then demonstrates CRUD operations, indexes with `explain()` before and after, and two aggregation pipelines.

| Collection | One document per | `_id` | Devices | Relationships |
|---|---|---|---|---|
| `customers` | payer | `customer_id` | **embedded** array `devices[]` | none |
| `transactions` | payment attempt | `transaction_id` | **referenced** by `device_id` | `customer_id` references `customers._id` |

## How to run

The same steps ship two ways: as the notebook `sentinel_mongodb.ipynb` and as the plain script `sentinel_mongodb.py`. Both do exactly the same thing. Choose one.

### Setup (both options)

1. In Atlas, go to **Network Access** and add your IP address. Then go to **Database Access** and create a database user.
2. In Atlas, choose **Connect → Drivers** and copy the `mongodb+srv://...` connection string.
3. Install the packages (Python 3.10 or later):

   ```powershell
   cd C:\tmp\sentinel\MONGO_DB_COLLECTION
   pip install -r requirements.txt
   ```

4. Create `.env` from the template and put your connection string in it:

   ```powershell
   copy .env.example .env
   notepad .env        # set MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.xxxxx.mongodb.net/
   ```

   If the password contains special characters such as `@ : / ? #`, URL-encode them (for example `@` becomes `%40`).

### Option A: Jupyter notebook

```powershell
jupyter notebook sentinel_mongodb.ipynb
```

Then choose **Run → Run All Cells**. In VS Code, open the `.ipynb` file, pick a Python kernel, and click **Run All**.

### Option B: Python script

```powershell
python sentinel_mongodb.py
```

The script prints each section's heading followed by its results: load counts, CRUD results, the three `explain()` summaries and both aggregation tables. To keep a copy of the output:

```powershell
python sentinel_mongodb.py > run_output.txt
```

The script locates `.env` and `data/` relative to its own folder, so it can be started from any directory. Settings can also be passed as environment variables instead of `.env`. Values already set in the environment take precedence over `.env`:

```powershell
$env:SAMPLE_CUSTOMERS = "all"     # PowerShell: load the full dataset for this run
python sentinel_mongodb.py
```

```bash
SAMPLE_CUSTOMERS=all python sentinel_mongodb.py      # bash / macOS / Linux
```

### Settings

| Setting | Default | Meaning |
|---|---|---|
| `MONGODB_URI` | required | Atlas SRV connection string |
| `SENTINEL_DB` | `sentinel` | target database |
| `SENTINEL_DATA` | `data` | dataset folder containing `tables/`. Set `../sentinel_data` to read the original instead |
| `SAMPLE_CUSTOMERS` | `2000` | random sample of customers (seed 42). `all` loads all 25,000 |
| `DROP_DATABASE` | `false` | `true` makes the final step drop the whole `SENTINEL_DB` database (irreversible) |

The notebook **drops and recreates** both collections on every run.

### Dropping the database when you are done

The last step (section 8) can delete the whole `SENTINEL_DB` database: both collections, their indexes and their validators. It frees the space on your cluster, which matters on the 512 MB M0 tier. **This is irreversible**, but the data can be rebuilt at any time by running the notebook or script again.

As a guard, the step only drops the database when `DROP_DATABASE=true`. With the default (`false`), **Run All** loads and demonstrates everything, then prints `DROP_DATABASE is not set, so the database was kept.`

To drop the database:

- **Notebook:** set `DROP_DATABASE=true` in `.env` and run all cells. To drop it without reloading, run sections 0 and 8 only (section 8 needs the `client` connection from section 0). Alternatively, edit the cell to `DROP_DATABASE = True` and run it.
- **Script:** run it with the flag set. The script reloads everything and then drops it at the end.

  ```powershell
  $env:DROP_DATABASE = "true"; python sentinel_mongodb.py; Remove-Item Env:DROP_DATABASE
  ```

- **Directly, without the notebook:** in `mongosh` or the Atlas UI (**Browse Collections → sentinel → Drop Database**):

  ```powershell
  mongosh "<your MONGODB_URI>" --eval "db.getSiblingDB('sentinel').dropDatabase()"
  ```

Expected output when the drop runs:

```text
database 'sentinel' collections: ['customers', 'transactions']
dropped database 'sentinel'
'sentinel' still exists: False
```

**Sizing** (measured on a test run against MongoDB 8.0):

| Load | customers | transactions | transaction data / on disk / indexes | Load time (local) |
|---|---|---|---|---|
| `SAMPLE_CUSTOMERS=2000` | 2,000 | 76,574 | 53 MB / small / 2 MB | ~2 s |
| `SAMPLE_CUSTOMERS=all` | 25,000 | 959,548 | 666 MB / 132 MB / 44 MB | ~30 s |

The M0 free tier has a 512 MB quota, so keep the 2,000-customer sample there. Use M10 or larger for the full load. Loading over the internet to Atlas takes longer than the local times above.

**Splits.** Only the `warmup`, `train` and `validation` splits are loaded. `holdout` (January to February 2026) is the blind evaluation window. Keeping it off the cluster stops it leaking into analysis by accident. The `transactions` validator rejects `split: "holdout"`.

## The `data/` folder

`data/` holds a copy of exactly the files the notebook loads, taken from `../sentinel_data`, so this folder is self-contained. Only the compressed `*.csv.gz` parts were copied. Each file's MD5 checksum was verified against its original.

```text
data/
├── DATA_CARD.md                       dataset card (scope, splits, caveats)
└── tables/
    ├── customers/all/          5 files   516 KB   -> customers collection
    ├── devices/all/           21 files   1.2 MB   -> embedded customers.devices[].device_kind
    ├── merchants/all/          1 file     40 KB   read (reference data; category and location are already on each transaction)
    ├── transactions/warmup/   20 files   5.8 MB   -> transactions collection
    ├── transactions/train/   143 files    42 MB   -> transactions collection
    ├── transactions/validation/ 29 files 8.5 MB   -> transactions collection
    ├── labels/warmup/         20 files   1.1 MB   -> transactions.label
    ├── labels/train/         143 files   7.4 MB   -> transactions.label
    └── labels/validation/     29 files   1.5 MB   -> transactions.label
                                          68 MB total
```

**Not copied:**
- the `holdout` split, which is never loaded (see **Splits** above)
- stray uncompressed duplicates (`part-00003.csv/`, `.zip`)
- tables the notebook doesn't use (documents, features, decision_audit, and others)

To refresh the copy after the source changes, run this from this folder (PowerShell):

```powershell
foreach ($t in "customers","devices","merchants") {
  New-Item -ItemType Directory -Force "data\tables\$t\all" | Out-Null
  Copy-Item "..\sentinel_data\tables\$t\all\*.csv.gz" "data\tables\$t\all\" }
foreach ($t in "transactions","labels") { foreach ($s in "warmup","train","validation") {
  New-Item -ItemType Directory -Force "data\tables\$t\$s" | Out-Null
  Copy-Item "..\sentinel_data\tables\$t\$s\*.csv.gz" "data\tables\$t\$s\" } }
```

## Document shapes

```js
// customers
{
  _id: "C_ef13d0be3f91f70c",
  created_at: ISODate("2020-06-27T18:30:00Z"),
  age: 60, home_city: "Jaipur", region: "north", is_synthetic: true,
  devices: [                                   // 1-8 entries in this data
    { device_id: "D_c90626db699cc2ed", device_kind: "browser",
      first_seen_at: ISODate("2024-11-18T12:52:54Z"),
      last_seen_at:  ISODate("2025-12-14T08:01:18Z"), txn_count: 30 },
    { device_id: "D_8d335dc9de5ce518", device_kind: "mobile", ... }
  ]
}

// transactions
{
  _id: "TX_0000000001",
  customer_id: "C_8fb90ed8a623338e",           // reference -> customers._id
  device_id:   "D_e0959777859c7272",           // reference -> customers.devices.device_id
  merchant_id: "M_de33bf6b5f3b23e0",
  merchant_category: "grocery",                // copied in from merchants: filtered on constantly
  merchant_location: { city: "Kolkata", geo: { type: "Point", coordinates: [88.36, 22.57] } },
  customer_location: { city: "Jamshedpur", geo: { type: "Point", coordinates: [86.2, 22.8] } },
  amount_paise: 124087,                        // integer paise is authoritative; INR = /100
  payment_channel: "card",
  transaction_time: ISODate("2024-09-30T18:30:13.992Z"),
  snapshot: { customer_age: 34, account_age_days: 1668, previous_transactions: 0,
              average_transaction_value: NaN, failed_transactions: 0 },
  label: { fraud: false, source: "mature_no_fraud", available_at: ISODate(...) },
  split: "warmup", is_synthetic: true
}
```

## Why embed devices, and why reference from transactions

### Devices are embedded in `customers`

1. **Bounded, small cardinality.** Customers use 1 to 8 devices across the whole dataset. That is a short array that will not grow without limit, so the document stays at a few hundred bytes, far below the 16 MB document limit. The validator caps the array at 50 as a guard.
2. **Read together.** The main question about devices is *"is this a device we have seen for this customer before, and how recently?"* That question is always asked in the context of one customer. With the devices embedded, it is answered in a single read by `_id`, with no `$lookup`.
3. **Device data is tiny and owned by the relationship.** The source `devices` table has only `device_id` and `device_kind`. The useful facts (`first_seen_at`, `last_seen_at`, `txn_count`) describe the *customer and device pair*. They only make sense inside the customer, so a separate `devices` collection would hold almost nothing.
4. **Atomic updates.** One `update_one` on the customer document can add a new device or bump `last_seen_at` and `txn_count`, using `$push`, `$set` and the positional `$` operator. Single-document writes are atomic without a transaction.

Trade-off: a device shared by several customers is a strong fraud signal, and that device would appear inside several customer documents. The question *"which customers share this device?"* is answered with a multikey index on `devices.device_id` (or from `transactions.device_id`), not by a device document. That is a rare investigative query, so the cost is acceptable.

### Transactions reference their customer (and device)

1. **Unbounded growth.** Customers have up to about 100 transactions in this data, and in production the count grows forever. Embedding transactions in `customers` would create ever-growing documents. Every new payment would rewrite a large document, and eventually the 16 MB limit would be hit. Transactions are the high-volume, append-only entity, so they get their own collection.
2. **Independent access patterns.** Analytics (fraud rate per category, time-window scans, aggregations across all customers) work on transactions directly. They should not have to `$unwind` arrays out of customer documents.
3. **Index-friendly lookups.** `customer_id` plus the compound index `{customer_id: 1, transaction_time: -1}` makes *"this customer's recent history"* a tight index range scan. That is all the reference costs.
4. **Selective denormalisation.** `merchant_category` and the merchant location are copied into each transaction instead of referenced, because nearly every fraud query groups or filters on them. Merchants are small, slow-changing reference data. The point-in-time customer features (`snapshot`) are also copied in, because they must reflect the values *at event time* rather than the customer's current profile.

## What the notebook demonstrates

| Section | Operation | Example |
|---|---|---|
| 3 | `insert_many` | bulk load in batches of 5,000, `ordered=False` |
| 4.1 | `insert_one` | a demo customer with one embedded device |
| 4.2 | `insert_many` | four demo transactions for that customer |
| 4.3 | `find` + filter + projection | fraud-labelled UPI gift-card or gaming payments of ₹10,000 or more; customers with 2 or more devices (`"devices.1": {$exists: true}`) |
| 4.4 | `update_many` | label the demo customer's gift-card transactions as fraud |
| 4.5 | `delete_one` | delete one mistaken demo transaction |
| 5 | `create_index` + `explain()` | before and after (see below) |
| 6.1 | aggregation | fraud rate per `merchant_category` |
| 6.2 | aggregation | top 10 customers by amount in their last 24 h of activity |
| 7 | `delete_many` | remove the demo documents, then print collection sizes |
| 8 | `drop_database` | drop the whole database, only when `DROP_DATABASE=true` |

### Indexes and `explain()`

Query: *one customer's transactions in the last 30 days of their history, newest first*.

```python
transactions.find({"customer_id": CID, "transaction_time": {"$gte": SINCE}}).sort("transaction_time", -1)
```

Results from the full-data test run (959,548 transactions):

| Indexes present | Winning plan | Keys examined | Docs examined | Time |
|---|---|---|---|---|
| `_id` only (**before**) | `COLLSCAN` → `SORT` | 0 | 959,551 | 718 ms |
| `customer_id_1`, `transaction_time_1` (**after**) | `IXSCAN(customer_id_1)` → `FETCH` → `SORT` | 102 | 102 | 7 ms |
| + `customer_id_1_transaction_time_-1` | `IXSCAN(compound)` → `FETCH` (no `SORT`) | 2 | 2 | 1 ms |

The two single-field indexes asked for in the task already remove the collection scan. The planner picks `customer_id_1`, because equality on one customer is much more selective than a time range. It still filters by time and sorts in memory. The compound index follows the **ESR rule** (Equality, Sort, Range). It reads exactly the matching keys, already in order. The notebook keeps the compound index because the 24-hour pipeline also relies on it. In `customers`, `customer_id` *is* `_id`, so that collection is indexed by default.

### Aggregation 1: fraud rate per `merchant_category`

`$match` labelled transactions → `$group` by category (count, fraud count, fraud amount) → `$project` the rate → `$sort`. On the full data, `gift_cards` (2.68 %), `gaming` (2.07 %) and `electronics` (1.52 %) stand far above every other category, all of which are at about 0.03 %.

### Aggregation 2: top 10 customers by amount in their last 24 hours of activity

"Last 24 hours of activity" is a **per-customer** window: the 24 hours ending at that customer's own most recent transaction. A global "now minus 24 h" would return almost nothing, because the loaded data ends in December 2025.

1. `$group` by `customer_id` → `last_txn_at = $max(transaction_time)`
2. `$lookup` with a correlated sub-pipeline: the same customer's transactions with `transaction_time` in `[last_txn_at − 24h, last_txn_at]`, summed. This uses the compound index.
3. `$sort` by the 24-hour amount, `$limit 10`, then `$lookup` the customer profile.

Amounts are summed from `amount_paise` and shown in INR. The SENTINEL authorisation histories include failed attempts, so this figure is "attempted amount", not settled value.

## Files

| File | Purpose |
|---|---|
| `sentinel_mongodb.ipynb` | the notebook |
| `sentinel_mongodb.py` | the same steps as a plain Python script (`python sentinel_mongodb.py`) |
| `requirements.txt` | `pymongo`, `pandas`, `jupyter` |
| `.env.example` | settings template (copy to `.env`), including `DROP_DATABASE` |
| `data/` | the source files that get loaded (copied from `../sentinel_data`, see below) |
| `.gitignore` | keeps `.env` (credentials), `data/` (68 MB source copy) and `run_output.txt` out of version control |

All data is synthetic (see `data/DATA_CARD.md`). Fraud labels are sampled, not real outcomes.

## Loaded data summary (Atlas run, 2026-10-28)

These are the results of running `python sentinel_mongodb.py` against the Atlas cluster with `SAMPLE_CUSTOMERS=2000`. For this run, `DROP_DATABASE=false` was set in the environment so the data would stay on the cluster. The run finished without errors, and the demo documents from section 4 were cleaned up (none remain).

**Target:** database `SentinelDB` on MongoDB 8.0.34 (Atlas). Load time over the internet: customers 3.9 s, transactions 51 s.

### Collections

| Collection | Documents | Avg doc size | Data size | Storage (compressed) | Index size | Indexes |
|---|---|---|---|---|---|---|
| `customers` | 2,000 | 428 B | 0.9 MB | 0.3 MB | 0.1 MB | `_id_` |
| `transactions` | 76,574 | 694 B | 53.2 MB | 7.5 MB | 4.1 MB | `_id_`, `customer_id_1`, `transaction_time_1`, `customer_id_1_transaction_time_-1` |

### Transactions by split

Times are UTC; the IST calendar starts 5½ hours later.

| Split | Transactions | From | To | Amount (INR) | Fraud | Fraud rate |
|---|---|---|---|---|---|---|
| `warmup` | 8,027 | 2024-09-30 19:45 | 2024-12-31 18:04 | 3,46,85,900.79 | 49 | 0.61 % |
| `train` | 57,192 | 2024-12-31 19:01 | 2025-10-31 18:05 | 22,71,14,937.15 | 360 | 0.63 % |
| `validation` | 11,355 | 2025-10-31 19:36 | 2025-12-31 18:07 | 3,64,42,389.63 | 68 | 0.60 % |
| **Total** | **76,574** | 2024-09-30 | 2025-12-31 | **29,82,43,227.57** | **477** | **0.62 %** |

The holdout split was not loaded, as intended. Every loaded transaction has a label:

| Label source | Transactions |
|---|---|
| `mature_no_fraud` | 76,097 |
| `investigator_verdict` (fraud) | 371 |
| `confirmed_chargeback` (fraud) | 106 |

### Transaction profile

| Measure | Value |
|---|---|
| Distinct customers with transactions | 1,942 of 2,000 (58 sampled customers have no transactions in the loaded splits, so their `devices` array is empty) |
| Distinct merchants | 2,000 |
| Distinct devices | 4,086 (843 transactions have no `device_id`) |
| Transactions per active customer | min 1, avg 39.4, max 93 |
| Amount per transaction | avg ₹3,894.84, max ₹76,82,203.64 |

| Payment channel | Transactions | Fraud | Fraud rate |
|---|---|---|---|
| UPI | 44,460 | 249 | 0.56 % |
| card | 23,743 | 168 | 0.71 % |
| wallet | 5,341 | 41 | 0.77 % |
| net_banking | 3,030 | 19 | 0.63 % |

### Customers and embedded devices

| Measure | Value |
|---|---|
| Age | 18 to 80, average 48.9 |
| Account `created_at` | 2019-12-31 to 2026-02-25 |
| Home cities | 16 |
| Region | south 523, east 495, north 380, west 345, central 132, northeast 125 |
| Embedded device entries | 4,682 (mobile 2,582, browser 2,100) over 4,086 distinct devices |
| Devices per customer | 0: 58 · 1: 389 · 2: 733 · 3: 526 · 4: 232 · 5: 52 · 6: 9 · 7: 1 |
| Devices shared by more than one customer | 119; the most widely shared device appears in 13 customers' `devices` arrays |

The 119 shared devices are the trade-off of embedding noted in the design section. A query for "which customers share a device" has to look across customer documents; a multikey index on `devices.device_id` would serve it.

### Query and aggregation results on Atlas

`explain()` for one customer's last 30 days (customer `C_a3d0457235940892`, 93 transactions, 18 in the window):

| Indexes | Winning plan | Keys examined | Docs examined | Time |
|---|---|---|---|---|
| `_id` only (before) | `COLLSCAN` → `SORT` | 0 | 76,577 | 62 ms |
| `customer_id_1` + `transaction_time_1` (after) | `IXSCAN(customer_id_1)` → `SORT` | 93 | 93 | 3 ms |
| + compound index | `IXSCAN(customer_id_1_transaction_time_-1)` | 18 | 18 | 1 ms |

Fraud rate per `merchant_category`:

| Category | Transactions | Fraud | Fraud rate | Fraud amount (INR) |
|---|---|---|---|---|
| gift_cards | 5,483 | 148 | 2.699 % | 5,94,946.72 |
| gaming | 7,317 | 156 | 2.132 % | 10,42,660.04 |
| electronics | 10,157 | 160 | 1.575 % | 8,82,905.00 |
| healthcare | 5,124 | 3 | 0.059 % | 11,502.66 |
| travel | 4,353 | 2 | 0.046 % | 2,286.98 |
| food | 10,143 | 4 | 0.039 % | 4,127.03 |
| grocery | 14,180 | 5 | 0.035 % | 11,246.58 |
| quick_commerce | 11,674 | 1 | 0.009 % | 719.45 |
| education | 4,481 | 0 | 0.000 % | 0.00 |
| other | 3,664 | 0 | 0.000 % | 0.00 |

Top 10 customers by amount in their last 24 hours of activity (the pipeline ran in 0.6 s):

| # | Customer | City | Last transaction (UTC) | Txns in 24 h | Amount (INR) | Categories |
|---|---|---|---|---|---|---|
| 1 | C_dc3e11ecf7480d43 | Chennai | 2025-11-25 07:02 | 9 | 41,90,651.11 | travel |
| 2 | C_b89fb79db188845d | Kolkata | 2025-11-10 19:12 | 6 | 2,67,461.72 | gift_cards |
| 3 | C_429ad93f13f07636 | Patna | 2025-12-05 04:06 | 10 | 2,28,915.97 | gaming, gift_cards |
| 4 | C_0dd8d34d505a0a4a | Pune | 2025-12-16 09:11 | 5 | 1,53,979.89 | gift_cards |
| 5 | C_0ed894228d7dd08a | Chennai | 2025-12-31 00:55 | 1 | 1,50,431.47 | electronics |
| 6 | C_c3c4ba15815143b1 | Kolkata | 2025-12-31 10:01 | 6 | 1,49,708.67 | gift_cards |
| 7 | C_c7c5ba9b3d64237e | Patna | 2025-12-27 01:33 | 10 | 1,28,064.71 | healthcare, electronics |
| 8 | C_53387c2676f2a6bf | Kolkata | 2025-11-26 21:50 | 9 | 1,27,207.35 | gaming |
| 9 | C_8e9e573da56c6ebc | Mumbai | 2025-12-25 20:49 | 5 | 1,25,637.09 | gift_cards |
| 10 | C_8014b102f7aa3f68 | Kolkata | 2025-12-21 12:52 | 5 | 1,17,015.62 | gaming |

Amounts use Indian digit grouping (1,00,000 = 1 lakh; 1,00,00,000 = 1 crore). The loaded transactions total about ₹29.82 crore.
