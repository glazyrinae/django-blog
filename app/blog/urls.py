from django.urls import path
from . import views

app_name = "blog"
urlpatterns = [
    # представления поста
    path(
        "<str:url_path>/<int:year>/<int:month>/<int:day>/<slug:post>/",
        views.post_detail,
        name="post_detail",
    ),
    path("", views.post_list, name="post_list"),
    path(
        "<slug:category>/",
        views.post_list,
        name="category",
    ),
]
