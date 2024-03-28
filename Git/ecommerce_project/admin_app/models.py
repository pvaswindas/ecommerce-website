from django.db import models
from django.dispatch import receiver
from user_app.models import *



class Category(models.Model):
    name = models.CharField(max_length = 50)
    description = models.TextField()
    is_deleted = models.BooleanField(default = False)
    is_listed = models.BooleanField(default = True)
    
    def __str__(self):
        return self.name
    
    
    
class Brand(models.Model):
     name = models.CharField(max_length = 50)
     country_of_origin = models.CharField(max_length = 100)
     manufacturer_details = models.TextField()
     is_deleted = models.BooleanField(default = False)
     is_listed = models.BooleanField(default = True)
     
     
     def __str__(self):
        return self.name
        
    
    
    
class Products(models.Model):
    name = models.CharField(max_length = 100)
    description = models.TextField()
    information = models.TextField()
    type = models.CharField(max_length = 50)
    category = models.ForeignKey(Category, on_delete = models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete = models.CASCADE)
    is_deleted = models.BooleanField(default = False)
    is_listed = models.BooleanField(default = True)
    
    
    def __str__(self):
        return self.name
    
    
    
    
class ProductColorImage(models.Model):
    products = models.ForeignKey(Products, on_delete = models.CASCADE)
    color = models.CharField(max_length = 50)
    price = models.PositiveBigIntegerField()
    main_image =  models.FileField(upload_to= ' product_all_images/')
    side_image = models.FileField(upload_to= ' product_all_images/')
    top_image = models.FileField(upload_to= ' product_all_images/')
    back_image = models.FileField(upload_to= ' product_all_images/')
    is_deleted = models.BooleanField(default = False)
    is_listed = models.BooleanField(default = True)
    
    def __str__(self):
        return self.color
    
    

    
class ProductSize(models.Model):
    product_color_image = models.ForeignKey(ProductColorImage, on_delete = models.CASCADE)
    size = models.CharField(max_length = 50)
    quantity = models.BigIntegerField()
    is_listed = models.BooleanField(default = True)
    is_deleted = models.BooleanField(default = False)
    
    def __str__(self):
        return self.size

 
    
class Coupon(models.Model):
    name = models.CharField(max_length = 200)
    value = models.BigIntegerField()
    starting_date = models.DateField()
    expiry_date = models.DateField()
    is_listed = models.BooleanField(default = True)
    
    def __str__(self):
        return self.name
  


class Payment(models.Model):
    method_name = models.CharField(max_length = 100)
    
    def __str__(self):
        return self.method_name


    
class Order(models.Model):
    products = models.OneToOneField(Products, on_delete = models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete = models.CASCADE)
    order_status = models.CharField(max_length = 100)
    address = models.OneToOneField(Address, on_delete = models.CASCADE)
    coupon = models.OneToOneField(Coupon, on_delete = models.CASCADE)
    payment = models.OneToOneField(Payment, on_delete = models.CASCADE)
    
    
    def __str__(self):
        return self.order_status
    



class Banner(models.Model):
    name = models.CharField(max_length = 200)
    image_video = models.FileField(upload_to= 'banner_images/')
    target_id = models.IntegerField()
    target_name = models.CharField()
    start_date = models.DateField()
    expiry_date = models.DateField()
    is_listed = models.BooleanField()
    
    def __str__(self):
        return self.name
    
    
    



class Review(models.Model):
    products = models.ForeignKey(Products, on_delete = models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete = models.CASCADE)
    rating = models.BigIntegerField()
    review_text = models.TextField()
    review_date = models.DateField()
    verified_purchase = models.BooleanField(default = False)
    
    
    def __str__(self):
        return self.rating
    
    
    
class Wishlist(models.Model):
    customer = models.OneToOneField(Customer, on_delete = models.CASCADE)
    products = models.ForeignKey(Products, on_delete = models.CASCADE)
    in_stock = models.BooleanField(default = True)
    
    def __str__(self):
        return f"{self.customer}, {self.product}, {self.in_stock}"
    
    
    
class Cart(models.Model):
    customer = models.OneToOneField(Customer, on_delete = models.CASCADE)
    
    def __str__(self):
        return f"{self.customer.user.first_name} {self.customer.user.last_name}"
    
    
    
@receiver(post_save, sender=Customer)
def create_cart(sender, instance, created, **kwargs):
    if created:
        Cart.objects.create(customer=instance)

    

class CartProducts(models.Model):
    cart = models.ForeignKey(Cart, on_delete = models.CASCADE)
    product = models.ForeignKey(ProductSize, on_delete = models.CASCADE)
    quantity = models.PositiveBigIntegerField(default = 1)
    
    def __str__(self):
        return f"{self.cart.customer.user.first_name} {self.cart.customer.user.last_name},  {self.product.product_color_image.color} {self.product.product_color_image.products.name}"