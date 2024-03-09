from django.urls import path
from admin_app import views

urlpatterns = [
    path('sneakerheads/admin/log_in', views.admin_login, name='admin_login'),
    path('sneakerheads/admin/log_out', views.admin_logout, name = 'admin_logout'),
    path('sneakerheads/admin/customers', views.admin_customers, name = 'admin_customers'),
    path('block-user/<int:user_id>/', views.block_user, name='block_user'),
    path('unblock-user/<int:user_id>/', views.unblock_user, name='unblock_user'),
    path('sneakerheads/admin/customer/search', views.search_user, name='search_user'),
]
