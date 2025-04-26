from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.html import escape
from .models import Post, Category


def post_list(request, category: str = None):
    params = dict()
    tmp = "blog/post/list.html"
    if category:
        cat_type = Category.objects.filter(url_path=category).values().first()
        q_post = Post.objects.select_related("category").filter(
            category__url_path=category
        )
        if cat_type["type_category"] == "posts":
            posts = q_post.all()
            params.update({"cnt": posts.count()})
            params.update(
                {
                    "posts": posts,
                    "category": cat_type["title"],
                }
            )
        else:
            page = q_post.values().first()
            tmp = "blog/post/detail.html"
            params.update({"post": page, "category": cat_type["title"]})
            return render(
                request,
                tmp,
                params,
            )
    elif search := escape(request.GET.get("search", "")):
        posts = Post.get_posts_by_search(search)
        params.update({"search": search, "cnt": posts.count()})
    else:
        posts = Post.published.all()
        paginator = Paginator(posts, 3)
        page_number = request.GET.get("page", 1)
        try:
            posts = paginator.page(page_number)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)

    params.update({"posts": posts})
    return render(
        request,
        tmp,
        params,
    )


def post_detail(request, url_path, year, month, day, post):
    current_post = get_object_or_404(
        Post.objects.select_related("category"),
        status=Post.Status.PUBLISHED,
        slug=post,
        publish__year=year,
        publish__month=month,
        publish__day=day,
        category__url_path=url_path,
    )

    return render(
        request,
        "blog/post/detail.html",
        {
            "post": current_post,
            "category": current_post,
            "next_post": Post.get_prev_next_posts(url_path, current_post.pk, "pk"),
            "previous_post": Post.get_prev_next_posts(url_path, current_post.pk, "-pk"),
        },
    )
