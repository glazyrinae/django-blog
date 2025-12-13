import logging
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Post, Category
from .utils import validate_search_query, check_rate_limit

POSTS_PER_PAGE = 3
logger = logging.getLogger("blog")


def handle_blog_exceptions(view_func):
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Http404 as e:
            # Обрабатываем явный Http404
            return render(
                request,
                "base/_error.html",
                {"error": str(e) or "Page not found", "status_code": 404},
                status=404,
            )
        except Category.DoesNotExist:
            return render(
                request,
                "base/_error.html",
                {"error": "Category not found", "status_code": 404},
                status=404,
            )
        except Post.DoesNotExist:
            return render(
                request,
                "base/_error.html",
                {"error": "Post not found", "status_code": 404},
                status=404,
            )
        except Exception as e:
            logger.error(f"Unexpected error in {view_func.__name__}: {e}")
            return render(
                request,
                "base/_error.html",
                {"error": str(e), "status_code": 500},
                status=500,
            )

    return wrapper


@handle_blog_exceptions
def post_list(request, category: str = ""):
    """
    Display list of posts or single page based on category and search.
    """
    template_name = "blog/post/list.html"
    context = {}

    if category:
        return _handle_category_view(request, category, template_name, context)

    if search_query := validate_search_query(request.GET.get("search", "")):
        if not check_rate_limit(request, "search", 15, 60):
            return render(
                request,
                "base/_error.html",
                {
                    "error": "No published posts found for this category",
                    "status_code": 423,
                },
                status=423,
            )
        return _handle_search_view(request, search_query, template_name, context)

    return _handle_main_list_view(request, template_name, context)


@handle_blog_exceptions
def post_detail(request, url_path: str, year: int, month: int, day: int, post: str):
    """
    Display single post detail.
    """
    post_obj = get_object_or_404(
        Post.objects.select_related("category", "author").prefetch_related("images"),
        slug=post,
        publish__year=year,
        publish__month=month,
        publish__day=day,
        status=Post.Status.PUBLISHED,
    )

    # Проверяем соответствие категории в URL
    if post_obj and post_obj.category.url_path != url_path:
        raise Http404("Post not found in this category")

    context = {
        "post": post_obj,
        "category": post_obj.category.title,
    }

    return render(request, "blog/post/detail.html", context)


@handle_blog_exceptions
def _handle_category_view(request, category: str, template_name: str, context: dict):
    """Handle category-specific views."""
    category_obj = get_object_or_404(Category, url_path=category)
    logger.info(f"Открываю категорию для постов - {category}")
    posts_query = (
        Post.objects.select_related("category", "author")
        .prefetch_related("images")
        .filter(category__url_path=category, status=Post.Status.PUBLISHED)
    )

    if category_obj.type_category == Category.TYPE_POSTS:
        # Posts list for this category
        posts = posts_query.all()
        context.update(
            {
                "posts": posts,
                "category": category_obj.title,
                "cnt": posts.count(),
            }
        )
        template_name = "blog/post/list.html"
    else:
        # Single page for this category
        post = posts_query.first()
        if not post:
            raise Http404("No published posts found for this category")

        context.update(
            {
                "post": post,
                "category": category_obj.title,
            }
        )
        template_name = "blog/post/detail.html"

    return _handle_main_list_view(request, template_name, context)


@handle_blog_exceptions
def _handle_search_view(request, search_query: str, template_name: str, context: dict):
    """Handle search functionality."""
    posts = Post.get_posts_by_search(search_query)
    context.update(
        {
            "posts": posts,
            "search": search_query,
            "cnt": posts.count(),
        }
    )
    return _handle_main_list_view(request, template_name, context)


@handle_blog_exceptions
def _handle_main_list_view(request, template_name: str, context: dict):
    """Handle main posts list with pagination."""
    posts = Post.published.select_related("category", "author").prefetch_related(
        "images"
    )

    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get("page", 1)

    try:
        posts_page = paginator.page(page_number)
    except PageNotAnInteger:
        posts_page = paginator.page(1)
    except EmptyPage:
        posts_page = paginator.page(paginator.num_pages)

    context["posts"] = posts_page
    return render(request, template_name, context)
