from django.urls import path
from admin_app import views

urlpatterns = [
    path('sneakerheads/admin/login/', views.admin_login, name='admin_login'),
    path('sneakerheads/admin/logout/', views.admin_logout, name = 'admin_logout'),
    
    path('sneakerheads/admin/products/', views.admin_products, name = 'admin_products'),
    
    path('sneakerheads/admin/categories/', views.admin_categories, name = 'admin_categories'),
    path('add-category/page', views.add_category_page, name = 'add_category_page'),
    path("add_categories/", views.add_categories ,name="add_categories"),
    
    path('sneakerheads/admin/customers/', views.admin_customers, name = 'admin_customers'),
    path('block-user/<int:user_id>/', views.block_user, name='block_user'),
    path('unblock-user/<int:user_id>/', views.unblock_user, name='unblock_user'),
    path('sneakerheads/admin/customer/search/', views.search_user, name='search_user'),
]
