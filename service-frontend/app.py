import logging
import socket
import sys
from flask import Flask, jsonify, render_template_string, request

# Configure logging to standard output for Google Cloud Logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

app = Flask(__name__)
SERVICE_NAME = "frontend"


def get_hostname():
    """Retrieve the current container/host name to demonstrate load balancing."""
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


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Microservice Frontend - High Availability Demo</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --primary-hover: #0ea5e9;
      --accent: #a855f7;
      --border: #334155;
      --code-bg: #090d16;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 2rem 1rem;
    }
    .container {
      max-width: 860px;
      width: 100%;
    }
    header {
      text-align: center;
      margin-bottom: 2rem;
    }
    h1 {
      font-size: 2rem;
      font-weight: 700;
      background: linear-gradient(135deg, var(--primary), var(--accent));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.5rem;
    }
    .subtitle {
      color: var(--text-muted);
      font-size: 0.95rem;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
      box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }
    .badge-row {
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
      margin-top: 0.75rem;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: var(--primary);
      padding: 0.35rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.85rem;
      font-family: monospace;
    }
    .btn-group {
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
      margin-bottom: 1.5rem;
    }
    button {
      flex: 1;
      min-width: 200px;
      background: var(--primary);
      color: #041324;
      border: none;
      border-radius: 8px;
      padding: 0.85rem 1.25rem;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s, transform 0.1s;
    }
    button:hover {
      background: var(--primary-hover);
      transform: translateY(-1px);
    }
    button:active {
      transform: translateY(0);
    }
    .result-section h3 {
      font-size: 1rem;
      margin-bottom: 0.5rem;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    pre {
      background: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 0.85rem;
      color: #e2e8f0;
      overflow-x: auto;
      min-height: 180px;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .status-dot {
      display: inline-block;
      width: 8px;
      height: 8px;
      background: #10b981;
      border-radius: 50%;
      margin-right: 6px;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Cloud Microservices Dashboard</h1>
      <p class="subtitle">High Availability & Autoscaling Demonstration behind HTTP Load Balancer</p>
    </header>

    <div class="card">
      <h2>Serving Instance Details</h2>
      <div class="badge-row">
        <span class="badge"><span class="status-dot"></span>Service: {{ service_name }}</span>
        <span class="badge">Host: {{ hostname }}</span>
        <span class="badge">Port: 8080 (Container)</span>
      </div>
    </div>

    <div class="card">
      <h2 style="margin-bottom: 1rem; font-size: 1.2rem;">Test Path-Based Routing</h2>
      <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1rem;">
        Click the buttons below to issue relative <code>fetch()</code> requests via the Load Balancer to verify downstream service routing:
      </p>
      <div class="btn-group">
        <button id="btnOrders" onclick="fetchEndpoint('/api/orders')">Fetch Orders (/api/orders)</button>
        <button id="btnInventory" onclick="fetchEndpoint('/api/inventory')">Fetch Inventory (/api/inventory)</button>
      </div>

      <div class="result-section">
        <h3>
          <span>Response JSON Output</span>
          <span id="endpointLabel" style="font-family: monospace; font-size: 0.8rem;">Ready</span>
        </h3>
        <pre id="output">// Click a button above to fetch data through the load balancer...</pre>
      </div>
    </div>
  </div>

  <script>
    async function fetchEndpoint(url) {
      const outputEl = document.getElementById('output');
      const labelEl = document.getElementById('endpointLabel');
      outputEl.textContent = 'Requesting ' + url + ' ...';
      labelEl.textContent = url;

      try {
        const startTime = performance.now();
        const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
        const elapsed = Math.round(performance.now() - startTime);

        if (!res.ok) {
          throw new Error('HTTP ' + res.status + ' ' + res.statusText);
        }

        const data = await res.json();
        outputEl.textContent = JSON.stringify({
          _fetch_metadata: {
            requested_url: url,
            status: res.status,
            roundtrip_ms: elapsed
          },
          ...data
        }, null, 2);
      } catch (err) {
        outputEl.textContent = JSON.stringify({
          error: true,
          message: err.message,
          hint: 'Ensure your load balancer path-routing rules or local proxies are active.'
        }, null, 2);
      }
    }
  </script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    """Serves the dashboard showing service name, hostname, and test fetch buttons."""
    return render_template_string(
        HTML_TEMPLATE,
        service_name=SERVICE_NAME,
        hostname=get_hostname(),
    )


if __name__ == "__main__":
    # Local fallback for direct execution
    app.run(host="0.0.0.0", port=8080)
