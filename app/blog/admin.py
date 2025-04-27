from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import Post, Category, Images, BlogSettings, SocialMedia


class ImageInline(admin.StackedInline):
    model = Images
    extra = 1
    readonly_fields = ("thumbnail_preview",)
    fields = ("image", "thumbnail_preview", "image_type")

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" width="350" height="200" />', obj.thumbnail.url
            )
        return "-"

    thumbnail_preview.short_description = "Thumbnail Preview"


class SocialMediaInline(admin.StackedInline):
    model = SocialMedia
    extra = 1
    # readonly_fields = ()
    fields = ("title", "url_link")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["title", "url_path", "num_item"]
    search_fields = ["title"]
    prepopulated_fields = {"url_path": ("title",)}


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
                "rows": "20",
                "style": "width: 100%; font-family: monospace; font-size: 16px",
            }
        )
        return form


@admin.register(BlogSettings)
class BlogSettingsAdmin(admin.ModelAdmin):
    inlines = [SocialMediaInline]
    list_display = ["blog_title", "blog_desc", "blog_footer", "avatar"]
    search_fields = ["blog_title"]

    def has_add_permission(self, request):
        return BlogSettings.objects.count() == 0

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["blog_desc"].widget = forms.Textarea(attrs={
            'rows': 6,
            'cols': 60,
            'style': 'font-family: monospace;'  # дополнительные стили
        })
        return form