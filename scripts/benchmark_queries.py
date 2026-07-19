import asyncio
import time
import uuid
import sys
import httpx
import websockets
import json
import statistics

BACKEND_HTTP = "http://localhost:8000/api/v1"
BACKEND_WS = "ws://localhost:8000/api/v1/ws"


async def run_queries_benchmark():
    print("=== Chronos Read & WebSocket Latency Benchmark ===")

    # 1. Fetch trace list to get a valid trace ID
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{BACKEND_HTTP}/traces/")
            traces = resp.json()
        except Exception as e:
            print(f"Error: Unable to connect to backend: {e}")
            return

    trace_count = len(traces)
    print(f"Database currently contains {trace_count} traces.")

    if trace_count == 0:
        print(
            "Error: No traces in database. Please run benchmark.py first to populate data!"
        )
        return

    # Select a trace with several spans to make it a realistic detail query
    # Find trace with highest span count or just pick first one
    traces_with_spans = [t for t in traces if t.get("span_count", 0) > 1]
    target_trace = traces_with_spans[0] if traces_with_spans else traces[0]
    trace_id = target_trace["id"]
    print(
        f"Selected trace ID {trace_id} ({target_trace.get('span_count', 1)} spans) for detail queries.\n"
    )

    # 2. Benchmark GET /traces/ (Trace list query)
    print("Benchmarking GET /traces/ (100 runs)...")
    list_latencies = []
    async with httpx.AsyncClient() as client:
        for _ in range(100):
            start = time.perf_counter()
            resp = await client.get(f"{BACKEND_HTTP}/traces/")
            duration = (time.perf_counter() - start) * 1000.0  # ms
            if resp.status_code == 200:
                list_latencies.append(duration)

    # 3. Benchmark GET /traces/{id} (Trace details query)
    print(f"Benchmarking GET /traces/{trace_id} (100 runs)...")
    detail_latencies = []
    async with httpx.AsyncClient() as client:
        for _ in range(100):
            start = time.perf_counter()
            resp = await client.get(f"{BACKEND_HTTP}/traces/{trace_id}")
            duration = (time.perf_counter() - start) * 1000.0  # ms
            if resp.status_code == 200:
                detail_latencies.append(duration)

    # 4. Benchmark WebSocket update delay (50 runs)
    print("Benchmarking WebSocket update delay (50 runs)...")
    ws_delays = []

    try:
        async with websockets.connect(BACKEND_WS) as websocket:
            # Read and discard any initial connection hello messages
            # Wait a split second to clear buffer
            await asyncio.sleep(0.5)

            async with httpx.AsyncClient() as client:
                for i in range(50):
                    test_trace_id = uuid.uuid4().hex
                    test_span_id = uuid.uuid4().hex
                    payload = {
                        "name": f"ws_benchmark_span_{i}",
                        "span_id": test_span_id,
                        "trace_id": test_trace_id,
                        "service_name": "benchmark-runner",
                        "parent_span_id": None,
                        "start_time": time.time() - 1.0,
                        "end_time": time.time(),
                        "attributes": {"test": True},
                        "events": [],
                    }

                    start_time = time.perf_counter()
                    # Post the span
                    post_resp = await client.post(
                        f"{BACKEND_HTTP}/spans/", json=payload
                    )
                    if post_resp.status_code != 201:
                        continue

                    # Wait to receive the corresponding update on the WS connection
                    ws_received = False
                    while not ws_received:
                        # Set a timeout so we don't block forever if a message is lost
                        msg_str = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        msg = json.loads(msg_str)
                        if msg.get("type") == "trace_updated" and msg.get(
                            "trace", {}
                        ).get("id") == str(uuid.UUID(test_trace_id)):
                            ws_delay = (time.perf_counter() - start_time) * 1000.0  # ms
                            ws_delays.append(ws_delay)
                            ws_received = True

    except Exception as e:
        print(f"Warning: WebSocket delay benchmark skipped or failed: {e}")

    # Calculate statistics
    avg_list = statistics.mean(list_latencies) if list_latencies else 0
    p99_list = (
        statistics.quantiles(list_latencies, n=100)[98]
        if len(list_latencies) >= 100
        else (max(list_latencies) if list_latencies else 0)
    )

    avg_detail = statistics.mean(detail_latencies) if detail_latencies else 0
    p99_detail = (
        statistics.quantiles(detail_latencies, n=100)[98]
        if len(detail_latencies) >= 100
        else (max(detail_latencies) if detail_latencies else 0)
    )

    avg_ws = statistics.mean(ws_delays) if ws_delays else 0
    p99_ws = (
        statistics.quantiles(ws_delays, n=100)[98]
        if len(ws_delays) >= 100
        else (max(ws_delays) if ws_delays else 0)
    )

    print("\n=== Engineering Report: Query Latencies ===")
    print(f"GET /traces ({trace_count} traces) avg: {avg_list:.2f} ms")
    print(f"GET /traces ({trace_count} traces) p99: {p99_list:.2f} ms")
    print(f"GET /traces/{{id}} avg:          {avg_detail:.2f} ms")
    print(f"GET /traces/{{id}} p99:          {p99_detail:.2f} ms")
    if ws_delays:
        print(f"WebSocket update delay avg:   {avg_ws:.2f} ms")
        print(f"WebSocket update delay p99:   {p99_ws:.2f} ms")
    else:
        print("WebSocket update delay:       N/A (Failed to connect/stream)")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_queries_benchmark())
