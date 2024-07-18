import time

from locust import HttpUser, TaskSet, between, task


class UserBehavior(TaskSet):
    @task
    def test_user(self):
        self.client.get("/users/", headers=self.headers)

    @task
    def test_edit_user(self):
        self.client.put(
            self.url,
            data={
                "username": self.username + "new",
                "password": self.password + "new",
                "email": self.email + "new",
            },
            headers=self.headers,
        )

    @task
    def test_delete_user(self):
        self.client.delete(self.url, headers=self.headers)
        # Create user after delete
        self.on_start()


class QuickstartUser(HttpUser):
    wait_time = between(1, 2)
    tasks = [UserBehavior]

    # Create a unique user for each test
    def on_start(self):
        self.username = "testuser" + str(time.time())
        self.password = "testpassword"
        self.email = "testuser" + str(time.time()) + "@gmail.com"
        # Set host of the client
        self.client.post(
            "/users/",
            data={
                "username": self.username,
                "password": self.password,
                "email": self.email,
            },
        )

        response = self.client.post(
            "/api-token-auth/",
            data={"username": self.username, "password": self.password},
        )
        self.token = response.json()["token"]

        self.headers = {"Authorization": "Token " + self.token}
        response = self.client.get("/users/", headers=self.headers)
        self.url = response.json()[0]["url"]

    def on_stop(self):
        self.client.delete(self.url, headers=self.headers)
