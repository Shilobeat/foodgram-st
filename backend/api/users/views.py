
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Subscription, User
from .pagination import LimitPageNumberPagination
from .serializers import (
    SetAvatarSerializer,
    SubscriptionSerializer,
    UserSerializer,
    UserSubscribeSerializer,
    UserWithRecipesSerializer
)


class UserViewSet(viewsets.ModelViewSet):

    lookup_value_regex = r'\d+'
    queryset = User.objects.all().order_by('id')
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
            if not user.avatar:
                return Response(
                    {'error': 'Аватар отсутствует'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.avatar.delete(save=False)
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)


class SubscribeAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LimitPageNumberPagination

    def post(self, request, id):
        author = get_object_or_404(User, id=id)
        serializer = SubscriptionSerializer(
            data={'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user_serializer = UserSubscribeSerializer(
            author,
            context={'request': request}
        )
        return Response(user_serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        author = get_object_or_404(User, id=id)
        subscription = Subscription.objects.filter(
            subscriber=request.user,
            author=author
        ).first()

        if not subscription:
            return Response(
                {'detail': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsListView(generics.ListAPIView):

    serializer_class = UserWithRecipesSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LimitPageNumberPagination

    def get_queryset(self):
        return User.objects.filter(subscribers__subscriber=self.request.user)


class UserAvatarAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        serializer = SetAvatarSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user
        if not user.avatar:
            return Response(
                {'error': 'Аватар отсутствует'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.avatar.delete(save=False)
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
