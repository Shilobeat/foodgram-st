
import re

from django.apps import apps
from django.core.exceptions import ValidationError

from .constants import MIN_VALUE_TIME


def validate_time(value):
    if value < MIN_VALUE_TIME:
        raise ValidationError('Количество минут должно быть больше 0')
    return value


def validate_ingredient_name(value):
    ingredient_model = apps.get_model('recipes', 'Ingredient')
    normalized_name = ' '.join(value.strip().lower().split())

    if ingredient_model.objects.filter(name__iexact=normalized_name).exists():
        raise ValidationError(
            'Ингредиент с таким названием уже существует',
            code='duplicate_ingredient'
        )
    return value


def _extract_ids(items):
    ids = []
    for item in items:
        if isinstance(item, dict):
            item_id = item.get('id')
        elif hasattr(item, 'id'):
            item_id = item.id
        else:
            item_id = item
        try:
            ids.append(int(item_id))
        except (TypeError, ValueError):
            raise ValidationError('Неверный формат идентификатора.')
    return ids


def validate_ingredients(value):
    ingredient_model = apps.get_model('recipes', 'Ingredient')
    if not value:
        raise ValidationError('Добавьте хотя бы один ингредиент')

    ingredient_ids = _extract_ids(
        [item.get('id') if isinstance(item, dict) else item for item in value]
    )
    if len(ingredient_ids) != len(set(ingredient_ids)):
        raise ValidationError('Ингредиенты не должны повторяться')
    ids_set = set(ingredient_ids)
    existing = ingredient_model.objects.filter(id__in=ids_set).count()
    if existing != len(ids_set):
        raise ValidationError(
            'Некоторые ингредиенты не существуют в базе данных'
        )
    return value

