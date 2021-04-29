import json

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.shortcuts import redirect

from authapp.models import HubUser, HubUserProfile
from hub.models import HubCategory, Hub
from ckeditor.fields import RichTextField

# Create your models here.

NULLABLE = {'blank': True, 'null': True}


class Tags(models.Model):
    tag = models.CharField(max_length=200, verbose_name='тэг поста')


class Post(models.Model):
    STATUS_PUBLISHED = 'published'
    STATUS_UNPUBLISHED = 'unpublished'
    STATUS_ARCHIVE = 'archive'
    STATUS_TEMPLATE = 'template'
    STATUS_ON_MODERATE = 'on_moderate'
    STATUS_NEED_REVIEW = 'need_review'
    STATUS_MODERATE_FALSE = 'moderate_false'

    STATUSES = (
        (STATUS_PUBLISHED, 'опубликован'),
        (STATUS_UNPUBLISHED, 'не опубликован'),
        (STATUS_ARCHIVE, 'в архиве'),
        (STATUS_TEMPLATE, 'шаблон'),
        (STATUS_ON_MODERATE, 'на модерации'),
        (STATUS_NEED_REVIEW, 'необходимы исправления'),
        (STATUS_MODERATE_FALSE, 'модерация не пройдена'),
    )

    class Meta:
        verbose_name = 'пост'
        verbose_name_plural = 'Посты'
        ordering = ('-created_at',)

    name = models.CharField(max_length=200, verbose_name='название', )
    hub_category = models.ForeignKey(HubCategory, related_name='hub_category',
                                     verbose_name='подкатегория', on_delete=models.CASCADE, **NULLABLE)
    status = models.CharField(verbose_name='статус', choices=STATUSES, default=STATUS_UNPUBLISHED, max_length=20)
    # need_moderate = models.BooleanField(default=False, verbose_name='нужна модерация')
    moderate_desc = models.CharField(max_length=200, verbose_name='причина непройденной модерации', **NULLABLE)
    moderated = models.BooleanField(default=False, verbose_name='модерация проводилась', )
    moderated_at = models.DateTimeField(verbose_name='время модерации', **NULLABLE)
    user = models.ForeignKey(HubUser, related_name='user_id', verbose_name='пользователь', on_delete=models.CASCADE,
                             **NULLABLE)
    karma_count = models.IntegerField(default=0, verbose_name='количество кармы')
    created_at = models.DateTimeField(verbose_name='время создания', auto_now_add=True, )
    updated_at = models.DateTimeField(verbose_name='время обновления', auto_now=True, )
    content = RichTextField()
    tags = models.ManyToManyField(Tags, verbose_name='тэги поста')

    # Метод возвращает посты конкретного пользователя
    # pk - id пользователя
    @staticmethod
    def get_user_posts(pk):
        return Post.objects.filter(user=pk).order_by('-updated_at')

    def __str__(self):
        return f'{self.name} ({self.hub_category.name})'

    # Метод возвращает все посты всех пользователей и сортирует по дате
    @staticmethod
    def get_all_posts():
        return Post.objects.filter(status=Post.STATUS_PUBLISHED).order_by('-updated_at')
      
    # подсчет постов на модерации
    @staticmethod
    def on_moderate_count():
        return Post.objects.filter(status=Post.STATUS_ON_MODERATE).count()

    # свойство класса для интерактивного подсчета кармы
    @property
    def post_karma(self):
        karma_objects = self.post_id.all()
        karma = 0
        for obj in karma_objects:
            karma += obj.karma
        return karma

    def clean_tags(self):
        Post.objects.get(id=self.id).clean()

    def get_all_tags(self):
        res = ''
        all_tags = Post.objects.get(id=self.id).tags.all()
        if all_tags:
            for tag in all_tags:
                res = res + str(tag.tag) + ', '
            res = res[:-2]
            return res
        return f'[Тэги не заданы]'


def get_all_tags(pk):
    res = ''
    all_tags = Post.objects.get(id=pk).tags.all()
    for tag in all_tags:
        res = res + str(tag.tag) + ', '
    res = res[:-2]
    return res


class PostKarma(models.Model):
    class Meta:
        verbose_name = 'карма поста'
        verbose_name_plural = 'Карма постов'
        ordering = ('-created_at',)

    post = models.ForeignKey(Post, related_name='post_id', on_delete=models.CASCADE, verbose_name='пост',
                             **NULLABLE)
    user = models.ForeignKey(HubUser, related_name='post_karma', on_delete=models.CASCADE,
                             verbose_name='пользователь', **NULLABLE)
    karma = models.SmallIntegerField(verbose_name='карма', **NULLABLE)
    created_at = models.DateTimeField(verbose_name='время создания', auto_now_add=True)

    def __str__(self):
        return f'{self.user} - "{self.post}": {self.karma}'


class Comment(models.Model):
    class Meta:
        db_table = "comments"

    published = models.BooleanField(default=True)  # True - опубликован, False - удалено
    path = ArrayField(models.IntegerField())
    comment_post = models.ForeignKey(Post, related_name='comment_post_id', verbose_name='пост',
                                     on_delete=models.CASCADE, **NULLABLE)
    author = models.ForeignKey(HubUser, related_name='author_id', verbose_name='пользователь', on_delete=models.CASCADE,
                               **NULLABLE)
    content = models.TextField(verbose_name='комментарий')
    created_at = models.DateTimeField(verbose_name='время создания', auto_now_add=True)

    def __str__(self):
        return self.content[0:200]

    def get_offset(self):
        level = len(self.path) - 1
        if level > 5:
            level = 5
        return level

    def get_col(self):
        level = len(self.path) - 1
        if level > 5:
            level = 5
        return 12 - level

    def get_absolute_url(self):
        return f'/post/{self.comment_post.pk}/'

    # свойство класса для интерактивного подсчета кармы
    @property
    def comment_karma(self):
        karma_objects = self.karma.all()
        karma = 0
        for obj in karma_objects:
            karma += obj.karma
        return karma


def get_all_comments(user_id):
    ''':user_id - id пользователя
        :return - возвращает словарь объектов { пост: [комментарий,...]}
    '''

    comments_dict = {}

    comments = Comment.objects.filter(author=user_id)
    if comments:
        for comment in comments:
            post = Post.objects.get(id=comment.comment_post.id)
            list_comm = []  # список объектов comment конкретного поста
            for el in comments:
                if el.comment_post.id == post.id:
                    list_comm.append(el)
            comments_dict[post] = list_comm

            # для поста собрали список комментов

        # print(f'comments_dict: {comments_dict}')

        return comments_dict

    comments_dict = {}
    # нет коментов у пользователя
    return comments_dict


class CommentKarma(models.Model):
    class Meta:
        verbose_name = 'карма комментария'
        verbose_name_plural = 'Карма комментариев'
        ordering = ('-created_at',)

    comment = models.ForeignKey(Comment, related_name='karma', on_delete=models.CASCADE, verbose_name='комментарий',
                                **NULLABLE)
    user = models.ForeignKey(HubUser, related_name='comment_karma_user', on_delete=models.CASCADE,
                             verbose_name='пользователь', **NULLABLE)
    karma = models.SmallIntegerField(verbose_name='карма', **NULLABLE)
    created_at = models.DateTimeField(verbose_name='время создания', auto_now_add=True)

    def __str__(self):
        return f'{self.user} - "{self.comment}": {self.karma}'
