from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from user_app.models import Customer
from django.contrib.auth import authenticate
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required 
from django.views.decorators.cache import never_cache




@never_cache
def admin_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
            user_list = User.objects.all().order_by('username').values()
            return render(request, 'admin_index.html', {'user_list': user_list})
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_superuser:
            auth.login(request, user)
            user_list = User.objects.all().order_by('username').values()
            return render(request, 'admin_index.html', {'user_list': user_list})
        else:
            messages.error(request, 'Invalid credentials, please try logging in again.')
            return redirect('admin_login')
    else:
        return render(request, 'admin_login.html')






@login_required
@never_cache
def admin_customers(request):
    if request.user.is_superuser:
        user_list = User.objects.all().order_by('username').values()
        customer_list = Customer.objects.all().order_by('user__first_name').values()
        return render(request, 'pages/customers/customers.html',{'user_list' : user_list, 'customer_list' : customer_list})
    else:
        return redirect('admin_login')
        
        
def block_user(request, user_id):
    if request.user.is_superuser:
        if request.method == 'POST':
            user_to_block = User.objects.get(id=user_id)
            user_to_block.is_active = False
            user_to_block.save()
            return redirect(admin_customers)
        else:
            return redirect(admin_customers)
    else:
        return redirect(admin_login)

def unblock_user(request, user_id):
    if request.user.is_superuser:
        if request.method == 'POST':
            user_to_unblock = User.objects.get(id=user_id)
            user_to_unblock.is_active = True
            user_to_unblock.save()
            return redirect(admin_customers)
        else:
            return redirect(admin_customers)
    else:
        return redirect(admin_login)
        
        
        
        
@login_required
def search_user(request):
    if request.user.is_superuser:
        query = request.GET.get('query', '')
        
        if query:
             user_list = User.objects.filter(username__icontains = query)
        else:
            user_list = User.objects.all().order_by('username').values()
        
        return render(request,'pages/customers/customers.html' ,{'user_list' : user_list})

        
        
def admin_logout(request):
    if request.method == 'POST' :
        auth.logout(request)
        messages.info(request, 'Login again!')
        return redirect('admin_login')
    else:
        return render(request, '404.html')