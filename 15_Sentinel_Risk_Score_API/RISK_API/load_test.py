"""Load test for POST /score that reports which pod / node served each request.

Uses only the standard library, so it also runs inside the API image in the cluster:

    # in-cluster (requests are balanced across pods by the Service)
    Get-Content load_test.py | kubectl run sentinel-loadtest --rm -i --restart=Never `
        --image=sent-score-api:v3 --image-pull-policy=IfNotPresent `
        --env=URL=http://sentinel-score-service/score -- python -

    # from your machine through a port-forward (all requests hit ONE pod)
    python load_test.py

Settings come from env vars: URL, SENTINEL_API_KEY (else read from .env), TOTAL_REQUESTS,
CONCURRENT_USERS.
"""

import json
import os
import random
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

# 127.0.0.1, not localhost: on Windows "localhost" tries IPv6 first and adds ~2 s per request
URL = os.getenv("URL", "http://127.0.0.1:3005/score")
TOTAL_REQUESTS = int(os.getenv("TOTAL_REQUESTS", "300"))
CONCURRENT_USERS = int(os.getenv("CONCURRENT_USERS", "20"))

# same transactions as test_payloads_to_use/ (real customers, history looked up by the API),
# inlined so the script is self-contained
PAYLOADS = [
    {"transaction_id": "TX_0000082702", "customer_id": "C_469e0fa92a3c0ddc", "transaction_amount": 1051.68, "merchant_category": "grocery", "transaction_time": "2025-11-03T08:51:57.123+00:00", "device_id": "D_a0e5f2468d7988cc", "customer_age": 44, "customer_location": {"lat": 22.8, "lon": 86.2, "city": "Jamshedpur"}, "merchant_location": {"lat": 22.57, "lon": 88.36, "city": "Kolkata"}},
    {"transaction_id": "TX_0000078458", "customer_id": "C_2b5a7851536d15e2", "transaction_amount": 14216.45, "merchant_category": "electronics", "transaction_time": "2025-10-16T14:47:45.409+00:00", "device_id": "D_5784ebb41256c617", "customer_age": 50, "customer_location": {"lat": 23.02, "lon": 72.57, "city": "Ahmedabad"}, "merchant_location": {"lat": 22.72, "lon": 75.86, "city": "Indore"}},
    {"transaction_id": "TX_0000027255", "customer_id": "C_7fef493a7c8d7ff0", "transaction_amount": 3865.09, "merchant_category": "gift_cards", "transaction_time": "2025-03-13T20:39:15.526+00:00", "device_id": "D_20050a5a54f18c76", "customer_age": 28, "customer_location": {"lat": 18.52, "lon": 73.86, "city": "Pune"}, "merchant_location": {"lat": 28.61, "lon": 77.21, "city": "Delhi"}},
    {"transaction_id": "TX_0000047155", "customer_id": "C_e779acf612d2338e", "transaction_amount": 19469.07, "merchant_category": "electronics", "transaction_time": "2025-06-06T12:00:01.811+00:00", "device_id": "D_b3accbe40e805381", "customer_age": 49, "customer_location": {"lat": 20.3, "lon": 85.82, "city": "Bhubaneswar"}, "merchant_location": {"lat": 26.14, "lon": 91.74, "city": "Guwahati"}},
    {"transaction_id": "TX_DEMO_36660_NEWDEV", "customer_id": "C_3b7f82da3eea26d5", "transaction_amount": 2368.73, "merchant_category": "electronics", "transaction_time": "2025-04-22T18:43:24.21+00:00", "customer_age": 60, "customer_location": {"lat": 26.91, "lon": 75.79, "city": "Jaipur"}, "merchant_location": {"lat": 9.93, "lon": 76.27, "city": "Kochi"}, "device_id": "D_never_seen_before"},
]


def api_key():
    key = os.getenv("SENTINEL_API_KEY")
    if key:
        return key
    for path in (".env", "/srv/.env"):  # project root, or inside the API image
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                if line.strip().startswith("SENTINEL_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"')
    return ""


API_KEY = api_key()


def send_request(request_id):
    body = json.dumps(random.choice(PAYLOADS)).encode()
    req = urllib.request.Request(URL, data=body, method="POST", headers={
        "Content-Type": "application/json", "X-API-Key": API_KEY})
    t0 = time.perf_counter()
    try:
        # a new connection per request, so the Service can route each one to a different pod
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return {
                "success": True,
                "pod": resp.headers.get("X-Pod-Name", "unknown"),
                "node": resp.headers.get("X-Node-Name", "unknown"),
                "decision": data["decision"],
                "ms": (time.perf_counter() - t0) * 1000,
            }
    except (urllib.error.URLError, OSError, ValueError) as error:
        print(f"Request {request_id} failed: {error}")
        return {"success": False}


def main():
    print(f"POST {URL}  requests={TOTAL_REQUESTS} concurrency={CONCURRENT_USERS} "
          f"api_key={'set' if API_KEY else 'NOT set'}")
    start_time = time.perf_counter()
    with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        results = list(executor.map(send_request, range(TOTAL_REQUESTS)))
    elapsed = time.perf_counter() - start_time

    successful = [r for r in results if r["success"]]
    latencies = sorted(r["ms"] for r in successful)

    print("\n=== LOAD TEST RESULTS ===")
    print(f"Total requests: {TOTAL_REQUESTS}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {TOTAL_REQUESTS - len(successful)}")
    print(f"Duration: {elapsed:.2f} seconds")
    print(f"Throughput: {TOTAL_REQUESTS / elapsed:.2f} req/sec")
    if latencies:
        print(f"Latency p50: {latencies[len(latencies) // 2]:.1f} ms  "
              f"p99: {latencies[int(len(latencies) * 0.99) - 1]:.1f} ms")

    for title, key in (("Pod", "pod"), ("Node", "node"), ("Decision", "decision")):
        print(f"\nRequests by {title}:")
        for name, count in Counter(r[key] for r in successful).most_common():
            print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
