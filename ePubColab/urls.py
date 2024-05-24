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
from ePubColab import api_views

router = routers.DefaultRouter()
router.register(r'users', api_views.UserViewSet)


urlpatterns = [
    path("admin/", admin.site.urls),
     path('', include(router.urls)),
    path('api-token-auth/', views.obtain_auth_token),
    #path("create_user/", api_views.CreateUserView.as_view(), name="create_user"),
]