import re
import time
import random
import logging
import razorpay # type: ignore
from random import shuffle
from datetime import datetime
from user_app.models import *
from admin_app.models import *
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
from django.http import HttpResponse
from django.core.mail import send_mail
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.http import HttpResponseBadRequest
from django.utils.text import normalize_newlines
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.cache import never_cache
from django.contrib.auth.hashers import check_password


# ---------------------------------------------------------------------------------- CC_INDEX PAGE FUNCTIONS ----------------------------------------------------------------------------------





def get_cart_wishlist_address_order_data(request):
    data = {}
    if request.user.is_authenticated:
        user = request.user
        customer = Customer.objects.get(user=user)
        cart = Cart.objects.get(customer=customer)
        cart_items = CartProducts.objects.filter(cart=cart)
        wishlist = Wishlist.objects.get(customer=customer)
        wishlist_item_count = WishlistItem.objects.filter(wishlist=wishlist).count()
        addresses = Address.objects.filter(customer = customer)
        orders = Orders.objects.filter(customer = customer)
        order_items = OrderItem.objects.filter(order__customer=customer).order_by('-order__placed_at')
        data.update({
            'user': user,
            'customer': customer,
            'cart': cart,
            'cart_items': cart_items,
            'wishlist': wishlist,
            'wishlist_item_count': wishlist_item_count,
            'addresses' : addresses,
            'orders' : orders,
            'order_items' : order_items,
        })
        
        if cart_items:
            item_count = 0
            subtotal = 0
            for item in cart_items:
                item_count += 1
                if item.product.product_color_image.productoffer.exists():
                    offer = item.product.product_color_image.productoffer.first()
                    each_price = offer.offer_price * item.quantity
                else:
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
def index_page(request):
    if request.user.is_authenticated:
        context = {}
        cart_wishlist_address_order_data = get_cart_wishlist_address_order_data(request)
        context.update(cart_wishlist_address_order_data)
        return render(request, 'index.html', context)
    return render(request, 'index.html')

@never_cache
def sign_in(request):
    if request.user.is_authenticated:
        return redirect('index_page')
    else:
        return render(request, 'signin.html')


@never_cache
def sign_up(request):
    if request.user.is_authenticated:
        return redirect('index_page')
    else:
        return render(request, 'signup.html')
    
    
# ---------------------------------------------------------------------------------- CC_OTP GENERATE FUNCTIONS ----------------------------------------------------------------------------------

 
 
    
@never_cache
def verify_otp(request):
    if request.user.is_authenticated:
        return redirect('index_page')
    else:
        messages.success(request, 'OTP has been sent to your email')
        return render(request, 'verify_otp.html')
    


def generate_otp():
    return int(random.randint(100000,999999))

# ---------------------------------------------------------------------------------- CC_SEND OTP IN MAIL FUNCTIONS ----------------------------------------------------------------------------------


def send_otp_email(email, otp):
    subject = 'Your OTP for Email Verification'
    message = f'Your OTP is : {otp}'
    from_email = 'sneakerheadsweb@gmail.com'
    to_email = [email]
    send_mail(subject, message, from_email, to_email)

    

# ---------------------------------------------------------------------------------- CC_USER_REGISTER PAGE FUNCTIONS ----------------------------------------------------------------------------------



@never_cache
def register_function(request):
    if request.user.is_authenticated:
        return redirect('index_page')

    elif request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']


        email = normalize_newlines(email).strip()
        is_valid_email = True
        try:
            validate_email(email)
        except ValidationError as e:
            is_valid_email = False
            messages.error(request, f'Invalid email: {e}')
            
            
        if User.objects.filter(username = email).exists():
            messages.error(request, 'Email already exits, try logging in')
            is_valid_email = False

        is_valid_password = True
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            is_valid_password = False
        elif ' ' in password:
            messages.error(request, 'Password cannot contain spaces.')
            is_valid_password = False
        
        
        is_valid_confirm_password = True
        if password != confirm_password:
            messages.error(request, 'Passwords not match.')
            is_valid_confirm_password = False
            
            
        if is_valid_email and is_valid_password and is_valid_confirm_password:
            try:
                user = User(first_name = name, username = email, email=email)
                otp = generate_otp()
                email = user.email
                if otp:
                    send_otp_email(user, otp)
                    request.session['otp'] = otp
                    request.session['otp_created_at'] = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                    request.session['user_data'] = {
                        'name' : name,
                        'email' : email,
                        'password' : password
                    }
                    return redirect('otp_verification_page')
                else:
                    messages.error(request, 'Error generating OTP')
                    return redirect('sign_up')
            except Exception as e:
                messages.error(request, f'Error creating user: {str(e)}')
                return redirect('sign_up_page')
                
    return redirect('sign_up_page')   




