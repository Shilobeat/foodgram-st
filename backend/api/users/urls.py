from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.users.views import SubscriptionViewSet, SubscriptionsListView, UserViewSet

app_name = 'users'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    
    path(
        '<int:id>/subscribe/',
        SubscriptionViewSet.as_view({'post': 'create', 'delete': 'destroy'}),
        name='subscribe'
    ),
    path(
        'subscriptions/',
        SubscriptionsListView.as_view(),
        name='subscriptions'
    ),
]