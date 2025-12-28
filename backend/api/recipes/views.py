from io import BytesIO

from django.db.models import Exists, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.recipes.shared_serializers import ShortRecipeSerializer
from api.users.pagination import LimitPageNumberPagination

from api.recipes.filters import IngredientFilter, RecipeFilter
from recipes_app.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
)
from api.recipes.permissions import RecipePermissions
from api.recipes.serializers import (
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeReadSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer,
)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [IngredientFilter]
    search_fields = ['^name']


class RecipeViewSet(viewsets.ModelViewSet):

    pagination_class = LimitPageNumberPagination
    permission_classes = [RecipePermissions]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_queryset(self):
        user = self.request.user
        favorite_subquery = Favorite.objects.filter(
            recipe=OuterRef('pk'),
            user=user
        ) if user.is_authenticated else Favorite.objects.none()
        shopping_cart_subquery = ShoppingCart.objects.filter(
            recipe=OuterRef('pk'),
            user=user
        ) if user.is_authenticated else ShoppingCart.objects.none()
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'recipe_ingredients__ingredient',
            'favorite',
            'shoppingcart',
        ).annotate(
            is_favorited=Exists(favorite_subquery),
            is_in_shopping_cart=Exists(shopping_cart_subquery)
        ).all()
        return queryset

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeReadSerializer

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def my_recipes(self, request):
        recipes = self.get_queryset().filter(author=request.user)
        page = self.paginate_queryset(recipes)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(recipes, many=True)
        return Response(serializer.data)

    def _handle_add_remove(
        self, request, model, exists_error, not_found_error, pk=None
    ):
        recipe = get_object_or_404(
            Recipe.objects.select_related('author'),
            pk=pk
        )
        user = request.user
        if request.method == 'POST':
            if model == Favorite:
                serializer_class = FavoriteSerializer
            else:
                serializer_class = ShoppingCartSerializer
            serializer = serializer_class(
                data={'recipe': recipe.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            deleted_count, _ = model.objects.filter(
                user=user,
                recipe=recipe
            ).delete()
            if deleted_count == 0:
                return Response(
                    {'errors': not_found_error},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Метод не поддерживается'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        exists_error = 'Рецепт уже в избранном.'
        not_found_error = 'Рецепт не найден в избранном.'
        return self._handle_add_remove(
            request, Favorite, exists_error, not_found_error, pk=pk
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        exists_error = 'Рецепт уже в списке покупок.'
        not_found_error = 'Рецепт не найден в списке покупок.'
        return self._handle_add_remove(
            request, ShoppingCart, exists_error, not_found_error, pk=pk
        )

    def generate_shopping_list_file(self, user):
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shoppingcart__user=user
        ).select_related('ingredient')
        .values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount'))
        lines = ["Список покупок:\n"]
        for item in ingredients:
            line = f"{item['ingredient__name']} - {item['total_amount']} {item['ingredient__measurement_unit']}"
            lines.append(line)
        content = "\n".join(lines)
        buffer = BytesIO()
        buffer.write(content.encode('utf-8'))
        buffer.seek(0)
        return buffer

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        buffer = self.generate_shopping_list_file(request.user)
        response = HttpResponse(
            buffer.getvalue(),
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        detail=True, methods=['get'], url_path='get-link', url_name='get-link'
    )
    def get_recipe_link(self, request, pk=None):
        recipe = self.get_object()
        code = str(recipe.id)
        short_path = reverse('short-link', kwargs={'code': code})
        short_url = request.build_absolute_uri(short_path).rstrip('/')
        return Response({'short-link': short_url})


def short_link_redirect(request, code: int):
    recipe = get_object_or_404(Recipe, pk=code)
    return redirect(f'/recipes/{recipe.id}')