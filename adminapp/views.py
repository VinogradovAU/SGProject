from datetime import datetime, timedelta

import pytz
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView

from adminapp.forms import BanTimeForm
from authapp.models import HubUser
# Create your views here.


class HubUserListView(ListView):
    model = HubUser
    template_name = 'adminapp/users_list.html'
    context_object_name = 'users'
    paginate_by = 10

    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        return super(HubUserListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(HubUserListView, self).get_context_data(**kwargs)
        context['title'] = 'Пользователи'
        context['form'] = BanTimeForm()

        return context

    def get(self, request, *args, **kwargs):
        if self.request.user.banned in (HubUser.BANNED_FOREVER, HubUser.BANNED_FOR_TIME):
            messages.add_message(self.request, messages.SUCCESS, 'Забаненный пользователь не может зайти в админку')
            return HttpResponseRedirect(reverse('hub:main'))
        return super(HubUserListView, self).get(request, *args, **kwargs)


def user_ban(request, pk):
    user = get_object_or_404(HubUser, pk=pk)
    time = request.POST.get('ban_time', '')
    if time and user.banned == user.BANNED_FALSE:
        now = datetime.now(pytz.timezone(settings.TIME_ZONE)) + timedelta(days=int(time))
        user.banned_to = now
        user.banned = user.BANNED_FOR_TIME
        user.save()
    elif user.banned == user.BANNED_FOR_TIME:
        user.banned = user.BANNED_FALSE
        user.banned_to = None
        user.save()

    return HttpResponseRedirect(reverse('adminapp:users_list'))




