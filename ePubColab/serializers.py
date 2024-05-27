from django.contrib.auth.models import User
from rest_framework import serializers

from ePubColab.models import Book, Highlights, SharedBook


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "groups"]


class UpdateUserSerializer(serializers.ModelSerializer):
    # The CreateUserSerializer is used for creating, updating and deleting users.
    class Meta:
        model = User
        fields = ["username", "password", "email"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data["email"],
        )
        return user

    def update(self, instance, validated_data):
        instance.username = validated_data.get("username", instance.username)
        instance.email = validated_data.get("email", instance.email)
        instance.set_password(validated_data.get("password", instance.password))
        instance.save()
        return instance

    def destroy(self, instance):
        instance.delete()
        return instance


class BookSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        return Book.objects.create(
            epub=validated_data["epub"], user=validated_data["user"]
        )

    class Meta:
        model = Book
        fields = ["epub", "user"]
        unique_together = ("epub", "user")


class SharedBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedBook
        fields = ["epub", "shared_with", "user"]
        unique_together = ("epub", "shared_with", "user")


class HighlightsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Highlights
        fields = ["book", "user", "highlight", "cfi", "note"]
        unique_together = ("book", "user", "cfi")
