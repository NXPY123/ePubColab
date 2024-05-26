from django.contrib.auth.models import User
from ePubColab.models import Book
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']

class UpdateUserSerializer(serializers.ModelSerializer): 
    # The CreateUserSerializer is used for creating, updating and deleting users.
    class Meta:
        model = User
        fields = ['username', 'password', 'email']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email']
        )
        return user
    
    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.set_password(validated_data.get('password', instance.password))
        instance.save()
        return instance
    
    def destroy(self, instance):
        instance.delete()
        return instance

class BookSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        
        return Book.objects.create(epub=validated_data["epub"], user=validated_data["user"])
    
    
    class Meta:
        model = Book
        fields = ['epub','user']
        unique_together = ('epub', 'user')
