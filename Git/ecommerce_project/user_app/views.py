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
from django.db import transaction
import random
from django.urls import reverse
from django.core.mail import send_mail
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required





# ---------------------------------------------------------------------------------- INDEX PAGE ----------------------------------------------------------------------------------


@never_cache
def index_page(request):
    if request.user.is_authenticated:
        customer = Customer.objects.all()
        return render(request, 'index.html', {'customer': customer})
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
                        customer = Customer.objects.create(user = user)
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
    




# ---------------------------------------------------------------------------------- SHOP PAGE ----------------------------------------------------------------------------------


@never_cache
def shop_page_view(request):
        price_ranges = [
            {"min": 1000, "max": 1500},
            {"min": 1500, "max": 2500},
            {"min": 2500, "max": 4000},
            {"min": 2500, "max": 3500},
            {"min": 3500, "max": 5000},
            {"min": 5000, "max": None},
            ]
        product_list = Product.objects.all()
        latest_products = Product.objects.all()[:10]
        category_list = Category.objects.annotate(product_count= Count ('product'))
        brand_list = Brand.objects.annotate(product_count = Count('product'))
        return render(request, 'shop_page.html', {'product_list' : product_list, 'brand_list' : brand_list, 'category_list' : category_list, 'price_ranges' : price_ranges, 'latest_products' : latest_products,})

    
    


# -------------------------------------------------------------------------------- PRODUCT SINGLE VIEW PAGE --------------------------------------------------------------------------------


@never_cache
def product_single_view_page(request, product_name, pdt_id):
        product = Product.objects.get(pk=pdt_id)
        last_five_products = Product.objects.order_by('-id')[:5]
        return render(request, 'product_view.html', {'product': product, 'last_five_products': last_five_products})







# -------------------------------------------------------------------------------- USER ACCOUNT DETAILS VIEW PAGE --------------------------------------------------------------------------------





@login_required
@never_cache
def user_dashboard(request, user_id):
    print(user_id)
    if request.user.is_authenticated:
        if user_id:
            user = User.objects.get(pk = user_id)
            return render(request, 'dashboard.html', {'user' : user ,})
        else:
            messages.error(request, 'Not able to get user details at this moment')
            return redirect(index_page)
    else:
        return render(index_page)
    