<!-- Develop a FastAPI app in app/main.py with GET /health and POST /score. /score takes a transaction (amount, customer average amount over 90 days, is_new_device, distance in km, hour of day, failed attempts) and returns a risk score plus the reason codes that fire (R01 new device, R02 geo mismatch, R03 odd hours, R04 failed attempts, R05 amount spike, R06 new account). Simple rules are fine for this task. -->

# SENTINEL Risk API (rules only)

A FastAPI service that scores a payment transaction with simple, configurable rules. It returns a
risk score, a risk level, an ALLOW / REVIEW / BLOCK decision, the reason codes that fired, and a
plain-language explanation. It does **not** call the SENTINEL-LM model. It is the rules layer described
in sections 3, 8 and 10 of *Project SENTINEL — Client Requirement Document*.

**The caller sends only the transaction** (section 10.2 shape). The API looks up the customer's history in
the SENTINEL feature store (Supabase) by `customer_id` and computes every rule input itself.

```
Payment API ──POST /score──▶ SENTINEL Risk API ──one query by customer_id──▶ Supabase feature store
 (transaction only)            │                                               customers
                               │  features.py: 90-day avg, new device,         transactions (prior 90 days)
                               │  distance, new city, IST hour, fails 24h,     payment_outcomes
                               │  account age
                               ▼
                    rules.py: R01–R06 → risk_score → ALLOW / REVIEW / BLOCK
```

## Contents

