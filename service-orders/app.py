import hashlib
import logging
import socket
import sys
import time
from flask import Flask, jsonify, request

# Configure standard stdout logging for Google Cloud Logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

app = Flask(__name__)
SERVICE_NAME = "orders"

# 5 hardcoded sample orders for demonstration
SAMPLE_ORDERS = [
    {"id": 1, "item": "Cloud Architecture Guidebook", "quantity": 2, "status": "shipped"},
    {"id": 2, "item": "Developer Mechanical Keyboard", "quantity": 1, "status": "processing"},
    {"id": 3, "item": "USB-C Dual 4K Docking Station", "quantity": 1, "status": "delivered"},
    {"id": 4, "item": "Noise-Cancelling Headphones", "quantity": 1, "status": "shipped"},
    {"id": 5, "item": "Ergonomic Desk Mat", "quantity": 3, "status": "pending"},
]


def get_hostname():
    """Retrieve host/container name to demonstrate load balancer distribution."""
    return socket.gethostname()


@app.after_request
def log_request(response):
    """Log each request method, path, and response status code to stdout."""
    query_str = f"?{request.query_string.decode('utf-8')}" if request.query_string else ""
    app.logger.info(f"{request.method} {request.path}{query_str} -> {response.status_code}")
    return response


@app.route("/health", methods=["GET"])
def health():
    """Fast, lightweight health check endpoint for Load Balancer and MIG."""
    return jsonify({
        "status": "ok",
        "service": SERVICE_NAME,
        "hostname": get_hostname(),
    }), 200


@app.route("/api/orders/stress-cpu", methods=["GET"])
def stress_cpu():
    """
    CPU-intensive endpoint designed to hit the 60% CPU utilization threshold
    and trigger Managed Instance Group (MIG) auto-scaling under load.
    
    Repeatedly computes sha256 hashes in a busy loop for the requested milliseconds.
    """
    # Parse ?ms= parameter, defaulting to 200ms and clamped between 10ms and 2000ms
    raw_ms = request.args.get("ms", default="200")
    try:
        target_ms = int(raw_ms)
    except (ValueError, TypeError):
        target_ms = 200

    target_ms = max(10, min(target_ms, 2000))
    target_seconds = target_ms / 1000.0

    start_time = time.perf_counter()
    iterations = 0
    data = b"gcp-load-testing-autoscaling-stress-payload"

    # Busy loop computing SHA-256 to saturate CPU
    while (time.perf_counter() - start_time) < target_seconds:
        data = hashlib.sha256(data).digest()
        iterations += 1

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return jsonify({
        "service": SERVICE_NAME,
        "hostname": get_hostname(),
        "requested_ms": target_ms,
        "iterations_completed": iterations,
        "elapsed_ms": round(elapsed_ms, 2),
    }), 200


@app.route("/api/orders", methods=["GET"])
def get_orders():
    """Returns the list of 5 hardcoded sample orders."""
    return jsonify({
        "service": SERVICE_NAME,
        "hostname": get_hostname(),
        "count": len(SAMPLE_ORDERS),
        "orders": SAMPLE_ORDERS,
    }), 200


@app.route("/api/orders/<int:order_id>", methods=["GET"])
def get_order_by_id(order_id: int):
    """Returns a specific order by ID or HTTP 404."""
    order = next((o for o in SAMPLE_ORDERS if o["id"] == order_id), None)
    if order is None:
        return jsonify({
            "error": "Order not found",
            "requested_id": order_id,
            "service": SERVICE_NAME,
            "hostname": get_hostname(),
        }), 404

    return jsonify({
        "service": SERVICE_NAME,
        "hostname": get_hostname(),
        "order": order,
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