# ---------------------------------------------------------------------------------- CC_OTP VERIFICATION PAGE FUNCTIONS ----------------------------------------------------------------------------------




@never_cache
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
            
            otp_created_at = datetime.strptime(otp_created_at_str, '%Y-%m-%d %H:%M:%S')
            otp_created_at = timezone.make_aware(otp_created_at, timezone.get_current_timezone())
            
            now = timezone.localtime(timezone.now())
            
            if (now - otp_created_at).total_seconds() <= 120:
                if str(otp_entered) == str(otp):
                    user_data = request.session.get('user_data')
                    if user_data:
                        user = User.objects.create_user(
                            username = user_data['email'],
                            email = user_data['email'],
                            password = user_data['password'],
                            first_name = user_data['name']
                        )
                        user.save()
                        del request.session['user_data']
                        del request.session['otp']
                        del request.session['otp_created_at']
                        messages.success(request, 'Registration Successfully, Login Now')
                        return redirect('sign_in_page')
                    else:
                        messages.error(request, 'User data not found in session')
                else:
                    messages.error(request, 'Invalid OTP. Please try again.')
            else:
                messages.error(request, 'OTP has expired. Please request a new one.')
    else:
        return redirect('verify_otp')



@never_cache
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
            request.session['otp_created_at'] = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

            
            messages.info(request, 'OTP has been resent.')
            return redirect('otp_verification_page')
        else:
            messages.error(request, 'User data not found in session.')
            return redirect('sign_up')
    else:
        return redirect('resend_otp_page')






# ---------------------------------------------------------------------------------- CC_SIGN IN FUNCTIONS ----------------------------------------------------------------------------------


@never_cache
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
def forgot_password_page(request):
    return render(request, 'forgot_password.html')


@never_cache
def reset_password(request, user_id):
    timestamp = request.GET.get('timestamp')
    if not timestamp or int(timestamp) < int(time.time()):
        return HttpResponseBadRequest('The link has expired or is invalid.')
    
    return render(request, 'reset_password_page.html', {'user_id' : user_id})


@never_cache
def reset_password_change(request, user_id):
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
            
        is_valid_password = True
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
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
                messages.success(request, 'Password reset successfully. You can now log in with your new password.')
                return redirect('sign_in_page')
            except User.DoesNotExist:
                return HttpResponseBadRequest('Invalid user ID.')
    else:
        return HttpResponseBadRequest('Invalid request method.')
            
            


def send_link_email(email, page_url, timestamp):
    subject = 'Link to reset your password'
    message = format_html("Click <a href='{}'>here</a> to reset your password.", page_url)
    from_email = 'sneakerheadsweb@gmail.com'
    to_email = [email]
    send_mail(subject, '', from_email, to_email, html_message=message)
    
    
@never_cache
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
                        reverse('reset_password', kwargs={'user_id': user.id}) + f'?timestamp={timestamp}'
                    )
                    send_link_email(email, page_url, timestamp)
                    messages.success(request, 'Check email for the link to reset your password')
                    return redirect(forgot_password_page)
            else:
                messages.error(request, 'User does not exist. Please try with a correct email.')
                return redirect(forgot_password_page)
    else:
        return redirect('sign_in_page')
                

# ---------------------------------------------------------------------------------- CC_USER_LOGOUT PASSWORD FUNCTIONS ----------------------------------------------------------------------------------




@never_cache
def logout(request):
    if request.method == 'POST':
        auth.logout(request)
        messages.info(request, 'Login again!')
        return redirect(sign_in)
    
    
    else:
        return redirect('sign_in_page')
    




# ---------------------------------------------------------------------------------- CC_SHOP PAGE FUNCTIONS ----------------------------------------------------------------------------------


default = False
a_z = False
new_arrival = False
low_to_high = False
high_to_low = False



@never_cache
def get_product_sort(request):
    global default, a_z, new_arrival, low_to_high, high_to_low

    if request.method == 'POST':
        sortby = request.POST.get('sortby')
        
        default = False
        a_z = False
        new_arrival = False
        low_to_high = False
        high_to_low = False
            
        if sortby == 'a_z':
            a_z = True
        elif sortby == 'new_arrival':
            new_arrival = True
        elif sortby == 'low_to_high':
            low_to_high = True
        elif sortby == 'high_to_low':
            high_to_low = True
        else:
            default = True
            
    return redirect('shop_page_view')


search = ""


@never_cache
def search_for_product(request):
    global search      
    
    time.sleep(1)
    
    if request.method == 'POST':
        search_query = request.POST.get('search_query')
        
        if not str(search_query) == "":
            search = str(search_query)
        return redirect('shop_page_view')
    else:
        return redirect('shop_page_view')
        
        



selected_category = []

