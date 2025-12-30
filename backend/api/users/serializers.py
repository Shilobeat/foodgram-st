from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from recipes_app.models import Recipe
from users_app.models import Subscription
from users_app.validators import validate_username

User = get_user_model()


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

        
class UserSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField(read_only=True)
    email = serializers.EmailField(
        required=True,
        validators=[
            EmailValidator(),
            UniqueValidator(
                queryset=User.objects.all(),
                message='Пользователь с таким email уже зарегистрирован'
            )
        ]
    )
    username = serializers.CharField(
        validators=[
            validate_username,
            UniqueValidator(
                queryset=User.objects.all(),
                message='Пользователь с таким username уже существует'
            )
        ]
    )
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:

        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )
        read_only_fields = ('id',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and request.user.subscriptions.filter(author=obj).exists()
        )


class SetAvatarSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:

        model = User
        fields = ['avatar']

    def to_representation(self, instance):
        if instance.avatar:
            request = self.context.get('request')
            avatar_url = instance.avatar.url
            if request and not avatar_url.startswith('http'):
                avatar_url = request.build_absolute_uri(avatar_url)
            return {'avatar': avatar_url}
        return {'avatar': None}


class UserWithRecipesSerializer(serializers.ModelSerializer):

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True, default=0)
    avatar = serializers.ImageField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:

        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(
            subscriber=user, author=obj
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit and recipes_limit.isdigit():
                limit = int(recipes_limit)
                if limit > 0:
                    recipes = recipes[:limit]
        return ShortRecipeSerializer(
            recipes,
            many=True,
            context=self.context
        ).data


class SubscriptionSerializer(serializers.ModelSerializer):
    
    class Meta:

        model = Subscription
        fields = ()
 
    def validate(self, data):
        request = self.context.get('request')
        author = self.context.get('author')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(
                'Требуется авторизация.'
            )
        if request.user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        if Subscription.objects.filter(
            subscriber=request.user,
            author=author
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.'
            )
        return data

    def create(self, validated_data):
        request = self.context['request']
        author = self.context['author']
        return Subscription.objects.create(
            subscriber=request.user,
            author=author
        )
        
    def to_representation(self, instance):
        return UserSubscribeSerializer(
            instance.author,
            context=self.context
        ).data


class UserSubscribeSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.BooleanField(default=True, read_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True, default=0)
    avatar = serializers.SerializerMethodField()

    class Meta:

        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()  
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit is not None and recipes_limit.isdigit():
                limit = int(recipes_limit)
                if limit > 0:
                    recipes = recipes[:limit]
        return ShortRecipeSerializer(
            recipes,
            many=True,
            context=self.context
        ).data

    def get_avatar(self, obj):
        if obj.avatar:
            return self.context['request'].build_absolute_uri(obj.avatar.url)
        return None
