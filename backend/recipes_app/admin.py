from django.contrib import admin

from recipes_app.constants import EXTRA_VALUE_ON_RECIPE, MIN_VALUE_ON_RECIPE
from recipes_app.forms import IngredientInRecipeForm
from recipes_app.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart
)


class RecipeIngredientInline(admin.TabularInline):

    model = IngredientInRecipe
    form = IngredientInRecipeForm
    extra = EXTRA_VALUE_ON_RECIPE
    min_num = MIN_VALUE_ON_RECIPE
    autocomplete_fields = ['ingredient']


@admin.register(Recipe)
class RecipesAdmin(admin.ModelAdmin):

    inlines = [RecipeIngredientInline]
    list_display = (
        'name',
        'author',
        'display_ingredients',
        'cooking_time',
        'pub_date',
        'favorite_count'
    )
    search_fields = ('name', 'author__username')
    list_filter = ('author', 'pub_date')
    ordering = ('-pub_date',)
    autocomplete_fields = ['author']
    
    def favorite_count(self, obj):
        return obj.favorite_set.count()
    favorite_count.short_description = 'В избранном'

    def display_ingredients(self, obj):
        return ', '.join([
            f'{ing.ingredient.name} '
            f'({ing.amount} {ing.ingredient.measurement_unit})'
            for ing in obj.recipe_ingredients.all()
        ])
    display_ingredients.short_description = 'Ингредиенты'

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('author')
            .prefetch_related(
                'recipe_ingredients__ingredient'
            )
        )


@admin.register(Ingredient)
class IngredientsAdmin(admin.ModelAdmin):

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Favorite)
class FavoritesAdmin(admin.ModelAdmin):

    list_display = ('user', 'recipe', 'created_at')


@admin.register(ShoppingCart)
class ShoppingCartsAdmin(admin.ModelAdmin):

    list_display = ('user', 'recipe', 'created_at')
