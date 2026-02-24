import logging

from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Images, Post

logger = logging.getLogger("blog")

# Constants
THUMBNAIL_SIZE = (350, 200)
TEXT_ROWS = 20
FONT_SIZE = 16


class ImageInline(admin.StackedInline):
    model = Images
    extra = 0
    readonly_fields = ("thumbnail_preview",)
    fields = ("image", "thumbnail_preview", "image_type")

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                f'<img src="{obj.thumbnail.url}" width="{THUMBNAIL_SIZE[0]}" height="{THUMBNAIL_SIZE[1]}" />'
            )
        return "-"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["title", "url_path", "num_item"]
    search_fields = ["title"]
    prepopulated_fields = {"url_path": ("title",)}

    def save_model(self, request, obj, form, change):
        """Log category admin actions."""
        action = "updated" if change else "created"
        logger.info(f"Admin {request.user.username} {action} category: {obj.title}")
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        """Log category deletion."""
        logger.warning(f"Admin {request.user.username} deleted category: {obj.title}")
        super().delete_model(request, obj)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "slug", "author", "publish", "status"]
    list_filter = ["status", "created", "publish", "author"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ["author"]
    date_hierarchy = "publish"
    ordering = ["status", "publish"]
    inlines = [ImageInline]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["body"].widget.attrs.update(
            {
                "rows": TEXT_ROWS,
                "style": f"width: 100%; font-family: monospace; font-size: {FONT_SIZE}px",
            }
        )
        return form

    def save_model(self, request, obj, form, change):
        """Log post admin actions."""
        action = "updated" if change else "created"
        logger.info(
            f"Admin {request.user.username} {action} post: '{obj.title}' (status: {obj.status})"
        )
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        """Log post deletion."""
        logger.warning(f"Admin {request.user.username} deleted post: '{obj.title}'")
        super().delete_model(request, obj)
