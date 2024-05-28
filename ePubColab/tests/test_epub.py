import os

from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient

from ePubColab.models import Book


class ePubTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.client.post(
            "/users/",
            data={
                "username": "testuser",
                "password": "testpassword",
                "email": "testuser@gmail.com",
            },
        )

        response = cls.client.post(
            "/api-token-auth/",
            data={"username": "testuser", "password": "testpassword"},
        )
        cls.token = response.json()["token"]

        cls.headers = {"Authorization": "Token " + cls.token}
        response = cls.client.get("/users/", headers=cls.headers)
        cls.url = response.json()[0]["url"]

        os.makedirs("./ePubColab/tests/media", exist_ok=True)
        # Create a file in the media directory
        with open("./ePubColab/tests/media/test.epub", "w") as f:
            f.write("This is a test file")

        # Upload the file
        with open("./ePubColab/tests/media/test.epub", "rb") as f:
            response = cls.client.post("/files/", data={"file": f}, headers=cls.headers)
            cls.task_id = response.json()["task_id"]

        response = cls.client.get("/files/", headers=cls.headers)
        cls.filepath = response.json()[0]["epub"]

        response = cls.client.get(f"/files/status/{cls.task_id}/", headers=cls.headers)
        TestCase().assertIn(response.json()["status"], ["SUCCESS", "PENDING"])

    def test_upload_file(self):
        response = self.client.get("/files/", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.filepath, response.json()[0]["epub"])

    def test_download_link(self):
        params = {"epub": self.filepath}
        response = self.client.get("/files/link/", params, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.filepath.split("/", 1)[1], response.json()["secure_link"])

    def test_delete_file(self):
        # Send delete request to the API.
        response = self.client.delete(
            "/files/",
            data={"epub": self.filepath},
            headers=self.headers,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        # Query the file to check if status is 'DELETED'.
        file = Book.objects.all()
        self.assertEqual(file[0].status, "DELETED")

    # Delete the media directory with the files after the tests are done.
    @classmethod
    def tearDownClass(cls):
        # Find and remove all files in the media/testuser directory
        for file in os.listdir(settings.MEDIA_ROOT + "testuser"):
            os.remove(settings.MEDIA_ROOT + "testuser/" + file)
        os.rmdir(settings.MEDIA_ROOT + "testuser")


class ePubShareTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.client.post(
            "/users/",
            data={
                "username": "testuser",
                "password": "testpassword",
                "email": "testuser@gmail.com",
            },
        )

        cls.test_token = cls.client.post(
            "/api-token-auth/",
            data={"username": "testuser", "password": "testpassword"},
        )

        cls.client.post(
            "/users/",
            data={
                "username": "testuser2",
                "password": "testpassword2",
                "email": "testuser2@gmail.com",
            },
        )

        cls.test_token2 = cls.client.post(
            "/api-token-auth/",
            data={"username": "testuser2", "password": "testpassword2"},
        )

        cls.headers = {"Authorization": "Token " + cls.test_token.json()["token"]}
        cls.headers2 = {"Authorization": "Token " + cls.test_token2.json()["token"]}
        response = cls.client.get("/users/", headers=cls.headers)
        cls.url = response.json()[0]["url"]
        cls.url2 = response.json()[1]["url"]

        os.makedirs("./ePubColab/tests/media", exist_ok=True)
        # Create a file in the media directory
        with open("./ePubColab/tests/media/test.epub", "w") as f:
            f.write("This is a test file")

        # Upload the file
        with open("./ePubColab/tests/media/test.epub", "rb") as f:
            response = cls.client.post("/files/", data={"file": f}, headers=cls.headers)

        response = cls.client.get("/files/", headers=cls.headers)
        cls.filepath = response.json()[0]["epub"]

    def test_share_file(self):
        response = self.client.post(
            "/shared/",
            data={"epub": self.filepath, "shared_with": "testuser2"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/shared/", headers=self.headers2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(2, response.json()["books_recieved"][0]["shared_with_id"])

    def test_secure_link(self):
        response = self.client.post(
            "/shared/",
            data={"epub": self.filepath, "shared_with": "testuser2"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        params = {"epub": self.filepath}
        response = self.client.get("/files/link/", params, headers=self.headers2)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.filepath.split("/", 1)[1], response.json()["secure_link"])

    def test_unshare_file(self):
        response = self.client.post(
            "/shared/",
            data={"epub": self.filepath, "shared_with": "testuser2"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.delete(
            "/shared/",
            data={"epub": self.filepath, "shared_with": "testuser2"},
            headers=self.headers,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/shared/", headers=self.headers2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(0, len(response.json()["books_recieved"]))


class ePubHighlightTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.client.post(
            "/users/",
            data={
                "username": "testuser",
                "password": "testpassword",
                "email": "testuser@gmail.com",
            },
        )

        cls.test_token = cls.client.post(
            "/api-token-auth/",
            data={"username": "testuser", "password": "testpassword"},
        )

        cls.client.post(
            "/users/",
            data={
                "username": "testuser2",
                "password": "testpassword2",
                "email": "testuser2@gmail.com",
            },
        )

        cls.test_token2 = cls.client.post(
            "/api-token-auth/",
            data={"username": "testuser2", "password": "testpassword2"},
        )

        cls.headers = {"Authorization": "Token " + cls.test_token.json()["token"]}
        cls.headers2 = {"Authorization": "Token " + cls.test_token2.json()["token"]}
        response = cls.client.get("/users/", headers=cls.headers)
        cls.url = response.json()[0]["url"]
        cls.url2 = response.json()[1]["url"]

        os.makedirs("./ePubColab/tests/media", exist_ok=True)
        # Create a file in the media directory
        with open("./ePubColab/tests/media/test.epub", "w") as f:
            f.write("This is a test file")

        # Upload the file
        with open("./ePubColab/tests/media/test.epub", "rb") as f:
            response = cls.client.post("/files/", data={"file": f}, headers=cls.headers)

        response = cls.client.get("/files/", headers=cls.headers)
        cls.filepath = response.json()[0]["epub"]

        response = cls.client.post(
            "/shared/",
            data={"epub": cls.filepath, "shared_with": "testuser2"},
            headers=cls.headers,
        )

        response = cls.client.get("/shared/", headers=cls.headers2)
        cls.shared_file_id = response.json()["books_recieved"][0]["id"]
        cls.params = {"epub_id": cls.shared_file_id}

    def test_highlight(self):
        response = self.client.post(
            "/highlights/",
            data={
                "epub_id": self.shared_file_id,
                "highlight": "This is a test highlight",
                "cfi": "testcfi",
                "note": "This is a test note",
            },
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/highlights/", self.params, headers=self.headers2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(response.json()))

    def test_delete_highlight(self):
        response = self.client.post(
            "/highlights/",
            data={
                "epub_id": self.shared_file_id,
                "highlight": "This is a test highlight",
                "cfi": "testcfi",
                "note": "This is a test note",
            },
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/highlights/", self.params, headers=self.headers2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(response.json()))
        response = self.client.delete(
            "/highlights/",
            data={"epub_id": self.shared_file_id, "cfi": "testcfi"},
            headers=self.headers,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/highlights/", self.params, headers=self.headers2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(0, len(response.json()))

    def test_update_highlight(self):
        response = self.client.post(
            "/highlights/",
            data={
                "epub_id": self.shared_file_id,
                "highlight": "This is a test highlight",
                "cfi": "testcfi",
                "note": "This is a test note",
            },
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/highlights/", self.params, headers=self.headers2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(response.json()))
        response = self.client.put(
            "/highlights/" + str(self.shared_file_id) + "/",
            data={
                "epub_id": self.shared_file_id,
                "highlight": "This is an updated highlight",
                "cfi": "testcfi",
                "note": "This is an updated note",
            },
            headers=self.headers,
            content_type="application/json",
        )
        print(response.json())
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/highlights/", self.params, headers=self.headers2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(response.json()))
        self.assertEqual(
            "This is an updated highlight", response.json()[0]["highlight"]
        )
        self.assertEqual("This is an updated note", response.json()[0]["note"])

    def test_create_highlight_without_note(self):
        response = self.client.post(
            "/highlights/",
            data={
                "epub_id": self.shared_file_id,
                "highlight": "This is a test highlight",
                "cfi": "testcfi",
            },
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/highlights/", self.params, headers=self.headers2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(response.json()))
        self.assertEqual("", response.json()[0]["note"])

    def test_create_highlight_in_shared_file(self):
        response = self.client.post(
            "/highlights/",
            data={
                "epub_id": self.shared_file_id,
                "highlight": "This is a test highlight",
                "cfi": "testcfi",
            },
            headers=self.headers2,
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/highlights/", self.params, headers=self.headers2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(response.json()))

    def test_delete_highlight_in_shared_file(self):
        response = self.client.post(
            "/highlights/",
            data={
                "epub_id": self.shared_file_id,
                "highlight": "This is a test highlight",
                "cfi": "testcfi",
            },
            headers=self.headers2,
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/highlights/", self.params, headers=self.headers2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(response.json()))
        response = self.client.delete(
            "/highlights/",
            data={"epub_id": self.shared_file_id, "cfi": "testcfi"},
            headers=self.headers2,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/highlights/", self.params, headers=self.headers2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(0, len(response.json()))

    def test_update_highlight_in_shared_file(self):
        response = self.client.post(
            "/highlights/",
            data={
                "epub_id": self.shared_file_id,
                "highlight": "This is a test highlight",
                "cfi": "testcfi",
            },
            headers=self.headers2,
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/highlights/", self.params, headers=self.headers2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(response.json()))
        response = self.client.put(
            "/highlights/" + str(self.shared_file_id) + "/",
            data={
                "epub_id": self.shared_file_id,
                "highlight": "This is an updated highlight",
                "cfi": "testcfi",
            },
            headers=self.headers2,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/highlights/", self.params, headers=self.headers2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(response.json()))
        self.assertEqual(
            "This is an updated highlight", response.json()[0]["highlight"]
        )

    def test_get_highlight_in_shared_file(self):
        response = self.client.post(
            "/highlights/",
            data={
                "epub_id": self.shared_file_id,
                "highlight": "This is a test highlight",
                "cfi": "testcfi",
            },
            headers=self.headers2,
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/highlights/", self.params, headers=self.headers2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(response.json()))
        self.assertEqual("This is a test highlight", response.json()[0]["highlight"])
        self.assertEqual("testcfi", response.json()[0]["cfi"])
