from django.db.models.signals import post_save, post_delete, pre_delete, pre_save
from django.dispatch import receiver
from admin_app.models import *
from django.utils import timezone






@receiver(post_save, sender=Customer)
def create_cart(sender, instance, created, **kwargs):
    if created:
        Cart.objects.create(customer=instance)




@receiver(post_save, sender=Customer)
def create_wishlist(sender, instance, created, **kwargs):
    if created:
        Wishlist.objects.create(customer=instance)
        
        


@receiver(post_save, sender=User)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)
    



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



@receiver(post_save, sender=CartProducts)
@receiver(post_delete, sender=CartProducts)
def update_cart_coupon_status(sender, instance, **kwargs):
    cart = instance.cart
    cart.coupon_applied = False
    cart.coupon = None
    try:
        cart.save()
    except Exception as e:
        print("Error saving cart:", e)


@receiver(post_save, sender=ProductOffer)
def delete_expired_product_offers(sender, instance, **kwargs):
    if instance.end_date < timezone.now().date():
        instance.delete()
        
        
@receiver(post_save, sender=Coupon)
def delete_expired_coupon(sender, instance, **kwargs):
    if instance.end_date < timezone.now().date():
        instance.delete()