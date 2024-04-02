from django.db import models
from django.dispatch import receiver
from user_app.models import *
import string
import random



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
    in_stock = models.BooleanField(default = True)
    
    def __str__(self):
        return f"{self.color} - {self.products.name}"
    
    

    
class ProductSize(models.Model):
    product_color_image = models.ForeignKey(ProductColorImage, on_delete=models.CASCADE)
    size = models.CharField(max_length=50)
    quantity = models.PositiveBigIntegerField()
    is_listed = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    in_stock = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Size : {self.size} - {self.product_color_image.products.name}, {self.product_color_image.color}"

    def save(self, *args, **kwargs):
        if int(self.quantity) <= 0:
            self.in_stock = False
        else:
            self.in_stock = True
        super(ProductSize, self).save(*args, **kwargs)

 
 
    
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




    
class Orders(models.Model):
    order_id = models.CharField(primary_key=True, max_length=12, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    order_status = models.CharField(max_length=100)
    address = models.ForeignKey(Address, on_delete=models.PROTECT)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT)
    number_of_orders = models.PositiveBigIntegerField(default=1)
    subtotal = models.PositiveBigIntegerField(default=0)
    shipping_charge = models.PositiveBigIntegerField(default=0)
    total_charge = models.PositiveBigIntegerField(default=0)
    
    def __str__(self):
        return f"{self.customer.user.first_name} {self.customer.user.last_name} : {self.order_id} - {self.order_status}"
    
    def save(self, *args, **kwargs):
        if not self.order_id:
            first_part = 'OD'
            random_letters = ''.join(random.choices(string.ascii_uppercase, k=4))
            random_numbers = ''.join(random.choices(string.digits, k=6))
            self.order_id = f"{first_part}{random_letters}{random_numbers}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order_items_id = models.CharField(primary_key=True, max_length=12, unique=True)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductSize, on_delete=models.PROTECT)
    quantity = models.PositiveBigIntegerField(default=1)
    order_status = models.CharField(max_length=100)  
    each_price = models.PositiveBigIntegerField(default=0)
    
    def __str__(self):
        customer_name = f"{self.order.customer.user.first_name} {self.order.customer.user.last_name}"
        product_name = self.product.product_color_image.products.name
        return f"{customer_name}: {self.order.order_id} - {self.order_items_id} - {product_name}"
    
    def save(self, *args, **kwargs):
        if not self.order_items_id:
            first_part = 'ODIN'
            random_letters = ''.join(random.choices(string.ascii_uppercase, k=4))
            random_numbers = ''.join(random.choices(string.digits, k=4))
            self.order_items_id = f"{first_part}{random_letters}{random_numbers}"
        super().save(*args, **kwargs)

        
        
        

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
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductSize, on_delete=models.CASCADE)
    quantity = models.PositiveBigIntegerField(default=1)
    in_stock = models.BooleanField(default = True)
    
    def __str__(self):
        return f"{self.cart.customer.user.first_name} {self.cart.customer.user.last_name} :  {self.product.product_color_image.color} - {self.product.product_color_image.products.name}"
    
    @property
    def total_price(self):
        return self.quantity * self.product.product_color_image.price
