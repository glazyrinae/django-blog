"""Blog application models."""

import logging

from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import models
from django.urls import reverse
from django.utils import timezone
from settings.models import BlogSettings
from taggit.managers import TaggableManager

logger = logging.getLogger("blog")


class PublishedManager(models.Manager):
    """Manager for retrieving only published posts."""

    def get_queryset(self):
        """Return queryset filtered by published status and ordered by publish date."""
        return (
            super()
            .get_queryset()
            .filter(status=Post.Status.PUBLISHED)
            .order_by("-publish")
        )


class SocialMedia(models.Model):
    """Social media links associated with blog settings."""

    SOCIAL_MEDIA_TYPE_CHOICES = [
        ("fa-vk", "VK"),
        ("fa-linkedin", "LinkedIn"),
        ("fa-google", "Google"),
        ("fa-stack-overflow", "Stack Overflow"),
        ("fa-github", "GitHub"),
        ("fa-youtube", "YouTube"),
    ]

    title = models.CharField(
        max_length=250,
        choices=SOCIAL_MEDIA_TYPE_CHOICES,
        default="fa-vk",
        verbose_name="Social Media",
    )
    url_link = models.URLField(max_length=250, verbose_name="URL")
    blog_settings = models.ForeignKey(
        BlogSettings, on_delete=models.CASCADE, related_name="social_media"
    )

    class Meta:
        verbose_name = "Social Media"
        verbose_name_plural = "Social Media"

    def __str__(self):
        return self.get_title_display()

    def __repr__(self):
        return f"<SocialMedia: {self.title} - {self.url_link}>"

    def save(self, *args, **kwargs):
        """Override save to log social media changes."""
        action = "Updating" if self.pk else "Creating"
        logger.debug(f"{action} social media link: {self.title} - {self.url_link}")
        super().save(*args, **kwargs)


class Category(models.Model):
    """Blog content categories."""

    TYPE_POSTS = "posts"
    TYPE_PAGE = "page"

    TYPE_CATEGORY_CHOICES = [
        (TYPE_POSTS, "Посты"),
        (TYPE_PAGE, "Страница"),
    ]

    title = models.CharField(max_length=250, unique=True)
    num_item = models.SmallIntegerField(default=0, verbose_name="Number of Items")
    url_path = models.SlugField(max_length=250, unique=True)
    type_category = models.CharField(
        max_length=20,
        choices=TYPE_CATEGORY_CHOICES,
        default=TYPE_POSTS,
        verbose_name="Category Type",
    )

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["title"]

    def __str__(self):
        return self.title

    def __repr__(self):
        return f"<Category: {self.title} ({self.type_category})>"

    def save(self, *args, **kwargs):
        """Override save to log category changes."""
        action = "Updating" if self.pk else "Creating"
        logger.info(f"{action} category: {self.title} (type: {self.type_category})")
        super().save(*args, **kwargs)
        logger.debug(f"Category saved: {self.title} (ID: {self.pk})")

    def delete(self, *args, **kwargs):
        """Override delete to log deletion."""
        logger.warning(f"Deleting category: {self.title} (ID: {self.pk})")
        super().delete(*args, **kwargs)


