from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from api.users.serializers import (SetAvatarSerializer, SubscriptionSerializer,
                                   UserSerializer, UserSubscribeSerializer,
                                   UserWithRecipesSerializer)
from users_app.constants import MAX_PAGE_SIZE, PAGE_SIZE
from users_app.models import Subscription, User                            


class LimitPageNumberPagination(PageNumberPagination):

    page_size = PAGE_SIZE
    page_size_query_param = 'limit'
    max_page_size = MAX_PAGE_SIZE
    
    
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
        
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
        
    @me.mapping.put
    @me.mapping.patch
    def update_me(self, request):
        partial = request.method == 'PATCH'
        instance = request.user
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(methods=['put', 'delete'], detail=False, url_path='me/avatar')
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = SetAvatarSerializer(
                user,
                data=request.data,
                context=self.get_serializer_context()
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
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionViewSet(mixins.CreateModelMixin,
                         mixins.DestroyModelMixin,
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet):

    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LimitPageNumberPagination
    
    def get_queryset(self):
        return Subscription.objects.filter(subscriber=self.request.user)
        
    def perform_create(self, serializer):
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)
        serializer.save(subscribe=self.request.user, author=author)
        
    def destroy(self, request, *args, **kwargs):
        author_id = kwargs.get('id')
        subsciption = get_object_or_404(
            Subsciption,
            subscriber=request.user,
            author_id=author_id
        )
        self.perform_destroy(subscription)
        return Response(status=status.HTTP_204_NO_CONTENT)
