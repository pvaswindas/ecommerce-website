import re
import ast
import time
import random
import razorpay  # type: ignore
from datetime import datetime
from django.db.models import Q
from datetime import timedelta
from django.db.models import *
from django.contrib import auth
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from urllib.parse import urlencode
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from user_app.models import Customer, Address
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.utils.text import normalize_newlines
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.cache import never_cache
from django.contrib.auth.hashers import check_password
from admin_app.models import Category, Brand, ProductColorImage, ProductSize
from admin_app.models import ProductOffer, CategoryOffer, Coupon, Payment
from admin_app.models import Orders, OrderItem, Wallet, WalletTransaction
from admin_app.models import Wishlist, WishlistItem, Cart, CartProducts
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.http import HttpResponse
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter  # type: ignore
from reportlab.lib import colors  # type: ignore
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle  # type: ignore
from reportlab.pdfgen import canvas  # type: ignore
import os 

today = datetime.now().date()


alphabets_pattern = re.compile(r"^[a-zA-Z\s]+$")
street_address_pattern = re.compile(r'^[a-zA-Z0-9\s,]+$')


def clear_old_messages(view_func):
    def only_new_messages(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        all_messages = messages.get_messages(request)
        all_messages.used = True
        return response
    return only_new_messages


def clean_string(input_string):
    clean_string = re.sub(r'[^a-zA-Z0-9]', '', input_string)
    return clean_string


@clear_old_messages
def get_cart_wishlist_address_order_data(request):
    data = {}
    if request.user.is_authenticated:
        user = request.user
        customer = Customer.objects.get(user=user)
        cart = Cart.objects.get(customer=customer)
        cart_items = CartProducts.objects.filter(cart=cart)
        wishlist = Wishlist.objects.get(customer=customer)
        wishlist_item_count = WishlistItem.objects.filter(
            wishlist=wishlist).count()
        addresses = Address.objects.filter(customer=customer).order_by('name')
        orders = Orders.objects.filter(customer=customer).order_by('-placed_at')
        order_items = OrderItem.objects.filter(
            order__customer=customer).order_by('-order__placed_at')
        data.update({
            'user': user,
            'customer': customer,
            'cart': cart,
            'cart_items': cart_items,
            'wishlist': wishlist,
            'wishlist_item_count': wishlist_item_count,
            'addresses': addresses,
            'orders': orders,
            'order_items': order_items,
        })
        today = datetime.now().date()
        if cart_items:
            item_count = 0
            subtotal = 0
            for item in cart_items:
                item_count += 1
                try:
                    product_offer = ProductOffer.objects.filter(
                        product_color_image=item.product.product_color_image, end_date__gte=today).first()
                    category_offer = CategoryOffer.objects.filter(
                        category=item.product.product_color_image.products.category, end_date__gte=today).first()

                    if product_offer and category_offer:
                        highest_discount = max(
                            product_offer.discount_percentage, category_offer.discount_percentage)
                    elif product_offer:
                        highest_discount = product_offer.discount_percentage
                    elif category_offer:
                        highest_discount = category_offer.discount_percentage
                    else:
                        highest_discount = 0

                    if highest_discount > 0:
                        discount_amount = round(
                            (highest_discount * item.product.product_color_image.price) / 100)
                        highest_offer_price = item.product.product_color_image.price - discount_amount
                    else:
                        highest_offer_price = item.product.product_color_image.price

                    each_price = highest_offer_price * item.quantity
                except Exception as e:
                    each_price = item.product.product_color_image.price * item.quantity

                subtotal = subtotal + each_price
            shipping_charge = 99 if subtotal <= 2500 else 0
            total_charge = subtotal + shipping_charge
            data.update({
                'item_count': item_count,
                'shipping_charge': shipping_charge,
                'subtotal': subtotal,
                'total_charge': total_charge,
            })
    return data






@never_cache
@clear_old_messages
def sign_in(request):
    if request.user.is_authenticated:
        return redirect('index_page')
    else:
        return render(request, 'signin.html')


@never_cache
@clear_old_messages
def sign_up(request):
    if request.user.is_authenticated:
        return redirect('index_page')
    else:
        return render(request, 'signup.html')
    
    



# ---------------------------------------------------------------------------------- CC_INDEX PAGE FUNCTIONS ----------------------------------------------------------------------------------




@never_cache
@clear_old_messages
def index_page(request):
    if request.user.is_authenticated:
        context = {}
        all_products = ProductColorImage.objects.filter(
            is_listed=True, is_deleted=False)
        newest_five_products = all_products.order_by('-id').distinct()[:5]
        newest_women_products = all_products.filter(
            products__category__name='WOMEN').order_by('-id').distinct()[:5]
        newest_men_products = all_products.filter(
            products__category__name='MEN').order_by('-id').distinct()[:5]
        women_products_count = all_products.filter(
            products__category__name = 'WOMEN').count()
        men_products_count = all_products.filter(
            products__category__name = 'MEN').count()
        kids_products_count = all_products.filter(
            products__category__name = 'KIDS').count()
        
        ordered_items = OrderItem.objects.filter(order_status = 'Delivered')

        best_selling_products = ProductColorImage.objects.filter(
            is_listed=True, is_deleted=False,
            product_sizes__orderitems__in=ordered_items
        ).annotate(
            num_orders=Count('product_sizes__orderitems')
        ).order_by(
            '-num_orders'
        )
        top_selling_products = best_selling_products.distinct()[:10]
        women_top_selling_products = best_selling_products.filter(
            products__category__name='WOMEN').distinct()[:10]
        men_top_selling_products = best_selling_products.filter(
            products__category__name='MEN').distinct()[:10]
        context.update({
            'newest_five_products' : newest_five_products,
            'newest_women_products' : newest_women_products,
            'newest_men_products' : newest_men_products,
            'women_products_count' : women_products_count,
            'men_products_count' : men_products_count,
            'kids_products_count' : kids_products_count,
            'top_selling_products' : top_selling_products,
            'women_top_selling_products' : women_top_selling_products,
            'men_top_selling_products' : men_top_selling_products,
        })
        cart_wishlist_address_order_data = get_cart_wishlist_address_order_data(
            request)
        context.update(cart_wishlist_address_order_data)
        return render(request, 'index.html', context)
    return render(request, 'index.html')



# ---------------------------------------------------------------------------------- CC_OTP GENERATE FUNCTIONS ----------------------------------------------------------------------------------


@never_cache
@clear_old_messages
def verify_otp(request):
    if request.user.is_authenticated:
        return redirect('index_page')
    else:
        messages.success(request, 'OTP has been sent to your email')
        return render(request, 'verify_otp.html')


def generate_otp():
    return int(random.randint(100000, 999999))

# ---------------------------------------------------------------------------------- CC_SEND OTP IN MAIL FUNCTIONS ----------------------------------------------------------------------------------


def send_otp_email(email, otp):
    subject = 'OTP for Email Verification'

    html_message = render_to_string('send_otp_in_sign_up.html', {'otp': otp})

    plain_message = strip_tags(html_message)

    email_message = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email='sneakerheadsweb@gmail.com',
        to=[email]
    )

    email_message.attach_alternative(html_message, "text/html")

    email_message.send()


# ---------------------------------------------------------------------------------- CC_USER_REGISTER PAGE FUNCTIONS ----------------------------------------------------------------------------------


