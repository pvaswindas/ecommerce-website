import re
import time
import random
import razorpay # type: ignore
from random import shuffle
from datetime import datetime
from user_app.models import *
from admin_app.models import *
from django.db.models import Q
from django.db.models import *
from django.contrib import auth
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from django.http import JsonResponse
from django.http import HttpResponse
from django.core.mail import send_mail
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.shortcuts import redirect, render
from django.http import HttpResponseBadRequest
from django.utils.text import normalize_newlines
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.contrib.auth.hashers import check_password


# ---------------------------------------------------------------------------------- CC_INDEX PAGE FUNCTIONS ----------------------------------------------------------------------------------





@never_cache
def index_page(request):
    if request.user.is_authenticated:
        context = {}
        user = request.user
        customer = Customer.objects.get(user = user)
        cart = Cart.objects.get(customer = customer)
        cart_items = CartProducts.objects.filter(cart = cart)
        wishlist = Wishlist.objects.get(customer = customer)
        wishlist_item_count = WishlistItem.objects.filter(wishlist = wishlist).count()
        
        if cart_items:
            item_count = 0
            subtotal = 0
            for items in cart_items:
                item_count += 1
                each_price =  items.product.product_color_image.price * items.quantity
                subtotal = subtotal + each_price
            if subtotal <= 2500:
                shipping_charge = 99
                total_charge = subtotal + shipping_charge
            else:
                shipping_charge = 0
                total_charge = subtotal
            context.update({
                'item_count' : item_count,
                'shipping_charge' : shipping_charge,
                'subtotal' : subtotal,
                'total_charge' : total_charge,
                'user' : user,
                'customer' : customer,
                'cart' : cart,
                'cart_items' : cart_items,
            })
        context.update({
            'customer' : customer,
            'cart' : cart,
            'cart_items' : cart_items,
            'wishlist_item_count' : wishlist_item_count,
        })
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
            
            otp = generate_otp(user)
            
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
        return redirect('sign_in')
                

# ---------------------------------------------------------------------------------- CC_USER_LOGOUT PASSWORD FUNCTIONS ----------------------------------------------------------------------------------




@never_cache
def logout(request):
    if request.method == 'POST':
        auth.logout(request)
        messages.info(request, 'Login again!')
        return redirect(sign_in)
    
    
    else:
        return render(request, '404.html')
    




# ---------------------------------------------------------------------------------- CC_SHOP PAGE FUNCTIONS ----------------------------------------------------------------------------------




@never_cache
def shop_page_view(request):
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
        user = request.user
        customer = Customer.objects.get(user = user)
        wishlist = Wishlist.objects.get(customer = customer)
        wishlist_item_count = WishlistItem.objects.filter(wishlist = wishlist).count()
        cart = Cart.objects.get(customer = customer)
        cart_items = CartProducts.objects.filter(cart = cart)
        context.update({
            'cart' : cart,
            'cart_items' : cart_items,
            'wishlist' : wishlist,
            'wishlist_item_count' : wishlist_item_count,
            })
        if cart_items:
            item_count = 0
            subtotal = 0
            for items in cart_items:
                item_count += 1
                each_price =  items.product.product_color_image.price * items.quantity
                subtotal = subtotal + each_price
            if subtotal <= 2500:
                shipping_charge = 99
                total_charge = subtotal + shipping_charge
            else:
                shipping_charge = 0
                total_charge = subtotal
            context.update({
                'item_count' : item_count,
                'shipping_charge' : shipping_charge,
                'subtotal' : subtotal,
                'total_charge' : total_charge,
            })
        
    product_color_list = list(ProductColorImage.objects.filter(is_deleted = False, is_listed = True))
    shuffle(product_color_list)
    latest_products = ProductColorImage.objects.all()[:10]
    category_list = Category.objects.annotate(product_count=Count('products'))
    brand_list = Brand.objects.annotate(product_count=Count('products'))
    
    context.update({
        'product_color_list': product_color_list,
        'brand_list': brand_list,
        'category_list': category_list,
        'price_ranges': price_ranges,
        'latest_products': latest_products,
    })
        
    return render(request, 'shop_page.html', context)
    





# -------------------------------------------------------------------------------- CC_PRODUCT SINGLE PAGE FUNCTIONS --------------------------------------------------------------------------------




