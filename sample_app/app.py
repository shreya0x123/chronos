import time
import random
import uuid
import sys
import os

# Add parent directories to PYTHONPATH to allow importing local sdk
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../sdk")))

from chronos import ChronosClient, HTTPSpanExporter


def run_simulation(endpoint="http://localhost:8000/api/v1/spans/"):
    print(f"Starting Chronos Microservices Simulator targeting {endpoint}")
    print("Press Ctrl+C to stop.\n")

    # Initialize client singleton once
    exporter = HTTPSpanExporter(endpoint)
    client = ChronosClient(service_name="frontend", exporter=exporter)

    scenario_mix = [
        "success",
        "success",
        "success",
        "slow_payment",
        "inventory_error",
        "payment_error",
    ]

    try:
        while True:
            scenario = random.choice(scenario_mix)
            order_id = str(uuid.uuid4())
            user_id = f"usr_{random.randint(1000, 9999)}"

            print(
                f"Triggering checkout transaction: Scenario={scenario.upper()}, OrderID={order_id}"
            )

            # 1. Frontend Service
            client.service_name = "frontend"
            span_fe = client.start_span("checkout_click")
            span_fe.set_attribute("http.method", "POST")
            span_fe.set_attribute("http.url", "https://shop.chronos.com/checkout")
            span_fe.set_attribute("user.id", user_id)
            span_fe.add_event("button_clicked", {"device": "desktop"})
            time.sleep(0.02)  # Client latency

            # Call Gateway (Network boundary simulation)
            headers = {}
            client.inject_context(span_fe, headers)

            # 2. Gateway Service
            client.service_name = "gateway"
            ctx_gw = client.extract_context(headers)
            span_gw = client.start_span(
                "route_request",
                parent_span_id=ctx_gw["parent_span_id"],
                trace_id=ctx_gw["trace_id"],
            )
            span_gw.set_attribute("gateway.version", "v1.2.0")
            span_gw.add_event("request_received", {"route": "/api/checkout"})
            time.sleep(0.015)

            # Call Order Service (Network boundary simulation)
            headers_gw = {}
            client.inject_context(span_gw, headers_gw)

            # 3. Order Service
            client.service_name = "order-service"
            ctx_order = client.extract_context(headers_gw)
            span_order = client.start_span(
                "create_order",
                parent_span_id=ctx_order["parent_span_id"],
                trace_id=ctx_order["trace_id"],
            )
            span_order.set_attribute("order.id", order_id)
            span_order.add_event("validating_cart")
            time.sleep(0.03)

            # Call Inventory Service (Network boundary simulation)
            headers_order = {}
            client.inject_context(span_order, headers_order)

            # 4. Inventory Service
            client.service_name = "inventory-service"
            ctx_inventory = client.extract_context(headers_order)
            span_inv = client.start_span(
                "check_inventory",
                parent_span_id=ctx_inventory["parent_span_id"],
                trace_id=ctx_inventory["trace_id"],
            )
            span_inv.set_attribute("item.sku", "PROD-9988")

            if scenario == "inventory_error":
                time.sleep(0.04)
                # Fail with inventory error
                err = Exception("SKU PROD-9988 is out of stock in warehouse-east")
                span_inv.record_exception(err)
                client.finish_span(span_inv)

                # Rollback order span
                client.service_name = "order-service"
                span_order.set_attribute("http.status_code", 400)
                span_order.record_exception(
                    Exception("Order creation aborted: Inventory check failed")
                )
                client.finish_span(span_order)

                # Rollback gateway span
                client.service_name = "gateway"
                span_gw.set_attribute("http.status_code", 400)
                client.finish_span(span_gw)

                # Rollback frontend span
                client.service_name = "frontend"
                span_fe.set_attribute("http.status_code", 400)
                client.finish_span(span_fe)
                print("Transaction finished: INVENTORY_ERROR (rolled back)")
                print("-" * 60)
                time.sleep(3)
                continue
            else:
                time.sleep(random.uniform(0.02, 0.05))
                span_inv.add_event("items_reserved", {"count": 1})
                client.finish_span(span_inv)

            # Call Payment Service (Network boundary simulation)
            client.service_name = "order-service"
            headers_pay = {}
            client.inject_context(span_order, headers_pay)

            # 5. Payment Service
            client.service_name = "payment-service"
            ctx_payment = client.extract_context(headers_pay)
            span_pay = client.start_span(
                "charge_card",
                parent_span_id=ctx_payment["parent_span_id"],
                trace_id=ctx_payment["trace_id"],
            )
            span_pay.set_attribute("payment.provider", "stripe")
            span_pay.set_attribute("payment.amount", 99.99)

            if scenario == "slow_payment":
                # Simulate slow network latency
                time.sleep(random.uniform(1.2, 1.8))
                span_pay.add_event("charge_success_delayed")
                client.finish_span(span_pay)
            elif scenario == "payment_error":
                time.sleep(0.1)
                # Fail card payment
                err = Exception("Stripe: Card declined (insufficient_funds)")
                span_pay.record_exception(err)
                client.finish_span(span_pay)

                # Rollback order span
                client.service_name = "order-service"
                span_order.set_attribute("http.status_code", 402)
                span_order.record_exception(
                    Exception("Order creation aborted: Payment failed")
                )
                client.finish_span(span_order)

                # Rollback gateway span
                client.service_name = "gateway"
                span_gw.set_attribute("http.status_code", 402)
                client.finish_span(span_gw)

                # Rollback frontend span
                client.service_name = "frontend"
                span_fe.set_attribute("http.status_code", 402)
                client.finish_span(span_fe)
                print("Transaction finished: PAYMENT_ERROR (rolled back)")
                print("-" * 60)
                time.sleep(3)
                continue
            else:
                time.sleep(random.uniform(0.08, 0.15))
                span_pay.add_event("charge_success")
                client.finish_span(span_pay)

            # Call Notification Service (Async call)
            client.service_name = "order-service"
            headers_notif = {}
            client.inject_context(span_order, headers_notif)

            # 6. Notification Service
            client.service_name = "notification-service"
            ctx_notif = client.extract_context(headers_notif)
            span_notif = client.start_span(
                "send_invoice_email",
                parent_span_id=ctx_notif["parent_span_id"],
                trace_id=ctx_notif["trace_id"],
            )
            span_notif.set_attribute("email.template", "order_confirmation")
            span_notif.set_attribute("email.to", "user@chronos.com")
            time.sleep(random.uniform(0.04, 0.08))
            span_notif.add_event("smtp_handshake")
            span_notif.add_event("email_sent")
            client.finish_span(span_notif)

            # Complete Order Service
            client.service_name = "order-service"
            span_order.set_attribute("http.status_code", 201)
            span_order.add_event("order_saved_to_db")
            client.finish_span(span_order)

            # Complete Gateway
            client.service_name = "gateway"
            span_gw.set_attribute("http.status_code", 200)
            client.finish_span(span_gw)

            # Complete Frontend
            client.service_name = "frontend"
            span_fe.set_attribute("http.status_code", 200)
            client.finish_span(span_fe)

            print("Transaction finished: SUCCESS")
            print("-" * 60)

            # Wait between simulations
            time.sleep(random.uniform(2, 4))

    except KeyboardInterrupt:
        print("\nSimulator stopped by user.")


if __name__ == "__main__":
    # Check if a custom endpoint was passed as command line arg
    target_endpoint = (
        sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/api/v1/spans/"
    )
    run_simulation(target_endpoint)
