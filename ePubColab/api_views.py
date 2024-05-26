from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework import permissions, viewsets
from rest_framework.generics import CreateAPIView
from ePubColab.serializers import UserSerializer, UpdateUserSerializer, BookSerializer
import hashlib
import os
from ePubColab.models import Book
import time
from rest_framework.response import Response
from django.conf import settings


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

    def get_serializer_class(self): 
        if self.action == 'create' or self.action == 'update' or self.action=="destroy":
            return UpdateUserSerializer 
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
# Create endpoint to upload, delete and list files.
class FileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows files to be uploaded, deleted and listed.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def create(self, request):
        file = request.data['file']
        if file.size > 10000000: # Max file size is 10MB
            return Response({"error": "File size is greater than 10MB"}, status=400)
        if not file.name.endswith('.epub'):
            return Response({"error": "File type is not epub"}, status=400)

        token = request.headers['Authorization'].split(' ')[1]
        # Create directory for the user if it does not exist.
        os.makedirs(settings.MEDIA_ROOT + '/' + Token.objects.get(key=token).user.username, exist_ok=True)
        user = Token.objects.get(key=token).user
        book = BookSerializer(data={'epub': file, 'user': user.id})
        if book.is_valid():
            book.save()
            return Response({"success": "File uploaded successfully"}, status=200)
        return Response(book.errors, status=400)
    
    def delete(self, request):
        epub = request.data['epub']
        book = Book.objects.get(epub=epub, user=Token.objects.get(key=request.headers['Authorization'].split(' ')[1]).user.id, status="LIVE")
        try:
            book.status = "DELETED"
            book.save()
        except:
            return Response({"error": "File does not exist"}, status=400)
 
        return Response({"success": "File deleted successfully"}, status=200)
    
    def list(self, request):
        token = request.headers['Authorization'].split(' ')[1]
        user = Token.objects.get(key=token).user
        books = Book.objects.filter(user=user.id, status="LIVE")
        return Response(books.values())
    
    def update(self, request,pk=None):
        epub = request.data['epub']
        new_epub = request.data['new_epub']
        book = Book.objects.get(epub=epub, user=Token.objects.get(key=request.headers['Authorization'].split(' ')[1]).user.id, status="LIVE")
       # Check that new_epub and epub match till before the last slash.
        if new_epub.rsplit('/', 1)[0] != epub.rsplit('/', 1)[0]:
            return Response({"error": "File paths do not match"}, status=400)
        if not new_epub.endswith('.epub'):
            return Response({"error": "File type is not epub"}, status=400)
        book.epub = new_epub
        book.save()
        # Update the file in the storage.
        os.rename(epub, new_epub)
        return Response({"success": "File updated successfully"}, status=200)
    



