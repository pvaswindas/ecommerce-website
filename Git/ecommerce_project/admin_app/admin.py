from django.contrib import admin
from admin_app.models import *


admin.site.register(Category)
admin.site.register(Products)
admin.site.register(Cart)
admin.site.register(CartProducts)
admin.site.register(Orders)
admin.site.register(OrderItem)
admin.site.register(Wallet)
admin.site.register(WalletTransaction)
admin.site.register(Payment)
admin.site.register(Review)
admin.site.register(Wishlist)
admin.site.register(WishlistItem)
admin.site.register(ProductColorImage)
admin.site.register(ProductSize)
admin.site.register(ProductOffer)
admin.site.register(CategoryOffer)
admin.site.register(Coupon)
admin.site.register(Brand)
admin.site.register(Banner)
