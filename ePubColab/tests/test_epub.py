from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
import os
from ePubColab.models import Book
from django.conf import settings

class ePubTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):

        cls.client = APIClient()
        cls.client.post('/users/', data={'username':'testuser', 'password':'testpassword', 'email':'testuser@gmail.com'})

        response = cls.client.post('/api-token-auth/', data={'username':'testuser', 'password':'testpassword'})
        cls.token = response.json()['token']

        cls.headers = {'Authorization': 'Token ' + cls.token}
        response = cls.client.get('/users/', headers=cls.headers)
        cls.url = response.json()[0]["url"]

        os.makedirs('./ePubColab/tests/media', exist_ok=True)
        # Create a file in the media directory
        with open('./ePubColab/tests/media/test.epub', 'w') as f:
            f.write('This is a test file')

        # Upload the file 
        with open('./ePubColab/tests/media/test.epub', 'rb') as f:
            cls.client.post('/files/', data={'file': f}, headers=cls.headers)

        response = cls.client.get('/files/', headers=cls.headers)
        cls.filepath = response.json()[0]["epub"]
        print(cls.filepath)

    def test_upload_file(self):
        response = self.client.get('/files/', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.filepath, response.json()[0]["epub"])

    def test_delete_file(self):
        # Send delete request to the API.
        response = self.client.delete('/files/', data={"epub": self.filepath}, headers=self.headers, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        # Query the file to check if status is 'DELETED'.
        file = Book.objects.all()
        self.assertEqual(file[0].status, 'DELETED')
    
    # Delete the media directory with the files after the tests are done.
    @classmethod
    def tearDownClass(cls):
        os.remove(settings.MEDIA_ROOT + "testuser/test.epub")
        os.rmdir(settings.MEDIA_ROOT + 'testuser')