@never_cache
@clear_old_messages
def register_function(request):
    if request.user.is_authenticated:
        return redirect('index_page')

    elif request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        referral_code = request.POST.get('referral_code', None)

        is_every_field_valid = True

        if name and email and password and confirm_password:
            cleaned_name = clean_string(name)
            cleaned_password = clean_string(password)
            cleaned_confirm_password = clean_string(confirm_password)

            email = normalize_newlines(email).strip()

            try:
                validate_email(email)
            except ValidationError:
                is_every_field_valid = False
                messages.error(request, 'Enter a valid email address')

            if not alphabets_pattern.match(name):
                is_every_field_valid = False
                messages.error(request, 'Name should be in alphabetic format.')

            elif not 3 <= len(cleaned_name) <= 100:
                is_every_field_valid = False
                messages.error(
                    request, 'Name should not consist solely of special characters or be blank.')

            elif User.objects.filter(username=email).exists():
                is_every_field_valid = False
                messages.error(request, 'Email already exits, try logging in')

            elif not len(cleaned_password) >= 8:
                is_every_field_valid = False
                messages.error(
                    request, 'Password should not consist solely of special characters or be blank.')

            elif len(password) < 8:
                is_every_field_valid = False
                messages.error(
                    request, 'Password must be at least 8 characters long.')

            elif ' ' in password:
                is_every_field_valid = False
                messages.error(request, 'Password cannot contain spaces.')

            elif password != confirm_password:
                is_every_field_valid = False
                messages.error(request, 'Passwords not match.')

            elif not len(cleaned_confirm_password) >= 8:
                is_every_field_valid = False
                messages.error(
                    request, 'Confirm Password should not consist solely of special characters or be blank.')

            if referral_code:
                request.session['referral_code'] = referral_code

            if is_every_field_valid:
                try:
                    user = User(first_name=name, username=email, email=email)
                    otp = generate_otp()
                    email = user.email
                    if otp:
                        send_otp_email(user, otp)
                        request.session['otp'] = otp
                        request.session['otp_created_at'] = timezone.now().strftime(
                            '%Y-%m-%d %H:%M:%S')
                        request.session['user_data'] = {
                            'name': name,
                            'email': email,
                            'password': password
                        }
                        return redirect('otp_verification_page')
                    else:
                        messages.error(request, 'Error generating OTP')
                        return redirect('sign_up')
                except Exception as e:
                    messages.error(request, f'Error creating user: {str(e)}')
                    return redirect('sign_up_page')
            else:
                return redirect('sign_up_page')
        else:
            messages.error(request, 'Please fill all the fields.')

    return redirect('sign_up_page')


# ---------------------------------------------------------------------------------- CC_OTP VERIFICATION PAGE FUNCTIONS ----------------------------------------------------------------------------------


@never_cache
@clear_old_messages
def otp_verification_page(request):
    if request.user.is_authenticated:
        return redirect('index_page')

    elif request.method == 'POST':
        digit1 = request.POST['digit1']
        digit2 = request.POST['digit2']
        digit3 = request.POST['digit3']
        digit4 = request.POST['digit4']
        digit5 = request.POST['digit5']
        digit6 = request.POST['digit6']

        otp_combined = digit1 + digit2 + digit3 + digit4 + digit5 + digit6

        otp_entered = otp_combined

        otp = request.session.get('otp')

        otp_created_at_str = request.session.get('otp_created_at')

        if otp and otp_created_at_str:

            otp_created_at = datetime.strptime(
                otp_created_at_str, '%Y-%m-%d %H:%M:%S')
            otp_created_at = timezone.make_aware(
                otp_created_at, timezone.get_current_timezone())

            now = timezone.localtime(timezone.now())

            if (now - otp_created_at).total_seconds() <= 120:
                if str(otp_entered) == str(otp):
                    user_data = request.session.get('user_data')
                    referral_code = request.session.get('referral_code')

                    if user_data:
                        user = User.objects.create_user(
                            username=user_data['email'],
                            email=user_data['email'],
                            password=user_data['password'],
                            first_name=user_data['name']
                        )
                        user.save()
                        del request.session['user_data']
                        del request.session['otp']
                        del request.session['otp_created_at']

                        if referral_code:
                            customer = Customer.objects.get(user=user)
                            customer.used_referral_code = referral_code
                            customer.save()

                            referring_customer = Customer.objects.get(
                                referral_code=referral_code)

                            if referring_customer:
                                referring_wallet = Wallet.objects.get(
                                    user=referring_customer.user)
                                referring_wallet.balance += 250
                                referring_wallet.save()
                                WalletTransaction.objects.create(
                                    wallet=referring_wallet,
                                    money_deposit=250,
                                )

                                joining_wallet = Wallet.objects.get(user=user)
                                joining_wallet.balance += 100
                                joining_wallet.save()

                                WalletTransaction.objects.create(
                                    wallet=joining_wallet,
                                    money_deposit=100,
                                )

                            del request.session['referral_code']

                        messages.success(
                            request, 'Registration Successfully, Login Now')
                        return redirect('sign_in_page')
                    else:
                        messages.error(
                            request, 'User data not found in session')
                else:
                    messages.error(request, 'Invalid OTP. Please try again.')
            else:
                messages.error(
                    request, 'OTP has expired. Please request a new one.')
    else:
        return redirect('verify_otp')


@never_cache
@clear_old_messages
def resend_otp(request):
    if request.user.is_authenticated:
        return redirect('index_page')
    elif request.method == 'POST':
        user_data = request.session.get('user_data')
        if user_data:
            user = user_data
            email = user_data['email']

            otp = generate_otp()

            send_otp_email(email, otp)

            request.session['otp'] = otp
            request.session['otp_created_at'] = timezone.now().strftime(
                '%Y-%m-%d %H:%M:%S')

            messages.info(request, 'OTP has been resent.')
            return redirect('otp_verification_page')
        else:
            messages.error(request, 'User data not found in session.')
            return redirect('sign_up')
    else:
        return redirect('resend_otp_page')


# ---------------------------------------------------------------------------------- CC_SIGN IN FUNCTIONS ----------------------------------------------------------------------------------


