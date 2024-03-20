from django.contrib import admin
from admin_app.models import *


admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductVariant)