
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.recipes.shared_serializers import ShortRecipeSerializer
from api.users.pagination import LimitPageNumberPagination
from .filters import RecipeFilter
from .models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
)
from .permissions import RecipePermissions
from .serializers import (
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeReadSerializer,
)


class IngredientFilter(filters.SearchFilter):

    search_param = 'name'


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [IngredientFilter]
    search_fields = ['^name']


class RecipeViewSet(viewsets.ModelViewSet):

    queryset = Recipe.objects.all()
    pagination_class = LimitPageNumberPagination
    permission_classes = [RecipePermissions]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

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
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        if request.method == 'POST':
            if model.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': exists_error},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if not model.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': not_found_error},
                    status=status.HTTP_400_BAD_REQUEST
                )
            item = model.objects.get(user=user, recipe=recipe)
            item.delete()
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

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shoppingcart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount'))

        shopping_list = "Список покупок:\n\n"
        for item in ingredients:
            shopping_list += (
                f"{item['ingredient__name']} - "
                f"{item['total_amount']} "
                f"{item['ingredient__measurement_unit']}\n"
            )

        response = HttpResponse(shopping_list, content_type='text/plain')
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
