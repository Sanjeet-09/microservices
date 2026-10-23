# High-Availability 3-Microservice Cloud Deployment

A production-ready 3-microservice application built with **Python 3.11**, **Flask**, and **Gunicorn**, containerized with **Docker**, and engineered for high availability behind a Google Cloud HTTP(S) Load Balancer with Managed Instance Group (MIG) autoscaling.

---

## 1. Project Overview

The system consists of three independent microservices listening internally on port `8080`, managed by Gunicorn (`2 workers`, `4 threads`):

1. **`service-frontend`**: Serves a modern status dashboard displaying the serving instance hostname and enables interactive path-based testing to downstream microservices.
2. **`service-orders`**: Handles orders data and includes a dedicated CPU-intensive endpoint (`/api/orders/stress-cpu`) designed to simulate load and trigger autoscaling at >60% CPU utilization.
3. **`service-inventory`**: Manages product catalog and inventory availability.

Each service:
- Identifies the responding VM/container by injecting its hostname (`socket.gethostname()`) into every JSON response.
- Exposes a dedicated `/health` check returning `200 OK` for Load Balancer and MIG health probing.
- Streams structured request logs to `stdout` for Google Cloud Logging.

---

## 2. Service & Path Routing Contract

In production, Google Cloud HTTP(S) Load Balancers **do not strip path prefixes**. Therefore, microservices are implemented with their full routing paths:

| Service | Internal Port | Local Host Port | Method | Endpoint Path | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`service-frontend`** | `8080` | `8081` | `GET` | `/` | Web UI Dashboard |
| | `8080` | `8081` | `GET` | `/health` | Health Check |
| **`service-orders`** | `8080` | `8082` | `GET` | `/health` | Health Check |
| | `8080` | `8082` | `GET` | `/api/orders` | List 5 sample orders |
| | `8080` | `8082` | `GET` | `/api/orders/<int:id>` | Retrieve order by ID |
| | `8080` | `8082` | `GET` | `/api/orders/stress-cpu?ms=200` | CPU stress loop (10ms–2000ms) |
| **`service-inventory`** | `8080` | `8083` | `GET` | `/health` | Health Check |
| | `8080` | `8083` | `GET` | `/api/inventory` | List 5 sample products |
| | `8080` | `8083` | `GET` | `/api/inventory/<sku>` | Retrieve product by SKU |

---

## 3. Local Development & Docker Compose

### Prerequisites
- Docker & Docker Compose installed and running.
- Python 3.11 (optional for local non-Docker development).

### Run Locally with Docker Compose
To build all images from scratch and launch the containers:

```bash
docker compose up --build
```

To run in the background (detached mode):
```bash
docker compose up --build -d
```

To stop all containers:
```bash
docker compose down
```

---

## 4. Local Testing with cURL

Because there is no central load balancer running locally, each service is exposed on a distinct host port.

