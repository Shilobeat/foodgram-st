from django.contrib.auth import update_session_auth_hash
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
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def set_password(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        if not current_password:
            return Response(
                {'current_password': 'Это поле обязательно'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not new_password:
            return Response(
                {'new_password': 'Это поле обязательно'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not user.check_password(current_password):
            return Response(
                {'current_password': 'Неверный текущий пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if len(new_password) < 8:
            return Response(
                {'new_password': 'Пароль должен содержать минимум 8 символов'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        return Response(
            {'detail': 'Пароль успешно изменен'},
            status=status.HTTP_200_OK
        )
        
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
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == 'create' and 'id' in self.kwargs:
            author_id = self.kwargs['id']
            author = get_object_or_404(User, id=author_id)
            context['author'] = author
        return context
    
    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        serializer = self.get_serializer(data={})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)   
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )
    
    def destroy(self, request, *args, **kwargs):
        author_id = kwargs.get('id')
        subscription = get_object_or_404(
            Subscription,
            subscriber=request.user,
            author_id=author_id
        )
        self.perform_destroy(subscription)
        return Response(status=status.HTTP_204_NO_CONTENT)
