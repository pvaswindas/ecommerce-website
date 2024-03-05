from django.urls import path
from user_app import views

urlpatterns = [
    path('', views.index_page, name = 'index_page'),
    path('sign_in/', views.sign_in, name = 'sign_in'),
]
