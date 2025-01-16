from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models

from users.managers import SuperUserManager
import users.constants


class User(AbstractUser):
    """Модель пользователей."""

    email = models.EmailField(
        max_length=users.constants.MAX_LEN_FIELDS,
        unique=True
    )
    first_name = models.CharField(max_length=users.constants.MAX_LEN_NAME)
    last_name = models.CharField(max_length=users.constants.MAX_LEN_NAME)
    avatar = models.ImageField(upload_to='users/', blank=True, null=True)

    objects = SuperUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Subscription(models.Model):
    """Модель подписок."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    subscribed_to = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscribers'
    )

    class Meta:
        unique_together = ('user', 'subscribed_to')

    def save(self, *args, **kwargs):
        if self.user == self.subscribed_to:
            raise ValidationError("Вы не можете подписаться на самого себя.")
        super().save(*args, **kwargs)