@never_cache
@clear_old_messages
def sign_in_function(request):
    if request.user.is_authenticated:
        return redirect('index_page')

    elif request.method == 'POST':

        email = request.POST['email']
        password = request.POST['password']

        email = normalize_newlines(email).strip()

        user = authenticate(username=email, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('index_page')
        else:
            messages.error(request, 'Invalid email or password')
            return redirect('sign_in_page')

    else:
        return redirect('sign_in_page')


# ---------------------------------------------------------------------------------- CC_FORGOT PASSWORD FUNCTIONS ----------------------------------------------------------------------------------


@never_cache
@clear_old_messages
def forgot_password_page(request):
    return render(request, 'forgot_password.html')


@never_cache
@clear_old_messages
def reset_password(request, user_id):
    timestamp = request.GET.get('timestamp')
    if not timestamp or int(timestamp) < int(time.time()):
        return HttpResponseBadRequest('The link has expired or is invalid.')

    return render(request, 'reset_password_page.html', {'user_id': user_id})


@never_cache
@clear_old_messages
def reset_password_change(request, user_id):
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        is_valid_password = True
        if len(password) < 8:
            messages.error(
                request, 'Password must be at least 8 characters long.')
            is_valid_password = False
        elif ' ' in password:
            messages.error(request, 'Password cannot contain spaces.')
            is_valid_password = False

        is_valid_confirm_password = True
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            is_valid_confirm_password = False

        if is_valid_password and is_valid_confirm_password:
            try:
                user = User.objects.get(pk=user_id)
                user.set_password(password)
                user.save()
                messages.success(
                    request, 'Password reset successfully. You can now log in with your new password.')
                return redirect('sign_in_page')
            except User.DoesNotExist:
                return HttpResponseBadRequest('Invalid user ID.')
    else:
        return HttpResponseBadRequest('Invalid request method.')


def send_link_email(email, page_url, timestamp):
    subject = 'Link to reset your password'
    message = format_html(
        "Click <a href='{}'>here</a> to reset your password.", page_url)
    from_email = 'sneakerheadsweb@gmail.com'
    to_email = [email]
    send_mail(subject, '', from_email, to_email, html_message=message)


@never_cache
@clear_old_messages
def verify_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        if email:
            email = normalize_newlines(email).strip()
            is_valid_email = True
            try:
                validate_email(email)
            except ValidationError as e:
                is_valid_email = False
                messages.error(request, f'Invalid email: {e}')

            if User.objects.filter(username=email).exists():
                if is_valid_email:
                    user = User.objects.get(username=email)
                    timestamp = int(time.time()) + 120
                    page_url = request.build_absolute_uri(
                        reverse('reset_password', kwargs={
                                'user_id': user.id}) + f'?timestamp={timestamp}'
                    )
                    send_link_email(email, page_url, timestamp)
                    messages.success(
                        request, 'Check email for the link to reset your password')
                    return redirect(forgot_password_page)
            else:
                messages.error(
                    request, 'User does not exist. Please try with a correct email.')
                return redirect(forgot_password_page)
    else:
        return redirect('sign_in_page')


# ---------------------------------------------------------------------------------- CC_USER_LOGOUT PASSWORD FUNCTIONS ----------------------------------------------------------------------------------


@never_cache
@clear_old_messages
def logout(request):
    if request.method == 'POST':
        auth.logout(request)
        messages.info(request, 'Login again!')
        return redirect(sign_in)

    else:
        return redirect('sign_in_page')


# ---------------------------------------------------------------------------------- CC_SHOP PAGE FUNCTIONS ----------------------------------------------------------------------------------





@never_cache
@clear_old_messages
def shop_page_view(request):
    context = {}

    price_ranges = [
        {"min": 500, "max": 1000},
        {"min": 1000, "max": 2000},
        {"min": 2000, "max": 3000},
        {"min": 3000, "max": 5000},
        {"min": 5000, "max": 7000},
        {"min": 7000, "max": 10000},
        {"min": 10000, "max": 15000},
    ]
    if request.user.is_authenticated:
        cart_wishlist_address_order_data = get_cart_wishlist_address_order_data(request)
        context.update(cart_wishlist_address_order_data)
        
    sortby = request.GET.get('sortby', 'default')
    selected_categories = request.GET.getlist('category_wise')
    selected_brands = request.GET.getlist('brand_wise')
    search_query = request.GET.get('search_query')

    product_color_list = ProductColorImage.objects.filter(
        is_deleted=False, is_listed=True)
    
    selected_price_ranges = request.GET.getlist('price_range')

    selected_price_ranges = [int(x) for x in selected_price_ranges]

    price_range_mapping = {
        1: (500, 1000),
        2: (1000, 2000),
        3: (2000, 3000),
        4: (3000, 5000),
        5: (5000, 7000),
        6: (7000, 10000),
        7: (10000, 15000)
    }

    price_filter = []
    if selected_price_ranges:
        for option in selected_price_ranges:
            if option in price_range_mapping:
                min_value, max_value = price_range_mapping[option]
                price_filter.extend([min_value, max_value])

        price_filter = sorted(set(price_filter))

    if price_filter:
        filter_conditions = Q(price__gte=price_filter[0]) & Q(price__lte=price_filter[-1])
        product_color_list = product_color_list.filter(filter_conditions)
        
        
    if selected_categories:
        product_color_list = product_color_list.filter(products__category__name__in=selected_categories)

    if selected_brands:
        product_color_list = product_color_list.filter(products__brand__name__in=selected_brands)
            
    if search_query:
        product_color_list = product_color_list.filter(
            Q(products__name__icontains=search_query) |
            Q(color__icontains=search_query) |
            Q(price__icontains=search_query) |
            Q(products__type__icontains=search_query) |
            Q(products__category__name__icontains=search_query) |
            Q(products__brand__name__icontains=search_query)
        )
    
    
    if sortby == 'a_z':
        product_color_list = product_color_list.order_by('products__name')
    elif sortby == 'new_arrival':
        product_color_list = product_color_list.order_by('-created_at')
    elif sortby == 'low_to_high':
        product_color_list = product_color_list.order_by('price')
    elif sortby == 'high_to_low':
        product_color_list = product_color_list.order_by('-price')

    paginator = Paginator(product_color_list, 12)

    page_number = request.GET.get('page')
    try:
        product_color_list = paginator.page(page_number)
    except PageNotAnInteger:
        product_color_list = paginator.page(1)
    except EmptyPage:
        product_color_list = paginator.page(paginator.num_pages)

    latest_products = ProductColorImage.objects.filter(
        is_deleted=False, is_listed=True).order_by('-created_at')[:5]
    
    brand_list = Brand.objects.filter(is_deleted=False, is_listed=True)

    category_list = Category.objects.filter(is_deleted=False, is_listed=True).annotate(product_count=Count('products__product_color_image'))
    brand_list = brand_list.annotate(
        product_count=Count('products__product_color_image')
    )
    
    
    context.update({
        'product_color_list': product_color_list,
        'brand_list': brand_list,
        'category_list': category_list,
        'price_ranges': price_ranges,
        'latest_products': latest_products,
        'selected_categories' : selected_categories,
        'selected_brands' : selected_brands,
        'sortby' : sortby,
        'search_query': search_query,
        'selected_price_ranges' : selected_price_ranges,
    })

    return render(request, 'shop_page.html', context)




# -------------------------------------------------------------------------------- CC_PRODUCT SINGLE PAGE FUNCTIONS --------------------------------------------------------------------------------


@never_cache
@clear_old_messages
def product_single_view_page(request, product_name, pdt_id):
    context = {}
    product_color = ProductColorImage.objects.get(pk=pdt_id)
    today = datetime.now().date()

    try:
        try:
            product_offer = ProductOffer.objects.get(
                product_color_image=product_color, end_date__gte=today)
        except ProductOffer.DoesNotExist:
            product_offer = None

        try:
            category_offer = CategoryOffer.objects.get(
                category=product_color.products.category, end_date__gte=today)
        except CategoryOffer.DoesNotExist:
            category_offer = None

        if product_offer and category_offer:
            highest_discount = max(
                product_offer.discount_percentage, category_offer.discount_percentage)
        elif product_offer:
            highest_discount = product_offer.discount_percentage
        elif category_offer:
            highest_discount = category_offer.discount_percentage

        if category_offer or product_offer:
            discount_amount = round(
                (highest_discount * product_color.price) / 100)
            highest_offer_price = product_color.price - discount_amount
        else:
            highest_discount = None
            highest_offer_price = None

        context.update({
            'product_offer': product_offer,
            'category_offer': category_offer,
            'highest_discount': highest_discount,
            'highest_offer_price': highest_offer_price
        })
    except ObjectDoesNotExist:
        pass

    if request.user.is_authenticated:
        cart_wishlist_address_order_data = get_cart_wishlist_address_order_data(
            request)
        context.update(cart_wishlist_address_order_data)
        user = request.user
        customer = Customer.objects.get(user=user)
        wishlist = Wishlist.objects.get(customer=customer)
        in_wishlist = WishlistItem.objects.filter(
            wishlist=wishlist, product=product_color).exists()
        cart = Cart.objects.get(customer=customer)
        in_cart = CartProducts.objects.filter(
            cart=cart, product__product_color_image=product_color).exists()
        context.update({
            'in_wishlist': in_wishlist,
            'in_cart': in_cart,
        })

    last_five_products = ProductColorImage.objects.order_by('-id')[:5]
    product_sizes = ProductSize.objects.filter(
        product_color_image=product_color)

    context.update({
        'product_color': product_color,
        'last_five_products': last_five_products,
        'product_sizes': product_sizes,
    })

    return render(request, 'product_view.html', context)


# -------------------------------------------------------------------------------- CC_WISHLIST FUNCTIONS --------------------------------------------------------------------------------


@never_cache
@clear_old_messages
def wishlist_view(request):
    if request.user.is_authenticated:
        user = request.user
        customer = Customer.objects.get(user=user)
        cart = Cart.objects.get(customer=customer)
        cart_items = CartProducts.objects.filter(cart=cart)
        wishlist = Wishlist.objects.get(customer=customer)
        wishlist_items = WishlistItem.objects.filter(wishlist=wishlist)
        wishlist_item_count = WishlistItem.objects.filter(
            wishlist=wishlist).count()

        context = {
            'cart': cart,
            'cart_items': cart_items,
            'wishlist': wishlist,
            'wishlist_items': wishlist_items,
            'wishlist_item_count': wishlist_item_count,
        }
        return render(request, 'wishlist.html', context)


@never_cache
@clear_old_messages
def add_to_wishlist(request, product_color_id):
    if request.user.is_authenticated:
        user = request.user
        customer = Customer.objects.get(user=user)
        wishlist = Wishlist.objects.get(customer=customer)
        product_color = ProductColorImage.objects.get(pk=product_color_id)

        in_wishlist = WishlistItem.objects.filter(
            wishlist=wishlist, product=product_color)

        if not in_wishlist:
            wishlist_item = WishlistItem.objects.create(
                wishlist=wishlist,
                product=product_color
            )
            wishlist_item.save()
            return redirect('product_single_view_page', product_color.products.name, product_color.id)
        else:
            return redirect('product_single_view_page', product_color.products.name, product_color.id)
    else:
        return redirect('index_page')


@never_cache
@clear_old_messages
def remove_from_wishlist(request, product_color_id):
    if request.user.is_authenticated:
        user = request.user
        customer = Customer.objects.get(user=user)
        wishlist = Wishlist.objects.get(customer=customer)
        product_color = ProductColorImage.objects.get(pk=product_color_id)

        in_wishlist = WishlistItem.objects.filter(
            wishlist=wishlist, product=product_color)

        if in_wishlist:
            wishlist_item = WishlistItem.objects.get(
                wishlist=wishlist,
                product=product_color
            )
            wishlist_item.delete()
            return redirect('product_single_view_page', product_color.products.name, product_color.id)
        else:
            return redirect('product_single_view_page', product_color.products.name, product_color.id)
    else:
        return redirect('index_page')


@never_cache
@clear_old_messages
def remove_in_wishlist(request, product_color_id):
    if request.user.is_authenticated:
        user = request.user
        customer = Customer.objects.get(user=user)
        wishlist = Wishlist.objects.get(customer=customer)
        product_color = ProductColorImage.objects.get(pk=product_color_id)

        in_wishlist = WishlistItem.objects.filter(
            wishlist=wishlist, product=product_color)

        if in_wishlist:
            wishlist_item = WishlistItem.objects.get(
                wishlist=wishlist,
                product=product_color
            )
            wishlist_item.delete()
            return redirect('wishlist_view')
        else:
            return redirect('wishlist_view')
    else:
        return redirect('index_page')


# -------------------------------------------------------------------------------- CC_DASHBOARD DETAILS PAGE FUNCTIONS --------------------------------------------------------------------------------


@never_cache
@clear_old_messages
def user_dashboard(request, user_id):
    if request.user.is_authenticated:
        context = {}
        cart_wishlist_address_order_data = get_cart_wishlist_address_order_data(
            request)
        context.update(cart_wishlist_address_order_data)
        return render(request, 'dashboard.html', context)
    else:
        return redirect(index_page)


@never_cache
@clear_old_messages
def user_details_edit(request):
    if request.user.is_authenticated:
        user = request.user
        user_id = user.id
        if user:
            customer = Customer.objects.get(user=user)

            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            dob = request.POST.get('dob')
            gender = request.POST.get('gender')

            is_every_field_valid = True

            if first_name:
                cleaned_first_name = clean_string(first_name)
                if not 3 <= len(cleaned_first_name) <= 100:
                    is_every_field_valid = False
                    messages.error(
                        request, 'First name must be between 3 and 100 characters.')

            if email:
                email = normalize_newlines(email).strip()
                try:
                    validate_email(email)
                except ValidationError as e:
                    is_every_field_valid = False
                    messages.error(request, 'Email address is invalid.')
                else:
                    if User.objects.exclude(pk=user.pk).filter(email=email).exists():
                        is_every_field_valid = False
                        messages.error(
                            request, 'Email already exists for another user.')

            if phone:
                if not phone.isdigit():
                    is_every_field_valid = False
                    messages.error(request, 'Phone number should be digits.')
                elif len(phone) != 10:
                    is_every_field_valid = False
                    messages.error(request, 'Phone number must be 10 digits.')

            if is_every_field_valid:
                if first_name:
                    user.first_name = first_name
                if last_name:
                    user.last_name = last_name
                if email:
                    user.email = email
                if phone:
                    customer.phone_number = phone
                if dob:
                    customer.dob = dob
                if gender:
                    customer.gender = gender

                user.save()
                customer.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect(reverse('user_dashboard', kwargs={'user_id': user_id}))
            else:
                return redirect(reverse('user_dashboard', kwargs={'user_id': user_id}))
        else:
            messages.error(request, 'User details not found.')
            return redirect(index_page)
    else:
        return redirect(index_page)


# -------------------------------------------------------------------------------- CC_REFERRALS DETAILS PAGE FUNCTIONS --------------------------------------------------------------------------------


@never_cache
@clear_old_messages
def referrals_page_view(request):
    if request.user.is_authenticated:
        context = {}
        user = request.user
        customer = Customer.objects.get(user=user)
        referral_code = customer.referral_code

        sign_up_url = reverse('sign_up_page')

        referral_link = request.build_absolute_uri(
            sign_up_url + f'?ref={referral_code}')

        referral_usage = Customer.objects.filter(
            used_referral_code=referral_code)

        referral_count = referral_usage.count() if referral_usage else 0

        total_earnings = 250 * referral_count if referral_count else 0

        cart_wishlist_address_order_data = get_cart_wishlist_address_order_data(
            request)
        context.update(cart_wishlist_address_order_data)
        context.update({
            'user': user,
            'customer': customer,
            'referral_code': referral_code,
            'referral_link': referral_link,
            'referral_usage': referral_usage,
            'referral_count': referral_count,
            'total_earnings': total_earnings,
        })
        return render(request, 'referrals.html', context)
    else:
        return redirect('sign_up_page')


# -------------------------------------------------------------------------------- CC_WALLET DETAILS PAGE FUNCTIONS --------------------------------------------------------------------------------


@never_cache
@clear_old_messages
def wallet_page_view(request, user_id):
    if request.user.is_authenticated:
        try:
            context = {}
            user = request.user
            if user.id == user_id:
                wallet = Wallet.objects.get(user=user)
                wallet_transactions = WalletTransaction.objects.filter(
                    wallet=wallet).order_by('-time_of_transaction')
                cart_wishlist_address_order_data = get_cart_wishlist_address_order_data(
                    request)
                context.update(cart_wishlist_address_order_data)
                context.update({
                    'wallet': wallet,
                    'wallet_transactions': wallet_transactions,
                })
                return render(request, 'wallet.html', context)
            else:
                return redirect('index_page')
        except Wallet.DoesNotExist:
            return redirect('index_page')
    else:
        return redirect('sign_in_page')


# -------------------------------------------------------------------------------- CC_ADDRESS DETAILS PAGE FUNCTIONS --------------------------------------------------------------------------------


@never_cache
@clear_old_messages
def update_address(request, address_id):
    if request.user.is_authenticated:
        if request.method == 'POST':
            name = request.POST.get('name')
            phone_number = request.POST.get('phone_number')
            street_address = request.POST.get('street_address')
            city = request.POST.get('city')
            state = request.POST.get('state')
            country = request.POST.get('country')
            pin_code = request.POST.get('pin_code')

            user = request.user
            user_id = user.id

            is_every_field_valid = True

            if name and phone_number and street_address and city and state and country and pin_code:

                try:
                    address = Address.objects.get(pk=address_id)
                except Address.DoesNotExist:
                    messages.error(request, 'Address not found.')
                    return redirect('user_dashboard', user_id=user_id)

                cleaned_name = clean_string(name)
                cleaned_phone = clean_string(phone_number)
                cleaned_country = clean_string(country)
                cleaned_state = clean_string(state)
                cleaned_city = clean_string(city)
                cleaned_street_address = clean_string(street_address)
                cleaned_pin_code = clean_string(pin_code)

                if not 3 <= len(cleaned_name) <= 100:
                    is_every_field_valid = False
                    messages.error(
                        request, 'Name field should not consist solely of special characters or be blank')

                elif not 3 <= len(cleaned_phone) <= 100:
                    is_every_field_valid = False
                    messages.error(
                        request, 'Phone Number field should not consist solely of special characters or be blank')

                elif not 3 <= len(cleaned_country) <= 100:
                    is_every_field_valid = False
                    messages.error(
                        request, 'Country field should not consist solely of special characters or be blank')

                elif not 3 <= len(cleaned_state) <= 100:
                    is_every_field_valid = False
                    messages.error(
                        request, 'State field should not consist solely of special characters or be blank')

                elif not 3 <= len(cleaned_city) <= 100:
                    is_every_field_valid = False
                    messages.error(
                        request, 'City field should not consist solely of special characters or be blank')

                elif not 3 <= len(cleaned_street_address) <= 500:
                    is_every_field_valid = False
                    messages.error(
                        request, 'Street Address field should not consist solely of special characters or be blank')

                elif not 3 <= len(cleaned_pin_code) <= 50:
                    is_every_field_valid = False
                    messages.error(
                        request, 'Pincode field should not consist solely of special characters or be blank')

                elif not alphabets_pattern.match(name):
                    is_every_field_valid = False
                    messages.error(request, 'Name should be in alphabets')

                elif not phone_number.isdigit():
                    is_every_field_valid = False
                    messages.error(
                        request, 'Phone number should only contain numeric digits.')

                elif not re.match(r'^\d{10}$', phone_number):
                    is_every_field_valid = False
                    messages.error(request, 'Phone number must be 10 digits')

                elif not alphabets_pattern.match(country):
                    is_every_field_valid = False
                    messages.error(
                        request, 'Country should only contain letters, numbers, and spaces.')

                elif not alphabets_pattern.match(state):
                    is_every_field_valid = False
                    messages.error(
                        request, 'State should only contain letters, numbers, and spaces.')

                elif not street_address_pattern .match(street_address):
                    is_every_field_valid = False
                    messages.error(
                        request, 'Street address should only contain letters, numbers, and spaces.')

                elif not pin_code.isdigit():
                    is_every_field_valid = False
                    messages.error(
                        request, 'Pin code should only contain numeric digits.')

                elif not re.match(r'^\d{6}$', pin_code):
                    is_every_field_valid = False
                    messages.error(request, 'Pin code must be 6 digits')

                if is_every_field_valid:
                    address.name = name
                    address.phone_number = phone_number
                    address.street_address = street_address
                    address.city = city
                    address.state = state
                    address.country = country
                    address.pin_code = pin_code

                    address.save()
                    messages.success(request, 'Address Updated')
                    user_id = address.customer.user.id
                    return redirect('user_dashboard', user_id=user_id)
                else:
                    return redirect('user_dashboard', user_id=user_id)
            else:
                return redirect('user_dashboard', user_id=user_id)
        else:
            return redirect('user_dashboard', user_id=user_id)
    else:
        return redirect('index_page')


@never_cache
@clear_old_messages
def add_new_address(request, customer_id):
    if request.user.is_authenticated:
        if request.method == 'POST':
            customer = Customer.objects.get(pk=customer_id)
            user = request.user
            user_id = user.id
            name = request.POST.get('name')
            phone_number = request.POST.get('phone_number')
            street_address = request.POST.get('street_address')
            city = request.POST.get('city')
            state = request.POST.get('state')
            country = request.POST.get('country')
            pin_code = request.POST.get('pincode')

            is_every_field_valid = True

            if customer and name and phone_number and street_address and city and state and country and pin_code:
                cleaned_name = clean_string(name)
                cleaned_phone = clean_string(phone_number)
                cleaned_country = clean_string(country)
                cleaned_state = clean_string(state)
                cleaned_city = clean_string(city)
                cleaned_street_address = clean_string(street_address)
                cleaned_pin_code = clean_string(pin_code)

                if not 3 <= len(cleaned_name) <= 100:
                    is_every_field_valid = False
                    messages.error(
                        request, 'Name field should not consist solely of special characters or be blank')

                elif not 3 <= len(cleaned_phone) <= 100:
                    is_every_field_valid = False
                    messages.error(
                        request, 'Phone Number field should not consist solely of special characters or be blank')

                elif not 3 <= len(cleaned_country) <= 100:
                    is_every_field_valid = False
                    messages.error(
                        request, 'Country field should not consist solely of special characters or be blank')

                elif not 3 <= len(cleaned_state) <= 100:
                    is_every_field_valid = False
                    messages.error(
                        request, 'State field should not consist solely of special characters or be blank')

                elif not 3 <= len(cleaned_city) <= 100:
                    is_every_field_valid = False
                    messages.error(
                        request, 'City field should not consist solely of special characters or be blank')

                elif not 3 <= len(cleaned_street_address) <= 500:
                    is_every_field_valid = False
                    messages.error(
                        request, 'Street Address field should not consist solely of special characters or be blank')

                elif not 3 <= len(cleaned_pin_code) <= 50:
                    is_every_field_valid = False
                    messages.error(
                        request, 'Pincode field should not consist solely of special characters or be blank')

                elif not alphabets_pattern.match(name):
                    is_every_field_valid = False
                    messages.error(request, 'Name should be in alphabets')

                elif not phone_number.isdigit():
                    is_every_field_valid = False
                    messages.error(
                        request, 'Phone number should only contain numeric digits.')

                elif not re.match(r'^\d{10}$', phone_number):
                    is_every_field_valid = False
                    messages.error(request, 'Phone number must be 10 digits')

                elif not alphabets_pattern.match(country):
                    is_every_field_valid = False
                    messages.error(
                        request, 'Country should only contain letters, numbers, and spaces.')

                elif not alphabets_pattern.match(state):
                    is_every_field_valid = False
                    messages.error(
                        request, 'State should only contain letters, numbers, and spaces.')

                elif not street_address_pattern .match(street_address):
                    is_every_field_valid = False
                    messages.error(
                        request, 'Street address should only contain letters, numbers, and spaces.')

                elif not pin_code.isdigit():
                    is_every_field_valid = False
                    messages.error(
                        request, 'Pin code should only contain numeric digits.')

                elif not re.match(r'^\d{6}$', pin_code):
                    is_every_field_valid = False
                    messages.error(request, 'Pin code must be 6 digits')

                if is_every_field_valid:
                    address = Address.objects.create(
                        customer=customer,
                        name=name,
                        phone_number=phone_number,
                        country=country,
                        state=state,
                        city=city,
                        street_address=street_address,
                        pin_code=pin_code
                    )
                    address.save()
                    messages.success(request, 'New shipping address created')
                    user_id = customer.user.id
                    return redirect('user_dashboard', user_id=user_id)
                else:
                    return redirect('user_dashboard', user_id=user_id)
            else:
                messages.error(
                    request, 'Please fill all the fields to add the address')
                return redirect('user_dashboard', user_id=user_id)
    else:
        return redirect(index_page)


@never_cache
@clear_old_messages
def user_change_password(request, user_id):
    if request.user.is_authenticated:
        if request.method == 'POST':
            try:
                current_password = request.POST.get('current_password')
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('confirm_password')

                user = User.objects.get(pk=user_id)
                is_valid_current_password = True
                if not check_password(current_password, user.password):
                    messages.error(request, '''Current password don't match''')
                    is_valid_current_password = False

                is_valid_new_password = True
                if len(new_password) < 8:
                    messages.error(
                        request, 'Password must be at least 8 characters long.')
                    is_valid_new_password = False
                elif ' ' in new_password:
                    messages.error(request, 'Password cannot contain spaces.')
                    is_valid_new_password = False

                is_valid_confirm_password = True
                if new_password != confirm_password:
                    messages.error(request, 'Passwords not match.')
                    is_valid_confirm_password = False

                if is_valid_current_password and is_valid_confirm_password and is_valid_new_password:
                    user.set_password(new_password)
                    user.save()

                    user = authenticate(
                        username=user.username, password=new_password)
                    if user is not None:
                        auth.login(request, user)

                    messages.success(request, 'Password Updated')
                    return redirect('user_dashboard', user_id=user_id)

                else:
                    return redirect('user_dashboard', user_id=user_id)
            except Exception as e:
                return redirect(index_page)
    else:
        return redirect(sign_in)


# -------------------------------------------------------------------------------- CC_ORDER FUNCTIONS --------------------------------------------------------------------------------


@never_cache
@clear_old_messages
def order_items_page(request, order_id):
    if request.user.is_authenticated:
        context = {}
        try:
            order = Orders.objects.get(order_id = order_id)
            order_products = order.order.all()
            count = sum(1 for item in order_products if item.order_status == 'Cancelled')
            cancelled = True if count == order.number_of_orders else None
            seven_days_ago = (timezone.now() - timedelta(days=7)).date()
            if order.delivery_date is not None:
                order_delivery_date = (order.delivery_date)
                can_return_order = True if order_delivery_date >= seven_days_ago else False
                return_end_date = order.delivery_date + timedelta(days=7)
            else:
                return_end_date = False
                can_return_order = False
            
            context.update({
                'order' : order,
                'order_products' : order_products,
                'cancelled' : cancelled,
                'can_return_order' : can_return_order,
                'return_end_date' : return_end_date,
            })
            cart_wishlist_address_order_data = get_cart_wishlist_address_order_data(request)
            context.update(cart_wishlist_address_order_data)
            return render(request, 'dashboard/orders/order_items_page.html', context)
        except Orders.DoesNotExist:
            return redirect('user_dashboard')
    else:
        return redirect('sign_in_page')    







def generate_invoice(request, order_id):
    if request.user.is_authenticated:
        try:
            order = Orders.objects.get(order_id=order_id)
            order_items = OrderItem.objects.filter(order=order)

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="invoice_{order_id}.pdf"'

            c = canvas.Canvas(response, pagesize=letter)

            company_name = "Your Company Name"
            today_date = datetime.now().strftime('%Y-%m-%d')
            order_info = f"Company: {company_name}\nDate: {today_date}\nOrder ID: {order_id}"
            c.drawString(letter[0] - c.stringWidth(company_name) - 50, letter[1] - 50, company_name)
            c.drawString(letter[0] - c.stringWidth(today_date) - 50, letter[1] - 70, today_date)
            c.drawString(letter[0] - c.stringWidth(f"Order ID: {order_id}") - 50, letter[1] - 90, f"Order ID: {order_id}")

            data = [
                ['No', 'Product', 'Qty', 'Price'],
            ]

            max_lengths = [len('No  '), len('Product'), len('Qty'), len('Price')]
            for item in order_items:
                max_lengths[1] = max(max_lengths[1], len(item.product.product_color_image.products.name))
                max_lengths[2] = max(max_lengths[2], len(str(item.quantity)))
                max_lengths[3] = max(max_lengths[3], len(str(item.each_price)))

            col_widths = [(length * 8) for length in max_lengths]
            counter = 1
            for item in order_items:
                data.append([counter, item.product.product_color_image.products.name, item.quantity, item.each_price])
                counter += 1
                
            table = Table(data, colWidths=col_widths, rowHeights=30)
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ]))

            table_width = sum(col_widths)
            start_x = (letter[0] - table_width) / 2
            start_y = letter[1] - 150

            table.wrapOn(c, 0, 0)
            table.drawOn(c, start_x, start_y)

            c.save()
            return response
        except Orders.DoesNotExist:
            return redirect('sign_in_page')
    else:
        return redirect('user_dashboard')





