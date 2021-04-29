from datetime import datetime, timedelta

import pytz
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.views.generic.base import View, ContextMixin
from django.db.models import Count

from hub.models import Hub, HubCategory, get_hub_cats_dict
from post.models import Post


class CustomDispatchMixin(View):

    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class BaseClassContextMixin(ContextMixin):
    title = ''

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context


# def main(request):
#     head_menu_object_list = get_hub_cats_dict()
#     all_posts = Post.get_all_posts()
#     title = 'Hub'
#
#     content = {
#         'head_menu_object_list': head_menu_object_list,
#         'posts': all_posts,
#         'title': title,
#     }
#
#     return render(request, 'hub/index.html', context=content)


class Main(ListView):
    model = Post
    context_object_name = 'posts'
    paginate_by = 10
    template_name = 'hub/index.html'

    def get_queryset(self):
        return ordering(self.request)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(Main, self).get_context_data(**kwargs)
        context['title'] = 'Hub'
        # context['msg_type'] = self.request.GET.get('msg_type', '')
        # context['days'] = self.request.GET.get('days', '')

        return context


class HubPostListView(ListView):
    model = Post
    context_object_name = 'posts'
    paginate_by = 10
    template_name = 'hub/index.html'

    def get_queryset(self):
        return ordering(self.request, pk=self.kwargs.get('pk', ''))

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(HubPostListView, self).get_context_data(**kwargs)
        category = Hub.objects.get(pk=self.kwargs.get('pk', ''))
        context['title'] = category.name
        # context['msg_type'] = self.request.GET.get('msg_type', '')
        # context['days'] = self.request.GET.get('days', '')

        return context


class HubCategoryPostListView(ListView):
    model = Post
    context_object_name = 'posts'
    paginate_by = 10
    template_name = 'hub/index.html'

    def get_queryset(self):
        return ordering(self.request, cat=self.kwargs.get('cat', ''))

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(HubCategoryPostListView, self).get_context_data(**kwargs)
        category = Hub.objects.get(pk=self.kwargs.get('pk', ''))
        hub_category = HubCategory.objects.get(pk=self.kwargs.get('cat', ''))
        context['title'] = category.name
        context['hub_category'] = hub_category.name
        # context['msg_type'] = self.request.GET.get('msg_type', '')
        # context['days'] = self.request.GET.get('days', '')

        return context


def ordering(request, pk=None, cat=None):
    if request.GET.get('days') == '':
        days_count = 20
    else:
        days_count = request.GET.get('days', 20)
    now = datetime.now(pytz.timezone(settings.TIME_ZONE)) - timedelta(days=int(days_count))
    posts = Post.objects.filter(status=Post.STATUS_PUBLISHED).filter(updated_at__gte=now).select_related().order_by('-updated_at')

    if pk is not None:
        posts = posts.filter(hub_category__category_id=pk)

    if cat is not None:
        posts = posts.filter(hub_category=cat)

    if request.GET.get('tags') != '':
        tag = request.GET.get('tags', None)
        if tag is not None:
            posts = posts.filter(tags__tag__iexact=tag)

    if request.GET.get('msg_type') == 'date_up':
        posts = posts.order_by('-updated_at')

    elif request.GET.get('msg_type') == 'date_down':
        posts = posts.order_by('updated_at')

    elif request.GET.get('msg_type') == 'karma_up':
        posts = posts.order_by('-karma_count')
        # posts = posts.annotate(num_karam=Count('post_id')).order_by('post_id')

    elif request.GET.get('msg_type') == 'karma_down':
        posts = posts.order_by('karma_count')
        # posts = posts.annotate(num_karam=Count('post_id')).order_by('-post_id')

    elif request.GET.get('msg_type') == 'comments_up':
        posts = posts.annotate(num_comment=Count('comment_post_id')).order_by('comment_post_id')

    elif request.GET.get('msg_type') == 'comments_down':
        posts = posts.annotate(num_comment=Count('comment_post_id')).order_by('-comment_post_id')

    return posts





