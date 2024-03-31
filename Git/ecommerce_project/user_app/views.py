from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib import auth
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.text import normalize_newlines
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from user_app.models import Customer
from admin_app.models import *
from django.utils import timezone
from datetime import datetime
from django.db.models import *
from django.db.models import Q
from django.http import JsonResponse
from django.db import transaction
import random
import re
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import check_password
from random import shuffle
from django.urls import reverse
from django.core.mail import send_mail
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required




# ---------------------------------------------------------------------------------- INDEX PAGE FUNCTIONS ----------------------------------------------------------------------------------


@never_cache
def index_page(request):
    if request.user.is_authenticated:
        context = {}
        user = request.user
        customer = Customer.objects.get(user = user)
        cart = Cart.objects.get(customer = customer)
        cart_items = CartProducts.objects.filter(cart = cart)
        
        if cart_items:
            item_count = 0
            subtotal = 0
            for items in cart_items:
                item_count += 1
                each_price =  items.product.product_color_image.price * items.quantity
                subtotal = subtotal + each_price
                print(subtotal)
            if subtotal <= 2500:
                shipping_charge = 99
                total_charge = subtotal + shipping_charge
                print(total_charge)
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
    
    
    
@never_cache
def verify_otp(request):
    if request.user.is_authenticated:
        return redirect('index_page')
    else:
        messages.success(request, 'OTP has been sent to your email')
        return render(request, 'verify_otp.html')
    


def generate_otp(user):
    return int(random.randint(100000,999999))


def send_otp_email(email, otp):
    subject = 'Your OTP for Email Verification'
    message = f'Your OTP is : {otp}'
    from_email = 'sneakerheadsweb@gmail.com'
    to_email = [email]
    send_mail(subject, message, from_email, to_email)

    


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
                otp = generate_otp(user)
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




@never_cache
def logout(request):
    if request.method == 'POST':
        auth.logout(request)
        messages.info(request, 'Login again!')
        return redirect(sign_in)
    
    
    else:
        return render(request, '404.html')
    








# ---------------------------------------------------------------------------------- SHOP PAGE FUNCTIONS ----------------------------------------------------------------------------------




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
        cart = Cart.objects.get(customer = customer)
        cart_items = CartProducts.objects.filter(cart = cart)
        context.update({
            'cart' : cart,
            'cart_items' : cart_items,
            })
        if cart_items:
            item_count = 0
            subtotal = 0
            for items in cart_items:
                item_count += 1
                each_price =  items.product.product_color_image.price * items.quantity
                subtotal = subtotal + each_price
                print(subtotal)
            if subtotal <= 2500:
                shipping_charge = 99
                total_charge = subtotal + shipping_charge
                print(total_charge)
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
    





# -------------------------------------------------------------------------------- PRODUCT SINGLE PAGE FUNCTIONS --------------------------------------------------------------------------------


@never_cache
def product_single_view_page(request, product_name, pdt_id):
    context = {}
    product_color = ProductColorImage.objects.get(pk=pdt_id)

    if request.user.is_authenticated:
        user = request.user
        customer = Customer.objects.get(user=user)
        cart = Cart.objects.get(customer=customer)
        cart_items = CartProducts.objects.filter(cart=cart)
        in_cart = CartProducts.objects.filter(cart=cart, product__product_color_image=product_color).exists()
        context.update({
            'user': user, 
            'cart': cart,
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
                print(subtotal)
            if subtotal <= 2500:
                shipping_charge = 99
                total_charge = subtotal + shipping_charge
                print(total_charge)
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




# -------------------------------------------------------------------------------- USER ACCOUNT DETAILS PAGE FUNCTIONS --------------------------------------------------------------------------------





@login_required
@never_cache
def user_dashboard(request, user_id):
    if request.user.is_authenticated:
        if user_id:
            user = User.objects.get(pk = user_id)
            customer = Customer.objects.get(user = user)
            cart = Cart.objects.get(customer = customer)
            cart_items = CartProducts.objects.filter(cart = cart)
            addresses = Address.objects.filter(customer = customer)
            context =  {
                'cart' : cart,
                'user' : user, 
                'customer' : customer,
                'addresses' : addresses,
                'cart_items' : cart_items
                }
            if cart_items:
                item_count = 0
                subtotal = 0
                for items in cart_items:
                    item_count += 1
                    each_price =  items.product.product_color_image.price * items.quantity
                    subtotal = subtotal + each_price
                    print(subtotal)
                if subtotal <= 2500:
                    shipping_charge = 99
                    total_charge = subtotal + shipping_charge
                    print(total_charge)
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
        return render(index_page)
    
    
@login_required
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
        return render(index_page)

            
        
        
# -------------------------------------------------------------------------------- USER ADDRESS DETAILS PAGE FUNCTIONS --------------------------------------------------------------------------------



@login_required
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



@login_required
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
                
                
                
                
                
@login_required
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
                
                
                
                


# -------------------------------------------------------------------------------- USER CART PAGE FUNCTIONS --------------------------------------------------------------------------------
                
                
@login_required
@never_cache
def cart_view_page(request, user_id):
    if request.user.is_authenticated:
        context = {}
        user = User.objects.get(pk = user_id)
        customer = Customer.objects.get(user = user)
        shipping_addresses = Address.objects.filter(customer = customer)
        cart = Cart.objects.get(customer = customer)
        cart_items = CartProducts.objects.filter(cart = cart)
        any_in_stock = any(item.in_stock for item in cart_items)
        if cart_items:
            item_count = 0
            subtotal = 0
            for items in cart_items:
                item_count += 1
                each_price =  items.product.product_color_image.price * items.quantity
                subtotal = subtotal + each_price
                print(subtotal)
            if subtotal <= 2500:
                shipping_charge = 99
                total_charge = subtotal + shipping_charge
                print(total_charge)
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
            'any_in_stock' : any_in_stock
        })
        return render(request, 'cart.html', context)
    
    
@login_required
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
        

@login_required
@never_cache
def remove_from_cart(request, cart_item_id):
    if request.user.is_authenticated:
        cart_item = CartProducts.objects.get(pk = cart_item_id)
        cart_item.delete()
        return redirect(reverse('cart_view_page', kwargs={'user_id': request.user.pk}))
    
    
@login_required
@never_cache
def clear_cart(request):
    if request.user.is_authenticated:
        user_id = request.user.id
        CartProducts.objects.filter(cart__customer__user_id=user_id).delete()
        return redirect('cart_view_page', user_id=user_id)
        
        
        
@login_required
@never_cache
def update_total_price(request):
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

    
    
    
@login_required
@never_cache
def update_quantity(request):
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
    
    





# -------------------------------------------------------------------------------- USER CHECKOUT PAGE FUNCTIONS --------------------------------------------------------------------------------
   
        
@login_required
@never_cache
def checkout_page(request):
    if request.user.is_authenticated:
        user = request.user
        customer = Customer.objects.get(user=user)
        cart = Cart.objects.get(customer=customer)
        cart_items = CartProducts.objects.filter(cart=cart, in_stock=True)
        
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
                'addresses': addresses,
            }
            return render(request, 'checkout.html', context)
        else:
            user_id = request.user.id
            return redirect('cart_view_page', user_id=user_id)
    else:
        return redirect(index_page)

            
            

@login_required
@never_cache
def place_order(request):
    if request.user.is_authenticated:
        with transaction.atomic():
            user = request.user
            customer = Customer.objects.get(user = user)
            
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    