@never_cache
@clear_old_messages
def order_detail(request, order_id):
    if request.user.is_authenticated:
        try:
            seven_days_ago = timezone.now() - timedelta(days=7)

            orders_placed_before_7_days = OrderItem.objects.filter(
                delivery_date__gte=seven_days_ago)
            order_items = OrderItem.objects.get(pk=order_id)

            if order_items.delivery_date is not None:
                return_end_date = order_items.delivery_date + timedelta(days=7)
            else:
                return_end_date = None

            can_return_product = False
            placed = False
            shipped = False
            delivery = False
            delivered = False
            if order_items in orders_placed_before_7_days:
                can_return_product = True
            if order_items.order_status == 'Order Placed':
                placed = True
            if order_items.order_status == 'Shipped':
                shipped = True
            if order_items.order_status == 'Out for Delivery':
                delivery = True
            if order_items.order_status == 'Delivered':
                delivered = True
            user = request.user
            wallet = Wallet.objects.get(user=user)
            
            if order_items.cancel_product == True:
                if not order_items.order.payment.method_name == 'Cash On Delivery':
                    wallet_transaction = WalletTransaction.objects.get(
                        wallet=wallet, money_withdrawn=0, order_item=order_items)
            else:
                wallet_transaction = None
            context = {
                'return_end_date': return_end_date,
                'can_return_product': can_return_product,
                'order_items': order_items,
                'placed': placed,
                'shipped': shipped,
                'delivery': delivery,
                'delivered': delivered,
                'wallet': wallet,
                'wallet_transaction': wallet_transaction,
            }
            return render(request, 'dashboard/orders/order_detailed_page.html', context)
        except:
            return redirect('user_dashboard')
    else:
        return redirect(sign_in)


