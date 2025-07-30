from django.contrib import admin

from apps.games.models import PlaytimeCategory


@admin.register(PlaytimeCategory)
class PlaytimeCategoryAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("playtime_id", "name", "min_minutes", "max_minutes")
    search_fields = ("name",)
    ordering = ("min_minutes",)
