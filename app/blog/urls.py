from django.urls import path
from . import views

app_name = "blog"
urlpatterns = [
    # представления поста
    path("", views.post_list, name="post_list"),
    # path('', views.PostListView.as_view(), name='post_list'),
    path(
        "<str:url_path>/<int:year>/<int:month>/<int:day>/<slug:post>/",
        views.post_detail,
        name="post_detail",
    ),
    path(
        "<slug:category>/",
        views.post_list,
        name="category",
    ),
]