# -------------------------------------------------------------------------------- CC_ORDER CANCEL FUNCTION --------------------------------------------------------------------------------


@never_cache
@clear_old_messages
def cancel_order(request, order_items_id):
    if request.user.is_authenticated:
        try:
            try:
                order_item = OrderItem.objects.get(pk=order_items_id)
            except OrderItem.DoesNotExist:
                return redirect('index_page')
            order_item.request_cancel = True
            order_item.order_status = 'Cancel Requested'
            order_item.save()
            time.sleep(1)
            return redirect('order_detail', order_items_id)
        except:
            return redirect('order_detail', order_items_id)
    else:
        return redirect(sign_in)


# -------------------------------------------------------------------------------- CC_SENT RETURN REQUEST FUNCTION --------------------------------------------------------------------------------


@never_cache
def sent_return_request(request, order_items_id):
    if request.user.is_authenticated:
        try:
            seven_days_ago = timezone.now() - timedelta(days=7)
            orders_items_seven_days = OrderItem.objects.filter(
                order__placed_at__gt=seven_days_ago)
            order_items = OrderItem.objects.get(pk=order_items_id)
            if order_items in orders_items_seven_days:
                order_items.request_return = True
                order_items.save()
            return redirect('order_detail', order_items_id)
        except Exception as e:
            return redirect(index_page)
    else:
        return redirect(sign_in)


