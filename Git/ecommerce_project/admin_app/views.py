from django.shortcuts import render, redirect

from django.contrib.auth.models import User
from user_app.models import Customer
from admin_app.models import *

from django.contrib.auth import authenticate
from django.contrib import auth
from django.contrib import messages

from django.contrib.auth.decorators import login_required 
from django.views.decorators.cache import never_cache

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from django.shortcuts import get_object_or_404





# ADMIN LOGIN PAGE
def admin_login_page(request):
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
            return redirect('admin_login_page')
 
    return render(request, 'admin_login.html')





# ADMIN LOGOUT FUNCTION
@login_required
@never_cache     
def admin_logout(request):
    if request.method == 'POST' :
        auth.logout(request)
        messages.info(request, 'Login again!')
        return redirect('admin_login_page')
    else:
        return redirect('admin_login_page')

 



# PAGE NOT FOUND   
@login_required
@never_cache
def page_not_found(request):
    if request.user.is_superuser:
        return redirect('admin_login_page')
    else:
        return render(request, 'pages/samples/error-404.html')




# ---------------------------------------------------------------- ADMIN CUSTOMER PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------




# CUSTOMER SHOW FUNCTION
@login_required
@never_cache
def admin_customers(request):
    if request.user.is_superuser:
        user_list = User.objects.all().order_by('username').values()
        customer_list = Customer.objects.all().order_by('user__first_name').values()
        return render(request, 'pages/customers/customers.html',{'user_list' : user_list, 'customer_list' : customer_list})
    else:
        return redirect('admin_login_page')
        
        
        
 
 
# BLOCK CUSTOMER FUNCTION    
@login_required
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
@login_required
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
@login_required
@never_cache
def search_user(request):
    if request.user.is_superuser:
        query = request.GET.get('query', '')
        
        if query:
             user_list = User.objects.filter(username__icontains = query)
        else:
            user_list = User.objects.all().order_by('username').values()
        
        return render(request,'pages/customers/customers.html' ,{'user_list' : user_list})
    
    
    


# ---------------------------------------------------------------- ADMIN CATEGORIES PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------
    
    
    
    
# CATEGORIES PAGES FUNCTION
@login_required
@never_cache
def admin_categories(request):
    if request.user.is_superuser:
        category_list = Category.objects.filter(is_deleted = False).order_by('name').values()
        return render(request, 'pages/category/category.html', {'category_list' : category_list})
    else:
        return redirect('admin_login_page')
    
    
    
    
    
# ADD CATEGORY PAGE FUNCTION   
@login_required
@never_cache
def add_category_page(request):
    if request.user.is_superuser:
        return render(request, 'pages/category/add_category_page.html')
    else:
        return redirect('admin_login_page')
    
    
    
    

# ADD CATEGORY FUNCTION 
@login_required
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
                return redirect(add_category_page)
    else:
        return redirect('admin_login_page')
    


# EDIT BRAND PAGE FUNCTION 
@login_required
@never_cache
def edit_category_page(request, cat_id):
    if request.user.is_superuser:
        category = Category.objects.get(pk = cat_id)
        return render(request, 'pages/category/edit_category.html', {'category' : category,'countries' : countries})
    else:
        return redirect('admin_login_page') 


# EDIT CATEGORIES FUNCTION   
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
@never_cache
def deleted_cat_view(request):
    if request.user.is_superuser:
        category_list = Category.objects.filter(is_deleted = True).order_by('name').values()
        return render(request, 'pages/category/deleted_categories.html', {'category_list' : category_list})
    else:
        return redirect('admin_login_page')
    
    


# RESTORE CATEGORIES FUNCTION
@login_required
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
   


# PRODUCT PAGE FUNCTION
@login_required
@never_cache
def list_product_page(request):
    if request.user.is_superuser:
        product_list = Product.objects.filter(is_deleted=False).order_by('pk').select_related('category', 'brand')
        return render(request, 'pages/products/product.html', {'product_list' : product_list})
    else:
        return redirect('admin_login_page')



# ADD PRODUCT PAGE FUNCTION
@login_required
@never_cache
def admin_add_product(request):
    if request.user.is_superuser:
        brand_list = Brand.objects.all().order_by('name').values()
        category_list = Category.objects.all().order_by('name').values()
        return render(request, 'pages/products/add_products.html', {'brand_list' : brand_list, 'category_list' : category_list})
    else:
        return redirect('admin_login_page')



