import re

from django.core.exceptions import ValidationError

from users_app.constants import USERNAME_LENGTH


def validate_username(value):
    if not re.fullmatch(r'^[\w.@+-]+$', value):
        raise ValidationError(
            'Недопустимые символы. Разрешены только латинские буквы, цифры, '
            'и символы @/./+/-/_'
        )
    if len(value) > USERNAME_LENGTH:
        raise ValidationError(
            'Имя пользователя не может быть длиннее '
            f'{USERNAME_LENGTH} символов.'
        )
    return value


def validate_not_blank(value):
    if not value or not value.strip():
        raise ValidationError('Поле не может быть пустым.')
    return value