# -------------------------------------------------------------------------------- CC_CART PAGE FUNCTIONS --------------------------------------------------------------------------------


@never_cache
def cart_view_page(request, user_id):
    if request.user.is_authenticated:
        context = {}
        cart_wishlist_address_order_data = get_cart_wishlist_address_order_data(
            request)

        context['today'] = datetime.now().date()

        context.update(cart_wishlist_address_order_data)

        return render(request, 'cart.html', context)
    else:
        return redirect('index_page')


@never_cache
def add_to_cart(request, product_id):
    if request.user.is_authenticated:
        try:
            if request.method == 'POST':
                user_id = request.user.id
                user = User.objects.get(pk=user_id)
                customer = Customer.objects.get(user=user)
                size = request.POST.get('size')

                product_size = ProductSize.objects.filter(
                    product_color_image__id=product_id).get(pk=size)

                cart = Cart.objects.get(customer=customer)

                cart_product = CartProducts.objects.create(
                    cart=cart,
                    product=product_size,
                )
                cart_product.save()
                return redirect('cart_view_page', user_id=user_id)
        except Exception as e:
            return redirect(index_page)
    else:
        return redirect(sign_in)


@never_cache
def remove_from_cart(request, cart_item_id):
    if request.user.is_authenticated:
        try:
            cart_item = CartProducts.objects.get(pk=cart_item_id)
            cart_item.delete()
            return redirect(reverse('cart_view_page', kwargs={'user_id': request.user.pk}))
        except Exception as e:
            return redirect(index_page)
    else:
        return redirect(sign_in)


@never_cache
def clear_cart(request):
    if request.user.is_authenticated:
        user_id = request.user.id
        CartProducts.objects.filter(cart__customer__user_id=user_id).delete()
        return redirect('cart_view_page', user_id=user_id)
    else:
        return redirect(sign_in)


