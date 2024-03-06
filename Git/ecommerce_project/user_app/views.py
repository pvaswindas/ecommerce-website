from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib import auth
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.text import normalize_newlines
from django.core.validators import validate_email
from django.core.exceptions import ValidationError



def index_page(request):
    return render(request, 'index.html')


def register_function(request):
    if request.user.is_authenticated:
        return redirect('index_page')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Normalize and validate email
        email = normalize_newlines(email).strip()
        is_valid_email = True
        try:
            validate_email(email)
        except ValidationError as e:
            is_valid_email = False
            messages.error(request, f'Invalid email: {e}')

        # Password validation
        is_valid_password = True
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long')
            is_valid_password = False
        elif ' ' in password:
            messages.error(request, 'Password cannot contain spaces')
            is_valid_password = False

        if is_valid_email and is_valid_password:
            try:
                user = User.objects.create_user(username=email, password=password)
                messages.success(request, 'User created successfully!')
                return redirect('sign_in_function')
            except Exception as e:
                messages.error(request, f'Error creating user: {str(e)}')

    return render(request, 'login.html')



def sign_in_function(request):
    if request.user.is_authenticated:
        return redirect('index_page')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(username=email, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('index_page')
        else:
            messages.error(request, 'Invalid email or password')

    return render(request, 'login.html')




def test_signin(request):
    return render(request, 'signin.html')

def test_signup(request):
    return render(request, 'signup.html')