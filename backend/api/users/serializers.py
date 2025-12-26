
from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from api.recipes.shared_serializers import ShortRecipeSerializer
from .models import Subscription
from .validators import validate_username

User = get_user_model()


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
            validate_username
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

    avatar = Base64ImageField(
        required=True,
        allow_null=True,
        allow_empty_file=True
    )

    class Meta:

        model = User
        fields = ['avatar']

    def validate_avatar(self, value):
        if value in [None, '', b'']:
            raise serializers.ValidationError("Аватар не может быть пустым")
        return value

    def update(self, instance, validated_data):
        avatar = validated_data.get('avatar')
        if avatar in [None, '', b'']:
            if instance.avatar:
                instance.avatar.delete(save=False)
            instance.avatar = None
        else:
            instance.avatar = avatar
        instance.save()
        return instance

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
    recipes_count = serializers.SerializerMethodField()
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

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get(
            'recipes_limit'
        ) if request else None
        recipes = obj.recipes.all()
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]
        return ShortRecipeSerializer(
            recipes,
            many=True,
            context=self.context
        ).data


class SubscriptionSerializer(serializers.ModelSerializer):

    class Meta:

        model = Subscription
        fields = ('author',)
        read_only_fields = ('subscriber',)

    def validate(self, data):
        author = data['author']
        request = self.context.get('request')
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
        validated_data['subscriber'] = self.context['request'].user
        return super().create(validated_data)


class UserSubscribeSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.BooleanField(default=True, read_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
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
        if not request:
            recipes = obj.recipes.all()
            return ShortRecipeSerializer(
                recipes,
                many=True,
                context=self.context
            ).data
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is None:
            recipes = obj.recipes.all()
        else:
            try:
                limit = int(recipes_limit)
                if limit <= 0:
                    recipes = obj.recipes.all()
                else:
                    recipes = obj.recipes.all()[:limit]
            except (ValueError, TypeError):
                recipes = obj.recipes.all()
        return ShortRecipeSerializer(
            recipes,
            many=True,
            context=self.context
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_avatar(self, obj):
        if obj.avatar:
            return self.context['request'].build_absolute_uri(obj.avatar.url)
        return None
