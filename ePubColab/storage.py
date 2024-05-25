from django.core.files.storage import Storage
from django.conf import settings
import os

class ePubStorage(Storage):
    def __init__(self,url=None):
        self.url = url
        if url is None:
            self.url = settings.MEDIA_ROOT
    def _save(self, name, content):
        print(name)
        with open(name, 'wb+') as destination:
            for chunk in content.chunks():
                destination.write(chunk)
        return name
    
    def _open(self, name, mode='rb'):
        return open(name, mode)
    
    def exists(self, name):
        return os.path.exists(name)
    
    def delete(self, name):
        os.remove(name)
    

    