- [Project layout](#project-layout)
- [Quick start](#quick-start)
- [Configuration (.env)](#configuration-env)
- [API key](#api-key)
- [Endpoints](#endpoints)
- [Scoring rules](#scoring-rules)
- [Testing](#testing)
- [Deployment](#deployment)
- [Requirement reference](#requirement-reference)

## Project layout

```
RISK_API/
├── app/
│   ├── main.py              # FastAPI app: GET /health, POST /score; loads .env
│   ├── history.py           # customer history lookup from the feature store (Supabase)
│   ├── features.py          # rule inputs computed from request + history (FE-01..FE-06)
│   └── rules.py             # rule thresholds, weights, bands, scoring logic
├── tests/
│   └── test_api.py          # pytest suite (23 tests, fake history store, no network)
├── scripts/
│   └── validate_against_feature_store.py   # replays stored transactions, compares features
├── test_payloads_to_use/    # 5 sample requests for real customers in the feature store
├── load_test.py             # load test showing which pod/node served each request
├── Dockerfile               # image: app/ + requirements.txt + .env
├── pod.yaml                 # single pod
├── deployment.yaml          # 3 replicas
├── service.yaml             # LoadBalancer on 127.0.0.1:3006
├── *.tf                     # Terraform: run the image as a local Docker container
├── .env                     # secrets and settings (not committed)
├── requirements.txt
└── README.md
```

## Quick start

```powershell
# 1. create and activate a virtual environment
python -m venv venv
venv\Scripts\activate                  # Linux/macOS: source venv/bin/activate

# 2. install dependencies
pip install -r requirements.txt

# 3. start the API (auto-reload while developing)
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The app loads `.env` from the project root on startup, so `--env-file` is not needed.

| URL | What it is |
|---|---|
| http://127.0.0.1:8000/docs | Swagger UI (try requests in the browser) |
| http://127.0.0.1:8000/redoc | ReDoc API reference |
| http://127.0.0.1:8000/health | Service status, history store, active rule config |

To make the API reachable from other machines, bind to all interfaces. Keep `SENTINEL_API_KEY` set when you do this:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Configuration (.env)

Settings come from environment variables. On startup the app reads `<project root>/.env`. A variable that is
already set in the environment wins over `.env`, for example one set with `docker run -e` or Kubernetes `env:`.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `SUPABASE_URL` | **Yes** | – | Feature store project URL. Without it `/score` returns `503`. |
| `SUPABASE_KEY` | **Yes** | – | Feature store API key; needs read access to `customers`, `transactions`, `payment_outcomes`. |
| `HISTORY_TIMEOUT_S` | No | `2` | Timeout in seconds for the history lookup. |
| `SENTINEL_API_KEY` | No | – | If set, `POST /score` requires the header `X-API-Key: <value>`. If unset, there is no auth. |
| `SENTINEL_RULES_CONFIG` | No | – | Path to a JSON file that overrides rule thresholds, weights or bands (FR-RE-01). |

Example `.env`:

```dotenv
# SENTINEL feature store (customer history)
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_KEY=<key>

# API key callers must send as X-API-Key on POST /score
SENTINEL_API_KEY=<generated-key>

# Optional
# HISTORY_TIMEOUT_S=2
# SENTINEL_RULES_CONFIG=rules.json
```

Example `rules.json`. Any subset of keys from `DEFAULT_CONFIG` in `app/rules.py` can go here:

```json
{
  "geo_distance_km": 800,
  "amount_spike_ratio": 10,
  "weights": {"R03_ODD_HOUR": 0.15}
}
```

Changes to `.env` or `rules.json` take effect when the server restarts. `GET /health` shows the active values.

> **Secrets:** `.env` holds the Supabase key and the API key. Do not commit it. The Docker image copies
> `.env` in, so do not push that image to a shared registry.

If the log shows `SUPABASE_URL / SUPABASE_KEY not set - customer history lookup disabled`, then `.env` is
missing from the project root or does not contain those two lines.

## API key

The API cannot generate keys, so Swagger has no option for it. Create a random secret and give it to the
server through `SENTINEL_API_KEY`.

**1. Generate a key**

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**2. Give it to the server.** Put `SENTINEL_API_KEY=<key>` in `.env`, or set it in the shell before starting:

```powershell
$env:SENTINEL_API_KEY = "<key>"          # PowerShell
uvicorn app.main:app --port 8000
```

```bash
SENTINEL_API_KEY="<key>" uvicorn app.main:app --port 8000     # Git Bash / Linux / macOS
```

`GET /health` then reports `"auth_required": true`.

**3. Send it on every `/score` call**

- **Swagger:** open `POST /score`, click **Try it out**, and paste the key into the `x-api-key` header field.
- **curl:** add `-H "X-API-Key: <key>"`.

A missing or wrong key returns `401 {"detail": "missing or invalid X-API-Key"}`. `GET /health` never needs a key.

## Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/health` | none | Service status, history store, serving pod, active rule config |
| `POST` | `/score` | `X-API-Key` (if configured) | Score one transaction |

Every response carries the headers `X-Pod-Name` and `X-Node-Name`, which show which replica served it.

### `GET /health`

```json
{
  "status": "ok",
  "rules_version": "sentinel-rules-0.2.0",
  "auth_required": true,
  "history_store": "supabase",
  "pod_name": "sentinel-score-deployment-85bbf4748b-mlmmm",
  "node_name": "desktop-worker4",
  "config": {
    "odd_hour_start": 0,
    "odd_hour_end": 5,
    "failed_attempts_min": 3,
    "new_account_days": 30,
    "geo_distance_km": 500,
    "amount_spike_ratio": 5.0,
    "weights": {"R01_NEW_DEVICE": 0.25, "R02_GEO_MISMATCH": 0.15, "R03_ODD_HOUR": 0.1,
                "R04_FAILED_ATTEMPTS": 0.25, "R05_AMOUNT_SPIKE": 0.2, "R06_NEW_ACCOUNT": 0.15},
    "combo_bonus_per_flag": 0.05,
    "bands": [[0.85, "CRITICAL", "BLOCK"], [0.6, "HIGH", "REVIEW"], [0.3, "MEDIUM", "ALLOW"], [0.0, "LOW", "ALLOW"]]
  }
}
```

`history_store` is `"not configured"` when `SUPABASE_URL` / `SUPABASE_KEY` are missing.

### `POST /score`

Send the transaction only. History is looked up by `customer_id`, and only events **before**
`transaction_time` count.

#### Request body

| Field | Type | Required | Used for |
|---|---|---|---|
| `transaction_id` | string | **Yes** | Echoed back; excluded from its own history |
| `customer_id` | string | **Yes** | History lookup. An unknown customer returns `404`. |
| `transaction_amount` | number > 0 | **Yes** | R05: ratio to the 90-day average |
| `transaction_time` | ISO 8601 **with timezone offset** | **Yes** | R03: IST hour. Also the cut-off for history. |
| `merchant_location` | `{lat, lon, city}` | **Yes** | R02: distance |
| `customer_location` | `{lat, lon, city}` | No | R02: distance and new city. If omitted, R02 cannot fire. |
| `device_id` | string | No | R01: new device. If omitted, R01 cannot fire. |
| `account_age` | integer (days) | No | R06. Computed from the customer record if omitted. |
| `merchant_category` | string | No | Accepted for contract compatibility; not used by R01–R06 |
| `customer_age` | integer | No | Accepted for contract compatibility; not used by R01–R06 |

#### Example 1: MEDIUM / ALLOW

`test_payloads_to_use/03_medium_new_device_geo_odd_hour.json`

Request:

```json
{
  "transaction_id": "TX_0000027255",
  "customer_id": "C_7fef493a7c8d7ff0",
  "transaction_amount": 3865.09,
  "merchant_category": "gift_cards",
  "transaction_time": "2025-03-13T20:39:15.526+00:00",
  "device_id": "D_20050a5a54f18c76",
  "customer_age": 28,
  "customer_location": {"lat": 18.52, "lon": 73.86, "city": "Pune"},
  "merchant_location": {"lat": 28.61, "lon": 77.21, "city": "Delhi"}
}
```

Response `200`:

```json
{
  "transaction_id": "TX_0000027255",
  "risk_score": 0.55,
  "risk_level": "MEDIUM",
  "decision": "ALLOW",
  "reason_codes": ["R01_NEW_DEVICE", "R02_GEO_MISMATCH", "R03_ODD_HOUR"],
  "explanation": "First use of this device, 1,173 km from the merchant in a city not seen in the last 90 days, in the 02h IST hour (unusual time).",
  "features": {
    "amount": 3865.09,
    "avg_amount_90d": 2455.1,
    "previous_transactions_90d": 5,
    "is_new_device": true,
    "distance_km": 1172.56,
    "is_new_city": true,
    "hour": 2,
    "failed_attempts": 0,
    "account_age_days": 503
  },
  "decision_source": "RULES",
  "rules_version": "sentinel-rules-0.2.0",
  "latency_ms": 266.4
}
```

#### Example 2: CRITICAL / BLOCK

`test_payloads_to_use/05_critical_new_device_after_failures.json`

Request:

```json
{
  "transaction_id": "TX_DEMO_36660_NEWDEV",
  "customer_id": "C_3b7f82da3eea26d5",
  "transaction_amount": 2368.73,
  "merchant_category": "electronics",
  "transaction_time": "2025-04-22T18:43:24.21+00:00",
  "device_id": "D_never_seen_before",
  "customer_age": 60,
  "customer_location": {"lat": 26.91, "lon": 75.79, "city": "Jaipur"},
  "merchant_location": {"lat": 9.93, "lon": 76.27, "city": "Kochi"}
}
```

Response `200`:

```json
{
  "transaction_id": "TX_DEMO_36660_NEWDEV",
  "risk_score": 1.0,
  "risk_level": "CRITICAL",
  "decision": "BLOCK",
  "reason_codes": ["R01_NEW_DEVICE", "R02_GEO_MISMATCH", "R03_ODD_HOUR", "R04_FAILED_ATTEMPTS", "R05_AMOUNT_SPIKE"],
  "explanation": "First use of this device, 1,889 km from the merchant, in the 00h IST hour (unusual time), after 4 failed attempts, amount is 14x the customer's 90-day average.",
  "features": {
    "amount": 2368.73,
    "avg_amount_90d": 169.56,
    "previous_transactions_90d": 12,
    "is_new_device": true,
    "distance_km": 1888.76,
    "is_new_city": false,
    "hour": 0,
    "failed_attempts": 4,
    "account_age_days": 332
  },
  "decision_source": "RULES",
  "rules_version": "sentinel-rules-0.2.0",
  "latency_ms": 294.5
}
```

#### Response fields

| Field | Type | Description |
|---|---|---|
| `transaction_id` | string | From the request |
| `risk_score` | number 0–1 | Rule score (not a model probability) |
| `risk_level` | `LOW` / `MEDIUM` / `HIGH` / `CRITICAL` | Band from section 10.4 |
| `decision` | `ALLOW` / `REVIEW` / `BLOCK` | Action for the Payment API |
| `reason_codes` | string[] | Codes that fired, in code order |
| `explanation` | string | Plain-language summary built only from the fired codes and their inputs |
| `features` | object | Rule inputs derived from the request and history (see below) |
| `decision_source` | string | Always `RULES` |
| `rules_version` | string | Version of the rule set |
| `latency_ms` | number | Time spent on history lookup and scoring |

#### How `features` are computed

These follow the definitions in `feature_catalogue.json` (sentinel-data bucket). Only events strictly before `transaction_time` count.

| Feature | Definition | Rule |
|---|---|---|
| `avg_amount_90d` | Mean amount of the customer's transactions in the preceding 90 days. `null` if none. | R05 |
| `previous_transactions_90d` | Number of those transactions | – |
| `is_new_device` | `device_id` not used by the customer in the preceding 90 days. `null` if no device was sent. | R01 |
| `distance_km` | Haversine distance between `customer_location` and `merchant_location` | R02 |
| `is_new_city` | `customer_location.city` not seen in the preceding 90 days | R02 |
| `hour` | Hour of `transaction_time` in IST | R03 |
| `failed_attempts` | `FAILED` payment outcomes received in the preceding 24 h | R04 |
| `account_age_days` | Complete days from the customer's `created_at` to `transaction_time` | R06 |

#### Errors

| Status | When | Example body |
|---|---|---|
| `401` | `SENTINEL_API_KEY` is set and `X-API-Key` is missing or wrong | `{"detail": "missing or invalid X-API-Key"}` |
| `404` | `customer_id` not found in the feature store | `{"detail": "unknown customer_id C_does_not_exist"}` |
| `422` | Missing field or invalid value, e.g. `transaction_amount: 0` or `transaction_time` without a timezone | FastAPI validation details |
| `503` | Feature store not configured or unreachable. Per FR-API-01 the Payment API then applies its fail-open policy. | `{"detail": "customer history unavailable"}` |

#### curl

In PowerShell, type `curl.exe` instead of `curl`.

```bash
curl http://127.0.0.1:8000/health

curl -X POST http://127.0.0.1:8000/score \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <key>" \
  -d @test_payloads_to_use/05_critical_new_device_after_failures.json
```

## Scoring rules

Each rule implements one feature rule from section 8 of the requirement document and maps to one reason code.
The thresholds match the reason codes stored in the feature store's `features` table (checked on 30,000 rows).
An unknown input (`null`) never fires a rule.

| Code | Fires when | Requirement | Weight |
|---|---|---|---|
| `R01_NEW_DEVICE` | `is_new_device` is true | FE-02 | 0.25 |
| `R02_GEO_MISMATCH` | `distance_km >= 500` **or** `is_new_city` | FE-03 | 0.15 |
| `R03_ODD_HOUR` | `0 <= hour < 5` (midnight–5 AM IST) | FE-04 | 0.10 |
| `R04_FAILED_ATTEMPTS` | `failed_attempts >= 3` | FE-05 | 0.25 |
| `R05_AMOUNT_SPIKE` | `amount / avg_amount_90d >= 5` | FE-01 | 0.20 |
| `R06_NEW_ACCOUNT` | `account_age_days < 30` | FE-06 | 0.15 |

**Score.** `risk_score` is the sum of the weights of the fired rules, plus 0.05 for each fired rule beyond
the second (FE-10, "risk compounds"), capped at 1.0.

**Decision policy** (section 10.4):

| `risk_score` | `risk_level` | `decision` | Action by Payment API |
|---|---|---|---|
| 0.00 – 0.29 | LOW | ALLOW | Approve normally |
| 0.30 – 0.59 | MEDIUM | ALLOW | Approve; step-up OTP if supported |
| 0.60 – 0.84 | HIGH | REVIEW | Send to manual review queue |
| 0.85 – 1.00 | CRITICAL | BLOCK | Decline and notify the customer |

Every threshold, weight and band can be changed through `SENTINEL_RULES_CONFIG` without a code change.

## Testing

**Unit tests.** These use a fake history store and need no network:

```powershell
pytest tests -q
```

**Check against the real feature store.** This replays stored transactions through `/score` and compares every
computed feature and reason code with what the original SENTINEL pipeline stored. It needs `.env`.

```powershell
python scripts/validate_against_feature_store.py --n 300
```

Last runs: 1,900 transactions in total, with a 100% match on every feature and on R01–R06.

**Sample payloads** in `test_payloads_to_use/`. These are real customers. Files 01–04 are stored transactions
replayed as-is. File 05 is stored transaction `TX_0000036660` sent with a device the customer has never used.

| File | Score | Level / Decision | Reason codes |
|---|---|---|---|
| `01_low_no_reasons.json` | 0.00 | LOW / ALLOW | none |
| `02_low_amount_spike.json` | 0.20 | LOW / ALLOW | R05 |
| `03_medium_new_device_geo_odd_hour.json` | 0.55 | MEDIUM / ALLOW | R01, R02, R03 |
| `04_high_geo_failed_attempts_spike.json` | 0.65 | HIGH / REVIEW | R02, R04, R05 |
| `05_critical_new_device_after_failures.json` | 1.00 | CRITICAL / BLOCK | R01, R02, R03, R04, R05 |

## Deployment

The current image tag is **`v3`**, the version that fetches history from the feature store. Images `v1` and
`v2` expect the old request body, with history fields sent by the caller.

### Docker

```powershell
docker build -t sent-score-api:v3 .
docker rm -f scoreapi-container                  # if a container with this name already exists
docker run -d --name scoreapi-container -p 5005:8000 sent-score-api:v3
```

Open http://127.0.0.1:5005/docs.

The image contains `app/`, `requirements.txt` and `.env`, and starts uvicorn with `--env-file .env`.
To keep secrets out of the image, remove `COPY .env .` from the `Dockerfile` and pass them at run time:
`docker run --env-file .env ...`.

### Kubernetes: single pod

```powershell
kubectl apply -f pod.yaml
kubectl get pod -o wide
kubectl describe pod sentinel-score-pod
kubectl port-forward sentinel-score-pod 5004:8000
```

Open http://127.0.0.1:5004/docs.

`imagePullPolicy` must be `IfNotPresent` (not `Never`) so the cluster nodes can pull the locally built image.
After rebuilding, recreate the pod with `kubectl delete pod sentinel-score-pod; kubectl apply -f pod.yaml`.

### Kubernetes: deployment (3 replicas)

```powershell
kubectl apply -f deployment.yaml
kubectl get deployments
kubectl get replicaset
kubectl get pods -o wide
kubectl get nodes -o wide
```

To roll out a rebuilt image, either change `image:` in `deployment.yaml` and apply it again, or keep the tag and run
`kubectl rollout restart deployment/sentinel-score-deployment`.

### Kubernetes: service (load balancing)

`service.yaml` is a `LoadBalancer` Service. Docker Desktop publishes it on `127.0.0.1:3006`, and each new
connection goes to one of the pods.

```powershell
kubectl apply -f service.yaml
kubectl get svc sentinel-score-service
kubectl get endpointslices -l kubernetes.io/service-name=sentinel-score-service
```

Open http://127.0.0.1:3006/docs. No port-forward is needed.

`kubectl port-forward svc/...` sends **all** traffic to a single pod, so don't use it to test load balancing.
It is only needed when the Service type is `ClusterIP`.

### Load test

```powershell
# from your machine, through the LoadBalancer Service (use 127.0.0.1, not localhost, on Windows)
$env:URL = "http://127.0.0.1:3006/score"; python load_test.py

# from inside the cluster
Get-Content load_test.py -Raw | kubectl run sentinel-loadtest --rm -i --restart=Never `
  --image=sent-score-api:v3 --image-pull-policy=IfNotPresent `
  --env=URL=http://sentinel-score-service/score -- python -
```

The output shows requests by pod, node and decision, and latency p50 / p99. Each request includes a Supabase
lookup, so expect about 200 ms median latency.

### Terraform (local Docker container)

The `*.tf` files run the image as a Docker container with the
[kreuzwerker/docker](https://registry.terraform.io/providers/kreuzwerker/docker/latest/docs) provider.
Install steps are in `terraform-install-steps`.

```powershell
terraform init
terraform fmt
terraform plan  -var image_tag=v3
terraform apply -var image_tag=v3
terraform destroy
```

Outputs: `api_url`, `swagger_url` and `health_url`, at http://localhost:8080 by default (`external_port`).
`image_tag` defaults to `v1` in `variable.tf`, so pass `-var image_tag=v3` or change the default.

## Requirement reference

Excerpts from *Project SENTINEL — Client Requirement Document* that this API is based on.

### 3. Reason codes

The API must translate model drivers into codes that support staff can read. The initial list is below; the team may propose additions.

| Code | Meaning | Implemented |
|---|---|---|
| `R01_NEW_DEVICE` | Transaction from a device not previously used by the customer | Yes |
| `R02_GEO_MISMATCH` | Customer far from merchant or in an unusual city | Yes |
| `R03_ODD_HOUR` | Transaction at an unusual time of day | Yes |
| `R04_FAILED_ATTEMPTS` | Multiple failed attempts before this transaction | Yes |
| `R05_AMOUNT_SPIKE` | Amount much higher than customer's usual spend | Yes |
| `R06_NEW_ACCOUNT` | Account created very recently | Yes |
| `R07_VELOCITY` | Unusually many transactions in a short period | Not yet |
| `R08_HIGH_RISK_MCC` | Merchant category with elevated fraud history | Not yet |

### 10. Scoring API and Rules Engine

The Payment API will call the Fraud Model API synchronously for every transaction and act on the returned decision. The response contract below is fixed; changes need product-owner approval.

**10.1 Endpoint:** `POST /v1/fraud/score`, authenticated with mutual TLS plus a service token, JSON in and out.

**10.2 Sample request**

```json
{
  "transaction_id": "TX98231",
  "customer_id": "C_7f31a9",
  "transaction_amount": 50000.00,
  "merchant_category": "electronics",
  "transaction_time": "2025-11-14T03:12:44+05:30",
  "device_id": "D_44be20",
  "customer_age": 27,
  "customer_location": {"lat": 18.52, "lon": 73.85, "city": "Pune"},
  "merchant_location": {"lat": 28.61, "lon": 77.20, "city": "Delhi"},
  "account_age": 6
}
```

Historical fields (`previous_transactions`, `average_transaction_value`, `failed_transactions`) are looked up by the service from the feature store, not sent by the caller.

**10.3 Sample response**

```json
{
  "transaction_id": "TX98231",
  "fraud_probability": 0.94,
  "decision": "BLOCK",
  "risk_level": "CRITICAL",
  "reason_codes": ["R01_NEW_DEVICE", "R04_FAILED_ATTEMPTS", "R03_ODD_HOUR"],
  "explanation": "First use of this device, 1,170 km from the merchant, at 3:12 AM, after 4 failed attempts in 24 hours; amount is 21x the customer's usual spend.",
  "decision_source": "MODEL",
  "model_version": "sentinel-lm-1.0.0-q8",
  "latency_ms": 118
}
```

### How this API differs from the contract

The request body follows §10.2, and history comes from the feature store. The remaining differences:

| Contract (§10) | This API |
|---|---|
| `POST /v1/fraud/score`, `GET /v1/health` | `POST /score`, `GET /health` |
| mTLS + service token | Optional `X-API-Key` header |
| `fraud_probability` from the model | `risk_score` from the rules (not a probability) |
| `decision_source: "MODEL"`, `model_version` | `decision_source: "RULES"`, `rules_version` |
| – | Extra `features` object showing the derived rule inputs |
| p99 latency ≤ 250 ms | About 200 ms median and 600 ms p99, because every request queries Supabase |
