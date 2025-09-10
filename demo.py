from locust import HttpUser, task, between

BASE_URL = "https://www.vibhoos.com"
BASE_URL = "http://127.0.0.1:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJrYXVzaGlrcGFsdmFpMjAwNEBnbWFpbC5jb20iLCJpc19wZGZpbGxlZCI6dHJ1ZSwiZXhwIjoxNzYyMjgxMDc0fQ.M2XWgNDOb_f4EaFTj7QGTyVTPZYNV37Nm4JeqiAI0Iw"  # Replace with actual token

class UserBehavior(HttpUser):
    wait_time = between(1, 3)  # seconds between requests

    @task
    def get_personal_data(self):
        self.client.get(
            f"{BASE_URL}/auth/get-personal-data",
            headers={"Authorization": f"Bearer {TOKEN}"}
        )

    # @task(2)  # weighted, runs more often
    def get_dashboard(self):
        self.client.get(
            f"{BASE_URL}/dashboard",
            headers={"Authorization": f"Bearer {TOKEN}"}
        )
