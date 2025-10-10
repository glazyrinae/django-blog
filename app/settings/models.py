import logging

from django.db import models

logger = logging.getLogger("settings")


class BlogSettings(models.Model):
    """Global blog settings and configuration."""

    avatar = models.ImageField(upload_to="blog/avatars/", blank=True)
    blog_title = models.CharField(max_length=250, unique=True)
    blog_desc = models.CharField(
        max_length=250, unique=True, verbose_name="Blog Description"
    )
    blog_footer = models.CharField(max_length=250, unique=True)

    class Meta:
        verbose_name = "Blog Settings"
        verbose_name_plural = "Blog Settings"

    def __str__(self):
        return self.blog_title

    def __repr__(self):
        return f"<BlogSettings: {self.blog_title}>"

    def save(self, *args, **kwargs):
        """Override save to log settings changes."""
        if self.pk:
            logger.info(f"Updating blog
