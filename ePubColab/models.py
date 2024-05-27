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