@never_cache
def category_wise(request):
    global selected_category
    if request.method == 'POST':
        category_wise = request.POST.get('category_wise')
        if category_wise in selected_category:
            selected_category.remove(category_wise)
        else:
            selected_category.append(category_wise)
        return redirect('shop_page_view')
    else:
        return redirect('index_page')
    





selected_brand = []

@never_cache
def brand_wise(request):
    global selected_brand
    if request.method == 'POST':
        brand_wise = request.POST.get('brand_wise')
        if brand_wise in selected_brand:
            selected_brand.remove(brand_wise)
        else:
            selected_brand.append(brand_wise)
        return redirect('shop_page_view')
    else:
        return redirect('index_page')



@never_cache
def clean_all(request):
    global selected_category, selected_brand
    selected_category = []
    selected_brand = []
    return redirect('shop_page_view')

      

@never_cache
def shop_page_view(request):
    global search, default, a_z, new_arrival, low_to_high, high_to_low, selected_category, selected_brand
    context = {}
    
    
    price_ranges = [
        {"min": 1000, "max": 1500},
        {"min": 1500, "max": 2500},
        {"min": 2500, "max": 4000},
        {"min": 2500, "max": 3500},
        {"min": 3500, "max": 5000},
        {"min": 5000, "max": None},
    ]
    if request.user.is_authenticated:
        cart_wishlist_address_order_data = get_cart_wishlist_address_order_data(request)
        context.update(cart_wishlist_address_order_data)
        
    product_color_list = ProductColorImage.objects.filter(is_deleted=False, is_listed=True)
    
    
    if selected_category and selected_brand:
        product_color_list = product_color_list.filter(Q(products__category__name__in=selected_category) & Q(products__brand__name__in=selected_brand))
        
    if selected_category or selected_brand:
        product_color_list = product_color_list.filter(Q(products__category__name__in=selected_category) | Q(products__brand__name__in=selected_brand))

    
    if not search == "":
        product_color = product_color_list.filter(
            Q(products__name__icontains=search) |
            Q(color__icontains=search) |
            Q(price__icontains=search) |
            Q(products__type__icontains=search) |
            Q(products__category__name__icontains=search) |
            Q(products__brand__name__icontains=search)
        )
        if product_color:
            product_color_list = product_color
        
        search = ""
    
    if a_z:
        product_color_list = product_color_list.order_by('products__name')
    elif new_arrival:
        product_color_list = product_color_list.order_by('-created_at')
    elif low_to_high:
        product_color_list = product_color_list.order_by('price')
    elif high_to_low:
        product_color_list = product_color_list.order_by('-price')
        
    
    active_offers = ProductOffer.objects.filter(
        Q(end_date__gte=timezone.now()) | Q(end_date=None),
        product_color_image__in=product_color_list
    )
        
    latest_products = ProductColorImage.objects.filter(is_deleted=False, is_listed=True).order_by('-created_at')[:3]

    
    category_list = Category.objects.annotate(product_count=Count('products'))
    
    brand_list = Brand.objects.annotate(product_count=Count('products'))
    
    context.update({
        'product_color_list': product_color_list,
        'brand_list': brand_list,
        'category_list': category_list,
        'price_ranges': price_ranges,
        'latest_products': latest_products,
        'default' : default,
        'a_z' : a_z,
        'new_arrival' : new_arrival,
        'low_to_high' : low_to_high,
        'high_to_low' : high_to_low,
        'selected_category' : selected_category,
        'selected_brand' : selected_brand,
        'active_offers' : active_offers,
        
    })
    default = False
    a_z = False
    new_arrival = False
    low_to_high = False
    high_to_low = False
    
        
    return render(request, 'shop_page.html', context)


    



# -------------------------------------------------------------------------------- CC_PRODUCT SINGLE PAGE FUNCTIONS --------------------------------------------------------------------------------




@never_cache
def product_single_view_page(request, product_name, pdt_id):
    context = {}
    product_color = ProductColorImage.objects.get(pk=pdt_id)
    
    try:
        product_offer = ProductOffer.objects.get(product_color_image=product_color)
        context['product_offer'] = product_offer
    except ObjectDoesNotExist:
        pass
    if request.user.is_authenticated:
        cart_wishlist_address_order_data = get_cart_wishlist_address_order_data(request)
        context.update(cart_wishlist_address_order_data)
        user = request.user
        customer = Customer.objects.get(user = user)
        wishlist = Wishlist.objects.get(customer = customer)
        in_wishlist = WishlistItem.objects.filter(wishlist = wishlist, product = product_color).exists()
        cart = Cart.objects.get(customer = customer)
        in_cart = CartProducts.objects.filter(cart = cart, product__product_color_image = product_color).exists()
        context.update({
            'in_wishlist' : in_wishlist,
            'in_cart' : in_cart,
        })
    last_five_products = ProductColorImage.objects.order_by('-id')[:5]
    product_sizes = ProductSize.objects.filter(product_color_image=product_color)

    context.update({
        'product_color': product_color,
        'last_five_products': last_five_products,
        'product_sizes': product_sizes,
    })

    return render(request, 'product_view.html', context)







