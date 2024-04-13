from django.contrib import admin
from admin_app.models import *


admin.site.register(Category)
admin.site.register(Products)
admin.site.register(Cart)
admin.site.register(CartProducts)
admin.site.register(Orders)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(Review)
admin.site.register(Wishlist)
admin.site.register(WishlistItem)
admin.site.register(ProductColorImage)
admin.site.register(ProductSize)
admin.site.register(ProductOffer)
admin.site.register(Brand)