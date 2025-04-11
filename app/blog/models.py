from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from taggit.managers import TaggableManager


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)


# Create your models here.
class Post(models.Model):
    tags = TaggableManager()

    class Status(models.TextChoices):
        DRAFT = "DF", "Draft"
        PUBLISHED = "PB", "Published"

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique_for_date="publish")
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=2, choices=Status.choices, default=Status.DRAFT
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="blog_posts"
    )

    body = models.TextField()

    objects = models.Manager()  # менеджер, применяемый по умолчанию
    published = PublishedManager()  # конкретно-прикладной менеджер

    class Meta:
        ordering = ["-publish"]
        indexes = [
            models.Index(fields=["-publish"]),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "blog:post_detail",
            args=[self.publish.year, self.publish.month, self.publish.day, self.slug],
        )

    def get_image(self, image_type: str):
        """Список файлов"""
        return (
            self.images.filter(image_type=image_type)
            .values_list('image', flat=True)
            .first()
        )
    
    @property
    def get_path_image_thumbnail(self):
        """Список файлов"""
        return (
            self.images.filter(image_type='thumbnail')
            .values_list('thumbnail', flat=True)
            .first()
        )
    
    @property
    def get_path_image_main(self):
        """Список файлов"""
        return (
            self.images.filter(image_type='main')
            .values_list('image', flat=True)
            .first()
        )
    # def get_thumbnail(self):
    #     return self.images.filter(post_id=self.id, image_type="thumbnail").thumbnail


class Images(models.Model):
    IMAGE_TYPE_CHOICES = [
        ("main", "Основное изображение"),
        ("secondary", "Дополнительное"),
        ("thumbnail", "Миниатюра"),
    ]

    image = models.ImageField(blank=True)
    thumbnail = models.ImageField(upload_to="%Y/%m/%d/thumbnails")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")

    image_type = models.CharField(
        max_length=10,
        choices=IMAGE_TYPE_CHOICES,
        default="secondary",
        verbose_name="Тип изображения",
    )
