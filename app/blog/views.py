import logging

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, render
from django.utils.html import escape

from .models import Category, Post

logger = logging.getLogger("blog")


def post_list(request, category: str = ""):
    """Display list of posts, optionally filtered by category or search."""
    logger.info(f"Accessing post list page. Category: {category or 'all'}")

    params = dict()
    tmp = "blog/post/list.html"

    if category:
        logger.debug(f"Filtering posts by category: {category}")
        try:
            cat_type = Category.objects.filter(url_path=category).values().first()

            if not cat_type:
                logger.warning(f"Category not found: {category}")
                # Continue with default behavior or raise 404
                posts = Post.published.all()
            else:
                q_post = Post.objects.select_related("category").filter(
                    category__url_path=category
                )

                if cat_type["type_category"] == "posts":
                    posts = q_post.all()
                    post_count = posts.count()
                    logger.info(
                        f"Found {post_count} posts in category '{cat_type['title']}'"
                    )
                    params.update({"cnt": post_count})
                    params.update(
                        {
                            "posts": posts,
                            "category": cat_type["title"],
                        }
                    )
                else:
                    # Page type category
                    page = q_post.values().first()
                    tmp = "blog/post/detail.html"
                    logger.debug(
                        f"Rendering page type category: {cat_type['title']}"
                    )
                    params.update({"post": page, "category": cat_type["title"]})
                    return render(request, tmp, params)

        except Exception as e:
            logger.error(f"Error filtering posts by category '{category}': {e}", exc_info=True)
            raise

    elif search := escape(request.GET.get("search", "")):
        logger.info(f"Searching posts with query: '{search}'")
        try:
            posts = Post.get_posts_by_search(search)
            result_count = posts.count()
            logger.info(f"Search found {result_count} results for query '{search}'")
            params.update({"search": search, "cnt": result_count})
        except Exception as e:
            logger.error(f"Error during search for '{search}': {e}", exc_info=True)
            raise

    else:
        logger.debug("Loading all published posts")
        try:
            posts = Post.published.all()
            paginator = Paginator(posts, 3)
            page_number = request.GET.get("page", 1)
            logger.debug(f"Pagination: page {page_number}")

            try:
                posts = paginator.page(page_number)
            except PageNotAnInteger:
                logger.warning(f"Invalid page number: {page_number}, loading page 1")
                posts = paginator.page(1)
            except EmptyPage:
                logger.warning(
                    f"Page {page_number} out of range, loading last page"
                )
                posts = paginator.page(paginator.num_pages)

        except Exception as e:
            logger.error(f"Error loading post list: {e}", exc_info=True)
            raise

    params.update({"posts": posts})
    return render(request, tmp, params)


def post_detail(request, url_path, year, month, day, post):
    """Display single post detail with navigation to previous/next posts."""
    logger.info(
        f"Accessing post detail: {url_path}/{year}/{month}/{day}/{post}"
    )

    try:
        current_post = get_object_or_404(
            Post.objects.select_related("category"),
            status=Post.Status.PUBLISHED,
            slug=post,
            publish__year=year,
            publish__month=month,
            publish__day=day,
            category__url_path=url_path,
        )

        logger.info(
            f"Post found: '{current_post.title}' (ID: {current_post.pk})"
        )
        logger.debug(f"Post author: {current_post.author.username}")

        # Get navigation posts
        next_post = Post.get_prev_next_posts(url_path, current_post.pk, "next", "pk")
        previous_post = Post.get_prev_next_posts(
            url_path, current_post.pk, "prev", "-pk"
        )

        if next_post:
            logger.debug(f"Next post: {next_post.title}")
        if previous_post:
            logger.debug(f"Previous post: {previous_post.title}")

        return render(
            request,
            "blog/post/detail.html",
            {
                "post": current_post,
                "category": current_post,
                "next_post": next_post,
                "previous_post": previous_post,
            },
        )

    except Exception as e:
        logger.error(
            f"Error accessing post {url_path}/{year}/{month}/{day}/{post}: {e}",
            exc_info=True,
        )
        raise
