from django.db.models.signals import post_save
from django.dispatch import receiver
from admin_app.models import *





@receiver(post_save, sender=Category)
def update_products_on_category_change(sender, instance, **kwargs):
    Products.objects.filter(category=instance).update(is_listed=instance.is_listed, is_deleted=instance.is_deleted)



@receiver(post_save, sender=Brand)
def update_products_on_brand_change(sender, instance, **kwargs):
    Products.objects.filter(brand=instance).update(is_listed=instance.is_listed, is_deleted = instance.is_deleted)
      


@receiver(post_save, sender = Products)
def update_product_color_change(sender, instance, **kwargs):
    ProductColorImage.objects.filter(products = instance).update(is_listed = instance.is_listed, is_deleted = instance.is_deleted)
    
    
@receiver(post_save, sender = ProductColorImage)
def update_product_size_change(sender, instance, **kwargs):
    ProductSize.objects.filter(product_color_image = instance).update(is_listed = instance.is_listed, is_deleted = instance.is_deleted)