# -------------------------------------------------------------------------------- CC_WISHLIST FUNCTIONS --------------------------------------------------------------------------------




@never_cache
def wishlist_view(request):
    if request.user.is_authenticated:
        user = request.user
        customer = Customer.objects.get(user = user)
        cart = Cart.objects.get(customer=customer)
        cart_items = CartProducts.objects.filter(cart=cart)
        wishlist = Wishlist.objects.get(customer = customer)
        wishlist_items = WishlistItem.objects.filter(wishlist = wishlist)
        wishlist_item_count = WishlistItem.objects.filter(wishlist = wishlist).count()
        
        context = {
            'cart' : cart,
            'cart_items' : cart_items,
            'wishlist' : wishlist,
            'wishlist_items' : wishlist_items,
            'wishlist_item_count' : wishlist_item_count,
        }
        return render(request, 'wishlist.html', context)

@never_cache
def add_to_wishlist(request, product_color_id):
    if request.user.is_authenticated:
        user = request.user
        customer = Customer.objects.get(user = user)
        wishlist = Wishlist.objects.get(customer = customer)
        product_color = ProductColorImage.objects.get(pk = product_color_id)
        
        
        in_wishlist = WishlistItem.objects.filter(wishlist = wishlist, product = product_color)
        
        
        if not in_wishlist:
            wishlist_item = WishlistItem.objects.create(
                wishlist = wishlist,
                product = product_color
            )
            wishlist_item.save()
            return redirect('product_single_view_page', product_color.products.name, product_color.id )
        else:
            return redirect('product_single_view_page', product_color.products.name, product_color.id )
    else:
        return redirect('index_page')
    
    
    
    
    
    
@never_cache
def remove_from_wishlist(request, product_color_id):
    if request.user.is_authenticated:
        user = request.user
        customer = Customer.objects.get(user = user)
        wishlist = Wishlist.objects.get(customer = customer)
        product_color = ProductColorImage.objects.get(pk = product_color_id)
        
        
        in_wishlist = WishlistItem.objects.filter(wishlist = wishlist, product = product_color)
        
        
        if in_wishlist:
            wishlist_item = WishlistItem.objects.get(
                wishlist = wishlist,
                product = product_color
            )
            wishlist_item.delete()
            return redirect('product_single_view_page', product_color.products.name, product_color.id )
        else:
            return redirect('product_single_view_page', product_color.products.name, product_color.id )
    else:
        return redirect('index_page')
            


@never_cache
def remove_in_wishlist(request, product_color_id):
    if request.user.is_authenticated:
        user = request.user
        customer = Customer.objects.get(user = user)
        wishlist = Wishlist.objects.get(customer = customer)
        product_color = ProductColorImage.objects.get(pk = product_color_id)
        
        
        in_wishlist = WishlistItem.objects.filter(wishlist = wishlist, product = product_color)
        
        
        if in_wishlist:
            wishlist_item = WishlistItem.objects.get(
                wishlist = wishlist,
                product = product_color
            )
            wishlist_item.delete()
            return redirect('wishlist_view' )
        else:
            return redirect('wishlist_view' )
    else:
        return redirect('index_page')




# -------------------------------------------------------------------------------- CC_DASHBOARD DETAILS PAGE FUNCTIONS --------------------------------------------------------------------------------



@never_cache
def user_dashboard(request, user_id):
    if request.user.is_authenticated:
        context = {}
        cart_wishlist_address_order_data = get_cart_wishlist_address_order_data(request)
        context.update(cart_wishlist_address_order_data)
        return render(request, 'dashboard.html', context)
    else:
        return redirect(index_page)
    
    





@never_cache
def user_details_edit(request):
    if request.user.is_authenticated:
        user = request.user
        user_id = user.id
        if user:
            customer = Customer.objects.get(user = user)
            
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            dob = request.POST.get('dob')
            gender = request.POST.get('gender')
            
            
            is_valid_phone = True
            
            email = normalize_newlines(email).strip()
            is_valid_email = True
            
            try:
                validate_email(email)
            except ValidationError as e:
                is_valid_email = False
                messages.error(request, f'Invalid email: {e}')
                
            current_user_email = request.user.email
            if User.objects.filter(~Q(username=current_user_email), username=email).exists():
                is_valid_email = False
                messages.error(request, 'Email already exists for another user')
                
            
            if not re.match(r'^\d{10}$', phone):
                is_valid_phone = False
                messages.error(request, 'Phone number must be 10 digits')
                
            if is_valid_email and is_valid_phone:
                user.first_name = first_name
                user.last_name = last_name
                user.username = email
                user.email = email
                customer.phone_number = phone
                customer.dob = dob
                customer.gender = gender
            
                user.save()
                customer.save()
                messages.success(request, 'Profile Updated')
            return redirect(reverse('user_dashboard', kwargs={'user_id': user_id}))
        else:
            messages.error(request, 'Not able to change user details at this moment')
            return redirect(index_page)
    else:
        return redirect(index_page)

            
        
