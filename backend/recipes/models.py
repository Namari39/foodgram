import uuid
from django.contrib.auth import get_user_model
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from recipes import constants

User = get_user_model()


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(
        max_length=constants.MAX_LEN_FIELD_TAG,
        unique=True
    )
    slug = models.SlugField(
        max_length=constants.MAX_LEN_FIELD_TAG,
        unique=True,
        null=True
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField(
        max_length=constants.MAX_LEN_FIELD_INGR,
        unique=True
    )
    measurement_unit = models.CharField(
        max_length=constants.MAX_LEN_FIELD_INGR
    )

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('name', 'measurement_unit')
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


class Recipe(models.Model):
    """Модель рецептов."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    name = models.CharField(max_length=constants.MAX_LEN_NAME)
    tags = models.ManyToManyField(Tag)
    image = models.ImageField(upload_to='recipes/', null=False, blank=False)
    text = models.TextField()
    cooking_time = models.PositiveIntegerField(
        null=False,
        blank=False,
        validators=[
            MinValueValidator(constants.MIN_VALIDATORS),
            MaxValueValidator(constants.MAX_VALIDATORS)
        ],
    )
    created_at = models.DateTimeField(default=timezone.now)
    short_link = models.CharField(
        max_length=constants.MAX_LEN_NAME,
        unique=True,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.short_link:
            short_id = str(uuid.uuid4())[:6]
            self.short_link = f"{short_id}"
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class RecipeIngredient(models.Model):
    """Модель содержания количества ингредиентов в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients'
    )
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(
        null=False,
        blank=False,
        validators=[MinValueValidator(constants.MIN_VALIDATORS)]
    )

    class Meta:
        unique_together = ('recipe', 'ingredient')
        ordering = ['ingredient']
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'


class BaseRecipeRelationship(models.Model):
    """Базовый класс для взаимосвязей с рецептами."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)s'
    )
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        abstract = True
        unique_together = ('user', 'recipe')


class FavoriteRecipe(BaseRecipeRelationship):
    """Модель рецептов в избранном."""

    class Meta(BaseRecipeRelationship.Meta):
        ordering = ['recipe']
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class ShoppingCart(BaseRecipeRelationship):
    """Модель для добавления рецепта в покупки."""

    class Meta(BaseRecipeRelationship.Meta):
        ordering = ['recipe']
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
