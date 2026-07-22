"""
M37-#7: Load test — 50 пользователей, 2 минуты.
Сценарий: каждый юзер делает login → /products → /detail/3 → /items/3/generate
Измеряем p50/p95/p99 latency, error rate, throughput.

Запуск:
  source venv/bin/activate
  locust -f test/load_test.py --host=https://217.114.7.5:8081 \\
    --users 50 --spawn-rate 5 --run-time 120s --headless \\
    --html test/load_report.html

Или с web UI:
  locust -f test/load_test.py --host=https://217.114.7.5:8081
  (открыть http://localhost:8089)
"""
import urllib3
import time
from locust import HttpUser, task, between

# Self-signed cert: ignore
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USERS = [
    ("techadmin", "admin"),
    ("vorobyev", "main_technologist"),
    ("tarrietsky", "technologist"),
    ("golubev", "workshop_chief"),
]

class BitTechnologUser(HttpUser):
    wait_time = between(1, 3)
    abstract = True

    def on_start(self):
        # login
        idx = len(self.environment.runner.user_greenlets) % len(USERS) if self.environment.runner else 0
        username, _ = USERS[idx % len(USERS)]
        r = self.client.post(
            "/login",
            data={"username": username, "password": "demo"},
            headers={"X-Requested-With": "XMLHttpRequest"},
            verify=False,
            allow_redirects=False,
        )
        if r.status_code not in (200, 303):
            # Login may be exempt from CSRF, try without XRW
            r = self.client.post(
                "/login",
                data={"username": username, "password": "demo"},
                verify=False,
                allow_redirects=False,
            )


class TechnologistUser(BitTechnologUser):
    weight = 4  # 80% технологи

    @task(2)
    def view_products(self):
        self.client.get("/products", verify=False)

    @task(3)
    def view_detail(self):
        self.client.get("/detail/3", verify=False)

    @task(1)
    def dashboard(self):
        self.client.get("/", verify=False)

    @task(1)
    def profiles(self):
        self.client.get("/profiles", verify=False)


class AdminUser(BitTechnologUser):
    weight = 1  # 20% админы

    @task(1)
    def dashboard(self):
        self.client.get("/", verify=False)

    @task(1)
    def llm_admin(self):
        self.client.get("/llm-admin", verify=False)

    @task(1)
    def settings(self):
        self.client.get("/settings", verify=False)

    @task(1)
    def metrics(self):
        self.client.get("/metrics", verify=False)
