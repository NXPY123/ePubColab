"""
URL configuration for ePubColab project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from rest_framework.authtoken import views

from ePubColab import api_views, chat_views

router = routers.DefaultRouter()
router.register(r"users", api_views.UserViewSet)
router.register(r"files", api_views.FileViewSet)
router.register(r"shared", api_views.SharedFileViewSet)
router.register(r"highlights", api_views.HighlightsViewSet)


urlpatterns = [
    path("files/link/", api_views.FileViewSet.as_view({"get": "download_link"})),
    path("admin/", admin.site.urls),
    path("chat/", chat_views.index, name="index"),
    path("chat/<str:room_name>/", chat_views.room, name="room"),
    path("", include(router.urls)),
    path("api-token-auth/", views.obtain_auth_token),
    path(
        "files/status/<str:task_id>/",
        api_views.FileViewSet.as_view({"get": "upload_status"}),
    ),
]