# -------------------------------------------------------------------------------- CC_WALLET DETAILS PAGE FUNCTIONS --------------------------------------------------------------------------------
       



@never_cache
def wallet_page_view(request, user_id):
    if request.user.is_authenticated:
        try:
            context = {}
            user = request.user
            if user.id == user_id:
                wallet = Wallet.objects.get(user=user)
                wallet_transactions = WalletTransaction.objects.filter(wallet = wallet).order_by('-time_of_transaction')
                cart_wishlist_address_order_data = get_cart_wishlist_address_order_data(request)
                context.update(cart_wishlist_address_order_data)
                context.update({
                    'wallet': wallet,
                    'wallet_transactions' : wallet_transactions,
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
                
            is_valid_phone_no = True
                
            if not re.match(r'^\d{10}$', phone_number):
                is_valid_phone_no = False
                messages.error(request, 'Phone number must be 10 digits')
                
            address = Address.objects.get(pk = address_id)
                
            if is_valid_phone_no:
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
                return redirect('user_dashboard', user_id = user_id)
    else:
        return redirect(index_page)






@never_cache
def add_new_address(request, customer_id):
    if request.user.is_authenticated:
        if request.method == 'POST':
            customer = Customer.objects.get(pk = customer_id)
            name = request.POST.get('name')
            phone_number = request.POST.get('phone_number')
            street_address = request.POST.get('street_address')
            city = request.POST.get('city')
            state = request.POST.get('state')
            country = request.POST.get('country')
            pin_code = request.POST.get('pincode')
                
            is_valid_phone_no = True
                
            if not re.match(r'^\d{10}$', phone_number):
                is_valid_phone_no = False
                messages.error(request, 'Phone number must be 10 digits')
                    
                
            if is_valid_phone_no:
                address = Address.objects.create(
                    customer = customer,
                    name = name,
                    phone_number = phone_number,
                    country = country,
                    state = state,
                    city = city,
                    street_address = street_address,
                    pin_code = pin_code
                )
                address.save()
                messages.success(request, 'New shipping address created')
                user_id = customer.user.id
                return redirect('user_dashboard', user_id = user_id)
    else:
        return redirect(index_page)
                
                
                
                
     
     
                

@never_cache
def user_change_password(request, user_id):
    if request.user.is_authenticated:
        if request.method == 'POST':
            try:
                current_password  = request.POST.get('current_password')
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('confirm_password')
                
                user = User.objects.get(pk = user_id)
                is_valid_current_password = True
                if not check_password(current_password, user.password):
                    messages.error(request, '''Current password don't match''')
                    is_valid_current_password = False
                    
                is_valid_new_password = True
                if len(new_password) < 8:
                    messages.error(request, 'Password must be at least 8 characters long.')
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
                    
                    user = authenticate(username=user.username, password=new_password)
                    if user is not None:
                        auth.login(request, user)
                        
                    messages.success(request, 'Password Updated')
                    return redirect('user_dashboard', user_id = user_id)
                    
                else:
                    return redirect('user_dashboard', user_id = user_id)
            except Exception as e:
                return redirect(index_page)
    else:
        return redirect(sign_in) 
                
                
                
                




# -------------------------------------------------------------------------------- CC_ORDER FUNCTIONS --------------------------------------------------------------------------------




@never_cache
def order_detail(request, order_id):
    if request.user.is_authenticated:
        try:
            seven_days_ago = timezone.now() - timedelta(days=7)
            orders_placed_before_7_days = OrderItem.objects.filter(order__placed_at__gte = seven_days_ago)
            order_items = OrderItem.objects.get(pk = order_id)
            return_end_date = order_items.order.placed_at + timedelta(days=7)
            return_end_date_local = return_end_date.astimezone(timezone.get_current_timezone())
            return_end_date_only_date = return_end_date_local.date()
            can_return_product = False
            if order_items in orders_placed_before_7_days:
                can_return_product = True
                placed = False
                shipped = False
                delivery = False
                delivered = False
            if order_items.order_status == 'Order Placed':
                placed = True
            if order_items.order_status == 'Shipped':
                shipped = True
            if order_items.order_status == 'Out for Delivery':
                delivery = True
            if order_items.order_status == 'Delivered':
                delivered = True
            user = request.user
            wallet = Wallet.objects.get(user = user)
            if order_items.cancel_product == True:
                wallet_transaction = WalletTransaction.objects.get(wallet = wallet, order_item = order_items)
            else:
                wallet_transaction = None    
            context = {
                'return_end_date_only_date' : return_end_date_only_date,
                'can_return_product' : can_return_product,
                'order_items' : order_items,
                'placed' : placed,
                'shipped' : shipped,
                'delivery' : delivery,
                'delivered' : delivered,
                'wallet' : wallet,
                'wallet_transaction' : wallet_transaction,
            }
            return render(request, 'dashboard/orders/order_detailed_page.html', context)
        except Exception as e:
            return redirect(index_page)
    else:
        return redirect(sign_in)




# -------------------------------------------------------------------------------- CC_ORDER CANCEL FUNCTION --------------------------------------------------------------------------------




@never_cache
def cancel_order(request, order_items_id):
    if request.user.is_authenticated:
        try:
            order_item = OrderItem.objects.get(pk = order_items_id)
            product_size = order_item.product
            order = order_item.order
            user = request.user
            wallet = Wallet.objects.get(user = user)
            
            if order.payment.method_name == "Razorpay":
                refund_money = 0
                other_item_price = 0
                sum_of_all_other = 0
                if order.number_of_orders > 1:
                    if order_item.order.coupon_applied:
                        minimum_amount = order.coupon_minimum_amount
                        maximum_amount = order.coupon_maximum_amount
                        item_price = order_item.total_price
                        discount_price = round((item_price * order.coupon_discount_percent) / 100)
                        coupon_applied_price = item_price - discount_price
                        total_after_reducing = order.total_charge - coupon_applied_price
                        
                        
                        other_order_items = OrderItem.objects.filter(order=order).exclude(pk=order_items_id)
                        
                        if minimum_amount <= total_after_reducing <= maximum_amount:
                            for item in other_order_items:
                                other_item_price = item.total_price
                                discount_for_other_item = round((other_item_price * order.coupon_discount_percent) / 100)
                                other_item_coupon_applied_price = other_item_price - discount_for_other_item
                                
                                item.total_price = other_item_coupon_applied_price
                                item.save()
                                
                            order.total_charge = total_after_reducing
                            order.save()
                            refund_money = coupon_applied_price
                            wallet_transaction = WalletTransaction.objects.create(
                                wallet = wallet,
                                order_item = order_item,
                                money_deposit = refund_money
                            )
                            wallet_transaction.save()
                            
                        else:
                            order_total = order.total_charge
                            for item in other_order_items:
                                other_item_price = item.each_price * item.quantity
                                sum_of_all_other += other_item_price
                                item.total_price = other_item_price
                                item.save()
                                
                            refund_money = order_total - sum_of_all_other
                            
                            wallet_transaction = WalletTransaction.objects.create(
                                wallet = wallet,
                                order_item = order_item,
                                money_deposit = refund_money
                            )
                            wallet_transaction.save()
                            
                            order.total_charge = sum_of_all_other
                            order.coupon_applied = False
                            order.coupon_name = None
                            order.discount_price = None
                            order.coupon_discount_percent = None
                            order.coupon_minimum_amount = None
                            order.coupon_maximum_amount = None
                            order.save()
                    else:
                        item_price = order_item.total_price
                        refund_money = item_price
                        wallet_transaction = WalletTransaction.objects.create(
                            wallet = wallet,
                            order_item = order_item,
                            money_deposit = refund_money,
                        )
                        wallet_transaction.save()  
                else:
                    refund_money = order.total_charge
                    wallet_transaction = WalletTransaction.objects.create(
                        wallet=wallet,
                        order_item = order_item,
                        money_deposit=refund_money,
                    )
                    wallet_transaction.save()
            new_wallet_balance = wallet.balance + refund_money
            wallet.balance = new_wallet_balance   
            wallet.save()
        
            product_size.quantity += order_item.quantity
            product_size.save()        
            order_item.cancel_product = True
            order_item.order_status = 'Cancelled'
            order_item.save()
            
            time.sleep(2)
            
            return redirect('order_detail', order_items_id)
        except Exception as e:
            return redirect(index_page)
    else:
        return redirect(sign_in)




# -------------------------------------------------------------------------------- CC_SENT RETURN REQUEST FUNCTION --------------------------------------------------------------------------------




@never_cache
def sent_return_request(request, order_items_id):
    if request.user.is_authenticated:
        try:
            seven_days_ago = timezone.now() - timedelta(days=7)
            orders_items_seven_days = OrderItem.objects.filter(order__placed_at__gt=seven_days_ago)
            order_items = OrderItem.objects.get(pk = order_items_id)
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
        cart_wishlist_address_order_data = get_cart_wishlist_address_order_data(request)
        context.update(cart_wishlist_address_order_data)
        return render(request, 'cart.html', context)
    else:
        return render(sign_in)
    
    
    
    
    
@never_cache
def add_to_cart(request, product_id):
    if request.user.is_authenticated:
        try:
            if request.method == 'POST':
                user_id = request.user.id
                user = User.objects.get(pk = user_id)
                customer = Customer.objects.get(user = user)
                size = request.POST.get('size')
                
                product_size = ProductSize.objects.filter(product_color_image__id = product_id).get(pk = size)
                
                cart = Cart.objects.get(customer =  customer)
                
                cart_product = CartProducts.objects.create(
                    cart = cart,
                    product = product_size,
                )
                cart_product.save()
                return redirect('cart_view_page', user_id = user_id)
        except Exception as e:
            return redirect(index_page)
    else:
        return redirect(sign_in)
        



@never_cache
def remove_from_cart(request, cart_item_id):
    if request.user.is_authenticated:
        try:
            cart_item = CartProducts.objects.get(pk = cart_item_id)
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
                    if product.product_color_image.productoffer.exists():
                        offer = product.product_color_image.productoffer.first()
                        total_price = offer.offer_price * quantity
                    else:
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
                cart_item.quantity = new_quantity
                cart_item.save()
                
                if cart_item.product.product_color_image.productoffer.exists():
                    offer = cart_item.product.product_color_image.productoffer.first()
                    total_price = offer.offer_price * new_quantity
                else:
                    total_price = cart_item.product.product_color_image.price * new_quantity
                
                return JsonResponse({'total_price': total_price})
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
        user = request.user
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

                total_charge_discounted, discount_amount   = calculate_total_charge_discounted(cart_items, cart)
            
            charge_for_shipping = 0
            
            if not cart.coupon_applied:
                pass
            sub_charge = total_charge_discounted
            
            if total_charge_discounted <= 2500:
                charge_for_shipping = 99
                total_charge_discounted = total_charge_discounted + charge_for_shipping
            
            orders_with_coupon = Orders.objects.filter(customer = customer, coupon_applied = True)
            
            used_coupons = orders_with_coupon.values_list('coupon_name', flat=True)

            available_coupons = Coupon.objects.filter(
                Q(minimum_amount__lte = total_price) & 
                Q(maximum_amount__gte = total_price) &
                ~Q(coupon_code__in = used_coupons)
                )
            context = {
                'coupon' : coupon,
                'available_coupons': available_coupons,
                'discount_amount' : discount_amount,
                'sub_charge' : sub_charge,
                'charge_for_shipping' : charge_for_shipping,
                'total_charge_discounted': total_charge_discounted,
            }
            cart_wishlist_address_order_data = get_cart_wishlist_address_order_data(request)
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
            total_charge_discounted = calculate_discounted_total_charge(cart_items, coupon)
        except Coupon.DoesNotExist:
            total_charge_discounted = None
    else:
        total_charge_discounted = None
    return total_charge_discounted





def calculate_discounted_total_charge(cart_items, coupon):
    cart_total_with_offer = 0
    cart_total_without_offer = 0
    
    for item in cart_items:
        if item.product.product_color_image.productoffer.exists():
            product_offer = ProductOffer.objects.get(product_color_image = item.product.product_color_image)
            offer_price = product_offer.offer_price
            cart_total_with_offer += offer_price * item.quantity
        else:
            cart_total_without_offer += item.product.product_color_image.price * item.quantity
    cart_total = cart_total_with_offer + cart_total_without_offer 
    
    if coupon:
        discount_amount = round((cart_total * coupon.discount_percentage) / 100)
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

    
            
            

            
    
    
# -------------------------------------------------------------------------------- CC_PLACE ORDER FUNCTIONS --------------------------------------------------------------------------------
    





razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))



