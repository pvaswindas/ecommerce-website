from django.db.models.signals import post_save, post_delete
import string
import random
from datetime import date
from django.db import models
from user_app.models import *
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
import logging
logger = logging.getLogger(__name__)


class Category(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    is_deleted = models.BooleanField(default=False)
    is_listed = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=50)
    country_of_origin = models.CharField(max_length=100)
    manufacturer_details = models.TextField()
    is_deleted = models.BooleanField(default=False)
    is_listed = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Products(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    information = models.TextField()
    type = models.CharField(max_length=50)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)
    is_listed = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ProductColorImage(models.Model):
    products = models.ForeignKey(Products, on_delete=models.CASCADE)
    color = models.CharField(max_length=50)
    price = models.PositiveBigIntegerField()
    main_image = models.FileField(upload_to=' product_all_images/')
    side_image = models.FileField(upload_to=' product_all_images/')
    top_image = models.FileField(upload_to=' product_all_images/')
    back_image = models.FileField(upload_to=' product_all_images/')
    is_deleted = models.BooleanField(default=False)
    is_listed = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.color} - {self.products.name}"


class ProductSize(models.Model):
    product_color_image = models.ForeignKey(
        ProductColorImage, on_delete=models.CASCADE)
    size = models.CharField(max_length=50)
    quantity = models.PositiveBigIntegerField()
    is_listed = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    in_stock = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product_color_image.products.name} ({self.product_color_image.color}) : Size {self.size}"

    def save(self, *args, **kwargs):
        if int(self.quantity) <= 0:
            self.in_stock = False
        else:
            self.in_stock = True
        super(ProductSize, self).save(*args, **kwargs)


class ProductOffer(models.Model):
    product_color_image = models.ForeignKey(
        ProductColorImage, on_delete=models.CASCADE, related_name='productoffer')
    discount_percentage = models.PositiveBigIntegerField()
    offer_price = models.PositiveBigIntegerField(blank=True, null=True)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()

    def save(self, *args, **kwargs):
        if self.product_color_image and self.discount_percentage:
            discount_price = int(
                round((self.product_color_image.price * self.discount_percentage) / 100))
            self.offer_price = (
                self.product_color_image.price - discount_price)
        super(ProductOffer, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_color_image.products.name} - {self.product_color_image.color} : {self.discount_percentage} % Offer | Offer Price : {self.offer_price}"


class CategoryOffer(models.Model):
    category = models.OneToOneField(Category, on_delete=models.CASCADE, related_name='categoryoffer')
    discount_percentage = models.PositiveBigIntegerField()
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()

    def __str__(self):
        return f"{self.category.name} - {self.discount_percentage}% discount | from {self.start_date} to {self.end_date}"


class Coupon(models.Model):
    coupon_code = models.CharField(
        primary_key=True, unique=True, max_length=12)
    name = models.CharField(max_length=100)
    discount_percentage = models.PositiveBigIntegerField()
    minimum_amount = models.PositiveBigIntegerField(blank=True, default=0)
    maximum_amount = models.PositiveBigIntegerField(blank=True)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()

    def __str__(self):
        return f"{self.coupon_code} - {self.name} : {self.discount_percentage}% off | Start Date : {self.start_date} End Date : {self.end_date}"

    def save(self, *args, **kwargs):
        if not self.coupon_code:
            first_part = "COUPNCD"
            while True:
                random_numbers = ''.join(random.choices(string.digits, k=5))
                coupon_code = f"{first_part}{random_numbers}"
                if not Coupon.objects.filter(coupon_code=coupon_code).exists():
                    break
            self.coupon_code = coupon_code
        super().save(*args, **kwargs)


class Payment(models.Model):
    method_name = models.CharField(max_length=100)
    paid_at = models.DateTimeField(null=True)
    pending = models.BooleanField(default=True)
    failed = models.BooleanField(default=False)
    success = models.BooleanField(default=False)

    def __str__(self):

        if self.success:
            status = "Success"
        elif self.failed:
            status = "Failed"
        else:
            status = "Pending"

        return f"{self.method_name} : {status}"


