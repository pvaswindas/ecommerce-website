from django.urls import path
from admin_app import views

urlpatterns = [
    path('sneakerheads/admin/login/', views.admin_login, name='admin_login'),
    path('sneakerheads/admin/logout/', views.admin_logout, name = 'admin_logout'),
    
    
    path('sneakerheads/admin/products/', views.admin_products, name = 'admin_products'),
    
    
    path('sneakerheads/admin/categories/', views.admin_categories, name = 'admin_categories'),
    path('add-category/page', views.add_category_page, name = 'add_category_page'),
    path("add-categories/", views.add_categories ,name="add_categories"),
    path('delete-category/<int:cat_id>/', views.delete_category, name='delete_category'),
    path('list-category/<int:cat_id>/', views.list_category, name='list_category'),
    path('un-list-category/<int:cat_id>/', views.un_list_category, name='un_list_category'),
    path('deleted-view', views.deleted_cat_view, name='deleted_cat_view'),
    path('restore-categories/<int:cat_id>/', views.restore_categories, name='restore_categories'),
    
    
    path('sneakerheads/admin/customers/', views.admin_customers, name = 'admin_customers'),
    path('block-user/<int:user_id>/', views.block_user, name='block_user'),
    path('unblock-user/<int:user_id>/', views.unblock_user, name='unblock_user'),
    path('sneakerheads/admin/customer/search/', views.search_user, name='search_user'),
]
