from django.db import transaction
from rest_framework import serializers
from rest_framework.fields import CreateOnlyDefault, CurrentUserDefault

from api.users.serializers import Base64ImageField, UserSerializer

from recipes_app.constants import MIN_VALUE_AMOUNT_INGREDIENTS
from recipes_app.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
)
from api.recipes.shared_serializers import ShortRecipeSerializer
from recipes_app.validators import validate_time


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id',)


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:

        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientAmountWriteSerializer(serializers.Serializer):

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=MIN_VALUE_AMOUNT_INGREDIENTS)


class RecipeReadSerializer(serializers.ModelSerializer):

    author = UserSerializer()
    ingredients = IngredientInRecipeReadSerializer(
        many=True,
        source='recipe_ingredients'
    )
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:

        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'name', 'image', 'text',
            'cooking_time', 'is_favorited', 'is_in_shopping_cart'
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):

    ingredients = IngredientAmountWriteSerializer(many=True)
    image = Base64ImageField(required=False)
    cooking_time = serializers.IntegerField(
        required=True,
        validators=[validate_time]
    )
    author = serializers.HiddenField(
        default=CreateOnlyDefault(CurrentUserDefault())
    )
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:

        model = Recipe
        fields = (
            'ingredients',
            'image',
            'image_url',
            'name',
            'text',
            'cooking_time',
            'author'
        )

    def validate(self, data):
        empty_fields = {
            'image': 'Поле image не может быть пустым.',
            'ingredients': 'Добавьте хотя бы один ингредиент.',
            'cooking_time': 'Поле cooking_time не может быть пустым.'
        }
        for field, message in empty_fields.items():
            if field in data and (data[field] in (None, '', [], {})):
                raise serializers.ValidationError({field: [message]})

        return data

    def validate_ingredients(self, value):
        ingredient_ids = [item['id'].pk for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться'
            )
        return value

    def _update_ingredients(self, recipe, ingredients_data):
        IngredientInRecipe.objects.filter(recipe=recipe).delete()
        if ingredients_data:
            IngredientInRecipe.objects.bulk_create([
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient=item['id'],
                    amount=item['amount']
                )
                for item in ingredients_data
            ])

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self._update_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data.pop('author', None)
        ingredients_data = validated_data.pop('ingredients', None)
        instance = super().update(instance, validated_data)
        if ingredients_data is not None:
            self._update_ingredients(instance, ingredients_data)
        return instance

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class FavoriteSerializer(serializers.ModelSerializer):

    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:

        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if Favorite.objects.filter(
                user=request.user,
                recipe=data['recipe']
            ).exists():
                raise serializers.ValidationError(
                    {'recipe': 'Рецепт уже в избранном.'}
                )
        return data

    def to_representation(self, instance):
        return ShortRecipeSerializer(instance.recipe).data


class ShoppingCartSerializer(serializers.ModelSerializer):

    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:

        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if ShoppingCart.objects.filter(
                user=request.user,
                recipe=data['recipe']
            ).exists():
                raise serializers.ValidationError(
                    {'recipe': 'Рецепт уже в списке покупок.'}
                )
        return data

    def to_representation(self, instance):
        return ShortRecipeSerializer(instance.recipe).data