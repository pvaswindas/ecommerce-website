from django.urls import path
from user_app import views

urlpatterns = [
    path('', views.index_page, name = 'index_page'),
    path('sign-in/', views.sign_in, name='sign_in_page'),
    path('sign-up/', views.sign_up, name='sign_up_page'),
    path('user-logout/', views.logout, name='logout'),
    path('register/', views.register_function, name='register_function'),
    path('sign-in/user', views.sign_in_function, name='sign_in_function'),
    path('custom-google-login/', views.custom_google_login, name='custom_google_login'),
]
