from django.urls import path
from user_app.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", index_page, name="index_page"),
    path("sneakerheads/sign-in/", sign_in, name="sign_in_page"),
    path("sneakerheads/sign-up/", sign_up, name="sign_up_page"),
    path("sneakerheads/user/logout/", logout, name="logout"),
    path("sneakerheads/verify/otp/", verify_otp, name="verify_otp"),
    path("sneakerheads/resend/otp/page/", resend_otp, name="resend_otp_page"),
    path("sneakerheads/resend-otp/", resend_otp, name="resend_otp"),
    path(
        "sneakerheads/otp/verification/",
        otp_verification_page,
        name="otp_verification_page",
    ),
    path("sneakerheads/user/register/", register_function, name="register_function"),
    path("sneakerheads/sign-in/user/", sign_in_function, name="sign_in_function"),
    path(
        "sneakerheads/user/forgot-password/",
        forgot_password_page,
        name="forgot_password_page",
    ),
    path(
        "sneakerheads/user/reset-password/<int:user_id>/",
        reset_password,
        name="reset_password",
    ),
    path("sneakerheads/user/verify-email/", verify_email, name="verify_email"),
    path(
        "sneakerheads/user/reset_password_change/<int:user_id>/",
        reset_password_change,
        name="reset_password_change",
    ),
    path("sneakerheads/shop/page/", shop_page_view, name="shop_page_view"),
    path(
        "sneakerheads/<str:product_name>/<int:pdt_id>/",
        product_single_view_page,
        name="product_single_view_page",
    ),
    path("sneakerheads/user/dashboard/", user_dashboard, name="user_dashboard"),
    path(
        "sneakerheads/user/details-update/", user_details_edit, name="user_details_edit"
    ),
    path(
        "sneakerheads/user/manage-address/update/<int:address_id>/",
        update_address,
        name="update_address",
    ),
    path(
        "sneakerheads/user/manage-address/add-address/<int:customer_id>/",
        add_new_address,
        name="add_new_address",
    ),
    path(
        "sneakerheads/user/change-password/<int:user_id>/",
        user_change_password,
        name="user_change_password",
    ),
    path(
        "sneakerheads/user/cart/<int:user_id>/", cart_view_page, name="cart_view_page"
    ),
    path("update_total_price/", update_total_price, name="update_total_price"),
    path(
        "sneakerheads/user/remove_from_cart/<int:cart_item_id>/",
        remove_from_cart,
        name="remove_from_cart",
    ),
    path("clear_cart/", clear_cart, name="clear_cart"),
    path("update_quantity/", update_quantity, name="update_quantity"),
    path(
        "sneakerheads/user/add-to-cart/<int:product_id>/",
        add_to_cart,
        name="add_to_cart",
    ),
    path("sneakerheads/user/checkout/", checkout_page, name="checkout_page"),
    path("sneakerheads/user/apply-coupon", apply_coupon, name="apply_coupon"),
    path(
        "sneakerheads/user/order/order-details-page/<str:order_id>/",
        order_detail,
        name="order_detail",
    ),
    path(
        "sneakerheads/user/order/order-items-page/<str:order_id>/",
        order_items_page,
        name="order_items_page",
    ),
    path(
        "sneakerheads/user/order/razorpay_payment/<int:user_id>/",
        razorpay_payment,
        name="razorpay_payment",
    ),
    path("sneakerheads/user/order/place-order/", place_order, name="place_order"),
    path(
        "sneakerheads/user/order/cancel_order/<str:order_items_id>/",
        cancel_order,
        name="cancel_order",
    ),
    path(
        "sneakerheads/user/order/sent_return_request/<str:order_items_id>/",
        sent_return_request,
        name="sent_return_request",
    ),
    path(
        "sneakerheads/user/order/placed_order_details/<str:order_id>/",
        order_placed_view,
        name="order_placed_view",
    ),
    path(
        "sneakerheads/user/order/invoice/<str:order_id>/",
        generate_invoice,
        name="generate_invoice",
    ),
    path("sneakerheads/error/", error_page, name="error_page"),
    path("sneakerheads/user/wishlist/", wishlist_view, name="wishlist_view"),
    path(
        "sneakerheads/user/add-to-wishlist/<int:product_color_id>/",
        add_to_wishlist,
        name="add_to_wishlist",
    ),
    path(
        "sneakerheads/user/remove-from-wishlist/<int:product_color_id>/",
        remove_from_wishlist,
        name="remove_from_wishlist",
    ),
    path(
        "sneakerheads/user/remove-in-wishlist/<int:product_color_id>",
        remove_in_wishlist,
        name="remove_in_wishlist",
    ),
    path(
        "sneakerheads/user/wallet/<int:user_id>/",
        wallet_page_view,
        name="wallet_page_view",
    ),
    path(
        "sneakerheads/user/referrals/", referrals_page_view, name="referrals_page_view"
    ),
    path(
        "sneakerheads/user/repayment/<str:order_id>/",
        razorpay_repayment_payment,
        name="razorpay_repayment_payment",
    ),
    
    path('sneakerheads/user/payment_failed/<str:order_id>/', payment_failed, name='payment_failed'),
    
    path('sneakerheads/user/review-product/<int:product_color_id>/',
         review_product_page, name='review_product_page'),
    
    path('sneakerheads/user/rate-and-review/<int:product_color_id>/',
         rate_and_review, name='rate_and_review'),
    
    
    path('sneakerheads/user/mens/', mens_page, name='mens_page'),
    path('sneakerheads/user/women/', women_page, name='women_page'),
    path('sneakerheads/user/kids/', kids_page, name='kids_page'),
    path('sneakerheads/user/shoe-collections/', sneakers_and_athletic_page, name='sneakers_and_athletic_page'),
    
    path('sneakerheads/user/cart/remove-out-of-stock-items/<int:user_id>/',
         remove_out_of_stock_items, name='remove_out_of_stock_items'),
    
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