class Post(models.Model):
    """Blog post model with full-text search and tagging support."""

    class Status(models.TextChoices):
        DRAFT = "DF", "Draft"
        PUBLISHED = "PB", "Published"

    # Fields
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique_for_date="publish")
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=2, choices=Status.choices, default=Status.DRAFT
    )
    body = models.TextField()

    # Relations
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="blog_posts"
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="posts"
    )
    tags = TaggableManager()

    # Managers
    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        verbose_name = "Post"
        verbose_name_plural = "Posts"
        ordering = ["-publish"]
        indexes = [
            models.Index(fields=["-publish"]),
        ]

    def __str__(self):
        return self.title

    def __repr__(self):
        return f"<Post: {self.title} ({self.status})>"

    def save(self, *args, **kwargs):
        """Override save to log post changes."""
        action = "Updating" if self.pk else "Creating"
        logger.info(
            f"{action} post: '{self.title}' (status: {self.status}, author: {self.author.username})"
        )

        try:
            super().save(*args, **kwargs)
            logger.debug(f"Post saved: {self.title} (ID: {self.pk})")
        except Exception as e:
            logger.error(f"Error saving post '{self.title}': {e}", exc_info=True)
            raise

    def delete(self, *args, **kwargs):
        """Override delete to log deletion."""
        logger.warning(f"Deleting post: '{self.title}' (ID: {self.pk})")
        try:
            super().delete(*args, **kwargs)
            logger.info(f"Post deleted: {self.title}")
        except Exception as e:
            logger.error(f"Error deleting post '{self.title}': {e}", exc_info=True)
            raise

    def get_absolute_url(self):
        """Return the canonical URL for the post."""
        return reverse(
            "blog:post_detail",
            args=[
                self.category.url_path,
                self.publish.year,
                self.publish.month,
                self.publish.day,
                self.slug,
            ],
        )

    def get_image(self, image_type: str) -> str | None:
        """
        Get image path by type.

        Args:
            image_type: Type of image ('main', 'secondary', 'thumbnail')

        Returns:
            Image path or None if not found
        """
        return (
            self.images.filter(image_type=image_type)
            .values_list("image", flat=True)
            .first()
        )

    @classmethod
    def get_posts_by_search(cls, search_query: str):
        """
        Perform full-text search on posts.

        Args:
            search_query: Search term

        Returns:
            QuerySet of posts matching the search, ordered by relevance
        """
        logger.debug(f"Performing full-text search for: '{search_query}'")
        try:
            search_vector = SearchVector("title", "body")
            search_query_obj = SearchQuery(search_query)
            results = (
                cls.published.annotate(
                    search=search_vector,
                    rank=SearchRank(search_vector, search_query_obj),
                )
                .filter(search=search_query_obj)
                .order_by("-rank")
            )
            logger.debug(f"Search completed, found {results.count()} results")
            return results
        except Exception as e:
            logger.error(f"Search error for query '{search_query}': {e}", exc_info=True)
            raise

    @classmethod
    def get_prev_next_posts(
        cls, url_path: str, pk: int, option: str, sorted_by_pk: str
    ) -> str | None:
        """
        Get previous or next post in the same category.

        Args:
            url_path: Category URL path
            pk: Current post primary key
            option: 'next' or 'prev'
            sorted_by_pk: Sorting order ('pk' or '-pk')

        Returns:
            Post object or None if not found
        """
        logger.debug(f"Getting {option} post for pk={pk} in category {url_path}")

        try:
            if option == "next":
                post = (
                    cls.objects.filter(
                        category__url_path=url_path,
                        status=cls.Status.PUBLISHED,
                        pk__gt=pk,
                    )
                    .order_by(sorted_by_pk)
                    .first()
                )
            else:
                post = (
                    cls.objects.filter(
                        category__url_path=url_path,
                        status=cls.Status.PUBLISHED,
                        pk__lt=pk,
                    )
                    .order_by(sorted_by_pk)
                    .first()
                )

            if post:
                logger.debug(f"Found {option} post: {post.title}")
            else:
                logger.debug(f"No {option} post found")

            return post
        except Exception as e:
            logger.error(f"Error getting {option} post: {e}", exc_info=True)
            return None

    @property
    def thumbnail_path(self) -> str | None:
        """Get thumbnail image path."""
        return (
            self.images.filter(image_type=Images.TYPE_THUMBNAIL)
            .values_list("thumbnail", flat=True)
            .first()
        )

    @property
    def main_image_path(self) -> str | None:
        """Get main image path."""
        return (
            self.images.filter(image_type=Images.TYPE_MAIN)
            .values_list("image", flat=True)
            .first()
        )


class Images(models.Model):
    """Images associated with blog posts."""

    TYPE_MAIN = "main"
    TYPE_SECONDARY = "secondary"
    TYPE_THUMBNAIL = "thumbnail"

    IMAGE_TYPE_CHOICES = [
        (TYPE_MAIN, "Основное изображение"),
        (TYPE_SECONDARY, "Дополнительное"),
        (TYPE_THUMBNAIL, "Миниатюра"),
    ]

    image = models.ImageField(upload_to="blog/images/%Y/%m/%d/", blank=True)
    thumbnail = models.ImageField(upload_to="blog/images/%Y/%m/%d/thumbnails/")
    image_type = models.CharField(
        max_length=10,
        choices=IMAGE_TYPE_CHOICES,
        default=TYPE_SECONDARY,
        verbose_name="Тип изображения",
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")

    class Meta:
        verbose_name = "Image"
        verbose_name_plural = "Images"

    def __str__(self):
        return f"{self.post.title} - {self.get_image_type_display()}"

    def __repr__(self):
        return f"<Images: {self.post.title} - {self.image_type}>"

    def save(self, *args, **kwargs):
        """Override save to log image uploads."""
        action = "Updating" if self.pk else "Uploading"
        logger.info(
            f"{action} image for post '{self.post.title}': {self.image_type}"
        )
        try:
            super().save(*args, **kwargs)
            logger.debug(f"Image saved (ID: {self.pk})")
        except Exception as e:
            logger.error(
                f"Error saving image for post '{self.post.title}': {e}",
                exc_info=True,
            )
            raise

    def delete(self, *args, **kwargs):
        """Override delete to log deletion."""
        logger.info(
            f"Deleting image for post '{self.post.title}': {self.image_type} (ID: {self.pk})"
        )
        super().delete(*args, **kwargs)
