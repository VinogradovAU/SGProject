# Generated by Django 3.1.7 on 2021-04-08 20:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('post', '0004_post_content'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='content',
        ),
    ]
