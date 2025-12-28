from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from users_app.constants import (
    EMAIL_LENGTH,
    FIRST_NAME_LENGTH,
    LAST_NAME_LENGTH,
    USERNAME_LENGTH
)
from users_app.validators import validate_not_blank, validate_username


class User(AbstractUser):

    email = models.EmailField(
        max_length=EMAIL_LENGTH,
        unique=True,
        verbose_name='Адрес электронной почты',
        error_messages={
            'unique': 'Пользователь с таким email уже зарегистрирован'
        }
    )
    username = models.CharField(
        max_length=USERNAME_LENGTH,
        unique=True,
        error_messages={
            'unique': 'Пользователь с таким username уже существует',
            'max_length': (
                'Имя пользователя не может быть длиннее 150 символов.'
            )
        },
        validators=[validate_username],
        verbose_name='Имя пользователя',
    )
    first_name = models.CharField(
        max_length=FIRST_NAME_LENGTH,
        verbose_name='Имя',
        validators=[validate_not_blank]
    )
    last_name = models.CharField(
        max_length=LAST_NAME_LENGTH,
        verbose_name='Фамилия',
        validators=[validate_not_blank]
    )
    avatar = models.ImageField(
        upload_to='users/avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['id']

    def __str__(self):
        return self.email


class Subscription(models.Model):

    subscriber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор'
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'author'],
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(subscriber=models.F('author')),
                name='prevent_self_subscription'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.subscriber} подписан на {self.author}'