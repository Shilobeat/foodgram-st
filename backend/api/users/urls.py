
from django.urls import path

from .views import SubscribeAPIView, SubscriptionsListView, UserAvatarAPIView

app_name = 'users'

urlpatterns = [
    path(
        'users/<int:id>/subscribe/',
        SubscribeAPIView.as_view(),
        name='subscribe'
    ),
    path(
        'users/subscriptions/',
        SubscriptionsListView.as_view(),
        name='subscriptions'
    ),
    path(
        'users/me/avatar/',
        UserAvatarAPIView.as_view(),
        name='user-avatar'
    ),
]
