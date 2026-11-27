# Load testing: isolated production-profile local stack
The first stage is read-only anonymous home and trip search traffic, with 10 companies, 100 buses, 200 departures. No bookings, payments, provider calls or real users. This measures API performance, not full browser rendering or VPS capacity. The test deliberately uses the private recipe HTTP gateway and a trusted forwarded-proto simulation; it is not an HTTPS transport test.

Create a separate Compose project sirago-load, separate secrets, database sirago_load, DJANGO_ALLOWED_HOSTS=load.example.test and DJANGO_CSRF_TRUSTED_ORIGINS=https://load.example.test. Use compose.production.yaml alone, no published ports. Build current backend/migrate/gateway and reuse the audited candidate db/redis/backup images only if they are still present. Start with --no-build --pull never --wait. Run seed.py through Django shell on that project's backend; it refuses a populated database or wrong profile. Keep LOAD_DATE from output.

Run from repository root on PowerShell:
    docker run --rm --network sirago-load_edge -v "$($PWD.Path)/tests/load:/load:ro" -e VUS=10 -e "LOAD_DATE=$loadDate" grafana/k6:latest run /load/public.js

Record the k6 version/digest for reproducibility. Repeat with 50, 100, 200 only if the preceding stage passes and Docker host resources remain healthy. One minute per stage; 1-3 seconds think time after each pair of requests. Initial acceptance: fewer than 1% HTTP failures, >99% functional checks, p95 <1s, p99 <2.5s, search p95 <1s. These provisional thresholds are not an SLA. Record p95/p99, requests/s, CPU, memory and PostgreSQL/Redis behavior. Monitor docker stats in a second terminal during execution. Stop increasing load on threshold failures, OOM, timeouts or resource exhaustion. Do not use --network host or target a public site. Stop the load project when finished (docker compose @load stop); do not remove volumes from other projects.

Next: authenticated read-only workloads with synthetic accounts and separate concurrency/inventory tests. A real TLS browser security recipe and new production image audit are still required. Never infer KVM2 capacity from local Docker alone.
