import logging
import socket
import sys
from flask import Flask, jsonify, request

# Configure standard stdout logging for Google Cloud Logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

app = Flask(__name__)
SERVICE_NAME = "inventory"

# 5 hardcoded sample products for inventory catalog
SAMPLE_PRODUCTS = [
    {"sku": "SKU-KB-001", "name": "Mechanical Keyboard (Cherry MX Blue)", "stock": 42},
    {"sku": "SKU-MO-002", "name": "Wireless Ergonomic Precision Mouse", "stock": 115},
    {"sku": "SKU-DK-003", "name": "Dual 4K Thunderbolt 4 Docking Station", "stock": 18},
    {"sku": "SKU-MN-004", "name": "34-inch Ultrawide Curved Monitor", "stock": 7},
    {"sku": "SKU-HS-005", "name": "Active Noise Cancelling Headset", "stock": 64},
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


@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    """Returns the list of 5 hardcoded sample inventory products."""
    return jsonify({
        "service": SERVICE_NAME,
        "hostname": get_hostname(),
        "total_items": len(SAMPLE_PRODUCTS),
        "products": SAMPLE_PRODUCTS,
    }), 200


@app.route("/api/inventory/<string:sku>", methods=["GET"])
def get_product_by_sku(sku: str):
    """Returns a single product by SKU or HTTP 404."""
    product = next((p for p in SAMPLE_PRODUCTS if p["sku"].lower() == sku.lower()), None)
    if product is None:
        return jsonify({
            "error": "Product not found",
            "requested_sku": sku,
            "service": SERVICE_NAME,
            "hostname": get_hostname(),
        }), 404

    return jsonify({
        "service": SERVICE_NAME,
        "hostname": get_hostname(),
        "product": product,
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
