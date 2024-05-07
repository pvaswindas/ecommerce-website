from django.contrib import admin
from django.urls import path, include
from user_app.views import error_page

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("user_app.urls")),
    path("", include("admin_app.urls")),
    path("accounts/", include("allauth.urls"), name="accounts"),
]


handler404 = "user_app.views.error_page"
