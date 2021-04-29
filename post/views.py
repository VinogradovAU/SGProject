import json
from datetime import datetime, timedelta

import pytz
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, Count, F
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect

from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, CreateView, ListView, UpdateView

from authapp.models import HubUser
from backend import settings
from backend.utils import LoginRequiredDispatchMixin
from hub.models import get_hub_cats_dict
from post.forms import PostEditForm, PostCreationForm, CommentForm, PostModeratorEditForm
from post.models import Post, PostKarma, Comment, get_all_comments, CommentKarma, Tags, get_all_tags


def perform_karma_update(post, user, karma):
    """
    Функция выполняющая несколько проверок, прежде чем поставить карму для поста.
    Сначала функция проверяет, чтобы юзер не оценивал свой собственный пост.
    Далее функция проверяет, чтобы юзер оценивал пост в первый раз (повторно оценивать пост нельзя).
    Если все проверки пройдены, то функция возвращает соответствующий ответ в формате JSON.

    :param post: идентификатор поста, с которым взаимодействуют
    :param user: идентификатор пользователя, который взаимодействует
    :param karma: оценка, может быть 1 или -1
    :return:
    """
    if user.banned != 'active':
        return JsonResponse({'result': 'Действие недоступно для забаненных пользователей'})

    else:

        already_liked = PostKarma.objects.filter(Q(user=user.id) & Q(post=post.id))

        if user.id == post.user.id:

            resp = 'Нельзя оценивать свой собственный пост!'
            return JsonResponse({'result': resp})
        elif not already_liked:
            new_object = PostKarma.objects.create(post=post, user=user, karma=karma)
            new_object.save()
            post.karma_count = F('karma_count') + karma
            post.save()
            updated_post_karma = Post.objects.filter(id=post.id).first().post_karma
            return JsonResponse({'result': str(updated_post_karma)})
        else:
            already_liked.delete()
            if post.karma_count >= 0:
                post.karma_count = F('karma_count') - 1
            else:
                post.karma_count = F('karma_count') + 1
            post.save()
            updated_post_karma = Post.objects.filter(id=post.id).first().post_karma
            return JsonResponse({'result': str(updated_post_karma)})


def perform_comment_karma_update(post, comment, user, karma):
    """
    Функция выполняющая несколько проверок, прежде чем поставить карму для поста.
    Сначала функция проверяет, чтобы юзер не оценивал свой собственный пост.
    Далее функция проверяет, чтобы юзер оценивал пост в первый раз (повторно оценивать пост нельзя).
    Если все проверки пройдены, то функция возвращает соответствующий ответ в формате JSON.

    :param post: идентификатор поста, с которым взаимодействуют
    :param comment идентификатор комментария, с которым взаимодействуют
    :param user: идентификатор пользователя, который взаимодействует
    :param karma: оценка, может быть 1 или -1
    :return:
    """
    already_liked = CommentKarma.objects.filter(Q(user=user.id) & Q(comment=comment.id))
    if user.id == comment.author.id:
        resp = 'Нельзя оценивать свой собственный комментарий!'
        return JsonResponse({'result': resp})
    elif not already_liked:
        new_object = CommentKarma.objects.create(comment=comment, user=user, karma=karma)
        new_object.save()
        updated_comment_karma = Comment.objects.filter(id=comment.id).first().comment_karma
        return JsonResponse({'result': str(updated_comment_karma)})
    else:
        already_liked.delete()
        updated_comment_karma = Comment.objects.filter(id=comment.id).first().comment_karma
        return JsonResponse({'result': str(updated_comment_karma)})


