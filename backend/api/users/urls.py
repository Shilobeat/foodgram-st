from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.users.views import (SubscriptionViewSet, UserViewSet)

app_name = 'users'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = router.urls + [
    path(
        'users/<int:id>/subscribe/',
        SubscriptionViewSet.as_view({'post': 'create', 'delete': 'destroy'}),
        name='subscribe'
    ),
    path(
        'subscriptions/',
        SubscriptionViewSet.as_view({'get': 'list'}),
        name='subscriptions'
    ),
]
