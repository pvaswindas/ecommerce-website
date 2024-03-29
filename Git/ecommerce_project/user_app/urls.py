from django.urls import path
from user_app import views

urlpatterns = [
    path('', views.index_page, name = 'index_page'),
    path('sneakerheads/sign-in/', views.sign_in, name='sign_in_page'),
    path('sneakerheads/sign-up/', views.sign_up, name='sign_up_page'),
    path('sneakerheads/user/logout/', views.logout, name='logout'),
    path('sneakerheads/verify/otp/', views.verify_otp, name='verify_otp'),
    path('sneakerheads/resend/otp/page/', views.resend_otp, name ='resend_otp_page'),
    path('sneakerheads/resend-otp/', views.resend_otp, name='resend_otp'),
    path('sneakerheads/otp/verification/', views.otp_verification_page, name='otp_verification_page'),
    path('sneakerheads/user/register/', views.register_function, name='register_function'),
    path('sneakerheads/sign-in/user/', views.sign_in_function, name='sign_in_function'),
    
    
    path('sneakerheads/shop/page/', views.shop_page_view, name='shop_page_view'),
    path('sneakerheads/<str:product_name>/<int:pdt_id>/', views.product_single_view_page, name='product_single_view_page'),
    
    
    
    path('sneakerheads/user/dashboard/<int:user_id>/', views.user_dashboard, name='user_dashboard'),
    path('sneakerheads/user/details-update/<int:user_id>/', views.user_details_edit, name='user_details_edit'),
    
    path('sneakerheads/user/manage-address/update/<int:address_id>/', views.update_address, name='update_address'),
    path('sneakerheads/user/manage-address/add-address/<int:customer_id>/', views.add_new_address, name='add_new_address'),
    
    
    path('sneakerheads/user/change-password/<int:user_id>/', views.user_change_password, name='user_change_password'),
    
    path('sneakerheads/user/cart/<int:user_id>/', views.cart_view_page, name='cart_view_page'),
    path('update_total_price/', views.update_total_price, name='update_total_price'),
    path('sneakerheads/user/remove_from_cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('clear_cart/', views.clear_cart, name='clear_cart'),
    path('update_quantity/', views.update_quantity, name='update_quantity'),
    
    path('sneakerheads/user/add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    
]
