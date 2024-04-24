import calendar
from django.shortcuts import render, redirect
import re
from django.contrib.auth.models import User
from user_app.models import Customer
from admin_app.models import *
from datetime import datetime
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib import auth
from django.contrib import messages
from django.utils.timezone import make_aware
from django.contrib.auth.decorators import login_required 
from django.views.decorators.cache import never_cache

import datetime
import xlsxwriter # type: ignore

from django.db.models import Q

from reportlab.lib.pagesizes import letter # type: ignore
from reportlab.lib import colors # type: ignore
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle # type: ignore
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle # type: ignore
from reportlab.lib.units import inch # type: ignore
from reportlab.platypus import Paragraph, Spacer # type: ignore


from reportlab.platypus import Paragraph # type: ignore
from reportlab.lib.styles import getSampleStyleSheet # type: ignore

from django.http import HttpResponse
from django.template.loader import render_to_string
from reportlab.pdfgen import canvas # type: ignore
from reportlab.lib.pagesizes import letter # type: ignore
from reportlab.lib import colors # type: ignore
from reportlab.platypus import Table, TableStyle # type: ignore
from io import BytesIO

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.http import HttpResponse




is_active_dashboard = True
is_active_customer = True
is_active_product = True
is_active_brand = True
is_active_category = True
is_active_order = True
is_active_product_offer = True
is_active_coupon = True
is_active_banner = True
is_active_sales  = True


five_days_ago = timezone.now() - timedelta(days=5)