class PostDetailView(DetailView):
    template_name = 'post/post.html'
    context_object_name = 'post'
    model = Post
    comment_form = CommentForm

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(PostDetailView, self).get_context_data(**kwargs)
        context['title'] = f'{self.object.name}'
        context['tags'] = get_all_tags(self.object.pk)
        if self.request.method == 'GET':
            context['comments'] = Comment.objects.filter(comment_post=self.kwargs['pk']).order_by('path')
            if self.request.user.is_authenticated:
                context['form'] = self.comment_form

        if self.request.method == 'POST':
            form = CommentForm(self.request.POST)
            if form.is_valid():
                comment = Comment(
                    path=[],
                    comment_post=self.object.pk,
                    author=self.request.user,
                    content=form.cleaned_data['comment_area']
                )
                comment.save()

                # сформируем path после первого сохранения
                # и пересохраним комментарий

                try:
                    comment.path.extend(Comment.objects.get(id=form.cleaned_data['parent_comment']).path)
                    comment.path.append(comment.id)
                    # print('получилось')
                except ObjectDoesNotExist:
                    comment.path.append(comment.id)
                    # print('не получилось')

                comment.save()

        return context

    # def get(self, request, *args, **kwargs):
    #
    #     post = get_object_or_404(Post, id=self.kwargs['pk'])
    #     context = {}
    #     context.update(request)
    #     user = auth.get_user(request)
    #     context['post'] = post
    #     context['head_menu_object_list'] = get_hub_cats_dict()
    #     # context['title'] = f'Пост - {self.object.name}'
    #     # Помещаем в контекст все комментарии, которые относятся к статье
    #     # попутно сортируя их по пути, ID автоинкрементируемые, поэтому
    #     # проблем с иерархией комментариев не должно возникать
    #     # context['comments'] = Comment.objects.all().order_by('path')
    #
    #     context['comments'] = Comment.objects.filter(comment_post_id_id=self.kwargs['pk']).order_by('path')
    #     # context['next'] = Comment.get_absolute_url()
    #     # Будем добавлять форму только в том случае, если пользователь авторизован
    #     if user.is_authenticated:
    #         context['form'] = self.comment_form
    #
    #     return render(request, template_name=self.template_name, context=context)

    # Декораторы по которым, только авторизованный пользователь
    # может отправить комментарий и только с помощью POST запроса
    # @method_decorator(login_required)
    # def post(self, request, *args, **kwargs):
    #     form = CommentForm(request.POST)
    #     post = get_object_or_404(Post, id=self.kwargs['pk'])
    #     if form.is_valid():
    #         comment = Comment(
    #             path=[],
    #             comment_post_id=post.pk,
    #             author_id=request.user,
    #             content=form.cleaned_data['comment_area']
    #         )
    #         comment.save()
    #
    #         # сформируем path после первого сохранения
    #         # и пересохраним комментарий
    #
    #         try:
    #             comment.path.extend(Comment.objects.get(id=form.cleaned_data['parent_comment']).path)
    #             comment.path.append(comment.id)
    #             # print('получилось')
    #         except ObjectDoesNotExist:
    #             comment.path.append(comment.id)
    #             # print('не получилось')
    #
    #         comment.save()
    #     return redirect(post.get_absolute_url())


@login_required
def delete_comment(request, pk2, pk):
    comment = get_object_or_404(Comment, id=pk)
    comment.content = f"[----русские хакеры удалили этот коммент---]"
    comment.published = False
    comment.save()
    return redirect(comment.get_absolute_url())


@login_required
@require_http_methods(["POST"])
def add_comment(request, pk):
    form = CommentForm(request.POST)
    post = get_object_or_404(Post, id=pk)

    if form.is_valid():
        comment = Comment()
        comment.path = []
        comment.comment_post = post
        comment.author = auth.get_user(request)
        comment.content = form.cleaned_data['comment_area']
        comment.save()

        # Django не позволяет увидеть ID комментария по мы не сохраним его,
        # сформируем path после первого сохранения
        # и пересохраним комментарий
        try:
            comment.path.extend(Comment.objects.get(id=form.cleaned_data['parent_comment']).path)
            comment.path.append(comment.id)
        except ObjectDoesNotExist:
            comment.path.append(comment.id)

        comment.save()

    return redirect(comment.get_absolute_url())


class PostCreateView(CreateView, SuccessMessageMixin, LoginRequiredDispatchMixin):
    template_name = 'post/post_form.html'
    form_class = PostCreationForm
    success_url = reverse_lazy('post:users_posts')
    success_message = 'пост создан'

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, self.success_message)
        tags = form.cleaned_data['tags_str']  # строка с тегами из формы
        if tags:
            tmp_tags = str(tags).split(',') # распарсил теги
            for key, el in enumerate(tmp_tags):
                tmp_tags[key] = el.strip() # убрал пробелы

            new_tags = [] # массив куда складываются id тэгов для записи в поле тэг поста

            if form.is_valid():
                f = form.save()
            for tmp_tag in tmp_tags:
                # проевряем есть тэг в таблице тэгов
                tag_exists = tmp_tag is not None and Tags.objects.filter(tag=tmp_tag).exists()
                if not tag_exists:
                    # # создаем новый тэг в таблицу тэгов
                    # tag_id = Tags.objects.create(tag=tmp_tag)
                    # добавляем тэг в массив для поста
                    form.instance.tags.create(tag=tmp_tag)

                else:
                    form.instance.tags.add(Tags.objects.filter(tag=tmp_tag).first())

        return super().form_valid(form)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(PostCreateView, self).get_context_data(**kwargs)
        context['form']['user'].initial = self.request.user
        context['title'] = f'Создание поста'
        return context

    def get(self, request, *args, **kwargs):
        if self.request.user.banned in (HubUser.BANNED_FOREVER, HubUser.BANNED_FOR_TIME):
            messages.add_message(self.request, messages.SUCCESS, 'Забаненный пользователь не может создавать посты')
            return HttpResponseRedirect(reverse('hub:main'))
        return super(PostCreateView, self).get(request, *args, **kwargs)


