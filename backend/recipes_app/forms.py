from django import forms
from django.core.validators import MinValueValidator

from recipes_app.constants import (
    MIN_VALUE_AMOUNT_INGREDIENTS,
    MIN_VALUE_TIME,
    UNIT_NAME_LENGTH
)
from recipes_app.models import Ingredient, IngredientInRecipe, Recipe
from recipes_app.validators import validate_ingredient_name, validate_time


class IngredientInRecipeForm(forms.ModelForm):

    amount = forms.IntegerField(
        validators=[MinValueValidator(MIN_VALUE_AMOUNT_INGREDIENTS)],
    )

    class Meta:

        model = IngredientInRecipe
        fields = ('ingredient', 'amount')


class RecipeForm(forms.ModelForm):

    cooking_time = forms.IntegerField(
        min_value=MIN_VALUE_TIME,
        validators=[validate_time]
    )
    ingredients = forms.ModelMultipleChoiceField(
        queryset=Ingredient.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:

        model = Recipe
        fields = (
            'author',
            'name',
            'image',
            'text',
            'ingredients',
            'cooking_time'
        )


class IngredientForm(forms.ModelForm):

    measurement_unit = forms.CharField(max_length=UNIT_NAME_LENGTH)

    class Meta:

        model = Ingredient
        fields = ('name', 'measurement_unit')

    def clean_name(self):
        name = self.cleaned_data['name']
        normalized = ' '.join(name.strip().lower().split())
        validate_ingredient_name(normalized)
        return normalized