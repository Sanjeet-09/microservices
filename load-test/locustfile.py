from locust import HttpUser, task, between


class MicroserviceLoadTester(HttpUser):
    """
    Simulates traffic through the Cloud Load Balancer with a heavy emphasis
    on the CPU-intensive endpoint (/api/orders/stress-cpu) to drive CPU utilization
    above 60% and trigger Managed Instance Group (MIG) autoscaling.
    """
    # Wait between 0.1 and 0.5 seconds between tasks to generate rapid requests
    wait_time = between(0.1, 0.5)

    @task(8)
    def stress_orders_cpu(self):
        """Heavy task (weight 8) calling the CPU burn endpoint."""
        self.client.get("/api/orders/stress-cpu?ms=200", name="[Orders] Stress CPU (200ms)")

    @task(1)
    def get_orders(self):
        """Standard task (weight 1) fetching the orders list."""
        self.client.get("/api/orders", name="[Orders] List Orders")

    @task(1)
    def get_inventory(self):
        """Standard task (weight 1) fetching the inventory list."""
        self.client.get("/api/inventory", name="[Inventory] List Inventory")

    @task(1)
    def get_frontend(self):
        """Standard task (weight 1) loading the frontend dashboard."""
        self.client.get("/", name="[Frontend] Dashboard Index")
