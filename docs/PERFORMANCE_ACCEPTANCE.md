# ATPLCRM v0.15 Local Performance Acceptance

The release was measured on 16 September 2026 in an isolated local Docker Compose deployment using PostgreSQL 17. The deterministic disposable profile contained 20,006 contacts, 5,000 open scale leads, 5,000 open scale opportunities and the showcase records. Raw results are stored in `performance-v0.15.json`.

| Interaction | Dataset | Target | Observed | Result |
|---|---:|---:|---:|---|
| Board/bootstrap working set | 10,013 pursuits; 100 loaded | 2.0 s | 1.093 s | Pass |
| Contact list | 20,006 contacts | 2.0 s | 0.565 s | Pass |
| Opportunity list | 5,007 opportunities | 2.0 s | 0.260 s | Pass |
| Ranked broad search | 31,000 matches | 3.5 s | 2.297 s | Pass |
| Full management report | 10,013 report records | 10.0 s | 8.743 s | Pass |

These are single-run local acceptance limits for the client demo, not production percentile claims. The board deliberately loads the 100 most recently updated pursuits and directs users to complete server-paginated lists/search for older work. Production sizing must repeat the workload under representative concurrency, latency, Azure compute and telemetry.

Reproduce only in a disposable workspace:

```sh
docker compose --env-file .env.test up -d --build --wait
docker compose --env-file .env.test exec -T api python -m atplcrm.scale_data \
  --contacts 20000 --leads 5000 --opportunities 5000 --confirm SCALE-DISPOSABLE
python3 scripts/benchmark.py --env-file .env.test --report docs/performance-v0.15.json
```
