# Generated by Django 5.0.6 on 2024-05-26 17:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ePubColab", "0004_alter_book_unique_together"),
    ]

    operations = [
        migrations.CreateModel(
            name="BookUploadTask",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("book", models.CharField(max_length=200)),
                ("task_id", models.CharField(max_length=200)),
            ],
            options={
                "unique_together": {("book", "task_id")},
            },
        ),
    ]