class CommentUserlist(ListView):
    model = Comment
    template_name = 'post/comments_list.html'
    context_object_name = 'comments'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super(CommentUserlist, self).get_context_data(**kwargs)
        context['title'] = f'Ваши комментарии {self.request.user.username}'
        context['comments_dict'] = get_all_comments(self.request.user.id)  # словарь объектов { пост: [комментарий,...]}
        return context


class PostUserListView(ListView, LoginRequiredDispatchMixin):
    model = Post
    template_name = 'post/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):

        posts = Post.objects.filter(user=self.request.user)

        if self.request.GET.get('status') == 'unpublished':
            posts = posts.filter(status='unpublished')

        elif self.request.GET.get('status') == 'archive':
            posts = posts.filter(status='archive')

        elif self.request.GET.get('status') == 'template':
            posts = posts.filter(status='template')

        elif self.request.GET.get('status') == 'moderate':
            posts = posts.filter(Q(status='on_moderate') | Q(status='need_review') | Q(status='moderate_false'))

        else:
            posts = posts.filter(status='published')

        return posts

        # return ordering(self.request)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(PostUserListView, self).get_context_data(**kwargs)
        context['title'] = f'Мои посты'

        return context


class PostModerateListView(ListView, LoginRequiredDispatchMixin):
    model = Post
    template_name = 'post/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.filter(status='on_moderate')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(PostModerateListView, self).get_context_data(**kwargs)
        context['title'] = f'Модерация постов'

        return context


class PostUpdateView(UpdateView, LoginRequiredDispatchMixin):
    model = Post
    template_name = 'post/post_form.html'
    form_class = PostEditForm
    success_url = reverse_lazy('post:users_posts')
    success_message = 'пост отредактирован'

    def get_context_data(self, **kwargs):
        post = get_object_or_404(Post, id=self.kwargs.get('pk', ''))
        context = super(PostUpdateView, self).get_context_data(**kwargs)
        context['title'] = f'Редактирование поста {self.object.name}'
        context['form']['tags_str'].initial = post.get_all_tags()

        return context

    def get(self, request, *args, **kwargs):
        post = get_object_or_404(Post, id=self.kwargs.get('pk', ''))
        if post.user == self.request.user or self.request.user.is_staff:
            if post.status == post.STATUS_PUBLISHED:
                return HttpResponseRedirect(reverse('post:post', kwargs={'pk': post.id}))
            else:
                form = self.form_class(instance=post)
                form.fields['tags_str'].initial = get_all_tags(post.id)
                return render(request, self.template_name, {'form': form})
        return HttpResponseRedirect(reverse('post:post', kwargs={'pk': post.id}))

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, self.success_message)
        tags = form.cleaned_data['tags_str']  # строка с тегами из формы
        self.object.tags.clear()
        self.object.save()
        if tags:
            tmp_tags = str(tags).split(',')  # распарсил теги
            for key, el in enumerate(tmp_tags):
                tmp_tags[key] = el.strip()  # убрал пробелы

            new_tags = []  # массив куда складываются id тэгов для записи в поле тэг поста

            for tmp_tag in tmp_tags:
                # проевряем есть тэг в таблице тэгов
                tag_exists = tmp_tag is not None and Tags.objects.filter(tag=tmp_tag).exists()
                if not tag_exists:
                    # # создаем новый тэг в таблицу тэгов
                    # tag_id = Tags.objects.create(tag=tmp_tag)
                    # добавляем тэг в массив для поста
                    form.instance.tags.create(tag=tmp_tag)

                else:

                    form.instance.tags.add(Tags.objects.filter(tag=tmp_tag).first())

        return super().form_valid(form)


class PostModerateView(UpdateView, LoginRequiredDispatchMixin):
    model = Post
    template_name = 'post/post_form.html'
    form_class = PostModeratorEditForm
    success_url = reverse_lazy('post:users_posts')
    success_message = 'пост проверен'

    def get_context_data(self, **kwargs):
        context = super(PostModerateView, self).get_context_data(**kwargs)
        context['title'] = f'Модерирование поста {self.object.name}'

        return context

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, self.success_message)

        if form.instance.status == 'unpublished':
            form.instance.moderated = True
            form.instance.moderated_at = datetime.now(pytz.timezone(settings.TIME_ZONE))
            form.instance.save()

        return super().form_valid(form)


@login_required  # TODO проверить, может ли другой пользователь в строке браузера изменить чужой пост
def post_publish(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.status = post.STATUS_PUBLISHED
    post.save()
    return HttpResponseRedirect(reverse('post:users_posts'))


@login_required  # TODO проверить, может ли другой пользователь в строке браузера изменить чужой пост
def post_archive(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.status = post.STATUS_ARCHIVE
    post.save()
    return HttpResponseRedirect(reverse('post:users_posts'))


@login_required  # TODO проверить, может ли другой пользователь в строке браузера изменить чужой пост
def post_restore(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.status = post.STATUS_UNPUBLISHED
    post.save()
    return HttpResponseRedirect(reverse('post:users_posts'))


@login_required  # TODO проверить, может ли другой пользователь в строке браузера изменить чужой пост
def post_moderate(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.status = post.STATUS_ON_MODERATE
    post.save()
    return HttpResponseRedirect(reverse('post:users_posts'))


@login_required  # TODO проверить, может ли другой пользователь в строке браузера изменить чужой пост
def post_need_review(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.status = post.STATUS_NEED_REVIEW
    post.save()
    return HttpResponseRedirect(reverse('post:users_posts'))


@login_required  # TODO проверить, может ли другой пользователь в строке браузера изменить чужой пост
def post_moderate_done(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.status = post.STATUS_UNPUBLISHED
    post.moderated = True
    post.moderated_at = datetime.now(pytz.timezone(settings.TIME_ZONE))
    post.save()
    return HttpResponseRedirect(reverse('post:users_posts'))


@login_required  # TODO проверить, может ли другой пользователь в строке браузера изменить чужой пост
def post_moderate_false(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.status = post.STATUS_MODERATE_FALSE
    post.moderated_at = datetime.now(pytz.timezone(settings.TIME_ZONE))
    post.save()
    return HttpResponseRedirect(reverse('post:users_posts'))


@login_required  # TODO проверить, может ли другой пользователь в строке браузера изменить чужой пост
def post_template(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.pk = None

    if post.status == post.STATUS_UNPUBLISHED:
        post.status = post.STATUS_TEMPLATE
        post.save()

    elif post.status == post.STATUS_TEMPLATE:
        post.status = post.STATUS_UNPUBLISHED
        post.save()
        return HttpResponseRedirect(reverse('post:post_update', kwargs={'pk': post.id}))

    return HttpResponseRedirect(reverse('post:users_posts'))


@login_required
def karma_update(request, pk, pk2):
    '''
    функция обработки ajax запроса на изменение кармы поста
    :param request:
    :param pk: id поста в таблице Post
    :param pk2: сигнал (если 1 - значит поставили лайк, если 0 - то поставили дизлайк)
    :return: возвращает карму прочитанную из БД в виде json
    '''

    if request.is_ajax():
        post = get_object_or_404(Post, id=pk)
        user = get_object_or_404(HubUser, id=request.user.pk)
        result = None
        if pk2 == 1:
            result = perform_karma_update(post, user, 1)
        elif pk2 == 0:
            result = perform_karma_update(post, user, -1)
        if result:
            return result


@login_required
def comment_karma_update(request, pk, pk2, pk3):
    """
    Функция, обрабатывающая ajax-запрос на изменение кармы комментария.

    :param request:
    :param pk: id поста в таблице Post
    :param pk2: id комментария в таблице Comment
    :param pk3: сигнал (если 1 - значит поставили лайк, если 0 - то поставили дизлайк)
    :return: возвращает карму прочитанную из БД в виде json
    """
    if request.is_ajax():
        post = get_object_or_404(Post, id=pk)
        comment = get_object_or_404(Comment, id=pk2)
        user = get_object_or_404(HubUser, id=request.user.pk)
        result = None
        if pk3 == 1:
            result = perform_comment_karma_update(post, comment, user, 1)
        elif pk3 == 0:
            result = perform_comment_karma_update(post, comment, user, -1)
        if result:
            return result


def ordering(request):
    days_count = int(request.GET.get('days', 20))
    now = datetime.now(pytz.timezone(settings.TIME_ZONE)) - timedelta(days=days_count)
    posts = Post.objects.filter(user=request.user).select_related().filter(updated_at__gte=now)

    if request.GET.get('msg_type') == 'date_up':
        posts = posts.order_by('-updated_at')

    elif request.GET.get('msg_type') == 'date_down':
        posts = posts.order_by('updated_at')

    elif request.GET.get('msg_type') == 'karma_up':
        posts = posts.order_by('-karma_count')

    elif request.GET.get('msg_type') == 'karma_down':
        posts = posts.order_by('karma_count')

    return posts
