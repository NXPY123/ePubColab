from django.conf import settings
from django.db import models

from .storage import ePubStorage


def user_directory_path(instance, filename):
    return settings.MEDIA_ROOT + "{0}/{1}".format(instance.user.username, filename)


class Book(models.Model):
    epub = models.FileField(upload_to=user_directory_path, storage=ePubStorage)
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    status = models.CharField(max_length=100, default="LIVE")

    class Meta:
        unique_together = ("epub", "user")


class BookUploadTask(models.Model):
    book = models.CharField(max_length=200)
    task_id = models.CharField(max_length=200)

    class Meta:
        unique_together = ("book", "task_id")


class SharedBook(models.Model):
    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="shared_books"
    )
    epub = models.ForeignKey(Book, on_delete=models.CASCADE)
    shared_with = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="received_books"
    )

    class Meta:
        unique_together = ("epub", "shared_with", "user")


class Highlights(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    highlight = models.TextField()
    cfi = models.CharField(max_length=200)
    note = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("book", "user", "cfi")
