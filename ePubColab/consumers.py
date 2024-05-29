import json
from time import sleep

from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.room_individual_user_group_name = (
            f"chat_{self.room_name}_user_{self.scope['user'].username}"
        )

        if self.scope["user"].is_anonymous:
            await self.close()
            return

        await self.add_group_user()
        await self.assign_group_owner()
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.channel_layer.group_add(
            self.room_individual_user_group_name, self.channel_name
        )
        await self.accept()

    async def assign_group_owner(self):
        owner_key = f"{self.room_group_name}_owner"
        lock_key = f"{self.room_group_name}_group_owner_lock"
        lock_acquired = False
        while not lock_acquired:
            sleep(0.1)
            lock_acquired = cache.add(lock_key, True, 2)
        try:
            if cache.get(owner_key) is None:
                cache.set(owner_key, self.scope["user"].username)
                self.is_owner = True
                await self.send(text_data=json.dumps({"owner": True}))
            else:
                self.is_owner = False
                await self.send(text_data=json.dumps({"owner": False}))
        except Exception as e:
            print(e)
        finally:
            cache.delete(lock_key)

    async def add_group_user(self):
        lock_key = f"{self.room_group_name}_group_user_lock"
        user_list_key = f"{self.room_group_name}_users"
        lock_acquired = False
        while not lock_acquired:
            sleep(0.1)
            lock_acquired = cache.add(lock_key, True, 2)
        try:
            user_list = cache.get(user_list_key)
            if user_list is None:
                user_list = "[]"
            user_list = json.loads(user_list)
            user_list.append(self.scope["user"].username)
            cache.set(user_list_key, json.dumps(user_list))
        except Exception as e:
            print(e)
        finally:
            cache.delete(lock_key)

    async def disconnect(self, close_code):
        # Leave room group
        if self.is_owner:
            await self.reassign_group_owner()
            self.is_owner = False
        lock_key = f"{self.room_group_name}_group_user_lock"
        user_list_key = f"{self.room_group_name}_users"
        lock_acquired = False
        await self.remove_group_user()
        await self.channel_layer.group_discard(
            self.room_individual_user_group_name, self.channel_name
        )
        while not lock_acquired:
            sleep(0.1)
            lock_acquired = cache.add(lock_key, True, 2)
        try:
            user_list = cache.get(user_list_key)
            if user_list is None:
                await self.channel_layer.group_discard(
                    self.room_group_name, self.channel_name
                )
        except Exception as e:
            print(e)
        finally:
            cache.delete(lock_key)

    async def remove_group_user(self):
        lock_key = f"{self.room_group_name}_group_user_lock"
        user_list_key = f"{self.room_group_name}_users"
        lock_acquired = False
        while not lock_acquired:
            sleep(0.1)
            lock_acquired = cache.add(lock_key, True, 2)
        try:
            user_list = cache.get(user_list_key)
            if user_list is None:
                user_list = "[]"
            user_list = json.loads(user_list)
            try:
                user_list.remove(self.scope["user"].username)
            except ValueError:
                pass
            cache.set(user_list_key, json.dumps(user_list))
            if len(user_list) == 0:
                cache.delete(user_list_key)
        except Exception as e:
            print(e)
        finally:
            cache.delete(lock_key)

    async def reassign_group_owner(self):
        lock_key = f"{self.room_group_name}_group_owner_lock"
        lock_acquired = False
        user_list_key = f"{self.room_group_name}_users"
        while not lock_acquired:
            sleep(0.1)
            lock_acquired = cache.add(lock_key, True, 2)
        try:
            user_list = cache.get(user_list_key)
            if user_list is None:
                user_list = "[]"
            user_list = json.loads(user_list)
            owner_key = f"{self.room_group_name}_owner"
            if user_list == []:
                cache.delete(owner_key)
            else:
                cache.set(owner_key, user_list[0])
                user_group = f"chat_{self.room_name}_user_{user_list[0]}"
                await self.channel_layer.group_send(
                    user_group, {"type": "chat.ownerMessage", "owner": True}
                )
            self.is_owner = False
            await self.send(text_data=json.dumps({"owner": False}))
        except Exception as e:
            print(e)
        finally:
            cache.delete(lock_key)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))

    async def chat_ownerMessage(self, event):
        owner = event["owner"]
        if owner:
            await self.send(text_data=json.dumps({"owner": True}))
        else:
            await self.send(text_data=json.dumps({"owner": False}))

    async def chat_userList(self, event):
        user_list = event["user_list"]
        await self.send(text_data=json.dumps({"user_list": user_list}))

    async def chat_userJoined(self, event):
        user = event["user"]
        await self.send(text_data=json.dumps({"user_joined": user}))

    async def kick_user(self, event):
        user = event["user"]
        # If the user sending the message is the owner, then kick the user
        if user == self.scope["user"].username:
            await self.send(text_data=json.dumps({"error": "Cannot kick yourself"}))
        if not self.is_owner:
            await self.send(
                text_data=json.dumps({"error": "You are not the owner of the room"})
            )
        user_room_group = f"chat_{self.room_name}_user_{user}"
        await self.channel_layer.group_send(
            user_room_group, {"type": "chat.kicked", "room_name": self.room_name}
        )

    async def chat_kicked(self, event):
        room_name = event["room_name"]
        if room_name == self.room_name:
            await self.send(text_data=json.dumps({"kicked": True}))
            await self.disconnect(1000)
        else:
            await self.send(text_data=json.dumps({"kicked": False}))