@never_cache
def product_single_view_page(request, product_name, pdt_id):
    context = {}
    product_color = ProductColorImage.objects.get(pk=pdt_id)

    if request.user.is_authenticated:
        user = request.user
        customer = Customer.objects.get(user=user)
        cart = Cart.objects.get(customer=customer)
        cart_items = CartProducts.objects.filter(cart=cart)
        wishlist = Wishlist.objects.get(customer = customer)
        wishlist_items = WishlistItem.objects.filter(wishlist = wishlist)
        in_wishlist = WishlistItem.objects.filter(wishlist = wishlist, product = product_color).exists()
        wishlist_item_count = WishlistItem.objects.filter(wishlist = wishlist).count()
        in_cart = CartProducts.objects.filter(cart=cart, product__product_color_image=product_color).exists()
        context.update({
            'user': user, 
            'cart': cart,
            'wishlist' : wishlist,
            'wishlist_items' : wishlist_items,
            'in_wishlist' : in_wishlist,
            'wishlist_item_count' : wishlist_item_count,
            'in_cart': in_cart,
            'cart_items': cart_items,
        })
        if cart_items:
            item_count = 0
            subtotal = 0
            for items in cart_items:
                item_count += 1
                each_price =  items.product.product_color_image.price * items.quantity
                subtotal = subtotal + each_price
            if subtotal <= 2500:
                shipping_charge = 99
                total_charge = subtotal + shipping_charge
            else:
                shipping_charge = 0
                total_charge = subtotal
            context.update({
                'item_count' : item_count,
                'shipping_charge' : shipping_charge,
                'subtotal' : subtotal,
                'total_charge' : total_charge,
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
        wishlist = Wishlist.objects.get(customer = customer)
        wishlist_items = WishlistItem.objects.filter(wishlist = wishlist)
        wishlist_item_count = WishlistItem.objects.filter(wishlist = wishlist).count()
        
        context = {
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




# -------------------------------------------------------------------------------- CC_ACCOUNT DETAILS PAGE FUNCTIONS --------------------------------------------------------------------------------



@never_cache
def user_dashboard(request, user_id):
    if request.user.is_authenticated:
        if user_id:
            user = User.objects.get(pk = user_id)
            customer = Customer.objects.get(user = user)
            cart = Cart.objects.get(customer = customer)
            cart_items = CartProducts.objects.filter(cart = cart)
            wishlist = Wishlist.objects.get(customer = customer)
            wishlist_item_count = WishlistItem.objects.filter(wishlist = wishlist).count()
            addresses = Address.objects.filter(customer = customer)
            orders = Orders.objects.filter(customer = customer)
            
            context =  {
                'cart' : cart,
                'user' : user, 
                'customer' : customer,
                'addresses' : addresses,
                'cart_items' : cart_items,
                'wishlist_item_count' : wishlist_item_count,
                'orders' : orders,
                }
            if cart_items:
                item_count = 0
                subtotal = 0
                for items in cart_items:
                    item_count += 1
                    each_price =  items.product.product_color_image.price * items.quantity
                    subtotal = subtotal + each_price
                if subtotal <= 2500:
                    shipping_charge = 99
                    total_charge = subtotal + shipping_charge
                else:
                    shipping_charge = 0
                    total_charge = subtotal
                context.update({
                    'item_count' : item_count,
                    'shipping_charge' : shipping_charge,
                    'subtotal' : subtotal,
                    'total_charge' : total_charge,
                })
            return render(request, 'dashboard.html', context)
        else:
            messages.error(request, 'Not able to get user details at this moment')
            return redirect(index_page)
    else:
        return redirect(index_page)
    
    





@never_cache
def user_details_edit(request, user_id):
    if request.user.is_authenticated:
        if user_id:
            user = User.objects.get(pk = user_id)
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
    else:
        return redirect(index_page) 
                
                
                
                




# -------------------------------------------------------------------------------- CC_ORDER FUNCTIONS --------------------------------------------------------------------------------




@never_cache
def order_detail(request, order_id):
    if request.user.is_authenticated:
        if order_id:
            order = Orders.objects.get(pk = order_id)
            order_items = OrderItem.objects.filter(order = order)
            placed = False
            shipped = False
            delivery = False
            delivered = False
            if order.order_status == 'Order Placed':
                placed = True
            if order.order_status == 'Shipped':
                shipped = True
            if order.order_status == 'Out for delivery':
                delivery = True
            if order.order_status == 'Delivered':
                delivered = True
            
            context = {
                'order' : order,
                'order_items' : order_items,
                'placed' : placed,
                'shipped' : shipped,
                'delivery' : delivery,
                'delivered' : delivered,
            }
            return render(request, 'dashboard/orders/order_detailed_page.html', context)







# -------------------------------------------------------------------------------- CC_CART PAGE FUNCTIONS --------------------------------------------------------------------------------
                
                
                
                
@never_cache
def cart_view_page(request, user_id):
    if request.user.is_authenticated:
        context = {}
        user = User.objects.get(pk = user_id)
        customer = Customer.objects.get(user = user)
        shipping_addresses = Address.objects.filter(customer = customer)
        cart = Cart.objects.get(customer = customer)
        cart_items = CartProducts.objects.filter(cart = cart)
        wishlist = Wishlist.objects.get(customer = customer)
        wishlist_item_count = WishlistItem.objects.filter(wishlist = wishlist).count()
        any_in_stock = any(item.in_stock for item in cart_items)
        if cart_items:
            item_count = 0
            subtotal = 0
            for items in cart_items:
                item_count += 1
                each_price =  items.product.product_color_image.price * items.quantity
                subtotal = subtotal + each_price
            if subtotal <= 2500:
                shipping_charge = 99
                total_charge = subtotal + shipping_charge
            else:
                shipping_charge = 0
                total_charge = subtotal
            context.update({
                'item_count' : item_count,
                'shipping_charge' : shipping_charge,
                'subtotal' : subtotal,
                'total_charge' : total_charge,
            })
        context.update({
            'shipping_addresses' : shipping_addresses,
            'cart_items' : cart_items,
            'any_in_stock' : any_in_stock,
            'wishlist_item_count' : wishlist_item_count,
        })
        return render(request, 'cart.html', context)
    
    
    
    
    
@never_cache
def add_to_cart(request, product_id):
    if request.user.is_authenticated:
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
    else:
        return redirect(sign_in)
        



@never_cache
def remove_from_cart(request, cart_item_id):
    if request.user.is_authenticated:
        cart_item = CartProducts.objects.get(pk = cart_item_id)
        cart_item.delete()
        return redirect(reverse('cart_view_page', kwargs={'user_id': request.user.pk}))
    else:
        return redirect(index_page)
    
    
    
    
@never_cache
def clear_cart(request):
    if request.user.is_authenticated:
        user_id = request.user.id
        CartProducts.objects.filter(cart__customer__user_id=user_id).delete()
        return redirect('cart_view_page', user_id=user_id)
        
        
        
        
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
        wishlist = Wishlist.objects.get(customer = customer)
        wishlist_item_count = WishlistItem.objects.filter(wishlist = wishlist).count()
        
        addresses = Address.objects.filter(customer=customer)

        if cart_items:
            item_count = 0
            subtotal = 0
            for items in cart_items:
                item_count += 1
                each_price = items.product.product_color_image.price * items.quantity
                subtotal = subtotal + each_price
            if subtotal <= 2500:
                shipping_charge = 99
                total_charge = subtotal + shipping_charge
            else:
                shipping_charge = 0
                total_charge = subtotal
            context = {
                'item_count': item_count,
                'shipping_charge': shipping_charge,
                'subtotal': subtotal,
                'total_charge': total_charge,
                'user': user,
                'customer': customer,
                'cart': cart,
                'cart_items': cart_items,
                'wishlist_item_count' : wishlist_item_count,
                'addresses': addresses,
            }
            return render(request, 'checkout.html', context)
        else:
            user_id = request.user.id
            return redirect('cart_view_page', user_id=user_id)
    else:
        return redirect('index_page')

            
            

            
    
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
                item_count = 0
                subtotal = 0
                for items in cart_items:
                    item_count += 1
                    each_price = items.product.product_color_image.price * items.quantity
                    subtotal = subtotal + each_price
                if subtotal <= 2500:
                    shipping_charge = 99
                    total_charge = subtotal + shipping_charge
                else:
                    shipping_charge = 0
                    total_charge = subtotal

                address_id = request.POST.get('delivery_address')
                payment_method = request.POST.get('payment_method')
                order_status = "Order Placed"
                
                address = Address.objects.get(pk=address_id)

                
                
                razorpay = None
                
                if payment_method == 'Razorpay':
                    try: 
                        request.session['address_id'] = address_id
                        request.session['payment_method'] = payment_method
                        currency = 'INR'
                        callback_url = request.build_absolute_uri(reverse('razorpay_payment'))
                        amount_in_paise = int(total_charge * 100)
                        razorpay_order = razorpay_client.order.create(dict(amount=amount_in_paise,currency=currency, payment_capture='0'))
                        razorpay_order_id = razorpay_order['id']
                        razorpay = {
                            'shipping_charge' : shipping_charge,
                            'address' : address,
                            'total_charge' : total_charge,
                            'razorpay_order_id' : razorpay_order_id,
                            'total' : amount_in_paise,
                            'currency' : currency,
                            'user' : user,
                            'callback_url' : callback_url,
                            'customer' : customer,
                            'settings' : settings,
                        }
                        return render(request, 'razorpay_test.html', razorpay)
                    except Exception as e:
                        return HttpResponseBadRequest("Razorpay Order Creation Failed: " + str(e))
                else:
                    payment = Payment.objects.create(
                        method_name=payment_method,
                        started_at = timezone.now()
                    )
                    order = Orders.objects.create(
                    customer=customer,
                    order_status=order_status,
                    address=address,
                    payment=payment,
                    number_of_orders=item_count,
                    subtotal=subtotal,
                    shipping_charge=shipping_charge,
                    total_charge=total_charge
                    )
                    order.save()
                    
                    for item in cart_items:
                        order_item = OrderItem.objects.create(
                            order = order,
                            product = item.product,
                            quantity = item.quantity,
                            order_status="Order Placed",
                            each_price = item.product.product_color_image.price,
                        )
                        order_item.save()
                        
                        product_size_id = item.product.id
                        product_size = ProductSize.objects.get(pk = product_size_id)
                        product_size.quantity -= item.quantity
                        product_size.save()
                        cart_items.delete()
                    return render(request, 'order_placed.html', { 'order' : order } )
        return redirect('index_page')
    else:
        return redirect('index_page')

                
                
                
                
                
                
                
# ---------------------------------------------------------------------------------- CC_RAZORPAY PAYMENT FUNCTIONS ----------------------------------------------------------------------------------

        
@csrf_exempt
def razorpay_payment(request):
    if request.method == "POST":
        try:
            payment_id = request.POST.get('razorpay_payment_id', '')
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')
            
            user = request.user
            customer = Customer.objects.get(user = user)
            cart = Cart.objects.get(customer = customer)
            cart_items = CartProducts.objects.filter(cart = cart)
            if cart_items:
                item_count = 0
                subtotal = 0
                for items in cart_items:
                    item_count += 1
                    each_price = items.product.product_color_image.price * items.quantity
                    subtotal = subtotal + each_price
                if subtotal <= 2500:
                    shipping_charge = 99
                    total_charge = subtotal + shipping_charge
                else:
                    shipping_charge = 0
                    total_charge = subtotal
                    
                print('REACHED NEAR')
                address_id = request.session.get('address_id')
                address = Address.objects.get(pk=address_id)
                payment_method = request.session.get('payment_method')
                order_status = "Order Placed"
                print(address)
                print(payment_method)
                print(order_status)
                
            
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            payment = Payment.objects.create(
                    method_name=payment_method,
                    started_at = timezone.now()
                )

            result = razorpay_client.utility.verify_payment_signature(params_dict)
            print(result)
            if result is not None:
                print('ENTERED RAZOR')
                order = Orders.objects.get(razorpay_id = razorpay_order_id)
                total = order.total_charge * 100
                try:
                    print('Entered inside razorpay')
                    razorpay_client.payment.capture(payment_id, total)
                    order = Orders.objects.create(
                        customer=customer,
                        order_status=order_status,
                        address=address,
                        payment=payment,
                        number_of_orders=item_count,
                        subtotal=subtotal,
                        shipping_charge=shipping_charge,
                        total_charge=total_charge,
                        razorpay_id = razorpay_order_id,
                        paid = True,
                    )
                    order.save()
                        
                    for item in cart_items:
                        print('print item in cart')
                        order_item = OrderItem.objects.create(
                            order = order,
                            product = item.product,
                            quantity = item.quantity,
                            order_status="Order Placed",
                            each_price = item.product.product_color_image.price,
                        )
                        order_item.save()
                            
                        product_size_id = item.product.id
                        product_size = ProductSize.objects.get(pk = product_size_id)
                        product_size.quantity -= item.quantity
                        product_size.save()
                        cart_items.delete()
                        order.paid = True
                        order.payment.pending = False
                        order.payment.success = True
                        order.payment.paid_at = timezone.now()
                        order.save()
                        
                        return render(request, 'order_placed.html', { 'order' : order })
                except Exception as e:
                    return render(request, 'paymentfail.html')

            else:
                return render(request, 'paymentfail.html')
        except Exception as e:
            return HttpResponseBadRequest()
    else:
        return HttpResponseBadRequest()
    
    
    