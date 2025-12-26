
from django.conf import settings
from django.db import models


class UserRecipeBaseModel(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='%(class)s'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='%(class)s'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        abstract = True
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(class)s'
            )
        ]

        def __str__(self):
            return f'{self.user} - {self.recipe}'
