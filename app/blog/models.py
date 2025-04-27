from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from taggit.managers import TaggableManager
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank


class PublishedManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(status=Post.Status.PUBLISHED)
            .order_by("-publish")
        )


class BlogSettings(models.Model):
    # TEMPLATE_COLORS = [
    #     ("", "vk"),
    #     ("fa-linkedin", "linkedin"),
    #     ("fa-google", "google"),
    #     ("fa-stack-overflow", "stack-overflow"),
    #     ("fa-github", "github"),
    #     ("fa-youtube", "youtube"),
    # ]
    avatar = models.ImageField(blank=True)
    blog_title = models.CharField(max_length=250, unique=True)
    blog_desc = models.CharField(max_length=250, unique=True)
    blog_footer = models.CharField(max_length=250, unique=True)
    #template_color=


    def __str__(self):
        return self.blog_title


class SocialMedia(models.Model):
    SOCIAL_MEDIA_TYPE_CHOICES = [
        ("fa-vk", "vk"),
        ("fa-linkedin", "linkedin"),
        ("fa-google", "google"),
        ("fa-stack-overflow", "stack-overflow"),
        ("fa-github", "github"),
        ("fa-youtube", "youtube"),
    ]

    title = models.CharField(
        max_length=250,
        choices=SOCIAL_MEDIA_TYPE_CHOICES,
        default="vk",
        verbose_name="social media",
    )
    url_link = models.CharField(max_length=250, default="")
    blog_settings = models.ForeignKey(
        BlogSettings, on_delete=models.CASCADE, related_name="social_media"
    )

    def __str__(self):
        return self.title


class Category(models.Model):
    TYPE_CATEGORY = [
        ("posts", "Посты"),
        ("page", "Страница"),
    ]

    title = models.CharField(max_length=250, unique=True)
    num_item = models.SmallIntegerField(default=0)
    url_path = models.SlugField(max_length=250, default="")
    type_category = models.CharField(
        max_length=20, choices=TYPE_CATEGORY, default="posts"
    )

    def __str__(self):
        return self.title


# class Page(models.Model):
#     class Status(models.TextChoices):
#         DRAFT = "DF", "Draft"
#         PUBLISHED = "PB", "Published"

#     title = models.CharField(max_length=250)
#     slug = models.SlugField(max_length=250, unique_for_date="publish")
#     created = models.DateTimeField(auto_now_add=True)
#     updated = models.DateTimeField(auto_now=True) 
#     publish = models.DateTimeField(default=timezone.now)   
#     body = models.TextField()
#     category = models.ForeignKey(
#         Category, on_delete=models.SET_NULL, null=True, related_name="page"
#     )
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
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="posts"
    )

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
            args=[
                self.category.url_path,
                self.publish.year,
                self.publish.month,
                self.publish.day,
                self.slug,
            ],
        )

    def get_image(self, image_type: str):
        """Список файлов"""
        return (
            self.images.filter(image_type=image_type)
            .values_list("image", flat=True)
            .first()
        )

    @classmethod
    def get_posts_by_search(cls, search):
        search_vector = SearchVector("title", "body")
        search_query = SearchQuery(search)
        results = (
            cls.published.annotate(
                search=search_vector, rank=SearchRank(search_vector, search_query)
            )
            .filter(search=search_query)
            .order_by("-rank")
        )
        return results

    @classmethod
    def get_prev_next_posts(cls, url_path: str, pk: int, option: str, sorted_by_pk: str) -> tuple:
        if option == "next": 
            return (
                cls.objects.filter(
                    category__url_path=url_path,
                    status=cls.Status.PUBLISHED,
                    pk__gt=pk,
                )
                .order_by(sorted_by_pk)
                .first()
            )
        else:
            return (
                cls.objects.filter(
                    category__url_path=url_path,
                    status=cls.Status.PUBLISHED,
                    pk__lt=pk,
                )
                .order_by(sorted_by_pk)
                .first()
            )

    @property
    def get_path_image_thumbnail(self):
        """Список файлов"""
        return (
            self.images.filter(image_type="thumbnail")
            .values_list("thumbnail", flat=True)
            .first()
        )

    @property
    def get_path_image_main(self):
        """Список файлов"""
        return (
            self.images.filter(image_type="main")
            .values_list("image", flat=True)
            .first()
        )


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
