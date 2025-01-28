from django.shortcuts import get_object_or_404, redirect
from .models import Recipe


def redirect_short_link(request, short_link):
    recipe = get_object_or_404(Recipe, short_link=short_link)
    frontend_url = f"/recipes/{recipe.id}/"
    return redirect(frontend_url)
