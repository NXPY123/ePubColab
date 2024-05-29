# import asyncio
# import websockets
# from django.contrib.auth.models import User
# from django.test import TestCase
# from rest_framework.test import APIClient


# async def connect_websocket(headers):
#     uri = "ws://localhost:80/chat/room1/"
#     async with websockets.connect(uri, extra_headers=headers) as websocket:
#         await websocket.send({
#             "type": "chat.message",
#             "message": "Hello"
#         })
#         response = await websocket.recv()
#         print(response)


# class ChatTestCase(TestCase):
#     def setUp(cls):
#         # Create a user
#         cls.user = User.objects.create_user(
#             username='testuser', password='testpassword',
#             email="testuser@gmail.com"
#         )

#         # Get the token for the user
#         cls.client = APIClient()
#         response = cls.client.post(
#             "/api-token-auth/",
#             data={"username": "testuser", "password": "testpassword"},
#         )
#         cls.token = response.json()["token"]
#         cls.headers = {"Authorization": "Token " + cls.token}


#     def test_chat(self):
#         # Pass the token in the headers
#         # Send a message to the chat room
#         asyncio.get_event_loop().run_until_complete(connect_websocket(self.headers))
