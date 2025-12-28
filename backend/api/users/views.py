from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from users_app.models import Subscription, User
from api.users.pagination import LimitPageNumberPagination
from api.users.serializers import (
    SetAvatarSerializer,
    SubscriptionSerializer,
    UserSerializer,
    UserSubscribeSerializer,
    UserWithRecipesSerializer
)


class UserViewSet(viewsets.ModelViewSet):

    lookup_value_regex = r'\d+'
    queryset = User.objects.annotate(recipes_count=Count('recipes')).prefetch_related(
        'recipes',
        'subscriptions',
    )
    serializer_class = UserSerializer
    pagination_class = LimitPageNumberPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(methods=['put', 'delete'], detail=False, url_path='me/avatar')
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = SetAvatarSerializer(
                user,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'error': 'Аватар отсутствует'},
                    status=status.HTTP_400_BAD_REQUEST
                )


class SubscriptionViewSet(mixins.CreateModelMixin,
                         mixins.DestroyModelMixin,
                         viewsets.GenericViewSet):

    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LimitPageNumberPagination
    
    def create(self, request, *args, **kwargs):
        author_id = kwargs.get('id')
        author = get_object_or_404(
            User.objects.annotate(recipes_count=Count('recipes')).prefetch_related(
            'recipes',
            'subscriptions',
            ),
            id=author_id
        )
        if Subscription.objects.filter(
            subscriber=request.user,
            author=author
        ).exists():
            return Response(
                {'detail': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.user == author:
            return Response(
                {'detail': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(data={'author': author.id})
        serializer.is_valid(raise_exception=True)
        serializer.save(subscriber=request.user)
        user_serializer = UserSubscribeSerializer(
            author,
            context={'request': request}
        )
        return Response(user_serializer.data, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        author_id = kwargs.get('pk') or kwargs.get('id')
        deleted_count, _ = Subscription.objects.filter(
            subscriber=request.user,
            author_id=author_id
        ).delete()
        if deleted_count == 0:
            return Response(
                {'detail': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsListView(generics.ListAPIView):

    serializer_class = UserWithRecipesSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LimitPageNumberPagination

    def get_queryset(self):
        return User.objects.filter(
            subscribers__subscriber=self.request.user
        ).annotate(recipes_count=Count('recipes')).prefetch_related(
            'recipes',
            'subscriptions',
        )