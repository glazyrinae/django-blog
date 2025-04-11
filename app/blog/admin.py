from django.contrib import admin
from django.utils.html import format_html
from .models import Post, Images


class ImageInline(admin.StackedInline):
    # exclude = ("thumbnail", )
    model = Images
    extra = 3
    readonly_fields = ("thumbnail_preview",)
    fields = ("image", "thumbnail_preview", "image_type")

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" width="350" height="200" />', obj.thumbnail.url
            )
        return "-"

    thumbnail_preview.short_description = "Thumbnail Preview"


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "author", "publish", "status"]
    list_filter = ["status", "created", "publish", "author"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ["author"]
    date_hierarchy = "publish"
    ordering = ["status", "publish"]
    inlines = [ImageInline]
