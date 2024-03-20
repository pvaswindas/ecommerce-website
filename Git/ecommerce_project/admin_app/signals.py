from django.db.models.signals import post_save
from django.dispatch import receiver
from admin_app.models import *





@receiver(post_save, sender=Category)
def update_products_on_category_change(sender, instance, **kwargs):
    Product.objects.filter(category=instance).update(is_listed=instance.is_listed)
    Product.objects.filter(category=instance).update(is_deleted=instance.is_deleted)

@receiver(post_save, sender=Brand)
def update_products_on_brand_change(sender, instance, **kwargs):
    Product.objects.filter(brand=instance).update(is_listed=instance.is_listed)
    Product.objects.filter(brand=instance).update(is_deleted=instance.is_deleted)
    
@receiver(post_save, sender=Category)
def update_product_variants_on_category_change(sender, instance, **kwargs):
    ProductVariant.objects.filter(product__category=instance).update(is_listed=instance.is_listed)
    ProductVariant.objects.filter(product__category=instance).update(is_deleted=instance.is_deleted)
    

@receiver(post_save, sender=Brand)
def update_product_variants_on_brand_change(sender, instance, **kwargs):
    ProductVariant.objects.filter(product__brand=instance).update(is_listed=instance.is_listed)
    ProductVariant.objects.filter(product__brand=instance).update(is_deleted=instance.is_deleted)
    
    