def clear_old_messages(view_func):
    def only_new_messages(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        storage = messages.get_messages(request)
        storage.used = True
        return response
    return only_new_messages


# 5 DAYS CUSTOMERS-----------------------------------------------------------------------------------------------------------------------------------------------------------------
customers_last_5_days = User.objects.filter(date_joined__gte=five_days_ago).count()
total_customers = Customer.objects.all().count()

if total_customers > 0:
    increase_of_customer_in_five_days = round((customers_last_5_days / total_customers) * 100, 2)
else:
    increase_of_customer_in_five_days = 0 



# 5 DAYS ORDERS---------------------------------------------------------------------------------------------------------------------------------------------------------------------
orders_last_5_days = OrderItem.objects.filter(order__placed_at__gte = five_days_ago).count()
total_orders = OrderItem.objects.all().count()

if total_orders > 0:
    increase_of_order_in_five_days = round((orders_last_5_days / total_orders ) * 100, 2)
else:
    increase_of_order_in_five_days = 0



# TODAY'S ORDER---------------------------------------------------------------------------------------------------------------------------------------------------------------------
today = date.today()
todays_order = OrderItem.objects.filter(order__placed_at__date = today).count()

if orders_last_5_days > 0:
    todays_order_vs_order_in_five_days = round(((todays_order - orders_last_5_days) / orders_last_5_days) * 100, 2)
else:
    todays_order_vs_order_in_five_days = 0



# 5 DAYS PRODUCTS--------------------------------------------------------------------------------------------------------------------------------------------------------------------
products_last_5_days = ProductColorImage.objects.filter(created_at__gte=five_days_ago).count()
total_products = ProductColorImage.objects.all().count()

if total_products > 0:
    increase_of_products_in_five_days = round((products_last_5_days / total_products) * 100, 2)
else:
    increase_of_products_in_five_days = 0




def get_data(request):
    data = {}
    if request.user.is_superuser:
        user = request.user
        data.update({
            'user' : user,
            'total_customers' : total_customers,
            'increase_of_customer_in_five_days' : increase_of_customer_in_five_days,
            'total_orders' : total_orders,
            'increase_of_order_in_five_days' : increase_of_order_in_five_days,
            'today' : today,
            'todays_order' : todays_order,
            'todays_order_vs_order_in_five_days' : todays_order_vs_order_in_five_days,
            'total_products' : total_products,
            'products_last_5_days' : products_last_5_days,
            'increase_of_products_in_five_days' : increase_of_products_in_five_days,
        })
        
    return data




# ---------------------------------------------------------------- ADMIN LOGIN FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------



# ADMIN LOGIN PAGE
@never_cache
def admin_login_page(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    else:
        return render(request, 'admin_login.html')
    
    
# ADMIN LOGIN CREDENTIALS CHECKING FUNCTION
@never_cache
def admin_check_login(request):
    try:
        if request.method == 'POST':
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None and user.is_superuser:
                auth.login(request, user)
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Invalid credentials, please try logging in again.')
                return redirect('admin_login_page')
    except Exception:
        return redirect('admin_login_page')
    



# ADMIN DASHBOARD PAGE
@never_cache
def admin_dashboard(request):
    if request.user.is_superuser:
        context = {}
        
        collect_data = get_data(request)
        context.update({**collect_data, 'is_active_dashboard': is_active_dashboard})
        
        return render(request, 'admin_index.html', context)
    else:
        return redirect('admin_login_page')





# ADMIN LOGOUT FUNCTION

@never_cache     
def admin_logout(request):
    if request.method == 'POST' :
        auth.logout(request)
        messages.info(request, 'Login again!')
        return redirect('admin_login_page')
    else:
        return redirect('admin_login_page')

 



# PAGE NOT FOUND   

@never_cache
def page_not_found(request):
    if request.user.is_superuser:
        return redirect('admin_login_page')
    else:
        return render(request, 'pages/samples/error-404.html')




# ---------------------------------------------------------------- ADMIN CUSTOMER PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------




# CUSTOMER SHOW FUNCTION

@never_cache
def admin_customers(request):
    if request.user.is_superuser:
        user_list = User.objects.all().order_by('username').values()
        customer_list = Customer.objects.all().order_by('user__first_name').values()
        return render(request, 'pages/customers/customers.html',{'user_list' : user_list, 'customer_list' : customer_list, 'is_active_customer' : is_active_customer})
    else:
        return redirect('admin_login_page')
        
        
        
 
 
# BLOCK CUSTOMER FUNCTION    

@never_cache       
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
        return redirect('admin_login_page')
    





# UNBLOCK CUSTOMER FUNCTION

@never_cache
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
        return redirect('admin_login_page')
        
        
        


# SEARCH CUSTOMER FUNCTION    

@never_cache
def search_user(request):
    if request.user.is_superuser:
        query = request.GET.get('query', '')
        
        if query:
             user_list = User.objects.filter(username__icontains = query)
        else:
            user_list = User.objects.all().order_by('username').values()
        
        return render(request,'pages/customers/customers.html' ,{'user_list' : user_list, 'is_active_customer' : is_active_customer})
    else:
        return redirect('admin_login_page')
    
    
    


# ---------------------------------------------------------------- ADMIN CATEGORIES PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------
    
    
    
    
# CATEGORIES PAGES FUNCTION

@never_cache
def admin_categories(request):
    if request.user.is_superuser:
        category_list = Category.objects.filter(is_deleted = False).order_by('name').values()
        return render(request, 'pages/category/category.html', {'category_list' : category_list, 'is_active_category' : is_active_category})
    else:
        return redirect('admin_login_page')
    
    
    
    
    
# ADD CATEGORY PAGE FUNCTION   

@never_cache
def admin_add_category_page(request):
    if request.user.is_superuser:
        return render(request, 'pages/category/add_category_page.html', { 'is_active_category' : is_active_category })
    else:
        return redirect('admin_login_page')
    
    
    
    

# ADD CATEGORY FUNCTION 

@never_cache
def add_categories(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            name = request.POST['category_name']
            description = request.POST['category_description']
            
            if not Category.objects.filter(name__icontains = name, is_deleted = False).exists():
                category = Category.objects.create(name = name, description = description)
                category.save()
                messages.success(request, 'New category was added!')
                return redirect(admin_categories)
            else:
                messages.error(request, 'Category already exists, create new category')
                return redirect(admin_add_category_page)
    else:
        return redirect('admin_login_page')
    


# EDIT BRAND PAGE FUNCTION 

@never_cache
def edit_category_page(request, cat_id):
    if request.user.is_superuser:
        category = Category.objects.get(pk = cat_id)
        return render(request, 'pages/category/edit_category.html', {'category' : category,'countries' : countries, 'is_active_category' : is_active_category })
    else:
        return redirect('admin_login_page') 


# EDIT CATEGORIES FUNCTION   

@never_cache
def edit_category(request, cat_id):
    if request.user.is_superuser:
        if request.method == 'POST':
            name = request.POST['category_name']
            description = request.POST['category_description']
            
            category = Category.objects.get(id = cat_id)
            
            if not Category.objects.filter(name__icontains = name).exists():
                category.name = name
                category.description = description
                category.save()
                messages.success(request, 'Category updated successfully!')
                return redirect(admin_categories)
            else:
                messages.error(request, 'Category already exits, add new category')
                return redirect(edit_category_page)
    else:
        return redirect('admin_login_page') 



# DELETE CATEGORY FUNCTION 

@never_cache    
def delete_category(request, cat_id):
    if request.user.is_superuser:
        if cat_id:
            category_to_delete = Category.objects.get(id = cat_id)
            category_to_delete.is_deleted = True
            category_to_delete.save()
            messages.success(request, 'Category has been deleted!')
            return redirect(admin_categories)
        else:
            messages.error(request, 'id cannot be found!')
            return redirect(admin_categories)
    else:
        return redirect('admin_login_page')
    
    


   
# LIST CATEGORY FUNCTION 

@never_cache   
def list_category(request, cat_id):
    if request.user.is_superuser:
        if cat_id:
            category_to_list = Category.objects.get(id = cat_id)
            category_to_list.is_listed = True
            category_to_list.save()
            messages.success(request, 'Category updated successfully!')
            return redirect(admin_categories)
        else:
            messages.error(request, 'id cannot be found!')
            return redirect(admin_categories)
    else:
        return redirect('admin_login_page')




# UNLIST CATEGORY FUNCTION

@never_cache
def un_list_category(request, cat_id):
    if request.user.is_superuser:
        if cat_id:
            category_to_list = Category.objects.get(id = cat_id)
            category_to_list.is_listed = False
            category_to_list.save()
            messages.success(request, 'Category updated successfully!')
            return redirect(admin_categories)
        else:
            messages.error(request, 'id cannot be found!')
            return redirect(admin_categories)
    else:
        return redirect('admin_login_page')
    
    
    
    
    
# DELETED CATEGORIES VIEW PAGE FUNCTION

@never_cache
def deleted_cat_view(request):
    if request.user.is_superuser:
        category_list = Category.objects.filter(is_deleted = True).order_by('name').values()
        return render(request, 'pages/category/deleted_categories.html', {'category_list' : category_list, 'is_active_category' : is_active_category })
    else:
        return redirect('admin_login_page')
    
    


# RESTORE CATEGORIES FUNCTION

@never_cache
def restore_categories(request, cat_id):
    if request.user.is_superuser:
        if cat_id:
            category_to_restore = Category.objects.get(id = cat_id)
            category_to_restore.is_deleted = False
            category_to_restore.save()
            messages.success(request, 'Category have been restored successfully!')
            return redirect(deleted_cat_view)
        else:
            messages.error(request, ' id cannot be found!')
            return redirect(deleted_cat_view)
    else:
        return redirect('admin_login_page')
    
    

# ---------------------------------------------------------------- ADMIN PRODUCT PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------
   


# PRODUCTS VIEW PAGE FUNCTION

@never_cache
def list_product_page(request):
    if request.user.is_superuser:
        product_color = ProductColorImage.objects.filter(is_deleted=False).prefetch_related('productsize_set').annotate(total_quantity=Sum('productsize__quantity'))
        return render(request, 'pages/products/product.html', {'product_color': product_color, 'is_active_product' : is_active_product})
    else:
        return redirect('admin_login_page')



@never_cache
def get_quantity(request, size):
    try:
        quantity = ProductSize.objects.get(size=size).quantity
        return JsonResponse({'quantity': quantity})
    except ProductSize.DoesNotExist:
        return JsonResponse({'quantity': 'Size not found'})


# ADD PRODUCT PAGE FUNCTION

@never_cache
def admin_add_product(request):
    if request.user.is_superuser:
        brand_list = Brand.objects.all().order_by('name').values()
        category_list = Category.objects.all().order_by('name').values()
        return render(request, 'pages/products/add_products.html', {'brand_list' : brand_list, 'category_list' : category_list, 'is_active_product' : is_active_product})
    else:
        return redirect('admin_login_page')



# ADD PRODUCT FUNCTION

@never_cache
def add_products(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            name = request.POST.get('product_name')
            description = request.POST.get('description')
            information = request.POST.get('information')
            type = request.POST.get('type')
            category_id = request.POST.get('category')
            brand_id = request.POST.get('brand')

            category = Category.objects.get(pk = category_id)
            brand = Brand.objects.get(pk = brand_id)
            
            if Products.objects.filter(name__icontains=name).exists():
                messages.error(request, 'Product already exists!')
                return redirect(admin_add_product)
            else:
                product = Products.objects.create(
                    name=name,
                    description=description,
                    information= information,
                    type=type,
                    category=category,
                    brand=brand,
                )
                product.save()
                messages.success(request, 'New Product was created, Add product image')
                return redirect(admin_add_image_page)

    else:
        return redirect('admin_login_page')
    
    
    

# EDIT PRODUCT VIEW PAGE FUNCTION

@never_cache
def edit_product_page(request, p_id):
    if request.user.is_superuser:
        try:
            product_color_image = ProductColorImage.objects.get(id=p_id)
            product = product_color_image.products
            product_sizes = ProductSize.objects.filter(product_color_image=product_color_image)
        except (ProductColorImage.DoesNotExist):
            return HttpResponse("One or more objects do not exist.", status=404)
        
        category_list = Category.objects.all()
        brand_list = Brand.objects.all()
        
        context = {
            'category_list': category_list,
            'brand_list': brand_list,
            'product': product,
            'product_color_image': product_color_image,
            'product_sizes': product_sizes,
            'is_active_product' : is_active_product,
        }
        return render(request, 'pages/products/edit_product.html', context)
    else:
        return redirect('admin_login_page')








# EDIT PRODUCT VIEW FUNCTION

@never_cache
def edit_product_update(request, p_id):
    if request.user.is_superuser:
        if request.method == 'POST':
            name = request.POST.get('product_name')
            description = request.POST.get('description')
            information = request.POST.get('information')
            category_id = request.POST.get('category')
            brand_id = request.POST.get('brand')
            
            
            product = Products.objects.get(pk=p_id)
            category = Category.objects.get(pk=category_id)
            brand = Brand.objects.get(pk=brand_id)
            
            product.name = name
            product.description = description
            product.information = information
            product.category = category
            product.brand = brand
            
            product.save()
            
            messages.success(request, 'Product Updated successfully!')
            return redirect(list_product_page)
    else:
        return redirect('admin_login_page')

            


# DELETED PRODUCTS VIEW PAGE FUNCTION   

@never_cache
def deleted_product_page(request):
    if request.user.is_superuser:
        deleted_product_colors = ProductColorImage.objects.filter(is_deleted=True).select_related('products__category', 'products__brand').annotate(total_quantity=Sum('productsize__quantity'))
        return render(request, 'pages/products/deleted_products.html', {'product_colors': deleted_product_colors, 'is_active_product' : is_active_product})
    else:
        return redirect('admin_login_page')

    

    
# RESTORE PRODUCT FUNCTION

@never_cache
def restore_product(request, pdt_id):
    if request.user.is_superuser:
        if pdt_id:
            product_to_delete = ProductColorImage.objects.get(pk=pdt_id)
            product_to_delete.is_deleted = False
            product_to_delete.save()
            messages.success(request, 'Product have been restored!')
            return redirect(list_product_page)
        else:
            messages.error()
    else:
        return redirect('admin_login_page')
        






# ---------------------------------------------------------------- ADMIN EDIT PRODUCT COLOR & IMAGE PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------


# EDIT PRODUCT COLOR PAGE VIEW FUNCTION

@never_cache
def edit_product_color_page(request, p_id):
    if request.user.is_superuser:
        try:
            product_color_image = ProductColorImage.objects.get(id=p_id)
            product = product_color_image.products
            product_sizes = ProductSize.objects.filter(product_color_image=product_color_image)
        except (ProductColorImage.DoesNotExist):
            return HttpResponse("One or more objects do not exist.", status=404)
        
        category_list = Category.objects.all()
        brand_list = Brand.objects.all()
        
        context = {
            'category_list': category_list,
            'brand_list': brand_list,
            'product': product,
            'product_color_image': product_color_image,
            'product_sizes': product_sizes,
            'is_active_product' : is_active_product
        }
        return render(request, 'pages/products/edit_product_color.html', context)
    else:
        return redirect('admin_login_page')



# EDIT PRODUCT COLOR FUNCTION

@never_cache
def edit_product_color(request, p_id):
    if request.user.is_superuser:
        product_color_image = ProductColorImage.objects.get(pk=p_id)
        if request.method == 'POST':
            color = request.POST.get('color')
            price = request.POST.get('price')
            main_image = request.FILES.get('main_image')
            side_image = request.FILES.get('side_image')
            top_image = request.FILES.get('top_image')
            back_image = request.FILES.get('back_image')
            
            product_color_image.color = color
            product_color_image.price = price
            
            if main_image:
                product_color_image.main_image = main_image
            if side_image:
                product_color_image.side_image = side_image
            if top_image:
                product_color_image.top_image = top_image
            if back_image:
                product_color_image.back_image = back_image
                
            product_color_image.save()
            
            messages.success(request, 'Product color & images have been updated successfully')
            return redirect(list_product_page)
        else:
            return render(request, 'edit_product_color.html', {'product_color_image': product_color_image , 'is_active_product' : is_active_product})
    else:
        return redirect(admin_login_page)



# For list_product function

@never_cache
def list_product(request, pdt_id):
    if request.user.is_superuser:
        if pdt_id:
            product_to_list = ProductColorImage.objects.get(pk=pdt_id)
            if product_to_list.products.brand.is_listed and product_to_list.products.category.is_listed:
                product_to_list.is_listed = True
                product_to_list.save()
                messages.success(request, 'Product updated successfully!')
            else:
                if product_to_list.products.brand.is_listed == False and product_to_list.products.category.is_listed == False:
                    messages.error(request, 'Cannot list product: Brand and Category is not listed.')
                elif product_to_list.products.brand.is_listed == False:
                    messages.error(request, 'Cannot list product: Brand is not listed.')
                else:
                    messages.error(request, 'Cannot list product: Category is not listed.')
            return redirect(list_product_page)
        else:
            messages.error(request, 'ID cannot be found.')
            return redirect(list_product_page)
    else:
        return redirect(admin_login_page)


# For un_list_product function

@never_cache
def un_list_product(request, pdt_id):
    if request.user.is_superuser:
        if pdt_id:
            product_to_un_list = ProductColorImage.objects.get(pk=pdt_id)
            product_to_un_list.is_listed = False
            product_to_un_list.save()
            messages.success(request, 'Product updated successfully!')
            return redirect(list_product_page)
        else:
            messages.error(request, 'id cannot be found.')
            return redirect(list_product_page)
    else:
        return redirect(admin_login_page)
    
    

# DELETE PRODUCT FUNCTION

@never_cache
def delete_product(request, pdt_id):
    if request.user.is_superuser:
        if pdt_id:
            product_to_delete = ProductColorImage.objects.get(pk=pdt_id)
            product_to_delete.is_deleted = True
            product_to_delete.save()
            messages.success(request, 'Product have been deleted!')
            return redirect(list_product_page)
        else:
            messages.error()
    else:
        return redirect('admin_login_page')



# ---------------------------------------------------------------- ADMIN EDIT PRODUCT SIZE PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------


# EDIT PRODUCT SIZE PAGE VIEW FUNCTION

@never_cache
def edit_product_size_page(request, p_id):
    if request.user.is_superuser:
        try:
            product_color_image = ProductColorImage.objects.get(id=p_id)
            product = product_color_image.products
            product_sizes = ProductSize.objects.filter(product_color_image=product_color_image)
        except (ProductColorImage.DoesNotExist):
            return HttpResponse("One or more objects do not exist.", status=404)
        
        category_list = Category.objects.all()
        brand_list = Brand.objects.all()
        context = {
            'category_list': category_list,
            'brand_list': brand_list,
            'product': product,
            'product_color_image': product_color_image,
            'product_sizes': product_sizes
        }
        
        return render(request, 'pages/products/edit_variant_page.html', context)
    else:
        return redirect('admin_login_page')
        


# EDIT PRODUCT SIZE FUNCTION

@never_cache
def edit_product_size(request, p_id):
    if request.user.is_superuser:
        if request.method == 'POST':
            size = request.POST.get('product_size')
            quantity = request.POST.get('product_quantity')
            
            product_size = ProductSize.objects.get(pk=p_id)
            
            if size and quantity:
                product_size.size = size
                product_size.quantity = quantity
                product_size.save()
                
                messages.success(request, 'Product sizes & quantity updated')
                return redirect(list_product_page)
            else:
                messages.error(request, 'Size or quantity is empty')
                return redirect('edit_product_size', p_id=p_id)
    else:
        return redirect(admin_login_page)



# ---------------------------------------------------------------- ADMIN ADD PRODUCT IMAGE PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------


# ADD PRODUCT IMAGE PAGE VIEW FUNCTION

@never_cache
def admin_add_image_page(request):
    if request.user.is_superuser:
        product_list = Products.objects.all()
        return render(request, 'pages/products/add_product_image.html', {'product_list' : product_list, 'is_active_product' : is_active_product})
    else:
        return redirect(admin_login_page)



# ADD PRODUCT IMAGE FUNCTION

@never_cache
def add_product_image(request):
    if request.user.is_superuser:
        if request.method == 'POST':
                products_id = request.POST.get('product')
                color = request.POST.get('color')
                price = request.POST.get('price')
                main_image = request.FILES.get('main_image')
                side_image = request.FILES.get('side_image')
                top_image = request.FILES.get('top_image')
                back_image = request.FILES.get('back_image')
                
                products = Products.objects.get(pk = products_id)
                existing_color = ProductColorImage.objects.filter(products=products, color=color).exists()
                if existing_color:
                    messages.error(request, f"A product image with the color '{color}' already exists for this product.")
                    return redirect('admin_add_image_page')
                else:
                    product_color_image = ProductColorImage.objects.create(
                        color = color,
                        price = price,
                        main_image = main_image,
                        side_image = side_image,
                        top_image = top_image,
                        back_image = back_image,
                        products = products
                        )
                    product_color_image.save()
                    messages.success(request, "Product Color and Image was added, now add product size")
                    return redirect(admin_add_variants)
        else:
            return redirect(admin_add_image_page)
    else:
        return redirect('admin_login_page')               
                

# ---------------------------------------------------------------- ADMIN PRODUCT VARIANTS PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------



adult_sizes = [6, 7, 8, 9, 10, 11, 12]
kids_sizes = ['8C', '9C', '10C', '11C', '12C', '13C']

# PRODUCT SIZE ADD PAGE VIEW PAGE FUNCTION

@never_cache
def admin_add_variants(request):
    if request.user.is_superuser:
        sizes = adult_sizes
        products = Products.objects.all().order_by('name')
        product_color = ProductColorImage.objects.all().order_by('color')
        return render(request, 'pages/products/add_product_variant.html', {'products': products, 'product_color' : product_color, 'sizes': sizes, 'is_active_product' : is_active_product})
    else:
        return redirect(admin_login_page)


# GET COLOR FUNCTION

@never_cache
def get_colors(request):
    if request.user.is_superuser:
        if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            product_id = request.GET.get('product_id')
            if product_id:
                colors = ProductColorImage.objects.filter(products_id=product_id).order_by('color').values('id', 'color')
                return JsonResponse({'colors': list(colors)})
        return JsonResponse({}, status=400)




# GET SIZES FUNCTION

@never_cache
@require_GET
def get_sizes_view(request):
    if request.user.is_superuser:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            product_id = request.GET.get('product_id')
            if product_id:
                try:
                    product = Products.objects.get(pk=product_id)
                    if product.category.name.lower() == "kid's":
                        sizes = ['8C', '9C', '10C', '11C', '12C', '13C']
                    else:
                        sizes = ['6', '7', '8', '9', '10', '11', '12']
                    return JsonResponse({'sizes': sizes})
                except Products.DoesNotExist:
                    pass
            return JsonResponse({'error': 'Invalid request'}, status=400)



# ADD PRODUCT SIZE FUNCTION

@never_cache
def add_size(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            product_id = request.POST.get('product')
            color_id = request.POST.get('color')
            size = request.POST.get('size')
            quantity = request.POST.get('quantity')
            
            product_color_image = ProductColorImage.objects.get(pk=color_id)
            
            existing_size = ProductSize.objects.filter(product_color_image=product_color_image, size=size).exists()
            
            if existing_size:
                messages.error(request, 'This size is already added')
                return redirect('admin_add_variants')
            else:
                product_size = ProductSize.objects.create(
                product_color_image=product_color_image,
                size=size,
                quantity=quantity
                )                
                product_size.save()
                messages.success(request, 'Added size to the product')
                return redirect(list_product_page)
        else:
            return redirect('admin_add_variants')
    else:
        return redirect('admin_login_page')

            
            
# ---------------------------------------------------------------- ADMIN BRAND PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------

# BRAND PAGE FUNCTION

@never_cache
def list_brand_page(request):
    if request.user.is_superuser:
        brand_list = Brand.objects.filter(is_deleted = False).order_by('name').values()
        return render(request, 'pages/brands/brand.html', {'brand_list' : brand_list, 'is_active_brand' : is_active_brand})
    else:
        return redirect('admin_login_page')


countries = [
    "Select a country", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", 
    "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", 
    "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", 
    "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", 
    "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", 
    "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", 
    "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", 
    "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", 
    "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini (fmr. 'Swaziland')", 
    "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", 
    "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", 
    "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", 
    "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", 
    "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", 
    "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", 
    "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", 
    "Mozambique", "Myanmar (formerly Burma)", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", 
    "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia (formerly Macedonia)", "Norway", 
    "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", 
    "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", 
    "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", 
    "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", 
    "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", 
    "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", 
    "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", 
    "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", 
    "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
    ]

        
        
# ADD BRAND PAGE FUNCTION

@never_cache
def admin_add_brand(request):
    if request.user.is_superuser:
        return render(request, 'pages/brands/add_brand.html', {'countries' : countries, 'is_active_brand' : is_active_brand})
    else:
        return redirect('admin_login_page')



# ADD BRAND FUNCTION

@never_cache
def add_brand(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            name = request.POST['name']
            country_of_origin = request.POST['country_of_origin']
            manufacturer_details = request.POST['manufacturer_details']
            
            
            
            if not Brand.objects.filter(name__icontains = name).exists():
                brand = Brand.objects.create(
                name = name,
                country_of_origin = country_of_origin,
                manufacturer_details = manufacturer_details,
                )
                brand.save()
                messages.success(request, 'New brand added!')
                return redirect(list_brand_page)
            else:
                messages.error(request, 'Brand already exits, add new brand')
                return redirect(admin_add_brand)
    else:
        return redirect('admin_login_page')
    




# EDIT BRAND PAGE FUNCTION 

@never_cache
def edit_brand_page(request, brand_id):
    if request.user.is_superuser:
        brand = get_object_or_404(Brand, id=brand_id)
        selected_country = brand.country_of_origin if brand.country_of_origin in countries else None
        return render(request, 'pages/brands/edit_brand.html', {'brand': brand, 'countries': countries, 'selected_country': selected_country, 'is_active_brand' : is_active_brand})
    else:
        return redirect('admin_login_page')

    



# EDIT BRAND FUNCTION   

@never_cache
def edit_brand(request, brand_id):
    if request.user.is_superuser:
        if request.method == 'POST':
            name = request.POST['name']
            country_of_origin = request.POST['country_of_origin']
            manufacturer_details = request.POST['manufacturer_details']
            
            brand = Brand.objects.get(id = brand_id)
            brand.name = name
            brand.country_of_origin = country_of_origin
            brand.manufacturer_details = manufacturer_details
            brand.save()
            messages.success(request, 'Brand updated successfully!')
            return redirect(list_brand_page)
    else:
        return redirect('admin_login_page')
            
            


# DELETE BRAND FUNCTION

@never_cache
def delete_brand(request, brand_id):
    if request.user.is_superuser:
        if brand_id:
            brand_to_delete = Brand.objects.get(id = brand_id)
            brand_to_delete.is_deleted = True
            brand_to_delete.save()
            messages.success(request, 'Brand has been deleted!')
            return redirect(list_brand_page)
        else:
            messages.error(request, 'id cannot be found!')
            return redirect(list_brand_page)
    else:
        return redirect('admin_login_page')
    


#  RESTORE BRAND FUNCTION

@never_cache
def restore_brand(request, brand_id):
    if request.user.is_superuser:
        if brand_id:
            brand_to_restore = Brand.objects.get(id = brand_id)
            brand_to_restore.is_deleted = False
            brand_to_restore.save()
            messages.success(request, 'Brand has been restored!')
            return redirect(list_brand_page)
        else:
            messages.error(request, 'id cannot be found!')
            return redirect(list_brand_page)
    else:
        return redirect('admin_login_page')
    
    

#  DELETED BRAND VIEW PAGE

@never_cache
def deleted_brand_view(request):
    if request.user.is_superuser:
        brand_list = Brand.objects.filter(is_deleted = True).order_by('name').values()
        return render(request, 'pages/brands/deleted_brand.html', {'brand_list' : brand_list, 'is_active_brand' : is_active_brand})
    else:
        return redirect('admin_login_page')
    
    

    
# LIST BRAND FUNCTION

@never_cache
def list_the_brand(request, brand_id):
    if request.user.is_superuser:
        if brand_id:
            brand_to_list = Brand.objects.get(id = brand_id)
            brand_to_list.is_listed = True
            brand_to_list.save()
            messages.success(request, 'Brand updated successfully!')
            return redirect(list_brand_page)
        else:
            messages.error(request, 'id cannot be found!')
            return redirect(list_brand_page)
    else:
        return redirect('admin_login_page')
    
    
    
    

# UNLIST BRAND FUNCTION   

@never_cache
def un_list_the_brand(request, brand_id):
    if request.user.is_superuser:
        if brand_id:
            brand_to_un_list = Brand.objects.get(id = brand_id)
            brand_to_un_list.is_listed = False
            brand_to_un_list.save()
            messages.success(request, 'Brand updated successfully!')
            return redirect(list_brand_page)
        else:
            messages.error(request, 'id cannot be found!')
            return redirect(list_brand_page)
    else:
        return redirect('admin_login_page')
    




# ---------------------------------------------------------------- ADMIN ORDER PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------




@never_cache
def orders_view_page(request):
    if request.user.is_superuser:
        orders = Orders.objects.all().order_by('customer').values()
        order_item = OrderItem.objects.all().order_by('-order__placed_at')
        context = {
            'order_item' : order_item,
            'orders' : orders,
            'is_active_order' : is_active_order,
        }
        return render(request, 'pages/orders/orders_view_page.html', context)
    else:
        return redirect('admin_login_page')
    
    



@never_cache
def order_detailed_view(request, order_id):
    if request.user.is_superuser:
        order_item = OrderItem.objects.get(pk = order_id)
        context = {
            'is_active_order' : is_active_order,
            'order_item' : order_item,
        }
        return render(request, 'pages/orders/single order_view_page.html', context)
    else:
        return redirect('admin_login_page')
    
    




@never_cache
def change_order_status(request, order_id):
    if request.user.is_superuser:
        order_status = request.POST.get('order_status')
        order_item = OrderItem.objects.get(pk = order_id)
        
        if order_item:
            order_item.order_status = order_status
            order_item.save()
            
            today = date.today()
            
            if order_status == 'Delivered':
                order_item.delivery_date = today
                order_item.save()
            messages.success(request, 'Order Status Updated')
            return redirect('orders_view_page')
        
        
        
    else:
        return redirect('admin_login_page')
        
        
        
        



@never_cache
def return_product(request, order_items_id):
    if request.user.is_superuser:
        try:
            order_items = OrderItem.objects.get(pk = order_items_id)
            order_items.return_product = True
            order_items.order_status = 'Returned'
            order_items.save()
            return redirect('order_detailed_view', order_items_id)
        except Exception as e:
            return redirect(admin_login_page)
    else:
        return redirect(admin_login_page)
    
    
    
    
    
    
    
# ----------------------------------------------------------------  SALES REPORT PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------
    


weekly_filter = False
monthly_filter = False
yearly_filter = False
custom_date_filter = False

current_date = timezone.now()
start_date = current_date - timedelta(days=current_date.weekday())
end_date = start_date + timedelta(days=6)

now = timezone.now()
current_year_and_month = now.strftime("%Y-%m")
first_day_of_month = None
last_day_of_month = None

current_year = now.strftime("%Y")
custom_start_date = None
custom_end_date = None

@never_cache
def sales_report_filtering(request):
    if request.user.is_superuser:
        global weekly_filter, monthly_filter, yearly_filter, custom_date_filter, current_year_and_month, current_year, custom_start_date, custom_end_date, first_day_of_month, last_day_of_month
        if request.method == 'POST':
            filter = request.POST.get('filter')
            
            if filter == "weekly":
                weekly_filter = True
                
                monthly_filter = False
                yearly_filter = False
                custom_date_filter = False
                
            elif filter == 'monthly':
                monthly_filter = True
                
                weekly_filter = False
                yearly_filter = False
                custom_date_filter = False
                
                current_year_and_month = request.POST.get('year_month')
                year, month = map(int, current_year_and_month.split('-'))
                
                first_day_of_month = timezone.datetime(year, month, 1).replace(hour=0, minute=0, second=0, microsecond=0)
                last_day_of_month = timezone.datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59, 999999)
                
            elif filter == 'yearly':
                yearly_filter = True
                
                weekly_filter = False
                monthly_filter = False
                custom_date_filter = False
                
                current_year = request.POST.get('year')
            elif filter == 'custom':
                custom_date_filter = True
                
                weekly_filter = False
                weekly_filter = False
                monthly_filter = False
                
                
                custom_start_date = request.POST.get('start_date')
                custom_end_date = request.POST.get('end_date')
                
            return redirect('sales_report_page')
    else:
        return redirect('admin_login_page')
                
                
                

    

@never_cache
def sales_report_page(request):
    if request.user.is_superuser:
        global weekly_filter, monthly_filter, yearly_filter, custom_date_filter, current_year_and_month, current_year, custom_start_date, custom_end_date, first_day_of_month, last_day_of_month

        
        today = timezone.now().date()
        
        sales_data = OrderItem.objects.filter(
            Q(cancel_product=False) & 
            Q(return_product=False) & 
            Q(order_status='Delivered') & 
            Q(order__placed_at__date = today)
        )
        
        if weekly_filter:
            sales_data = OrderItem.objects.filter(
                Q(cancel_product=False) & 
                Q(return_product=False) & 
                Q(order_status='Delivered') & 
                Q(order__placed_at__range=(start_date, end_date))
            )
            
        if monthly_filter:
            sales_data = OrderItem.objects.filter(
                Q(cancel_product=False) & 
                Q(return_product=False) & 
                Q(order_status='Delivered') & 
                Q(order__placed_at__range=(first_day_of_month, last_day_of_month))
            )
            
        
        overall_sales_count = sales_data.count()
        overall_order_amount = sales_data.aggregate(total_amount=Sum('total_price'))['total_amount'] if sales_data else 0
        overall_discount = sales_data.aggregate(total_discount=Sum('order__discount_price'))['total_discount'] if sales_data else 0
        
        
        context = {
            'sales_data': sales_data,
            'is_active_sales': is_active_sales,
            'overall_sales_count': overall_sales_count,
            'overall_order_amount': overall_order_amount,
            'overall_discount': overall_discount,
        }
        
        if request.method == 'POST':
            if 'sales_report' in request.POST and request.POST['sales_report'] == 'pdf':
                buffer = BytesIO()


                doc = SimpleDocTemplate(buffer, pagesize=letter)

                
                styles = getSampleStyleSheet()
                centered_style = ParagraphStyle(name='Centered', parent=styles['Heading1'], alignment=1)

                
                today_date = datetime.datetime.now().strftime("%Y-%m-%d")

                
                content = []

                
                company_details = f"<b>SneakerHeads</b><br/>Email: sneakerheadsweb@email.com<br/>Date: {today_date}"
                content.append(Paragraph(company_details, styles['Normal']))
                content.append(Spacer(1, 0.5 * inch))

                content.append(Paragraph("<b>Sales Report</b>", centered_style))
                content.append(Spacer(1, 0.5 * inch))

                data = [["Product", "Quantity", "Price", "Total Price", "Date"]]
                for sale in sales_data:
                    formatted_date = sale.order.placed_at.strftime("%a, %d %b %Y")
                    data.append([sale.product, sale.quantity, sale.each_price, sale.total_price, formatted_date])

                table = Table(data, repeatRows=1)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('TOPPADDING', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))

                content.append(table)

                content.append(Spacer(1, 0.5 * inch))

                overall_sales_count_text = f"<b>Overall Sales Count:</b> {overall_sales_count}"
                overall_order_amount_text = f"<b>Overall Order Amount:</b> {overall_order_amount}"
                overall_discount_amount_text = f"<b>Overall Discount:</b> {overall_discount}"
                
                content.append(Paragraph(overall_sales_count_text, styles['Normal']))
                content.append(Paragraph(overall_order_amount_text, styles['Normal']))
                content.append(Paragraph(overall_discount_amount_text, styles['Normal']))

                doc.build(content)

                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
                file_name = f"Sales_Report_{current_time}.pdf"

                response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{file_name}"'

                return response
            
            
            elif 'sales_report' in request.POST and request.POST['sales_report'] == 'excel':
                output = BytesIO()
                workbook = xlsxwriter.Workbook(output, {'in_memory': True})
                worksheet = workbook.add_worksheet('Sales Report')
                
                headings = ["Product", "Color", "Quantity", "Price", "Total Price", "Date", "Size"]
                for col, heading in enumerate(headings):
                    worksheet.write(0, col, heading)
                
                for row, sale in enumerate(sales_data, start=1):
                    formatted_date = sale.order.placed_at.strftime("%a, %d %b %Y")
                    color = sale.product.product_color_image.color
                    size = sale.product.size
                    
                    worksheet.write(row, 0, sale.product.product_color_image.products.name)
                    worksheet.write(row, 1, color)
                    worksheet.write(row, 2, sale.quantity)
                    worksheet.write(row, 3, sale.each_price)
                    worksheet.write(row, 4, sale.total_price)
                    worksheet.write(row, 5, formatted_date)
                    worksheet.write(row, 6, size)
                
                overall_row = len(sales_data) + 2
                worksheet.write(overall_row, 0, "Overall Sales Count:")
                worksheet.write(overall_row, 1, overall_sales_count)
                worksheet.write(overall_row + 1, 0, "Overall Order Amount:")
                worksheet.write(overall_row + 1, 1, overall_order_amount)
                worksheet.write(overall_row + 2, 0, "Overall Discount:")
                worksheet.write(overall_row + 2, 1, overall_discount)
                
                for i, heading in enumerate(headings):
                    max_length = max([len(str(getattr(row, heading.lower(), ""))) for row in sales_data] + [len(heading)])
                    worksheet.set_column(i, i, max_length + 2)
                
                date_width = max([len(sale.order.placed_at.strftime("%a, %d %b %Y")) for sale in sales_data])
                worksheet.set_column(5, 5, date_width + 2)
                color_width = max([len(color) for color in [sale.product.product_color_image.color for sale in sales_data]])
                worksheet.set_column(1, 1, color_width + 2)
                
                workbook.close()
                
                output.seek(0)
                response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
                file_name = f"Sales Report {current_time}.xlsx"
                response['Content-Disposition'] = f'attachment; filename="{file_name}"'
                
                return response

        
        return render(request, 'admin_sales_report.html', context)
    else:
        return redirect('admin_login_page')


        
        
    
    
# ---------------------------------------------------------------- PRODUCT OFFER MODULE PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------






@never_cache
@clear_old_messages
def product_offer_module_view(request):
    if request.user.is_superuser:
        product_offer = ProductOffer.objects.all().order_by('start_date', 'end_date')
        context = {
            'product_offer' : product_offer,
            'is_active_product_offer' : is_active_product_offer,
        }
        return render(request, 'pages/offers/product_offer_modules.html', context)
    else:
        return redirect('admin_login_page')
    
        

@never_cache
@clear_old_messages
def product_offer_edit_page(request, product_color_image_name, color):
    if request.user.is_superuser:
        try:
            product_offer = ProductOffer.objects.get(product_color_image__products__name = product_color_image_name, product_color_image__color = color)
            product_color = ProductColorImage.objects.all()
            context = {
                'product_offer' : product_offer,
                'product_color' : product_color,
                'is_active_product_offer' : is_active_product_offer,
            }
            return render(request, 'pages/offers/product_offer_edit_page.html', context)
        except ProductOffer.DoesNotExist:
            messages.error(request, 'Product Offer is not found')
        return redirect(product_offer_module_view)
    else:
        return redirect('admin_login_page')
        
        
        




@never_cache
@clear_old_messages
def product_offer_update(request, product_offer_id):
    if request.user.is_superuser:
        try:
            product_offer = ProductOffer.objects.get(pk=product_offer_id)
            
            if request.method == 'POST':
                discount_percentage_str = request.POST.get('offer_discount')
                start_date_str = request.POST.get('offer_start_date')
                end_date_str = request.POST.get('offer_end_date')
                
                valid_product = True
                valid_discount_percentage = True
                valid_start_date = True
                valid_end_date = True
                
                
                today = timezone.now().date()
                offer_start_date = product_offer.start_date
                
                
                if discount_percentage_str and start_date_str and end_date_str:
                    try:
                        discount_percentage = int(discount_percentage_str)
                    except ValueError:
                        messages.error(request, 'Discount percentage should be a number without decimals or symbols.')
                        return redirect('product_offer_edit_page', product_offer.product_color_image.products.name, product_offer.product_color_image.color)
                    
                    try:
                        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        messages.error(request, 'Please enter the dates in the format YYYY-MM-DD.')
                        return redirect('product_offer_edit_page', product_offer.product_color_image.products.name, product_offer.product_color_image.color)
                    
                    
                    if not 5 <= discount_percentage <= 70:
                        valid_discount_percentage = False
                        messages.error(request, 'Discount percentage should be minimum of 5%, and maximum of 70%.')
                        
                        
                    elif start_date < today and start_date != offer_start_date:
                        valid_start_date = False
                        messages.error(request, "Please select today's date or a future date for the start date.")
                    
                    elif end_date <= start_date and end_date <= today:
                        valid_end_date = False
                        messages.error(request, "Please select a future date for the offer end date, ensuring it is greater than today's date and the start date.")
                        
                
                    try:
                        if valid_product and valid_discount_percentage and valid_start_date and valid_end_date:
                            product_offer.discount_percentage = discount_percentage
                            product_offer.start_date = start_date
                            product_offer.end_date = end_date
                            product_offer.save()
                                
                            messages.success(request, 'Product Offer Updated Successfully!')
                            return redirect('product_offer_module_view')
                    except:
                        messages.error(request, 'Currently unable to update the product offer, try again after sometime.')
                        return redirect('product_offer_edit_page', product_offer.product_color_image.products.name, product_offer.product_color_image.color)
                else:
                    messages.error(request, 'Please fill in all required fields.')
                    return redirect('product_offer_edit_page', product_offer.product_color_image.products.name, product_offer.product_color_image.color)
            else:
                return redirect('product_offer_module_view')
        except ProductOffer.DoesNotExist:
            messages.error(request, 'Product Offer not found.')
        return redirect('product_offer_edit_page', product_offer.product_color_image.products.name, product_offer.product_color_image.color)
    else:
        return redirect('admin_login_page')
        

    
    
    

@never_cache
@clear_old_messages   
def product_offer_add_page(request):
    if request.user.is_superuser:
        product_color = ProductColorImage.objects.all()
        context = {
            'product_color' : product_color,
            'is_active_product_offer' : is_active_product_offer,
        }
        return render(request, 'pages/offers/product_offer_add_page.html', context)
    else:
        return redirect('admin_login_page')
    
    
    
@never_cache
@clear_old_messages   
def add_product_offer(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            product_color_image_id = request.POST.get('offer_name')
            discount_percentage_str = request.POST.get('offer_discount')
            end_date_str = request.POST.get('offer_end_date')
            
            
            valid_product = True
            valid_discount_percentage = True
            valid_end_date = True
            
            
            today = timezone.now().date()
            
            
            if product_color_image_id and discount_percentage_str and end_date_str:
                try:
                    discount_percentage = int(discount_percentage_str)
                except ValueError:
                    messages.error(request, 'Discount percentage should be a number without decimals or symbols.')
                    return redirect('product_offer_add_page')
                try:
                    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
                except ValueError:
                        messages.error(request, 'Please enter the dates in the format YYYY-MM-DD.')
                        return redirect('product_offer_add_page')
                try:
                    product_color_image = ProductColorImage.objects.get(pk=product_color_image_id)
                    
                    if ProductOffer.objects.filter(product_color_image = product_color_image).exists():
                        valid_product = False
                        messages.error(request, 'Product already have an offer')
                    
                    elif not 5 <= discount_percentage <= 70:
                        valid_discount_percentage = False
                        messages.error(request, 'Discount percentage should be minimum of 5%, and maximum of 70%')
                        
                    elif end_date <= today:
                        valid_end_date = False
                        messages.error(request, 'Please select a future date for the offer end date.')
                       
                    
                    try:
                        if valid_product and valid_discount_percentage and valid_end_date:
                            ProductOffer.objects.create(
                                product_color_image=product_color_image,
                                discount_percentage=int(discount_percentage),
                                end_date=end_date
                            )
                            messages.success(request, 'Offer Module Added Successfully!')
                            return redirect('product_offer_module_view')
                    except:
                        messages.error(request, 'Unable to create a product offer at this moment,')
                        return redirect('product_offer_add_page')
                except ProductColorImage.DoesNotExist:
                    messages.error(request, 'Selected product not found')
            else:
                messages.error(request, 'Please fill in all required fields')
            return redirect(product_offer_add_page)
        else:
            return redirect('product_offer_add_page')
    else:
        return redirect('admin_login_page')
    
    
    
   
@never_cache
@clear_old_messages
def delete_offer(request, product_offer_id):
    if request.user.is_superuser:
        try:
            product_offer = ProductOffer.objects.get(pk = product_offer_id)
            product_offer.delete()
            messages.success(request, 'Product Offer have been successfully deleted!')
        except ProductOffer.DoesNotExist:
            messages.error(request, 'Product offer not found')
        return redirect('product_offer_module_view')
    else:
         return redirect('admin_login_page')
    
    
    
    
# ----------------------------------------------------------------  COUPON PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------




@never_cache
@clear_old_messages
def coupon_page_view(request):
    if request.user.is_superuser:
        coupons = Coupon.objects.all()
        context = {
            'coupons' : coupons,
            'is_active_coupon' : is_active_coupon
        }
        return render(request, 'pages/coupons/coupon.html', context)
    else:
        return redirect('admin_login_page')
    
    


@never_cache
@clear_old_messages
def add_coupon_page(request):
    if request.user.is_superuser:
        context = {
            'is_active_coupon' : is_active_coupon
        }
        return render(request, 'pages/coupons/add_coupon.html', context)
    else:
        return redirect('admin_login_page')
    
    
alphabets_pattern = re.compile("^[a-zA-z]+$")
    
@never_cache
@clear_old_messages
def add_coupon(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            name_str = request.POST.get('coupon_name')
            discount_percentage_str = request.POST.get('offer_discount')
            end_date_str = request.POST.get('offer_end_date')
            minimum_amount_str = request.POST.get('minimum_amount')
            maximum_amount_str = request.POST.get('maximum_amount')
            
            valid_coupon_name = True
            valid_discount_percentage = True
            valid_end_date = True
            valid_min_max = True
            
            today = timezone.now().date()
            
            if name_str and discount_percentage_str and end_date_str and minimum_amount_str and maximum_amount_str:
                
                
                if not alphabets_pattern.match(name_str):
                    valid_coupon_name = False
                    messages.error(request, 'Coupon name should contain only alphabetical characters & should not contain any spaces')
                    return redirect('add_coupon_page')
                
                name = name_str.upper()
                
                try:
                    discount_percentage = int(discount_percentage_str)
                except ValueError:
                    messages.error(request, 'Discount percentage should be a number without decimals or symbols.')
                    return redirect('add_coupon_page')
                
                try:
                    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
                except ValueError:
                    messages.error(request, 'Please enter the dates in the format YYYY-MM-DD.')
                    return redirect('add_coupon_page')
                
                
                try:
                    minimum_amount = int(minimum_amount_str)
                    maximum_amount = int(maximum_amount_str)
                except:
                    valid_min_max = False
                    messages.error(request, 'Minimum and Maximum amounts should be a number without decimals or symbols.')
                    return redirect('add_coupon_page')
                
                
                if not (2500 <= minimum_amount <= 35000 and 3000 <= maximum_amount <= 25000):
                    valid_min_max = False
                    messages.error(request, 'Both the minimum and maximum amounts should be between ₹2500 and ₹25000')
                    return redirect('add_coupon_page')
                
                
                elif maximum_amount <= minimum_amount:
                    valid_min_max = False
                    messages.error(request, 'Maximum amount should be greater than minimum amount.')
                
                
                elif not 5 <= discount_percentage <= 20:
                    valid_discount_percentage = False
                    messages.error(request, 'Discount percentage should be minimum of 5%, and maximum of 20%.')
                
                elif end_date <= today:
                    valid_end_date = False
                    messages.error(request, 'Please select a future date for the offer end date.')
                    
                
                try:
                    if valid_coupon_name and  valid_discount_percentage and valid_end_date and valid_min_max:
                        Coupon.objects.create(
                            name = name,
                            discount_percentage = discount_percentage,
                            end_date = end_date,
                            minimum_amount = minimum_amount,
                            maximum_amount = maximum_amount,
                        )
                        messages.success(request, 'Coupon Added Successfully')
                        return redirect('coupon_page_view')
                except:
                    messages.error(request, 'Unable to create a coupon at this moment, try after sometime.')
            else:
                messages.error(request, 'Please fill in all the required fields')
        return redirect('add_coupon_page')
    else:
        return redirect('admin_login_page')
    




@never_cache
@clear_old_messages
def coupon_edit_page(request, coupon_id):
    if request.user.is_superuser:
        try:
            coupon = Coupon.objects.get(pk=coupon_id)
            context = {
                'coupon': coupon,
            }
            return render(request, 'pages/coupons/coupon_edit_page.html', context)
        except Coupon.DoesNotExist:
            messages.error(request, 'Coupon not found')
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request, f'An error occurred: {e}')
            return redirect('admin_dashboard')
    else:
        return redirect('admin_login_page')








@never_cache
@clear_old_messages
def update_coupon(request, coupon_id):
    if request.user.is_superuser:
        try:
            coupon = Coupon.objects.get(pk=coupon_id)
        
            if request.method == 'POST':
                
                coupon_start_date = coupon.start_date

                name_str = request.POST.get('coupon_name')
                discount_percentage_str = request.POST.get('offer_discount')
                start_date_str = request.POST.get('offer_start_date')
                end_date_str = request.POST.get('offer_end_date')
                minimum_amount_str = request.POST.get('minimum_amount')
                maximum_amount_str = request.POST.get('maximum_amount')
                
                valid_name = True
                valid_discount_percentage = True
                valid_start_date = True
                valid_end_date = True
                valid_min_max = True
                
                today = timezone.now().date()
                
                if name_str and discount_percentage_str and end_date_str and minimum_amount_str and maximum_amount_str:
                
                    if not alphabets_pattern.match(name_str):
                        valid_name = False
                        messages.error(request, 'Coupon name should contain only alphabetical characters & should not contain any spaces')
                    
                    else:
                        name = name_str.upper()
                        
                        if  Coupon.objects.filter(name=name).exclude(pk=coupon_id).exists():
                            valid_name = False
                            messages.error(request, 'A coupon with the same name already exists. Please choose a different name.')
                        
                        try:
                            discount_percentage = int(discount_percentage_str)
                        except ValueError:
                            valid_discount_percentage = False
                            messages.error(request, 'Discount percentage should be a number without decimals or symbols.')
                        
                        try:
                            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
                        except ValueError:
                            valid_start_date = False
                            messages.error(request, 'Please enter the dates in the format YYYY-MM-DD.')
                        
                        try:
                            minimum_amount = int(minimum_amount_str)
                            maximum_amount = int(maximum_amount_str)
                        except:
                            valid_min_max = False
                            messages.error(request, 'Minimum and Maximum amounts should be a number without decimals or symbols.')
                            
                        if not 5 <= discount_percentage <= 20:
                            valid_discount_percentage = False
                            messages.error(request, 'Discount percentage should be minimum of 5%, and maximum of 20%.')
                        
                        elif start_date < today and start_date != coupon_start_date:
                            valid_start_date = False
                            messages.error(request, "Please select today's date or a future date for the start date.")
                        
                        elif end_date <= start_date or end_date <= today:
                            valid_end_date = False
                            messages.error(request, "Please select a future date for the offer end date, ensuring it is greater than today's date and the start date.")
                            
                        elif not (2500 <= minimum_amount <= 35000 and 3000 <= maximum_amount <= 25000):
                            valid_min_max = False
                            messages.error(request, 'Both the minimum and maximum amounts should be between ₹2500 and ₹25000')
                        
                        elif maximum_amount <= minimum_amount:
                            valid_min_max = False
                            messages.error(request, 'The maximum amount should be greater than the minimum amount.')
                        
                        
                        if valid_name and valid_discount_percentage and valid_start_date and valid_end_date and valid_min_max:
                            coupon.name = name
                            coupon.discount_percentage = discount_percentage
                            coupon.start_date = start_date
                            coupon.end_date = end_date
                            coupon.minimum_amount = minimum_amount
                            coupon.maximum_amount = maximum_amount
                            coupon.save()
                            
                            messages.success(request, 'Coupon has been updated successfully')
                            return redirect('coupon_page_view')
                else:
                    messages.error(request, 'Please fill in all required fields.')
                
            return redirect('coupon_edit_page', coupon_id)
        
        except Coupon.DoesNotExist:
            messages.error(request, 'Coupon is not found')
            return redirect('coupon_page_view')
    else:
        return redirect('admin_login_page')



@never_cache
@clear_old_messages
def delete_coupon(request, coupon_id):
    if request.user.is_superuser:
        try:
            coupon = Coupon.objects.get(coupon_code = coupon_id)
            coupon.delete()
            messages.success(request, 'Coupon have been deleted!')
        except Coupon.DoesNotExist:
            messages.error(request, 'Coupon not found.')
        return redirect('coupon_page_view')
    else:
        return redirect('admin_login_page')