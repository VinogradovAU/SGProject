# Generated by Django 3.1.7 on 2021-04-20 20:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('post', '0019_auto_20210420_2342'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='author_id',
            new_name='author',
        ),
        migrations.RenameField(
            model_name='comment',
            old_name='comment_post_id',
            new_name='comment_post',
        ),
        migrations.RenameField(
            model_name='post',
            old_name='user_id',
            new_name='user',
        ),
        migrations.RenameField(
            model_name='postkarma',
            old_name='post_id',
            new_name='post',
        ),
        migrations.RenameField(
            model_name='postkarma',
            old_name='user_id',
            new_name='user',
        ),
    ]
