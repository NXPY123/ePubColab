from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient


class UserTestCase(TestCase):
    def setUp(self):
        # Create a user
        self.client = APIClient()
        self.client.post(
            "/users/",
            data={
                "username": "testuser",
                "password": "testpassword",
                "email": "testuser@gmail.com",
            },
        )

        # Create token for the user
        response = self.client.post(
            "/api-token-auth/",
            data={"username": "testuser", "password": "testpassword"},
        )
        self.token = response.json()["token"]

        self.headers = {"Authorization": "Token " + self.token}
        # Get the url of the user by sending a get request to /users/ endpoint.
        response = self.client.get("/users/", headers=self.headers)
        self.url = response.json()[0]["url"]

    def test_user(self):
        # Send get request to the API.
        response = self.client.get("/users/", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("testuser", response.json()[0]["username"])

    def test_edit_user(self):
        # Send put request to the API.
        response = self.client.put(
            self.url,
            data={
                "username": "testusernew",
                "password": "testusernewpassword",
                "email": "testusernew@gmail.com",
            },
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("testusernew", response.json()["username"])
        self.assertNotIn("testuser", response.json())

    def test_delete_user(self):
        # Send delete request to the API.
        response = self.client.delete(self.url, headers=self.headers)
        self.assertEqual(response.status_code, 204)
        # Query the user to check if it still exists.
        user = User.objects.all()
        self.assertEqual(len(user), 0)
