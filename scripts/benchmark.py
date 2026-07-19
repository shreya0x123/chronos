import asyncio
import time
import uuid
import sys
import os
import httpx
import statistics

# Set URL
BACKEND_URL = "http://localhost:8000/api/v1/spans/"


async def send_span(client, sem, payload, latencies):
    async with sem:
        start_time = time.perf_counter()
        try:
            resp = await client.post(BACKEND_URL, json=payload)
            latency = (time.perf_counter() - start_time) * 1000.0  # ms
            if resp.status_code == 201:
                latencies.append(latency)
                return True
        except Exception as e:
            pass
        return False


async def run_benchmark(num_spans=1000, concurrency=5):
    print(f"=== Chronos Ingestion Benchmark ===")
    print(f"Targeting: {BACKEND_URL}")
    print(f"Generating {num_spans} spans with concurrency limit of {concurrency}...")


    # Pre-generate spans payloads to avoid overhead during benchmarking
    payloads = []
    trace_ids = [uuid.uuid4().hex for _ in range(num_spans // 5)]  # 5 spans per trace average
    services = ["frontend", "gateway", "order-service", "inventory-service", "payment-service"]

    for i in range(num_spans):
        trace_id = trace_ids[i % len(trace_ids)]
        span_id = uuid.uuid4().hex
        parent_id = uuid.uuid4().hex if (i % 5 != 0) else None  # 80% are child spans
        
        payloads.append({
            "name": f"operation_{i % 10}",
            "span_id": span_id,
            "trace_id": trace_id,
            "service_name": random_choice(services),
            "parent_span_id": parent_id,
            "start_time": time.time() - 5.0,
            "end_time": time.time(),
            "attributes": {
                "http.status_code": 200,
                "environment": "benchmark",
                "custom_tag": f"value_{i % 100}"
            },
            "events": [
                {"name": "benchmark_event_1", "timestamp": time.time() - 2.5, "attributes": {"idx": i}}
            ]
        })

    latencies = []
    sem = asyncio.Semaphore(concurrency)
    limits = httpx.Limits(max_keepalive_connections=concurrency, max_connections=concurrency * 2)

    # Measure memory before if psutil is available
    memory_before = get_memory_usage()

    start_benchmark = time.perf_counter()

    async with httpx.AsyncClient(limits=limits, timeout=10.0) as client:
        tasks = [
            send_span(client, sem, payload, latencies)
            for payload in payloads
        ]
        results = await asyncio.gather(*tasks)

    end_benchmark = time.perf_counter()
    total_time = end_benchmark - start_benchmark
    successful_requests = sum(1 for r in results if r)
    memory_after = get_memory_usage()

    if not latencies:
        print("Error: All benchmark requests failed. Make sure the backend server is running on port 8000!")
        return

    # Calculate metrics
    throughput = successful_requests / total_time
    avg_latency = statistics.mean(latencies)
    p50_latency = statistics.median(latencies)
    p90_latency = statistics.quantiles(latencies, n=10)[8] if len(latencies) >= 10 else avg_latency
    p99_latency = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else avg_latency

    print("\n=== Benchmark Results ===")
    print(f"Total Telemetry Spans:     {successful_requests} / {num_spans} successfully ingested")
    print(f"Total Time Taken:          {total_time:.2f} seconds")
    print(f"Throughput (Rate):         {throughput:.2f} spans/sec")
    print(f"Average Ingestion Latency: {avg_latency:.2f} ms")
    print(f"p50 Latency:               {p50_latency:.2f} ms")
    print(f"p90 Latency:               {p90_latency:.2f} ms")
    print(f"p99 Latency:               {p99_latency:.2f} ms")
    
    if memory_before and memory_after:
        print(f"Memory Usage Before:       {memory_before:.2f} MB")
        print(f"Memory Usage After:        {memory_after:.2f} MB")
        print(f"Memory Delta Growth:       {max(0.0, memory_after - memory_before):.2f} MB")


def random_choice(lst):
    # Lightweight alternative to random.choice to speed up loop
    import random
    return random.choice(lst)


def get_memory_usage():
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB
    except ImportError:
        # If psutil not installed, try to guess or return None
        return None


if __name__ == "__main__":
    # If on windows, configure event loop policy for high concurrent requests
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    spans_count = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    asyncio.run(run_benchmark(spans_count))
