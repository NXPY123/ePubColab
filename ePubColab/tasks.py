from celery import shared_task

@shared_task
def upload_file(name, content):
    with open(name, 'wb+') as destination:
        for chunk in content.chunks():
            destination.write(chunk)
    return name