# ADD PRODUCT FUNCTION
@login_required
@never_cache
def add_products(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            name = request.POST.get('product_name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            category_id = request.POST.get('category')
            brand_id = request.POST.get('brand')

            category = Category.objects.get(pk = category_id)
            brand = Brand.objects.get(pk = brand_id)
            
            if Product.objects.filter(name__icontains=name).exists():
                messages.error(request, 'Product already exists!')
                return redirect(admin_add_product)
            else:
                product = Product.objects.create(
                    name=name,
                    description=description,
                    price=price,
                    category=category,
                    brand=brand,
                )
                product.save()
                messages.success(request, 'New Product was created, Add product image')
                return redirect(admin_add_image_page)

    else:
        return redirect('admin_login_page')
    
    
    

# EDIT PRODUCT VIEW PAGE FUNCTION
@login_required
@never_cache
def edit_product_page(request, pdt_id):
    if request.user.is_superuser:
        product = Product.objects.get(id=pdt_id)
        category_list = Category.objects.all()
        brand_list = Brand.objects.all()
        context = {
            'product': product,
            'category_list': category_list,
            'brand_list': brand_list,
            'selected_category_id': product.category.id if product.category else None,
            'selected_brand_id': product.brand.id if product.brand else None,
        }
        return render(request, 'pages/products/edit_product.html', context)
    else:
        return redirect(admin_login_page)





# EDIT PRODUCT VIEW FUNCTION
@login_required
@never_cache
def edit_product(request, pdt_id):
    if request.user.is_superuser:
        if request.method == 'POST':
            name = request.POST.get('product_name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            category_id = request.POST.get('category')
            brand_id = request.POST.get('brand')
            is_deleted = request.POST.get('delete_product') == 'on'
            
            
            product = Product.objects.get(pk = pdt_id)
            category = Category.objects.get(pk = category_id)
            
            brand = Brand.objects.get(pk = brand_id)
            
            product.name = name
            product.description = description
            product.price = price
            product.category = category
            product.brand = brand
            product.is_deleted = is_deleted
            product.save()
            messages.success(request, 'New Product was created!')
            return redirect(list_product_page)
    else:
        return redirect(admin_login_page)
            
            
            



# DELETE PRODUCT FUNCTION
@login_required
@never_cache
def delete_product(request, pdt_id):
    if request.user.is_superuser:
        if pdt_id:
            product_to_delete = Product.objects.get(pk=pdt_id)
            if product_to_delete.brand.is_deleted == False and product_to_delete.category.is_deleted == False:
                product_to_delete.is_deleted = False
                product_to_delete.save()
                messages.success(request, 'Product have been deleted!')
            else:
                if product_to_delete.brand.is_deleted and product_to_delete.category.is_deleted:
                    messages.error(request, 'Cannot restore product: Brand and Category is deleted.')
                elif product_to_delete.brand.is_deleted:
                    messages.error(request, 'Cannot restore product: Brand is deleted.')
                else:
                    messages.error(request, 'Cannot restore product: Category is deleted.')
            return redirect(list_product_page)
        else:
            messages.error(request, 'ID cannot be found.')
            return redirect(list_product_page)
    else:
        return redirect('admin_login_page')






# DELETED PRODUCTS VIEW PAGE FUNCTION   
@login_required
@never_cache
def deleted_product_page(request):
    if request.user.is_superuser:
        product_list = Product.objects.filter(is_deleted=True).order_by('name').select_related('category', 'brand')
        return render(request, 'pages/products/deleted_products.html', {'product_list' : product_list})
    else:
        return redirect('admin_login_page')
    
    

    
# RESTORE PRODUCT FUNCTION
@login_required
@never_cache
def restore_product(request, pdt_id):
    if request.user.is_superuser:
        
        product = Product.objects.get(pk = pdt_id)
        product.is_deleted = False
        product.save()
        messages.success(request, 'Product have been restored')
        return redirect(deleted_product_page)
    else:
        return redirect(admin_login_page)
        




# For list_product function
@login_required
@never_cache
def list_product(request, pdt_id):
    if request.user.is_superuser:
        if pdt_id:
            product_to_list = Product.objects.get(pk=pdt_id)
            if product_to_list.brand.is_listed and product_to_list.category.is_listed:
                product_to_list.is_listed = True
                product_to_list.save()
                messages.success(request, 'Product updated successfully!')
            else:
                if product_to_list.brand.is_listed == False and product_to_list.category.is_listed == False:
                    messages.error(request, 'Cannot list product: Brand and Category is not listed.')
                elif product_to_list.brand.is_listed == False:
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
@login_required
@never_cache
def un_list_product(request, pdt_id):
    if request.user.is_superuser:
        if pdt_id:
            product_to_un_list = Product.objects.get(pk=pdt_id)
            product_to_un_list.is_listed = False
            product_to_un_list.save()
            messages.success(request, 'Product updated successfully!')
            return redirect(list_product_page)
        else:
            messages.error(request, 'id cannot be found.')
            return redirect(list_product_page)
    else:
        return redirect(admin_login_page)




# ---------------------------------------------------------------- ADMIN ADD PRODUCT IMAGE PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------


@login_required
@never_cache
def admin_add_image_page(request):
    if request.user.is_superuser:
        product_list = Product.objects.all()
        return render(request, 'pages/products/add_product_image.html', {'product_list' : product_list})
    else:
        return redirect(admin_login_page)



@login_required
@never_cache
def add_product_image(request, pdt_id):
    if request.user.is_superuser:
        if pdt_id:
            if request.method == 'POST':
                pass
                


# ---------------------------------------------------------------- ADMIN PRODUCT VARIANTS PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------



adult_sizes = [6, 7, 8, 9, 10, 11, 12]
kids_sizes = ['8C', '9C', '10C', '11C', '12C', '13C']

@login_required
@never_cache
def admin_add_variants(request):
    if request.user.is_superuser:
        sizes = adult_sizes
        products = Product.objects.all().order_by('name')
        product_color = ProductColorImage.objects.all().order_by('color')
        return render(request, 'pages/products/add_product_variant.html', {'products': products, 'product_image' : product_color, 'sizes': sizes})
    else:
        return redirect(admin_login_page)




@require_GET
def get_sizes_view(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        product_id = request.GET.get('product_id')
        if product_id:
            try:
                product = Product.objects.get(pk=product_id)
                if product.category.name.lower() == "kids":
                    sizes = ['8C', '9C', '10C', '11C', '12C', '13C']
                else:
                    sizes = [6, 7, 8, 9, 10, 11, 12]
                return JsonResponse({'sizes': sizes})
            except Product.DoesNotExist:
                pass
    return JsonResponse({'error': 'Invalid request'}, status=400)





# ---------------------------------------------------------------- ADMIN BRAND PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------

# BRAND PAGE FUNCTION
@login_required
@never_cache
def list_brand_page(request):
    if request.user.is_superuser:
        brand_list = Brand.objects.filter(is_deleted = False).order_by('name').values()
        return render(request, 'pages/products/brand.html', {'brand_list' : brand_list})
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
@login_required
@never_cache
def admin_add_brand(request):
    if request.user.is_superuser:
        return render(request, 'pages/products/add_brand.html', {'countries' : countries})
    else:
        return redirect('admin_login_page')



# ADD BRAND FUNCTION
@login_required
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
@login_required
@never_cache
def edit_brand_page(request, brand_id):
    if request.user.is_superuser:
        brand = get_object_or_404(Brand, id=brand_id)
        selected_country = brand.country_of_origin if brand.country_of_origin in countries else None
        return render(request, 'pages/products/edit_brand.html', {'brand': brand, 'countries': countries, 'selected_country': selected_country})
    else:
        return redirect('admin_login_page')

    



# EDIT BRAND FUNCTION   
@login_required
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
@login_required
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
@login_required
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
@login_required
@never_cache
def deleted_brand_view(request):
    if request.user.is_superuser:
        brand_list = Brand.objects.filter(is_deleted = True).order_by('name').values()
        return render(request, 'pages/products/deleted_brand.html', {'brand_list' : brand_list})
    else:
        return redirect('admin_login_page')
    
    

    
# LIST BRAND FUNCTION
@login_required
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
@login_required
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
    


