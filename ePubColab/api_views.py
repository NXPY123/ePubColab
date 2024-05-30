import base64
import hashlib
import os
import time

import celery
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework import permissions, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from ePubColab.models import Book, BookUploadTask, Highlights, SharedBook
from ePubColab.serializers import (
    BookSerializer,
    HighlightsSerializer,
    SharedBookSerializer,
    UpdateUserSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if (
            self.action == "create"
            or self.action == "update"
            or self.action == "destroy"
        ):
            return UpdateUserSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == "create":
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
        file = request.data["file"]
        if file.size > 10000000:  # Max file size is 10MB
            return Response({"error": "File size is greater than 10MB"}, status=400)
        if not file.name.endswith(".epub"):
            return Response({"error": "File type is not epub"}, status=400)

        token = request.headers["Authorization"].split(" ")[1]
        # Create directory for the user if it does not exist.
        os.makedirs(
            settings.MEDIA_ROOT + "/" + Token.objects.get(key=token).user.username,
            exist_ok=True,
        )
        user = Token.objects.get(key=token).user
        book = BookSerializer(data={"epub": file, "user": user.id})
        if book.is_valid():
            book_obj = book.save()
            task_id = BookUploadTask.objects.get(book=book_obj.epub).task_id
            return Response(
                {
                    "processing": "File uploading. Check progress using task_id",
                    "task_id": task_id,
                },
                status=200,
            )
        return Response(book.errors, status=400)

    def delete(self, request):
        epub = request.data["epub"]
        book = Book.objects.get(
            epub=epub,
            user=Token.objects.get(
                key=request.headers["Authorization"].split(" ")[1]
            ).user.id,
            status="LIVE",
        )
        try:
            book.status = "DELETED"
            book.save()
        except Exception as e:
            return Response({"error": str(e)}, status=400)

        return Response({"success": "File deleted successfully"}, status=200)

    def list(self, request):
        token = request.headers["Authorization"].split(" ")[1]
        user = Token.objects.get(key=token).user
        books = Book.objects.filter(user=user.id, status="LIVE")
        return Response(books.values())

    def update(self, request, pk=None):
        epub = request.data["epub"]
        new_epub = request.data["new_epub"]
        book = Book.objects.get(
            epub=epub,
            user=Token.objects.get(
                key=request.headers["Authorization"].split(" ")[1]
            ).user.id,
            status="LIVE",
        )
        # Check that new_epub and epub match till before the last slash.
        if new_epub.rsplit("/", 1)[0] != epub.rsplit("/", 1)[0]:
            return Response({"error": "File paths do not match"}, status=400)
        if not new_epub.endswith(".epub"):
            return Response({"error": "File type is not epub"}, status=400)
        book.epub = new_epub
        book.save()
        # Update the file in the storage.
        os.rename(epub, new_epub)
        return Response({"success": "File updated successfully"}, status=200)

    def download_link(self, request):
        file_path = request.GET.get("epub")

        # Check if the file exists and file belongs to the user
        def generate_secure_link(file_path):
            expires = int(time.time()) + 3600  # Link valid for 1 hour
            secret_key = settings.NGINX_SECURE_LINK_SECRET_KEY
            print(secret_key)
            secure_string = f"{expires}{file_path} {secret_key}"
            md5_hash = hashlib.md5(str(secure_string).encode("utf-8")).digest()
            base64_hash = base64.urlsafe_b64encode(md5_hash)
            str_hash = base64_hash.decode("utf-8").rstrip("=")
            secure_link = f"{file_path}?md5={str_hash}&expires={expires}"
            return Response({"secure_link": secure_link}, status=200)

        try:
            file = Book.objects.get(epub=file_path)
            user = Token.objects.get(
                key=request.headers["Authorization"].split(" ")[1]
            ).user
            if (
                file.user != user
                and not SharedBook.objects.filter(
                    epub=file.id, shared_with=user.id
                ).exists()
            ):
                return Response(
                    {"error": "File does not belong to the user"}, status=400
                )
        except Book.DoesNotExist:
            return Response({"error": "File does not exist"}, status=400)
        file_path = file_path.split("ePubColab")[1]
        return generate_secure_link(file_path)

    def upload_status(self, request, task_id):
        task = celery.result.AsyncResult(task_id)
        if task.status == "SUCCESS":
            return JsonResponse({"status": "SUCCESS"}, status=200)
        elif task.status == "FAILURE":
            return JsonResponse({"status": "FAILURE"}, status=400)
        else:
            return JsonResponse({"status": "PENDING"}, status=200)


class SharedFileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows shared files to be viewed.
    """

    permission_classes = [permissions.IsAuthenticated]
    queryset = SharedBook.objects.all()
    serializer_class = SharedBookSerializer

    def list(self, request):
        token = request.headers["Authorization"].split(" ")[1]
        user = Token.objects.get(key=token).user
        return Response(
            {
                "books_recieved": user.received_books.values(),
                "books_shared": user.shared_books.values(),
            }
        )

    def create(self, request):
        epub = request.data["epub"]
        shared_with = request.data["shared_with"]
        user = Token.objects.get(
            key=request.headers["Authorization"].split(" ")[1]
        ).user
        if user.username == request.data["shared_with"]:
            return Response({"error": "Cannot share file with yourself"}, status=400)
        shared_with_user = User.objects.get(username=shared_with)
        book = Book.objects.get(epub=epub, user=user.id, status="LIVE")
        shared_book = SharedBookSerializer(
            data={"epub": book.id, "user": user.id, "shared_with": shared_with_user.id}
        )
        if shared_book.is_valid():
            shared_book.save()
            return Response({"success": "File shared successfully"}, status=200)
        return Response(shared_book.errors, status=400)

    def delete(self, request):
        epub = request.data["epub"]
        shared_with = request.data["shared_with"]
        user = Token.objects.get(
            key=request.headers["Authorization"].split(" ")[1]
        ).user
        shared_with_user = User.objects.get(username=shared_with)
        book = Book.objects.get(epub=epub, user=user.id)
        shared_book = SharedBook.objects.get(
            epub=book.id, shared_with=shared_with_user.id, user=user.id
        )
        shared_book.delete()
        return Response({"success": "File unshared successfully"}, status=200)


class HighlightsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows highlights to be viewed, created and deleted.
    """

    permission_classes = [permissions.IsAuthenticated]
    queryset = Highlights.objects.all()
    serializer_class = HighlightsSerializer

    def access_check(self, epub_id, user):
        try:
            book = Book.objects.get(id=epub_id)
        except Book.DoesNotExist:
            return False
        try:
            if (
                book.user.id != user.id
                and not SharedBook.objects.filter(
                    epub=epub_id, shared_with=user.id
                ).exists()
            ):
                return False
        except SharedBook.DoesNotExist:
            return False
        return True

    def list(self, request):
        token = request.headers["Authorization"].split(" ")[1]
        user = Token.objects.get(key=token).user
        epub_id = request.GET.get("epub_id")
        # Check if the user has access to the file.
        if not self.access_check(epub_id, user):
            return Response(
                {"error": "User does not have access to the file"}, status=400
            )
        highlights = Highlights.objects.filter(book=epub_id)
        return Response(highlights.values())

    def create(self, request):
        token = request.headers["Authorization"].split(" ")[1]
        user = Token.objects.get(key=token).user
        epub_id = request.data["epub_id"]
        # Check if the user has access to the file.
        if not self.access_check(epub_id, user):
            return Response(
                {"error": "User does not have access to the file"}, status=400
            )
        data = {
            "book": epub_id,
            "user": user.id,
            "highlight": request.data["highlight"],
            "cfi": request.data["cfi"],
            "note": request.data.get("note", ""),
        }
        highlight = HighlightsSerializer(data=data)
        if highlight.is_valid():
            highlight.save()
            return Response({"success": "Highlight created successfully"}, status=200)
        return Response(highlight.errors, status=400)

    def delete(self, request):
        token = request.headers["Authorization"].split(" ")[1]
        user = Token.objects.get(key=token).user
        epub_id = request.data["epub_id"]
        # Check if the user has access to the file.
        if not self.access_check(epub_id, user):
            return Response(
                {"error": "User does not have access to the file"}, status=400
            )
        cfi = request.data["cfi"]
        highlight = Highlights.objects.get(book=epub_id, user=user.id, cfi=cfi)
        highlight.delete()
        return Response({"success": "Highlight deleted successfully"}, status=200)

    def update(self, request, pk=None):
        token = request.headers["Authorization"].split(" ")[1]
        user = Token.objects.get(key=token).user
        epub_id = request.data["epub_id"]
        # Check if the user has access to the file.
        if not self.access_check(epub_id, user):
            return Response(
                {"error": "User does not have access to the file"}, status=400
            )
        cfi = request.data["cfi"]
        highlight = Highlights.objects.get(book=epub_id, user=user.id, cfi=cfi)
        highlight.highlight = request.data["highlight"]
        highlight.note = request.data.get("note", "")
        highlight.save()
        return Response({"success": "Highlight updated successfully"}, status=200)
