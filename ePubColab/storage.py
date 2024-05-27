import os

from django.apps import apps
from django.conf import settings
from django.core.files.storage import Storage

from .tasks import upload_file


class ePubStorage(Storage):
    def __init__(self, url=None):
        self.url = url
        if url is None:
            self.url = settings.MEDIA_ROOT

    def _save(self, name, content):
        print(name)
        result = upload_file.delay(name, content)
        BookUploadTask = apps.get_model("ePubColab", "BookUploadTask")
        BookUploadTask.objects.create(book=name, task_id=result.id)
        return name

    def _open(self, name, mode="rb"):
        return open(name, mode)

    def exists(self, name):
        return os.path.exists(name)

    def delete(self, name):
        os.remove(name)