@never_cache
def place_order(request):
    if request.user.is_authenticated:
            with transaction.atomic():
                user = request.user
                customer = Customer.objects.get(user=user)
                cart = Cart.objects.get(customer=customer)
                cart_items = CartProducts.objects.filter(cart=cart)
                if cart_items:
                    total_charge_discounted = request.POST.get('total_charge_discounted')
                    total_money = request.POST.get('total_charge')
                    
                    cart_total = 0
                    cart_total_with_offer = 0
                    cart_total_without_offer = 0
                    item_count = 0
                    for item in cart_items:
                        item_count += 1
                        if item.product.product_color_image.productoffer.exists():
                            product_offer = ProductOffer.objects.get(product_color_image = item.product.product_color_image)
                            offer_price = product_offer.offer_price
                            cart_total_with_offer += offer_price
                        else:
                            cart_total_without_offer += item.product.product_color_image.price
                    cart_total = cart_total_with_offer + cart_total_without_offer
                    
                    
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
                        coupon = Coupon.objects.get(coupon_code = cart.coupon)
                        discount_price = int(cart_total) - int(total_charge_discounted)
                        total_charge_discounted, discount_amount   = calculate_total_charge_discounted(cart_items, cart)
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
                            callback_query_string = urlencode(callback_params)
                            callback_url = request.build_absolute_uri(reverse('razorpay_payment', kwargs={'user_id': user.id})) + '?' + callback_query_string
                            currency = 'INR'
                            amount_in_paise = int(total_charge) * 100
                            razorpay_order = razorpay_client.order.create(dict(amount=amount_in_paise, currency=currency, payment_capture='0'))
                            razorpay_order_id = razorpay_order['id']
                            razorpay = {
                                'customer' : customer,
                                'cart' : cart,
                                'cart_items' : cart_items,
                                'shipping_charge' : shipping_charge,
                                'address' : address,
                                'discount_amount' : discount_amount,
                                'total_charge_discounted' : total_charge_discounted,
                                'total_charge' : total_charge,
                                'subtotal' : subtotal,
                                'razorpay_order_id' : razorpay_order_id,
                                'total' : amount_in_paise,
                                'currency' : currency,
                                'discount_price' : discount_price,
                                'user' : user,
                                'callback_url' : callback_url,
                                'customer' : customer,
                                'settings' : settings,
                            }
                            return render(request, 'razorpay_test.html', razorpay)
                        except Exception as e:
                            return HttpResponseBadRequest("Razorpay Order Creation Failed: " + str(e))
                    else:
                        payment = Payment.objects.create(method_name=payment_method)
                        order = Orders.objects.create(
                            customer=customer,
                            address=address,
                            payment=payment,
                            number_of_orders=item_count,
                            subtotal=subtotal,
                            shipping_charge=shipping_charge,
                            total_charge=total_charge,
                            coupon_applied = if_coupon_applied,
                            coupon_name = coupon_name,
                            coupon_discount_percent = discount_percentage,
                            discount_price = discount_price,
                            coupon_minimum_amount = minimum_amount,
                            coupon_maximum_amount = maximum_amount,
                        )
                        order.save()
                        
                        for item in cart_items:
                            price_of_each = 0
                            if item.product.product_color_image.productoffer.exists():
                                offer = ProductOffer.objects.get(product_color_image = item.product.product_color_image)
                                price_of_each = offer.offer_price * item.quantity
                            else:
                                price_of_each = item.product.product_color_image.price * item.quantity
    
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
                        cart_items.delete()
                            
                        time.sleep(2)
                            
                        return render(request, 'order_placed.html', {'order': order})
                else:
                    return redirect('index_page')
    else:
        return redirect('sign_in_page')

                
                
                
                
                
                
                
