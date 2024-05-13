import string
import random
from django.db import models
from django.db.models import Max
from django.utils import timezone
from django.contrib.auth.models import User
from user_app.models import Customer, Address
from django.core.exceptions import ObjectDoesNotExist


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
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="products")
    is_deleted = models.BooleanField(default=False)
    is_listed = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ProductColorImage(models.Model):
    products = models.ForeignKey(
        Products, on_delete=models.CASCADE, related_name="product_color_image"
    )
    color = models.CharField(max_length=50)
    price = models.PositiveBigIntegerField()
    main_image = models.FileField(upload_to=" product_all_images/")
    side_image = models.FileField(upload_to=" product_all_images/")
    top_image = models.FileField(upload_to=" product_all_images/")
    back_image = models.FileField(upload_to=" product_all_images/")
    is_deleted = models.BooleanField(default=False)
    is_listed = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.products.name} - {self.color}"


class ProductSize(models.Model):
    product_color_image = models.ForeignKey(
        ProductColorImage, on_delete=models.CASCADE, related_name="product_sizes"
    )
    size = models.CharField(max_length=50)
    quantity = models.PositiveBigIntegerField()
    is_listed = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    in_stock = models.BooleanField(default=True)

    def __str__(self):
        product_name = self.product_color_image.products.name
        color = self.product_color_image.color
        return f"{product_name} ({color}): Size {self.size}"

    def save(self, *args, **kwargs):
        if int(self.quantity) <= 0:
            self.in_stock = False
        else:
            self.in_stock = True
        super(ProductSize, self).save(*args, **kwargs)


class ProductOffer(models.Model):
    product_color_image = models.ForeignKey(
        ProductColorImage, on_delete=models.CASCADE, related_name="productoffer"
    )
    discount_percentage = models.PositiveBigIntegerField()
    offer_price = models.PositiveBigIntegerField(blank=True, null=True)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()

    def save(self, *args, **kwargs):
        if self.product_color_image and self.discount_percentage:
            discount_price = int(
                round((self.product_color_image.price * self.discount_percentage) / 100)
            )
            self.offer_price = self.product_color_image.price - discount_price
        super(ProductOffer, self).save(*args, **kwargs)

    def __str__(self):
        product = self.product_color_image.products.name
        color = self.product_color_image.color
        discount = self.discount_percentage
        offer_price = self.offer_price
        return f"{product} - {color}: {discount}% Offer | {offer_price}"


class CategoryOffer(models.Model):
    category = models.OneToOneField(
        Category, on_delete=models.CASCADE, related_name="categoryoffer"
    )
    discount_percentage = models.PositiveBigIntegerField()
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()

    def __str__(self):
        name = self.category.name
        discount = self.discount_percentage
        start = self.start_date
        end = self.end_date
        return f"{name} - {discount}% discount | from {start} to {end}"


class Coupon(models.Model):
    coupon_code = models.CharField(primary_key=True, unique=True, max_length=12)
    name = models.CharField(max_length=100)
    discount_percentage = models.PositiveBigIntegerField()
    minimum_amount = models.PositiveBigIntegerField(blank=True, default=0)
    maximum_amount = models.PositiveBigIntegerField(blank=True)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()

    def __str__(self):
        code = self.coupon_code
        name = self.name
        discount = self.discount_percentage
        return f"{code} - {name} : {discount}% off"

    def save(self, *args, **kwargs):
        if not self.coupon_code:
            first_part = "COUPNCD"
            while True:
                random_numbers = "".join(random.choices(string.digits, k=5))
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
    order_status = models.CharField(
        max_length=100, blank=True, null=True, default="Order Placed"
    )
    total_charge = models.PositiveBigIntegerField(default=0)
    razorpay_id = models.CharField(max_length=100, blank=True, null=True)
    paid = models.BooleanField(default=False)
    placed_at = models.DateTimeField(default=timezone.now)
    coupon_applied = models.BooleanField(default=False)
    coupon_name = models.CharField(blank=True, null=True)
    coupon_discount_percent = models.PositiveBigIntegerField(blank=True, null=True)
    discount_price = models.PositiveBigIntegerField(blank=True, null=True, default=0)
    coupon_minimum_amount = models.PositiveBigIntegerField(blank=True, null=True)
    coupon_maximum_amount = models.PositiveBigIntegerField(blank=True, null=True)
    delivery_date = models.DateField(blank=True, null=True)

    def __str__(self):
        paid_status = "- Paid" if self.paid else ""
        name = self.customer.user.first_name
        id = self.order_id
        payment = f"{self.payment} {paid_status}"
        total = self.total_charge
        return f": {name} {id} -  {payment} | {total}"

    def save(self, *args, **kwargs):
        if not self.order_id:
            first_part = "OD"
            while True:
                random_letters = "".join(random.choices(string.ascii_uppercase, k=4))
                random_numbers = "".join(random.choices(string.digits, k=6))
                order_id = f"{first_part}{random_letters}{random_numbers}"
                if not Orders.objects.filter(order_id=order_id).exists():
                    break
            self.order_id = order_id
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order_items_id = models.CharField(primary_key=True, max_length=12, unique=True)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name="order")
    product = models.ForeignKey(
        ProductSize, on_delete=models.PROTECT, related_name="orderitems"
    )
    quantity = models.PositiveBigIntegerField(default=1)
    order_status = models.CharField(max_length=100)
    each_price = models.PositiveBigIntegerField(default=0)
    request_cancel = models.BooleanField(default=False)
    cancel_product = models.BooleanField(default=False)
    return_product = models.BooleanField(default=False)
    request_return = models.BooleanField(default=False)
    delivery_date = models.DateField(null=True, blank=True)

    def __str__(self):
        name = f"{self.order.customer.user.first_name} {
            self.order.customer.user.last_name}"
        product = self.product.product_color_image.products.name
        id = self.order.order_id
        item_id = self.order_items_id
        price = self.each_price
        return f"{name}: {id} - {item_id} - {product} | {price}"

    def save(self, *args, **kwargs):
        if not self.order_items_id:
            first_part = "ODIN"
            while True:
                random_letters = "".join(random.choices(string.ascii_uppercase, k=4))
                random_numbers = "".join(random.choices(string.digits, k=4))
                order_items_id = f"{first_part}{
                    random_letters}{random_numbers}"
                if not OrderItem.objects.filter(order_items_id=order_items_id).exists():
                    break
            self.order_items_id = order_items_id

        if self.order_items_id:
            if self.order_status == "Delivered":
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
        name = f"{self.user.first_name} {self.user.last_name} "
        email = self.user.email
        balance = self.balance
        return f"{name} {email} | Balance : {balance}"


class WalletTransaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    order = models.ForeignKey(
        Orders, on_delete=models.CASCADE, blank=True,
        null=True, related_name="wallet_transaction"
    )
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE, blank=True,
        null=True, related_name='wallet_transaction'
    )
    transaction_id = models.CharField(primary_key=True, max_length=12, unique=True)
    money_deposit = models.PositiveBigIntegerField(blank=True, default=0)
    money_withdrawn = models.PositiveBigIntegerField(blank=True, default=0)
    time_of_transaction = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.money_deposit:
            money = "+{}".format(self.money_deposit)
        elif self.money_withdrawn:
            money = "-{}".format(self.money_withdrawn)
        id = self.transaction_id
        order = self.order
        order_items = self.order_item
        name = f"{self.wallet.user.first_name} {self.wallet.user.last_name}"
        time = self.time_of_transaction
        return f"{id} | {order} | {order_items} - {name} | {money}"

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            first_part = "TRNSCT"
            while True:
                random_numbers = "".join(random.choices(string.digits, k=6))
                transaction_id = f"{first_part}{random_numbers}"
                if not WalletTransaction.objects.filter(
                    transaction_id=transaction_id
                ).exists():
                    break
            self.transaction_id = transaction_id
        super().save(*args, **kwargs)


class Review(models.Model):
    product_color = models.ForeignKey(ProductColorImage, on_delete=models.CASCADE, default='')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    rating = models.PositiveBigIntegerField(default=1)
    review_text = models.TextField(default='')
    review_date = models.DateField(auto_now_add=True)
    title = models.CharField(default='')

    def __str__(self):
        return f"{self.product_color.products.name} {self.product_color.color} - {self.rating}"


class Wishlist(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)

    def __str__(self):
        id = self.id
        first_name = self.customer.user.first_name
        last_name = self.customer.user.last_name
        return f"{id} : {first_name} {last_name}"


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
        first_name = self.customer.user.first_name
        last_name = self.customer.user.last_name
        return f"{first_name} {last_name}"


class CartProducts(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductSize, on_delete=models.CASCADE)
    quantity = models.PositiveBigIntegerField(default=1)
    in_stock = models.BooleanField(default=True)

    def __str__(self):
        first_name = self.cart.customer.user.first_name
        last_name = self.cart.customer.user.last_name
        color = self.product.product_color_image.color
        product = self.product.product_color_image.products.name
        return f"{first_name} {last_name} :  {color} - {product}"

    @property
    def total_price(self):
        today = timezone.now().date()
        try:
            p_offer = self.product.product_color_image.productoffer
            product_offer = p_offer.filter(end_date__gte=today).aggregate(
                Max("offer_price")
            )["offer_price__max"]
            color = self.product.product_color_image
            product_offer = ProductOffer.objects.filter(
                product_color_image=color, end_date__gte=today
            ).first()
            category = self.product.product_color_image.products.category
            category_offer = CategoryOffer.objects.filter(
                category=category, end_date__gte=today
            ).first()

            if product_offer and category_offer:
                highest_discount = max(
                    product_offer.discount_percentage,
                    category_offer.discount_percentage,
                )
            elif product_offer:
                highest_discount = product_offer.discount_percentage
            elif category_offer:
                highest_discount = category_offer.discount_percentage
            else:
                highest_discount = 0

            if highest_discount > 0:
                discount_amount = round(
                    (highest_discount * self.product.product_color_image.price) / 100
                )
                price = self.product.product_color_image.price
                highest_offer_price = price - discount_amount
            else:
                highest_offer_price = self.product.product_color_image.price

            return self.quantity * highest_offer_price
        except ObjectDoesNotExist:
            return self.quantity * self.product.product_color_image.price





class Banner(models.Model):
    banner_name = models.CharField(max_length=200)
    banner_image = models.ImageField(upload_to="banner_images/", default='')
    product_color_image = models.ForeignKey(ProductColorImage, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200)
    price_text = models.CharField(max_length=200)
    is_listed = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.banner_name} - {self.title}"