from django.urls import path
from adminapp import views


app_name = 'adminapp'

urlpatterns = [
    path('users/', views.HubUserListView.as_view(), name='users_list'),
    path('user/ban/<int:pk>/', views.user_ban, name='user_ban'),
]