# ---------------------------------------------------------------------------------- CC_RAZORPAY PAYMENT FUNCTIONS ----------------------------------------------------------------------------------

 


@csrf_exempt
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
            cart_total_with_offer = 0
            cart_total_without_offer = 0
            for item in cart_items:
                if item.product.product_color_image.productoffer.exists():
                    product_offer = ProductOffer.objects.get(product_color_image = item.product.product_color_image)
                    offer_price = product_offer.offer_price
                    cart_total_with_offer += offer_price * item.quantity
                else:
                    cart_total_without_offer += item.product.product_color_image.price * item.quantity
            subtotal = cart_total_with_offer + cart_total_without_offer
            
            total_charge = subtotal
            if_coupon_applied = False
            coupon_name = None
            discount_price = 0
            discount_percentage = None
            minimum_amount = None
            maximum_amount = None
            
            if cart.coupon_applied:
                if_coupon_applied = True
                coupon = Coupon.objects.get(coupon_code = cart.coupon)
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
            params_dict = {'razorpay_order_id': razorpay_order_id, 'razorpay_payment_id': payment_id, 'razorpay_signature': signature}
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
                        coupon_applied = if_coupon_applied,
                        coupon_name = coupon_name,
                        coupon_discount_percent = discount_percentage,
                        discount_price = discount_price,
                        coupon_minimum_amount = minimum_amount,
                        coupon_maximum_amount = maximum_amount,
                    )
                    order.save()
                    for item in cart_items:
                        price_of_each = 0
                        if item.product.product_color_image.productoffer.exists():
                            offer = ProductOffer.objects.get(product_color_image = item.product.product_color_image)
                            price_of_each = offer.offer_price
                        else:
                            price_of_each = item.product.product_color_image.price
                            
                        
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
                    cart_items.delete()
                    
                    time.sleep(2)
                    
                    return render(request, 'order_placed.html', {'order': order})
            else:
                payment.failed = True
                payment.pending = False
                payment.save()
                
                time.sleep(2)
                
                return render(request, 'paymentfail.html')
    else:
        return redirect('index_page')