### 4.1 Test `service-frontend` (Port 8081)
```bash
# Health Check
curl -i http://localhost:8081/health

# Web Dashboard (HTML output)
curl -i http://localhost:8081/
```
Or open [http://localhost:8081/](http://localhost:8081/) in your web browser.

### 4.2 Test `service-orders` (Port 8082)
```bash
# Health Check
curl -i http://localhost:8082/health

# List all orders
curl -i http://localhost:8082/api/orders

# Retrieve specific order (ID: 1)
curl -i http://localhost:8082/api/orders/1

# Test 404 handler (Non-existent ID)
curl -i http://localhost:8082/api/orders/999

# Trigger CPU stress test (Default 200ms CPU burn)
curl -i http://localhost:8082/api/orders/stress-cpu

# Trigger CPU stress test with custom duration (e.g., 500ms)
curl -i "http://localhost:8082/api/orders/stress-cpu?ms=500"
```

### 4.3 Test `service-inventory` (Port 8083)
```bash
# Health Check
curl -i http://localhost:8083/health

# List all inventory products
curl -i http://localhost:8083/api/inventory

# Retrieve product by SKU
curl -i http://localhost:8083/api/inventory/SKU-KB-001

# Test 404 handler (Non-existent SKU)
curl -i http://localhost:8083/api/inventory/SKU-NON-EXISTENT
```

---

## 5. Simulating Traffic with Locust

The `load-test/` directory contains a Locust load test configured with task weights to heavily target the CPU burn endpoint (`/api/orders/stress-cpu`) and drive instance utilization beyond 60%.

### Running Locust Locally

1. Create and activate a Python virtual environment:
   ```bash
   cd load-test
   python -m venv .venv
   
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # Linux/macOS:
   source .venv/bin/activate
   ```

2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

3. Launch Locust pointing to your Load Balancer IP (or local service):
   ```bash
   # When pointing to Google Cloud Load Balancer:
   locust -f locustfile.py --host http://<LOAD_BALANCER_EXTERNAL_IP>
   
   # Or headless via command line:
   locust -f locustfile.py --host http://<LOAD_BALANCER_EXTERNAL_IP> --users 100 --spawn-rate 10 --run-time 5m --headless
   ```

4. Open the Locust web interface at [http://localhost:8089](http://localhost:8089) to start the test and view requests per second and latency.

---

## 6. Architecture Diagram

<!-- PLACEHOLDER: Insert your architecture diagram below (e.g., docs/screenshots/architecture_diagram.png) -->

```
+---------------------------------------------------------------------------------+
|                                 INTERNET / CLIENTS                              |
+---------------------------------------------------------------------------------+
                                         │
                                         ▼
                     +---------------------------------------+
                     |    GCP External HTTP Load Balancer    |
                     |           (Frontend IP: 80)           |
                     +---------------------------------------+
                                         │
                                [ Path URL Map ]
                 ┌───────────────────────┼───────────────────────┐
                 │ Path: /               │ Path: /api/orders*    │ Path: /api/inventory*
                 ▼                       ▼                       ▼
      +--------------------+  +--------------------+  +--------------------+
      |  Backend Service   |  |  Backend Service   |  |  Backend Service   |
      |     (Frontend)     |  |      (Orders)      |  |    (Inventory)     |
      +--------------------+  +--------------------+  +--------------------+
                 │                       │                       │
                 ▼                       ▼                       ▼
      +--------------------+  +--------------------+  +--------------------+
      |   MIG: Frontend    |  |    MIG: Orders     |  |   MIG: Inventory   |
      |   Min: 1, Max: 3   |  |   Min: 1, Max: 3   |  |   Min: 1, Max: 3   |
      |  (Autoscale @ 60%) |  |  (Autoscale @ 60%) |  |  (Autoscale @ 60%) |
      +--------------------+  +--------------------+  +--------------------+
```

---

## 7. Deployment on GCP

<!-- PLACEHOLDER: Document your Google Cloud deployment steps, instance templates, and commands here -->

1. **Artifact Registry**:
   - Repository created: `microservices-repo`
   - Images tagged and pushed:
     - `service-frontend`
     - `service-orders`
     - `service-inventory`
2. **Compute Engine Instance Templates**:
   - Deployed using Container-Optimized OS (COS) running the corresponding image.
   - Restart policy: `Always`. Port mapping: `8080:8080`.
3. **Managed Instance Groups (MIG)**:
   - Configured with HTTP Health Check (`/health` on port `8080`).
   - Autoscaling policy: Target CPU utilization `60%`, Min: 1 (or 2), Max: 3 (or 5).
4. **Cloud Load Balancing**:
   - Global External HTTP(S) Application Load Balancer.
   - Host and path routing rules mapping `/`, `/api/orders/*`, and `/api/inventory/*`.

---

## 8. Scaling Proof

<!-- PLACEHOLDER: Add your logs, metric graphs, and screenshots below to prove autoscaling -->

### 8.1 Metrics Graph (CPU Utilization > 60%)
- *Attach screenshot from Cloud Monitoring showing CPU utilization rising above the 60% threshold during the Locust test.*
- Path: `docs/screenshots/cpu_utilization_spike.png`

### 8.2 Instance Autoscaling Event
- *Attach screenshot showing the Managed Instance Group scaling up instances in response to the CPU breach.*
- Path: `docs/screenshots/mig_autoscaling_events.png`

### 8.3 Traffic Distribution
- *Attach screenshot from the Load Balancer Monitoring page showing requests distributed across healthy instance hostnames.*
- Path: `docs/screenshots/load_balancer_distribution.png`