class Orders(models.Model):
    order_id = models.CharField(primary_key=True, max_length=12, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    address = models.ForeignKey(Address, on_delete=models.PROTECT)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT)
    number_of_orders = models.PositiveBigIntegerField(default=1)
    subtotal = models.PositiveBigIntegerField(default=0)
    shipping_charge = models.PositiveBigIntegerField(default=0)
    total_charge = models.PositiveBigIntegerField(default=0)
    razorpay_id = models.CharField(max_length=100, blank=True, null=True)
    paid = models.BooleanField(default=False)
    placed_at = models.DateTimeField(default=timezone.now)
    coupon_applied = models.BooleanField(default=False)
    coupon_name = models.CharField(blank=True, null=True)
    coupon_discount_percent = models.PositiveBigIntegerField(
        blank=True, null=True)
    discount_price = models.PositiveBigIntegerField(blank=True, default=0)
    coupon_minimum_amount = models.PositiveBigIntegerField(
        blank=True, null=True)
    coupon_maximum_amount = models.PositiveBigIntegerField(
        blank=True, null=True)

    def __str__(self):
        paid_status = "- Paid" if self.paid else ""
        return f"{self.customer.user.first_name} {self.customer.user.last_name} : {self.order_id} - {self.payment} {paid_status}"

    def save(self, *args, **kwargs):
        if not self.order_id:
            first_part = 'OD'
            while True:
                random_letters = ''.join(
                    random.choices(string.ascii_uppercase, k=4))
                random_numbers = ''.join(random.choices(string.digits, k=6))
                order_id = f"{first_part}{random_letters}{random_numbers}"
                if not Orders.objects.filter(order_id=order_id).exists():
                    break
            self.order_id = order_id
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order_items_id = models.CharField(
        primary_key=True, max_length=12, unique=True)
    order = models.ForeignKey(
        Orders, on_delete=models.CASCADE, related_name='order')
    product = models.ForeignKey(ProductSize, on_delete=models.PROTECT)
    quantity = models.PositiveBigIntegerField(default=1)
    order_status = models.CharField(max_length=100)
    each_price = models.PositiveBigIntegerField(default=0)
    cancel_product = models.BooleanField(default=False)
    return_product = models.BooleanField(default=False)
    request_return = models.BooleanField(default=False)
    delivery_date = models.DateField(null=True, blank=True)
    total_price = models.PositiveBigIntegerField(default=0)

    def __str__(self):
        customer_name = f"{self.order.customer.user.first_name} {
            self.order.customer.user.last_name}"
        product_name = self.product.product_color_image.products.name
        return f"{customer_name}: {self.order.order_id} - {self.order_items_id} - {product_name} | {self.total_price}"

    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.each_price * self.quantity
        if not self.order_items_id:
            first_part = 'ODIN'
            while True:
                random_letters = ''.join(
                    random.choices(string.ascii_uppercase, k=4))
                random_numbers = ''.join(random.choices(string.digits, k=4))
                order_items_id = f"{first_part}{
                    random_letters}{random_numbers}"
                if not OrderItem.objects.filter(order_items_id=order_items_id).exists():
                    break
            self.order_items_id = order_items_id

        if self.order_items_id:
            if self.order_status == 'Delivered':
                self.order.payment.success = True
                self.order.payment.pending = False
                self.order.payment.save()

                self.order.paid = True
                self.order.save()
        super().save(*args, **kwargs)


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.PositiveBigIntegerField(blank=True, default=0)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.user.email} | Balance : {self.balance}"


class WalletTransaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE, blank=True, null=True)
    transaction_id = models.CharField(
        primary_key=True, max_length=12, unique=True)
    money_deposit = models.PositiveBigIntegerField(blank=True, default=0)
    money_withdrawn = models.PositiveBigIntegerField(blank=True, default=0)
    time_of_transaction = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.money_deposit:
            money = "+{}".format(self.money_deposit)
        elif self.money_withdrawn:
            money = "-{}".format(self.money_withdrawn)

        return f"{self.transaction_id} | {self.order_item} - {self.wallet.user.first_name} {self.wallet.user.last_name} : {self.time_of_transaction} | {money}"

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            first_part = 'TRNSCT'
            while True:
                random_numbers = ''.join(random.choices(string.digits, k=6))
                transaction_id = f"{first_part}{random_numbers}"
                if not WalletTransaction.objects.filter(transaction_id=transaction_id).exists():
                    break
            self.transaction_id = transaction_id
        super().save(*args, **kwargs)


class Review(models.Model):
    products = models.ForeignKey(Products, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    rating = models.BigIntegerField()
    review_text = models.TextField()
    review_date = models.DateField()
    verified_purchase = models.BooleanField(default=False)

    def __str__(self):
        return self.rating


class Wishlist(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id} : {self.customer.user.first_name} {self.customer.user.last_name}"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductColorImage, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id} : {self.product}"


class Cart(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)
    coupon_applied = models.BooleanField(default=False)
    coupon = models.CharField(blank=True, null=True)

    def __str__(self):
        return f"{self.customer.user.first_name} {self.customer.user.last_name}"


class CartProducts(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductSize, on_delete=models.CASCADE)
    quantity = models.PositiveBigIntegerField(default=1)
    in_stock = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.cart.customer.user.first_name} {self.cart.customer.user.last_name} :  {self.product.product_color_image.color} - {self.product.product_color_image.products.name}"

    @property
    def total_price(self):
        today = timezone.now().date()
        try:
            offer = self.product.product_color_image.productoffer.get(end_date__gte=today)
            return self.quantity * offer.offer_price
        except ObjectDoesNotExist:
            return self.quantity * self.product.product_color_image.price
