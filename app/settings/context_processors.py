import logging

from blog.models import Category, Post, SocialMedia

from .models import BlogSettings

logger = logging.getLogger("settings")


def global_context(request):
    """
    Global context processor for blog settings and navigation.

    Provides common data to all templates:
    - Blog settings (title, description, footer, avatar)
    - Categories list
    - Active section based on URL
    - Total published posts count
    - Social media links
    """
    logger.debug(f"Processing global context for path: {request.path}")

    # Вычисляем активный раздел
    url_parts = request.path.strip("/").split("/")
    active_section = url_parts[0] if url_parts else "home"
    logger.debug(f"Active section: {active_section}")

    # Получаем настройки блога
    try:
        settings = (
            BlogSettings.objects.values(
                "blog_title", "blog_desc", "blog_footer", "avatar"
            ).first()
            or {}
        )

        if not settings:
            logger.warning("No blog settings found in database")
        else:
            logger.debug(f"Loaded blog settings: {settings.get('blog_title', 'N/A')}")

    except Exception as e:
        logger.error(f"Error loading blog settings: {e}", exc_info=True)
        settings = {}

    # Получаем категории и посты
    try:
        categories = Category.objects.all()
        category_count = categories.count()
        logger.debug(f"Loaded {category_count} categories")

        posts_count = Post.published.count()
        logger.debug(f"Total published posts: {posts_count}")

        social_media = SocialMedia.objects.all()
        social_count = social_media.count()
        logger.debug(f"Loaded {social_count} social media links")

    except Exception as e:
        logger.error(f"Error loading context data: {e}", exc_info=True)
        categories = Category.objects.none()
        posts_count = 0
        social_media = SocialMedia.objects.none()

    context = {
        "categories": categories,
        "active": active_section,
        "cnt_posts": posts_count,
        "title": settings.get("blog_title", ""),
        "about": settings.get("blog_desc", ""),
        "footer": settings.get("blog_footer", ""),
        "avatar": settings.get("avatar", ""),
        "social_media": social_media,
    }

    logger.debug("Global context processing completed")
    return context
