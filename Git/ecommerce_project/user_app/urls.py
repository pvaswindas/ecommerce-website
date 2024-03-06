from django.urls import path
from user_app import views

urlpatterns = [
    path('', views.index_page, name = 'index_page'),
    path('register/', views.register_function, name='register_function'),
    path('sign-in/', views.sign_in_function, name='sign_in_function'),
    path('test/signin/', views.test_signin, name='test_sign_in'),
    path('test/signup/', views.test_signup, name='test_sign_up'),
]
