from django.urls import path
from admin_app.views import *
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('sneakerheads/admin/login/', admin_login_page, name='admin_login_page'),
    path('sneakerheads/admin/check_login/', admin_check_login, name='admin_check_login'),
    path('sneakerheads/admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('sneakerheads/admin/logout/', admin_logout, name = 'admin_logout'),
    
    
    path('page_not_found/', page_not_found, name='page_not_found'),
    
    path('sneakerheads/admin/get_quantity/<str:size>/', get_quantity, name='get_quantity'),
    
    path('sneakerheads/admin/product/', list_product_page, name='list_product_page'),
    path('sneakerheads/admin/product/add-products/', admin_add_product, name='admin_add_product'),
    path('sneakerheads/admin/product/add-product/page/', add_products, name='add_products'),
    path('sneakerheads/admin/product/edit-product-page/<int:p_id>/', edit_product_page, name='edit_product_page'),
    path('sneakerheads/admin/product/edit-product/update/<int:p_id>/', edit_product_update, name='edit_product_update'),
    path('sneakerheads/admin/product/delete-product/<int:pdt_id>/', delete_product, name='delete_product'),
    path('sneakerheads/admin/product/deleted-product-view/', deleted_product_page, name='deleted_product_page'),
    path('sneakerheads/admin/product/restore-product/<int:pdt_id>/', restore_product, name='restore_product'),
    path('sneakerheads/admin/product/add-product-variant/', admin_add_variants, name='admin_add_variants'),
    path('sneakerheads/admin/product/add-product-size/', add_size, name = 'add_size'),
    path('sneakerheads/admin/product/add-product-image/', admin_add_image_page, name='admin_add_image_page'),
    path('sneakerheads/admin/product/add-product-color-image/', add_product_image, name='add_product_image'),
    path('sneakerheads/admin/product/get-colors/', get_colors, name='get_colors'),
    path('sneakerheads/admin/product/list-product/<int:pdt_id>/', list_product, name='list_product'),
    path('sneakerheads/admin/product/un-list-product/<int:pdt_id>/', un_list_product, name='un_list_product'),
    path('sneakerheads/admin/product/get-sizes/', get_sizes_view, name='get_sizes'),
    
    path('sneakerheads/admin/product/edit-product-color/page/<int:p_id>/', edit_product_color_page, name='edit_product_color_page'),
    path('sneakerheads/admin/product/edit-product-size-page/<int:p_id>/', edit_product_size_page, name='edit_product_size_page'),
    
    path('sneakerheads/admin/product/product-color-edit/<int:p_id>/', edit_product_color, name='edit_product_color'),
    path('sneakerheads/admin/product/product-size-edit/<int:p_id>/', edit_product_size, name='edit_product_size'),
    
    
    
    path('sneakerheads/admin/brand/', list_brand_page, name='list_brand_page'),
    path('sneakerheads/admin/brand/add-brand/', admin_add_brand, name='admin_add_brand'),
    path('sneakerheads/admin/brand/add-brand/page/', add_brand, name='add_brand'),
    path('sneakerheads/admin/brand/list-brand/<int:brand_id>/', list_the_brand, name='list_the_brand'),
    path('sneakerheads/admin/brand/un-list-brand/<int:brand_id>/', un_list_the_brand, name='un_list_the_brand'),
    path('sneakerheads/admin/brand/delete-brand/<int:brand_id>/', delete_brand, name='delete_brand'),
    path('sneakerheads/admin/brand/deleted-brand-view/', deleted_brand_view, name='deleted_brand_view'),
    path('sneakerheads/admin/brand/restore-brand/<int:brand_id>/', restore_brand, name='restore_brand'),
    path('sneakerheads/admin/brand/edit-brand-page/<int:brand_id>/', edit_brand_page, name='edit_brand_page'),
    path('sneakerheads/admin/brand/edit-brand/<int:brand_id>/', edit_brand, name='edit_brand'),
    
    
    
    
    
    path('sneakerheads/admin/category/', admin_categories, name = 'admin_categories'),
    path('sneakerheads/admin/category/add-category/page', admin_add_category_page, name = 'admin_add_category_page'),
    path("sneakerheads/admin/category/add-categories/", add_categories ,name="add_categories"),
    path('sneakerheads/admin/category/edit-category-page/<int:cat_id>/', edit_category_page, name='edit_category_page'),
    path('sneakerheads/admin/category/edit-category/<int:cat_id>/', edit_category, name='edit_category'),
    path('sneakerheads/admin/category/delete-category/<int:cat_id>/', delete_category, name='delete_category'),
    path('sneakerheads/admin/category/list-category/<int:cat_id>/', list_category, name='list_category'),
    path('sneakerheads/admin/category/un-list-category/<int:cat_id>/', un_list_category, name='un_list_category'),
    path('sneakerheads/admin/category/deleted-category-view', deleted_cat_view, name='deleted_cat_view'),
    path('sneakerheads/admin/category/restore-categories/<int:cat_id>/', restore_categories, name='restore_categories'),
    
    
    
    path('sneakerheads/admin/customers/', admin_customers, name = 'admin_customers'),
    path('sneakerheads/admin/customers/block-user/<int:user_id>/', block_user, name='block_user'),
    path('sneakerheads/admin/customers/unblock-user/<int:user_id>/', unblock_user, name='unblock_user'),
    path('sneakerheads/admin/customers/sneakerheads/admin/customer/search/', search_user, name='search_user'),
    
    
    
    
    path('sneakerheads/admin/orders/', orders_view_page, name='orders_view_page'),
    path('sneakerheads/admin/orders/detailed-view/<str:order_id>/', order_detailed_view, name='order_detailed_view'),
    path('sneakerheads/admin/change-order-status/<str:order_id>/', change_order_status, name='change_order_status'),
    
    path('sneakerheads/admin/order/return-product/<str:order_items_id>/', return_product, name='return_product'),
    
    path('sneakerheads/admin/sales-report-page', sales_report_page, name='sales_report_page'),
    path('sneakerheads/admin/sales-report/download-option/', download_sales_report, name='download_sales_report'),
    
    
    
    path('sneakerheads/admin/offer/product-offer/module-view/', product_offer_module_view, name='product_offer_module_view'),
    path('sneakerheads/admin/offer/product-offer/edit-page/<str:product_color_image_name>/<str:color>/', product_offer_edit_page, name='product_offer_edit_page'),
    path('sneakerheads/admin/offer/product-offer/update/<int:product_offer_id>/', product_offer_update, name='product_offer_update'),
    path('sneakerheads/admin/offer/product-offer/add-page', product_offer_add_page, name='product_offer_add_page'),
    path('sneakerheads/admin/offer/product-offer/add-offer', add_product_offer, name='add_product_offer'),
    path('sneakerheads/admin/offer/product-offer/delete-offer/<int:product_offer_id>/', delete_offer, name='delete_offer'),
    
    
    path('sneakerheads/admin/offer/category-offer/module_view/', category_offer_module_view, name='category_offer_module_view'),
    path('sneakerheads/admin/offer/category-offer/add-page/', category_offers_add_page, name='category_offers_add_page'),
    path('sneakerheads/admin/offer/category-offer/add-category-offer/', add_category_offer, name='add_category_offer'),
    path('sneakerheads/admin/offer/category-offer/edit-page/<str:category_name>/', category_offer_edit_page, name='category_offer_edit_page'),
    path('sneakerheads/admin/offer/category-offer/update/<int:category_offer_id>/', category_offer_update, name='category_offer_update'),
    path('sneakerheads/admin/offer/category-offer/delete/<int:category_offer_id>/', delete_category_offer, name='delete_category_offer'),
    
    
    path('sneakerheads/admin/coupon/', coupon_page_view, name='coupon_page_view'),
    path('sneakerheads/admin/coupon/add-coupon-page/', add_coupon_page, name='add_coupon_page'),
    path('sneakerheads/admin/coupon/add-coupon/', add_coupon, name='add_coupon'),
    path('sneakerheads/admin/coupon_edit_page/<str:coupon_id>/', coupon_edit_page, name='coupon_edit_page'),
    path('sneakerheads/admin/coupon/update_coupon/<str:coupon_id>/', update_coupon, name='update_coupon'),
    path('sneakerheads/admin/coupon/delete_coupon/<str:coupon_id>/', delete_coupon, name='delete_coupon'),
    
]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)