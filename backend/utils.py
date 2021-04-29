from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View


class LoginRequiredDispatchMixin(View):

    @method_decorator(user_passes_test(lambda u: u.is_authenticated))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


# class BannedUserDispatchMixin(View):
#
#     @method_decorator(user_passes_test(lambda u: u.is_authenticated))
#     def dispatch(self, request, *args, **kwargs):
#         if request.user.BANNED_FOR_TIME or request.user.BANNED_FOREVER:
#             reverse
#         return super().dispatch(request, *args, **kwargs)


