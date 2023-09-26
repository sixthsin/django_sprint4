from django.contrib import admin

from .models import Category, Location, Post

admin.site.empty_value_display = 'Не задано'


class BaseAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'is_published',
    )
    list_editable = (
        'is_published',
    )
    search_fields = (
        'title',
    )
    list_filter = (
        'is_published',
    )


admin.site.register(Category, BaseAdmin)
admin.site.register(Post, BaseAdmin)
admin.site.register(Location)