@never_cache
def update_total_price(request):
    if request.user.is_authenticated:
        if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            product_id = request.POST.get('product_id')

            try:
                product = ProductSize.objects.get(pk=product_id)
                quantity = int(request.POST.get('quantity'))
                available_quantity = product.quantity

                if quantity <= available_quantity:
                    today = datetime.now().date()
                    try:
                        product_offer = ProductOffer.objects.filter(
                            product_color_image=product.product_color_image, end_date__gte=today).first()
                        category_offer = CategoryOffer.objects.filter(
                            category=product.product_color_image.products.category, end_date__gte=today).first()

                        if product_offer and category_offer:
                            highest_discount = max(
                                product_offer.discount_percentage, category_offer.discount_percentage)
                        elif product_offer:
                            highest_discount = product_offer.discount_percentage
                        elif category_offer:
                            highest_discount = category_offer.discount_percentage
                        else:
                            highest_discount = 0

                        if highest_discount > 0:
                            discount_amount = round(
                                (highest_discount * product.product_color_image.price) / 100)
                            highest_offer_price = product.product_color_image.price - discount_amount
                        else:
                            highest_offer_price = product.product_color_image.price

                        total_price = highest_offer_price * quantity
                    except ObjectDoesNotExist:
                        total_price = product.product_color_image.price * quantity
                    return JsonResponse({'total_price': total_price})
                else:
                    return JsonResponse({'error': f'Only {available_quantity} units available'})
            except ProductSize.DoesNotExist:
                return JsonResponse({'error': 'Product does not exist'})
        else:
            return JsonResponse({'error': 'Invalid request'})
    else:
        return redirect('index_page')


@never_cache
def update_quantity(request):
    if request.user.is_authenticated:
        if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            item_id = request.POST.get('item_id')
            new_quantity = int(request.POST.get('quantity'))

            try:
                cart_item = CartProducts.objects.get(pk=item_id)
                try:
                    new_quantity = int(new_quantity)
                except ValueError:
                    messages.error(
                        request, 'Add the cart quantity using the buttons')
                    return redirect('cart_view_page')
                try:
                    if cart_item.product.quantity >= new_quantity:
                        cart_item.quantity = new_quantity
                        cart_item.save()

                        try:
                            product_offer = ProductOffer.objects.filter(
                                product_color_image=cart_item.product.product_color_image, end_date__gte=today).first()
                            category_offer = CategoryOffer.objects.filter(
                                category=cart_item.product.product_color_image.products.category, end_date__gte=today).first()

                            if product_offer and category_offer:
                                highest_discount = max(
                                    product_offer.discount_percentage, category_offer.discount_percentage)
                            elif product_offer:
                                highest_discount = product_offer.discount_percentage
                            elif category_offer:
                                highest_discount = category_offer.discount_percentage
                            else:
                                highest_discount = 0

                            if highest_discount > 0:
                                discount_amount = round(
                                    (highest_discount * cart_item.product.product_color_image.price) / 100)
                                highest_offer_price = cart_item.product.product_color_image.price - discount_amount
                            else:
                                highest_offer_price = cart_item.product.product_color_image.price

                            total_price = highest_offer_price * new_quantity
                        except ObjectDoesNotExist:
                            total_price = cart_item.product.product_color_image.price * new_quantity

                        return JsonResponse({'total_price': total_price})

                except:
                    pass
            except CartProducts.DoesNotExist:
                return JsonResponse({'error': 'Product not found'})
        else:
            return JsonResponse({'error': 'Invalid request'})
    else:
        return redirect('index_page')


# -------------------------------------------------------------------------------- CC_CHECKOUT PAGE FUNCTIONS --------------------------------------------------------------------------------


@never_cache
def checkout_page(request):
    if request.user.is_authenticated:
        context = {}
        user = request.user
        wallet = Wallet.objects.get(user=user)
        wallet_balance = wallet.balance
        customer = Customer.objects.get(user=user)
        cart = Cart.objects.get(customer=customer)
        cart_items = CartProducts.objects.filter(cart=cart, in_stock=True)
        total_charge_discounted = 0
        discount_amount = 0
        if cart_items:
            total_price = sum(item.total_price for item in cart_items)
            coupon = None
            if cart.coupon_applied:
                try:
                    coupon = Coupon.objects.get(coupon_code=cart.coupon)
                except Coupon.DoesNotExist:
                    cart.coupon_applied = False
                    cart.coupon = None

                total_charge_discounted, discount_amount = calculate_total_charge_discounted(
                    cart_items, cart)

                sub_charge = total_charge_discounted
            charge_for_shipping = 0

            if not cart.coupon_applied:
                sub_charge = total_price

            today = datetime.now().date()

            if total_charge_discounted <= 2500:
                charge_for_shipping = 99
                total_charge_discounted = total_charge_discounted + charge_for_shipping

            orders_with_coupon = Orders.objects.filter(
                customer=customer,
                coupon_applied=True,
                order__cancel_product=False
            )

            used_coupons = orders_with_coupon.values_list(
                'coupon_name', flat=True)

            available_coupons = Coupon.objects.filter(
                Q(minimum_amount__lte=total_price) &
                Q(maximum_amount__gte=total_price) &
                Q(end_date__gte=today) &
                ~Q(coupon_code__in=used_coupons)
            )
            context.update({
                'coupon': coupon,
                'wallet': wallet,
                'wallet_balance': wallet_balance,
                'available_coupons': available_coupons,
                'discount_amount': discount_amount,
                'sub_charge': sub_charge,
                'charge_for_shipping': charge_for_shipping,
                'total_charge_discounted': total_charge_discounted,
            })
            cart_wishlist_address_order_data = get_cart_wishlist_address_order_data(
                request)
            context.update(cart_wishlist_address_order_data)
            return render(request, 'checkout.html', context)
        else:
            user_id = request.user.id
            return redirect('cart_view_page', user_id=user_id)
    else:
        return redirect('index_page')


def calculate_total_charge_discounted(cart_items, cart):
    if cart.coupon_applied:
        try:
            coupon = Coupon.objects.get(coupon_code=cart.coupon)
            total_charge_discounted = calculate_discounted_total_charge(
                cart_items, coupon)
        except Coupon.DoesNotExist:
            total_charge_discounted = None
    else:
        total_charge_discounted = None
    return total_charge_discounted


def calculate_discounted_total_charge(cart_items, coupon):
    cart_total_price = 0

    for item in cart_items:
        cart_total_price += item.total_price
    cart_total = cart_total_price

    if coupon:
        discount_amount = round(
            (cart_total * coupon.discount_percentage) / 100)
        total_charge_discounted = cart_total - discount_amount
    else:
        total_charge_discounted = cart_total

    return total_charge_discounted, discount_amount


@never_cache
def apply_coupon(request):
    if request.user.is_authenticated:
        try:
            if request.method == 'POST':
                coupon_code = request.POST.get('coupon_code')
                user = request.user
                customer = Customer.objects.get(user=user)
                cart = Cart.objects.get(customer=customer)
                cart.coupon_applied = True
                cart.coupon = coupon_code
                cart.save()

                return redirect('checkout_page')
        except Exception as e:
            return redirect('checkout_page')
    else:
        return redirect('sign_in_page')
    



# ---------------------------------------------------------------------------------- CC_ORDER CONFIRMATION EMAIL FUNCTIONS ----------------------------------------------------------------------------------
    



def send_order_confirmation_email(order):
    subject = 'Order Confirmation'

    html_message = render_to_string('order_confirmation_email.html', {'order': order})

    plain_message = strip_tags(html_message)

    email_message = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email='sneakerheadsweb@example.com',
        to=[order.customer.user.email]
    )

    email_message.attach_alternative(html_message, "text/html")

    email_message.send()
    
    


# -------------------------------------------------------------------------------- CC_PLACE ORDER FUNCTIONS --------------------------------------------------------------------------------


razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@never_cache
def place_order(request):
    if request.user.is_authenticated:
        try:
            if request.method == 'POST':
                with transaction.atomic():
                    user = request.user
                    customer = Customer.objects.get(user=user)
                    wallet = Wallet.objects.get(user=user)
                    cart = Cart.objects.get(customer=customer)
                    cart_items = CartProducts.objects.filter(cart=cart)
                    if cart_items:
                        total_charge_discounted = request.POST.get(
                            'total_charge_discounted')
                        total_money = request.POST.get('total_charge')

                        cart_total = 0
                        item_count = 0
                        cart_total_price = 0

                        for item in cart_items:
                            item_count += 1
                            cart_total_price += item.total_price

                        cart_total = cart_total_price

                        total_charge = 0
                        if total_charge_discounted is not None:
                            total_charge = total_charge_discounted
                        else:
                            total_charge = total_money

                        if_coupon_applied = False
                        coupon_name = None
                        discount_price = 0
                        discount_percentage = None
                        minimum_amount = None
                        maximum_amount = None
                        discount_amount = None
                        if cart.coupon_applied:
                            coupon = Coupon.objects.get(
                                coupon_code=cart.coupon)
                            discount_price = int(
                                cart_total) - int(total_charge_discounted)
                            total_charge_discounted, discount_amount = calculate_total_charge_discounted(
                                cart_items, cart)
                            if_coupon_applied = True
                            coupon_name = cart.coupon
                            discount_percentage = coupon.discount_percentage
                            minimum_amount = coupon.minimum_amount
                            maximum_amount = coupon.maximum_amount

                        subtotal = request.POST.get('subtotal')
                        shipping_charge = request.POST.get('shipping_charge')
                        if total_charge_discounted is not None:
                            if total_charge_discounted <= 2500:
                                shipping_charge = 99
                                total_charge_discounted
                            else:
                                shipping_charge = 0
                        address_id = request.POST.get('delivery_address')
                        payment_method = request.POST.get('payment_method')

                        address = Address.objects.get(pk=address_id)

                        razorpay = None

                        if payment_method == 'Razorpay':
                            try:
                                callback_params = {
                                    'address_id': address_id,
                                }
                                callback_query_string = urlencode(
                                    callback_params)
                                callback_url = request.build_absolute_uri(reverse(
                                    'razorpay_payment', kwargs={'user_id': user.id})) + '?' + callback_query_string
                                currency = 'INR'
                                amount_in_paise = int(total_charge) * 100
                                razorpay_order = razorpay_client.order.create(
                                    dict(amount=amount_in_paise, currency=currency, payment_capture='0'))
                                razorpay_order_id = razorpay_order['id']
                                razorpay = {
                                    'customer': customer,
                                    'cart': cart,
                                    'cart_items': cart_items,
                                    'shipping_charge': shipping_charge,
                                    'address': address,
                                    'discount_amount': discount_amount,
                                    'total_charge_discounted': total_charge_discounted,
                                    'total_charge': total_charge,
                                    'subtotal': subtotal,
                                    'razorpay_order_id': razorpay_order_id,
                                    'total': amount_in_paise,
                                    'currency': currency,
                                    'discount_price': discount_price,
                                    'user': user,
                                    'callback_url': callback_url,
                                    'customer': customer,
                                    'settings': settings,
                                }
                                return render(request, 'razorpay_test.html', razorpay)
                            except Exception as e:
                                return HttpResponseBadRequest("Razorpay Order Creation Failed: " + str(e))
                        else:
                            payment = Payment.objects.create(
                                method_name=payment_method)

                            order = Orders.objects.create(
                                customer=customer,
                                address=address,
                                payment=payment,
                                number_of_orders=item_count,
                                subtotal=subtotal,
                                shipping_charge=shipping_charge,
                                total_charge=total_charge,
                                coupon_applied=if_coupon_applied,
                                coupon_name=coupon_name,
                                coupon_discount_percent=discount_percentage,
                                discount_price=discount_price,
                                coupon_minimum_amount=minimum_amount,
                                coupon_maximum_amount=maximum_amount,
                            )
                            order.save()

                            for item in cart_items:
                                price_of_each = item.total_price

                                if cart.coupon_applied:
                                    coupon = Coupon.objects.get(pk=cart.coupon)
                                    discount_price = round(
                                        (price_of_each * coupon.discount_percentage) / 100)
                                    price_of_each = price_of_each - discount_price

                                order_item = OrderItem.objects.create(
                                    order=order,
                                    product=item.product,
                                    quantity=item.quantity,
                                    order_status="Order Placed",
                                    each_price=price_of_each,
                                )
                                order_item.save()
                                product_size_id = item.product.id
                                product_size = ProductSize.objects.get(
                                    pk=product_size_id)
                                product_size.quantity -= item.quantity
                                product_size.save()

                                if payment_method == 'Wallet':
                                    order.paid = True
                                    order.save()
                                    payment.paid_at = timezone.now()
                                    payment.pending = False
                                    payment.success = True
                                    payment.save()
                                    wallet_transaction = WalletTransaction.objects.create(
                                        wallet=wallet,
                                        order_item=order_item,
                                        money_withdrawn=price_of_each
                                    )
                                    wallet.balance -= price_of_each
                                    wallet.save()
                                    wallet_transaction.save()
                            
                            send_order_confirmation_email(order)
                            cart_items.delete()

                            time.sleep(2)

                            return redirect('order_placed_view', order_id=order.order_id)
                    else:
                        return redirect('index_page')
            else:
                return redirect('index_page')
        except:
            return redirect('index_page')
    else:
        return redirect('sign_in_page')


# ---------------------------------------------------------------------------------- CC_RAZORPAY PAYMENT FUNCTIONS ----------------------------------------------------------------------------------


@csrf_exempt
@never_cache
def razorpay_payment(request, user_id):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')

        user = User.objects.get(pk=user_id)
        customer = Customer.objects.get(user=user)

        cart = Cart.objects.get(customer=customer)
        cart_items = CartProducts.objects.filter(cart=cart)

        address_id = request.GET.get('address_id')
        address = Address.objects.get(pk=address_id)

        subtotal = 0
        cart_total_price = 0
        for item in cart_items:
            cart_total_price += item.total_price

        subtotal = cart_total_price

        total_charge = subtotal
        if_coupon_applied = False
        coupon_name = None
        discount_price = 0
        discount_percentage = None
        minimum_amount = None
        maximum_amount = None

        if cart.coupon_applied:
            if_coupon_applied = True
            coupon = Coupon.objects.get(coupon_code=cart.coupon)
            discount_percentage = coupon.discount_percentage
            discount_price = round(subtotal * discount_percentage / 100)
            coupon_name = cart.coupon
            minimum_amount = coupon.minimum_amount
            maximum_amount = coupon.maximum_amount
            total_charge = int(subtotal) - int(discount_price)
            subtotal = total_charge

        shipping_charge = 0
        if total_charge < 2500:
            shipping_charge = 99
            total_charge = total_charge + shipping_charge

        payment_method = 'Razorpay'
        payment = Payment.objects.create(method_name=payment_method)
        payment.save()
        params_dict = {'razorpay_order_id': razorpay_order_id,
                       'razorpay_payment_id': payment_id, 'razorpay_signature': signature}
        result = razorpay_client.utility.verify_payment_signature(params_dict)
        if result is not None:
            with transaction.atomic():
                payment.paid_at = timezone.now()
                payment.pending = False
                payment.success = True
                payment.save()
                total = total_charge * 100
                razorpay_client.payment.capture(payment_id, total)
                order = Orders.objects.create(
                    customer=customer,
                    address=address,
                    payment=payment,
                    number_of_orders=len(cart_items),
                    subtotal=subtotal,
                    shipping_charge=shipping_charge,
                    total_charge=total_charge,
                    razorpay_id=razorpay_order_id,
                    paid=True,
                    coupon_applied=if_coupon_applied,
                    coupon_name=coupon_name,
                    coupon_discount_percent=discount_percentage,
                    discount_price=discount_price,
                    coupon_minimum_amount=minimum_amount,
                    coupon_maximum_amount=maximum_amount,
                )
                order.save()

                for item in cart_items:
                    price_of_each = item.total_price

                    if cart.coupon_applied:
                        coupon = Coupon.objects.get(pk=cart.coupon)
                        discount_price = round(
                            (price_of_each * coupon.discount_percentage) / 100)
                        price_of_each = price_of_each - discount_price

                    order_item = OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        order_status="Order Placed",
                        each_price=price_of_each,
                    )

                    order_item.save()

                    product_size_id = item.product.id
                    product_size = ProductSize.objects.get(pk=product_size_id)
                    product_size.quantity -= item.quantity
                    product_size.save()
                
                send_order_confirmation_email(order)
                cart_items.delete()

                time.sleep(2)

                return redirect('order_placed_view', order_id=order.order_id)
        else:
            payment.failed = True
            payment.pending = False
            payment.save()

            time.sleep(2)

            return render(request, 'paymentfail.html')
    else:
        return redirect('index_page')


@never_cache
def order_placed_view(request, order_id):
    if request.user.is_authenticated:
        order = get_object_or_404(Orders, order_id=order_id)
        return render(request, 'order_placed.html', {'order': order})
    else:
        return redirect('index_page')
