from django.db import models
from authapp.models import HubUser, HubUserProfile
from hub.models import HubCategory, Hub

from tinymce.models import HTMLField

# Create your models here.

NULLABLE = {'blank': True, 'null': True}


class Post(models.Model):

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ('-created_at',)

    name = models.CharField(max_length=200, verbose_name='название', )
    short_desc = models.CharField(max_length=200, verbose_name='краткое описание', )
    post_text = models.TextField(verbose_name='пост', blank=False, null=True)
    hub_category = models.ForeignKey(HubCategory, related_name='hub_category',
                                     verbose_name='подкатегория', on_delete=models.CASCADE, **NULLABLE)
    published = models.BooleanField(default=False)
    user_id = models.ForeignKey(HubUser, related_name='user_id', on_delete=models.CASCADE, **NULLABLE)
    created_at = models.DateTimeField(verbose_name='время создания', auto_now_add=True, )
    updated_at = models.DateTimeField(verbose_name='время обновления', auto_now=True, )

    # Метод возвращает посты конкретного пользователя
    # pk - id пользователя
    @staticmethod
    def get_user_posts(pk):
        return Post.objects.filter(user=pk).order_by('updated_at')

    def __str__(self):
        return f'{self.name} ({self.hub_category.name})'

    # Метод возвращает все посты всех пользователей и сортирует по дате
    @staticmethod
    def get_all_posts():
        return Post.objects.all().order_by('updated_at')

