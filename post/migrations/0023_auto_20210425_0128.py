# Generated by Django 3.1.7 on 2021-04-24 22:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('post', '0022_auto_20210424_2332'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='need_moderate',
        ),
        migrations.AddField(
            model_name='post',
            name='moderate_desc',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='причина непройденной модерации'),
        ),
        migrations.AlterField(
            model_name='post',
            name='status',
            field=models.CharField(choices=[('published', 'опубликован'), ('unpublished', 'не опубликован'), ('archive', 'в архиве'), ('template', 'шаблон'), ('on_moderate', 'на модерации'), ('need_review', 'необходимы исправления'), ('moderate_false', 'модерация не пройдена')], default='unpublished', max_length=20, verbose_name='статус'),
        ),
    ]
