from django.db.models.signals import post_save
from django.dispatch import receiver
from admin_app.models import *





@receiver(post_save, sender=Category)
def update_products_on_category_change(sender, instance, **kwargs):
    products = Products.objects.filter(category=instance)
    products.update(is_listed=instance.is_listed, is_deleted=instance.is_deleted)
    for product in products:
        product_color_images = ProductColorImage.objects.filter(products=product)
        product_color_images.update(is_listed=instance.is_listed, is_deleted=instance.is_deleted)
        for product_color_image in product_color_images:
            product_sizes = ProductSize.objects.filter(product_color_image=product_color_image)
            product_sizes.update(is_listed=instance.is_listed, is_deleted=instance.is_deleted)


@receiver(post_save, sender=Brand)
def update_products_on_brand_change(sender, instance, **kwargs):
    products = Products.objects.filter(brand=instance)
    products.update(is_listed=instance.is_listed, is_deleted=instance.is_deleted)
    for product in products:
        product_color_images = ProductColorImage.objects.filter(products=product)
        product_color_images.update(is_listed=instance.is_listed, is_deleted=instance.is_deleted)
        for product_color_image in product_color_images:
            product_sizes = ProductSize.objects.filter(product_color_image=product_color_image)
            product_sizes.update(is_listed=instance.is_listed, is_deleted=instance.is_deleted)


@receiver(post_save, sender=ProductColorImage)
def update_product_size_on_color_image_change(sender, instance, **kwargs):
    product_sizes = ProductSize.objects.filter(product_color_image=instance)
    product_sizes.update(is_listed=instance.is_listed, is_deleted=instance.is_deleted)



@receiver(post_save, sender=ProductSize)
def update_cart_in_stock_on_product_size_quantity_change(sender, instance, **kwargs):
    cart_products = CartProducts.objects.filter(product = instance)
    cart_products.update(in_stock= instance.in_stock)
    
    

@receiver(post_save, sender=ProductSize)
def update_product_color_in_stock_on_product_size_quantity_change(sender, instance, **kwargs):
    product_color_image = instance.product_color_image
    total_sizes = ProductSize.objects.filter(product_color_image=product_color_image).count()
    out_of_stock_sizes = ProductSize.objects.filter(product_color_image=product_color_image, in_stock=False).count()
    if out_of_stock_sizes == total_sizes:
        ProductColorImage.objects.filter(pk=product_color_image.pk).update(in_stock=False)
    else:
        ProductColorImage.objects.filter(pk=product_color_image.pk).update(in_stock=True)
