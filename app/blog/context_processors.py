def global_context(request):
    from .models import Category, Post, SocialMedia, BlogSettings # пример моделей

    url_parts = request.path.split("/")
    url_parts = [url_part for url_part in url_parts if url_part]
    active = url_parts[0] if len(url_parts) > 0 else "home"
    blog_settings = BlogSettings.objects.values().first()

    
    return {
        "categories": Category.objects.all(),
        "active": active,
        "cnt_posts": Post.published.count(),
        "title": blog_settings.get("blog_title", "") if blog_settings else "",
        "about": blog_settings.get("blog_desc", "") if blog_settings else "",
        "footer": blog_settings.get("blog_footer", "") if blog_settings else "",
        "avatar": blog_settings.get("avatar", "") if blog_settings else "",
        "social_media": SocialMedia.objects.all()
    }
