from django.db import models
from .storage import ePubStorage
from django.conf import settings
def user_directory_path(instance, filename):
    return settings.MEDIA_ROOT + '{0}/{1}'.format(instance.user.username, filename)



class Book(models.Model):
    epub = models.FileField(upload_to=user_directory_path, storage=ePubStorage)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('epub', 'user')