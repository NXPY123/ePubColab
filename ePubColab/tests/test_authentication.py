from django.test import TestCase
from rest_framework.test import APIClient

class UserTestCase(TestCase):
    def setUp(self):
        # Create a user
        self.client = APIClient()
        self.client.post('/users/', data={'username':'testuser', 'password':'testpassword', 'email':'testuser@gmail.com'})

        # Create token for the user
        response = self.client.post('/api-token-auth/', data={'username':'testuser', 'password':'testpassword'})
        self.token = response.json()['token']

        # Get the url of the user by sending a get request to /users/ endpoint.
        response = self.client.get('/users/', headers={'Authorization': 'Token ' + self.token})
        self.url = response.json()[0]["url"]


    def test_user(self):
        # Send get request to the API.
        response = self.client.get('/users/', headers={'Authorization': 'Token ' + self.token} )
        self.assertEqual(response.status_code, 200)
        self.assertIn('testuser', response.json()[0]["username"])

    def test_edit_user(self):
        # Send put request to the API.
        response = self.client.put(self.url, data={'username':'testusernew', 'password':'testusernewpassword', 'email':'testusernew@gmail.com'}, headers={'Authorization': 'Token ' + self.token})
        self.assertEqual(response.status_code, 200)
        self.assertIn('testusernew', response.json()["username"])
        self.assertNotIn('testuser', response.json())
