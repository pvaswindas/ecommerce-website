import re
import time
import json
import calendar
from io import BytesIO
import pytz  # type: ignore
from django.db.models import Q
from django.contrib import auth
from django.db.models import Sum
from django.utils import timezone
from django.db import transaction
import xlsxwriter  # type: ignore
import pandas as pd # type: ignore
from django.contrib import messages
from django.http import HttpResponse
from user_app.models import Customer
from django.http import JsonResponse
from PIL import Image  # type: ignore
from django.contrib.auth.models import User
from django.utils.timezone import make_aware
from django.contrib.auth import authenticate
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from datetime import date, datetime, timedelta
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache

from django.db.models import F, ExpressionWrapper, DecimalField, Case, When
from django.db.models import Value, Subquery, Count, OuterRef, IntegerField
from admin_app.models import ProductOffer, CategoryOffer, Coupon
from admin_app.models import Orders, OrderItem, Wallet, WalletTransaction
from admin_app.models import Category, Brand
from admin_app.models import Products, ProductColorImage, ProductSize

from reportlab.lib import colors  # type: ignore
from reportlab.lib.units import inch  # type: ignore
from reportlab.platypus import TableStyle  # type: ignore
from reportlab.lib.pagesizes import letter  # type: ignore
from reportlab.lib.styles import ParagraphStyle  # type: ignore
from reportlab.platypus import Paragraph, Spacer  # type: ignore
from reportlab.lib.styles import getSampleStyleSheet  # type: ignore
from reportlab.platypus import SimpleDocTemplate, Table  # type: ignore

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


# -------------------------------------------------------------


is_active_dashboard = True
is_active_customer = True
is_active_product = True
is_active_brand = True
is_active_category = True
is_active_order = True
is_active_product_offer = True
is_active_coupon = True
is_active_banner = True
is_active_sales = True

alphabets_pattern = re.compile(r"^[a-zA-Z\s]+$")
description_pattern = re.compile(r"^[\w\s',.\-\(\)]*$")


def clean_string(input_string):
    clean_string = re.sub(r"[^a-zA-Z0-9]", "", input_string)
    return clean_string


def validate_image(file):
    try:
        img = Image.open(file)
        img.verify()
    except Exception as e:
        raise ValidationError("Invalid image file: {}".format(e))


five_days_ago = timezone.now() - timedelta(days=5)


def clear_old_messages(view_func):
    def only_new_messages(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        all_messages = messages.get_messages(request)
        all_messages.used = True
        return response

    return only_new_messages


# 5 DAYS CUSTOMERS-------------------------------------------------------------


customers_last_5_days = User.objects.filter(date_joined__gte=five_days_ago).count()
total_customers = Customer.objects.all().count()

if total_customers > 0:
    increase_of_customer_in_five_days = round(
        (customers_last_5_days / total_customers) * 100, 2
    )

    increase_of_customer_in_five_days = max(0, increase_of_customer_in_five_days)
else:
    increase_of_customer_in_five_days = 0


# 5 DAYS ORDERS----------------------------------------------------------------


orders_last_5_days = OrderItem.objects.filter(
    order__placed_at__gte=five_days_ago
).count()
total_orders = OrderItem.objects.all().count()

if total_orders > 0:
    increase_of_order_in_five_days = round((orders_last_5_days / total_orders) * 100, 2)

    increase_of_order_in_five_days = max(0, increase_of_order_in_five_days)
else:
    increase_of_order_in_five_days = 0


# TODAY'S ORDER----------------------------------------------------------------


today = date.today()
todays_order = OrderItem.objects.filter(order__placed_at__date=today).count()

if orders_last_5_days > 0:
    todays_order_vs_order_in_five_days = round(
        ((todays_order - orders_last_5_days) / orders_last_5_days) * 100, 2
    )

    todays_order_vs_order_in_five_days = max(0, todays_order_vs_order_in_five_days)
else:
    todays_order_vs_order_in_five_days = 0


# 5 DAYS PRODUCTS--------------------------------------------------------------
products_last_5_days = ProductColorImage.objects.filter(
    created_at__gte=five_days_ago
).count()
total_products = ProductColorImage.objects.all().count()

if total_products > 0:
    increase_of_products_in_five_days = round(
        (products_last_5_days / total_products) * 100, 2
    )

    increase_of_products_in_five_days = max(0, increase_of_products_in_five_days)
else:
    increase_of_products_in_five_days = 0


def get_data(request):
    data = {}
    if request.user.is_superuser:
        user = request.user
        data.update(
            {
                "user": user,
                "total_customers": total_customers,
                "increase_of_customer_in_five_days": increase_of_customer_in_five_days,
                "total_orders": total_orders,
                "increase_of_order_in_five_days": increase_of_order_in_five_days,
                "today": today,
                "todays_order": todays_order,
                "todays_order_vs_order_in_five_days": todays_order_vs_order_in_five_days,
                "total_products": total_products,
                "products_last_5_days": products_last_5_days,
                "increase_of_products_in_five_days": increase_of_products_in_five_days,
            }
        )

    return data


# ------------------------------------------------------------------- CC_ADMIN LOGIN FUNCTIONS STARTING FROM HERE -------------------------------------------------------------------


# ADMIN LOGIN PAGE
@never_cache
def admin_login_page(request):
    if request.user.is_superuser:
        return redirect("admin_dashboard")
    else:
        return render(request, "admin_login.html")


# ADMIN LOGIN CREDENTIALS CHECKING FUNCTION
@never_cache
def admin_check_login(request):
    try:
        if request.method == "POST":
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)

            if user is not None and user.is_superuser:
                auth.login(request, user)
                return redirect("admin_dashboard")
            else:
                messages.error(
                    request, "Invalid credentials, please try logging in again."
                )
                return redirect("admin_login_page")
    except Exception:
        return redirect("admin_login_page")


# ADMIN DASHBOARD PAGE


@never_cache
def admin_dashboard(request):
    if request.user.is_superuser:
        context = {}
        selected_month_year = request.GET.get('selected_month')
        selected_year = request.GET.get('selected_year')
        
        
        order_items = OrderItem.objects.filter(
            order_status='Delivered',
            request_cancel=False,
            cancel_product=False,
            return_product=False,
            request_return=False,
            delivery_date__isnull=False
        )
        if selected_year:
            year = selected_year
        else:
            year = current_year
            
        month_labels, month_data, month_check_data, year_month = get_monthly_sales_data(order_items, selected_month_year)
        yearly_sales_data = get_yearly_sales_data(order_items, selected_year)
        values = yearly_sales_data.values()
        integer_set_values = set(values)
        year_check_data = False if integer_set_values == {0} else True
        context.update({
            'month_labels': month_labels,
            'month_data': month_data,
            'month_check_data' : month_check_data,
            'selected_month_year' : selected_month_year,
            'year_month' : year_month,
            'year' : year,
            'year_check_data' : year_check_data,
            'selected_year' : selected_year,
        })
        
        
        context['yearly_sales_data'] = json.dumps(yearly_sales_data)

        collect_data = get_data(request)
        context.update({**collect_data, "is_active_dashboard": is_active_dashboard})

        return render(request, "admin_index.html", context)
    else:
        return redirect("admin_login_page")




def get_monthly_sales_data(order_items, selected_month_year=None):
    current_date = datetime.now().date()
    current_year = str(current_date.year)
    current_month = current_date.month
    current_month_name = calendar.month_name[current_month]
    current_month_year = current_month_name + ' ' + current_year
    first_day_of_month = current_date.replace(day=1)
    last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1, day=1) - timedelta(days=1))
    
    if selected_month_year is not None:
        selected_month, selected_year = selected_month_year.split()
        selected_month = datetime.strptime(selected_month, '%B').month
        filter_month_start = datetime(int(selected_year), selected_month, 1).date()
        last_day = calendar.monthrange(int(selected_year), selected_month)[1]
        filter_month_end = datetime(int(selected_year), selected_month, last_day).date()
        year_month = selected_month_year 
    else:
        filter_month_start = first_day_of_month
        filter_month_end = last_day_of_month
        year_month = current_month_year
        
    monthly_sales_data = {}
    current_day = filter_month_start
    while current_day <= filter_month_end:
        order_items_day = order_items.filter(delivery_date=current_day)
        total_sales_day = order_items_day.aggregate(total_sales=Sum('each_price'))['total_sales']
        monthly_sales_data[current_day] = total_sales_day or 0
        current_day += timedelta(days=1)
    month_labels = [day.strftime("%b %d") for day in monthly_sales_data.keys()]
    month_data = list(monthly_sales_data.values())
    set_data = set(month_data)
    month_check_data = False if set_data == {0} else True
    return month_labels, month_data, month_check_data, year_month




def get_yearly_sales_data(order_items, selected_year=None):
    current_date = datetime.now().date()
    current_year = current_date.year
    if selected_year is not None:
        filter_year = int(selected_year)
    else:
        filter_year = current_year
    yearly_sales_data = {}
    
    for month in range(1, 13):
        order_items_monthly = order_items.filter(delivery_date__year=filter_year, delivery_date__month=month)
        
        total_sales_month = order_items_monthly.aggregate(total_sales=Sum('each_price'))['total_sales'] or 0
        
        yearly_sales_data[calendar.month_abbr[month]] = total_sales_month
    
    return yearly_sales_data


    
    



# ADMIN LOGOUT FUNCTION


@never_cache
def admin_logout(request):
    if request.method == "POST":
        auth.logout(request)
        messages.info(request, "Login again!")
        return redirect("admin_login_page")
    else:
        return redirect("admin_login_page")


# PAGE NOT FOUND


@never_cache
def page_not_found(request):
    if request.user.is_superuser:
        return redirect("admin_login_page")
    else:
        return render(request, "pages/samples/error-404.html")


# ---------------------------------------------------------------- CC_ADMIN CUSTOMER PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------


# CUSTOMER SHOW FUNCTION


@never_cache
def admin_customers(request):
    if request.user.is_superuser:
        user_list = User.objects.all().order_by("username").values()
        customer_list = Customer.objects.all().order_by("user__first_name").values()
        return render(
            request,
            "pages/customers/customers.html",
            {
                "user_list": user_list,
                "customer_list": customer_list,
                "is_active_customer": is_active_customer,
            },
        )
    else:
        return redirect("admin_login_page")


# BLOCK CUSTOMER FUNCTION


@never_cache
def block_user(request, user_id):
    if request.user.is_superuser:
        if request.method == "POST":
            user_to_block = User.objects.get(id=user_id)
            user_to_block.is_active = False
            user_to_block.save()
            return redirect(admin_customers)
        else:
            return redirect(admin_customers)
    else:
        return redirect("admin_login_page")


# UNBLOCK CUSTOMER FUNCTION


@never_cache
def unblock_user(request, user_id):
    if request.user.is_superuser:
        if request.method == "POST":
            user_to_unblock = User.objects.get(id=user_id)
            user_to_unblock.is_active = True
            user_to_unblock.save()
            return redirect(admin_customers)
        else:
            return redirect(admin_customers)
    else:
        return redirect("admin_login_page")


# SEARCH CUSTOMER FUNCTION


@never_cache
def search_user(request):
    if request.user.is_superuser:
        query = request.GET.get("query", "")

        if query:
            user_list = User.objects.filter(username__icontains=query)
        else:
            user_list = User.objects.all().order_by("username").values()

        return render(
            request,
            "pages/customers/customers.html",
            {"user_list": user_list, "is_active_customer": is_active_customer},
        )
    else:
        return redirect("admin_login_page")


# ---------------------------------------------------------------- CC_ADMIN CATEGORIES PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------


# CATEGORIES PAGES FUNCTION


@never_cache
def admin_categories(request):
    if request.user.is_superuser:
        category_list = (
            Category.objects.filter(is_deleted=False).order_by("name").values()
        )
        return render(
            request,
            "pages/category/category.html",
            {"category_list": category_list, "is_active_category": is_active_category},
        )
    else:
        return redirect("admin_login_page")


# ADD CATEGORY PAGE FUNCTION


@never_cache
def admin_add_category_page(request):
    if request.user.is_superuser:
        return render(
            request,
            "pages/category/add_category_page.html",
            {"is_active_category": is_active_category},
        )
    else:
        return redirect("admin_login_page")


# ADD CATEGORY FUNCTION


@never_cache
@clear_old_messages
def add_categories(request):
    if request.user.is_superuser:
        if request.method == "POST":
            name_str = request.POST["category_name"]
            description_str = request.POST["category_description"]

            is_every_field_valid = True

            if name_str and description_str:
                cleaned_name = clean_string(name_str)
                cleaned_description = clean_string(description)

                if not alphabets_pattern.match(name_str):
                    is_every_field_valid = False
                    messages.error(
                        request,
                        "Category name should contain only alphabetical characters & should not contain any spaces",
                    )

                elif not 3 <= len(cleaned_name) <= 30:
                    is_every_field_valid = False
                    messages.error(
                        request,
                        "Category name should be between 3 and 30 characters long, and it should not be blank.",
                    )

                elif not description_pattern.match(description_str):
                    is_every_field_valid = False
                    messages.error(
                        request,
                        "The description should contain only alphabetical characters, digits, spaces, periods, commas, and hyphens.",
                    )

                elif not 10 <= len(cleaned_description) <= 300:
                    is_every_field_valid = False
                    messages.error(
                        request,
                        "Description should be between 10 and 300 characters long, and it should not be blank.",
                    )

                if is_every_field_valid:
                    name = name_str.upper()
                    description = description_str
                    try:
                        if not Category.objects.filter(
                            name__icontains=name, is_deleted=False
                        ).exists():
                            category = Category.objects.create(
                                name=name, description=description
                            )
                            category.save()
                            messages.success(request, "New category was added!")
                            return redirect(admin_categories)
                        else:
                            messages.error(
                                request, "Category already exists, create new category"
                            )
                            return redirect(admin_add_category_page)
                    except Exception:
                        messages.error(
                            request,
                            "Unable to add a category at this moment, try after sometime.",
                        )
                return redirect(admin_add_category_page)
            else:
                messages.error(request, "Please fill all the fields to add a category.")
        return redirect(admin_add_category_page)
    else:
        return redirect("admin_login_page")


# EDIT BRAND PAGE FUNCTION


@never_cache
def edit_category_page(request, cat_id):
    if request.user.is_superuser:
        category = Category.objects.get(pk=cat_id)
        return render(
            request,
            "pages/category/edit_category.html",
            {
                "category": category,
                "countries": countries,
                "is_active_category": is_active_category,
            },
        )
    else:
        return redirect("admin_login_page")


# EDIT CATEGORIES FUNCTION


@never_cache
def edit_category(request, cat_id):
    if request.user.is_superuser:
        if request.method == "POST":
            name_str = request.POST["category_name"]
            description_str = request.POST["category_description"]

            is_every_field_valid = True

            try:
                category = Category.objects.get(id=cat_id)
            except Category.DoesNotExist:
                messages.error("Category not found.")
                return redirect("admin_categories")

            if name_str and description_str:
                cleaned_name = clean_string(name_str)
                cleaned_description = clean_string(description_str)

                if not alphabets_pattern.match(name_str):
                    is_every_field_valid = False
                    messages.error(
                        request,
                        "Category name should contain only alphabetical characters & should not contain any spaces",
                    )

                elif not 3 <= len(cleaned_name) <= 30:
                    is_every_field_valid = False
                    messages.error(
                        request,
                        "Category name should be between 3 to 30 characters long, and it should not be blank.",
                    )

                elif not description_pattern.match(description_str):
                    is_every_field_valid = False
                    messages.error(
                        request,
                        "The description should contain only alphabetical characters, digits, spaces, periods, commas, and hyphens.",
                    )

                elif not 10 <= len(cleaned_description) <= 300:
                    is_every_field_valid = False
                    messages.error(
                        request,
                        "Description name should be between 10 to 300 characters long, and it should not be blank.",
                    )

                if is_every_field_valid:
                    name = name_str.upper()
                    description = description_str
                    try:
                        if (
                            not Category.objects.filter(name__iexact=name)
                            .exclude(pk=cat_id)
                            .exists()
                        ):
                            category.name = name
                            category.description = description
                            category.save()
                            messages.success(request, "Category updated successfully!")
                            return redirect("admin_categories")
                        else:
                            messages.error(
                                request, "Category already exits, add new category"
                            )
                            return redirect("edit_category_page", cat_id)
                    except:
                        messages.error(
                            request,
                            "Unable to add a category at this moment, try after sometime.",
                        )
                return redirect("edit_category_page", cat_id)

    else:
        return redirect("admin_login_page")


# DELETE CATEGORY FUNCTION


@never_cache
def delete_category(request, cat_id):
    if request.user.is_superuser:
        if cat_id:
            category_to_delete = Category.objects.get(id=cat_id)
            category_to_delete.is_deleted = True
            category_to_delete.save()
            messages.success(request, "Category has been deleted!")
            return redirect(admin_categories)
        else:
            messages.error(request, "id cannot be found!")
            return redirect(admin_categories)
    else:
        return redirect("admin_login_page")


# LIST CATEGORY FUNCTION


@never_cache
def list_category(request, cat_id):
    if request.user.is_superuser:
        if cat_id:
            category_to_list = Category.objects.get(id=cat_id)
            category_to_list.is_listed = True
            category_to_list.save()
            messages.success(request, "Category updated successfully!")
            return redirect(admin_categories)
        else:
            messages.error(request, "id cannot be found!")
            return redirect(admin_categories)
    else:
        return redirect("admin_login_page")


# UNLIST CATEGORY FUNCTION


@never_cache
def un_list_category(request, cat_id):
    if request.user.is_superuser:
        if cat_id:
            category_to_list = Category.objects.get(id=cat_id)
            category_to_list.is_listed = False
            category_to_list.save()
            messages.success(request, "Category updated successfully!")
            return redirect(admin_categories)
        else:
            messages.error(request, "id cannot be found!")
            return redirect(admin_categories)
    else:
        return redirect("admin_login_page")


# DELETED CATEGORIES VIEW PAGE FUNCTION


@never_cache
def deleted_cat_view(request):
    if request.user.is_superuser:
        category_list = (
            Category.objects.filter(is_deleted=True).order_by("name").values()
        )
        return render(
            request,
            "pages/category/deleted_categories.html",
            {"category_list": category_list, "is_active_category": is_active_category},
        )
    else:
        return redirect("admin_login_page")


# RESTORE CATEGORIES FUNCTION


@never_cache
def restore_categories(request, cat_id):
    if request.user.is_superuser:
        if cat_id:
            category_to_restore = Category.objects.get(id=cat_id)
            category_to_restore.is_deleted = False
            category_to_restore.save()
            messages.success(request, "Category have been restored successfully!")
            return redirect(deleted_cat_view)
        else:
            messages.error(request, " id cannot be found!")
            return redirect(deleted_cat_view)
    else:
        return redirect("admin_login_page")


# ---------------------------------------------------------------- CC_ADMIN PRODUCT PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------


# PRODUCTS VIEW PAGE FUNCTION


@never_cache
def list_product_page(request):
    if request.user.is_superuser:
        query = request.GET.get("query", "")
        product_color = (
            ProductColorImage.objects.filter(is_deleted=False)
            .prefetch_related("product_sizes")
            .annotate(total_quantity=Sum("product_sizes__quantity"))
            .order_by("-created_at")
        )

        if query:
            product_color = product_color.filter(
                Q(products__name__icontains=query)
                | Q(products__type__icontains=query)
                | Q(products__category__name__icontains=query)
                | Q(products__brand__name__icontains=query)
            )

        paginator = Paginator(product_color, 10)
        page_number = request.GET.get("page")
        try:
            product_color = paginator.page(page_number)
        except PageNotAnInteger:
            product_color = paginator.page(1)
        except EmptyPage:
            product_color = paginator.page(paginator.num_pages)

        context = {
            "product_color": product_color,
            "is_active_product": is_active_product,
        }
        return render(request, "pages/products/product.html", context)
    else:
        return redirect("admin_login_page")


@never_cache
def get_quantity(request, size):
    try:
        quantity = ProductSize.objects.get(size=size).quantity
        return JsonResponse({"quantity": quantity})
    except ProductSize.DoesNotExist:
        return JsonResponse({"quantity": "Size not found"})


# ADD PRODUCT PAGE FUNCTION


@never_cache
def admin_add_product(request):
    if request.user.is_superuser:
        brand_list = Brand.objects.all().order_by("name").values()
        category_list = Category.objects.all().order_by("name").values()
        return render(
            request,
            "pages/products/add_products.html",
            {
                "brand_list": brand_list,
                "category_list": category_list,
                "is_active_product": is_active_product,
            },
        )
    else:
        return redirect("admin_login_page")


# ADD PRODUCT FUNCTION
product_name_pattern = re.compile(r"^[a-zA-Z0-9\s\-_]+$")


@never_cache
@clear_old_messages
def add_products(request):
    if request.user.is_superuser:
        if request.method == "POST":
            name = request.POST.get("product_name")
            description = request.POST.get("description")
            information = request.POST.get("information")
            type_str = request.POST.get("type")
            category_id = request.POST.get("category")
            brand_id = request.POST.get("brand")

            is_every_field_valid = True

            min_length = 10
            max_length = 100

            if (
                name
                and description
                and information
                and type_str
                and category_id
                and brand_id
            ):

                cleaned_name = clean_string(name)
                cleaned_description = clean_string(description)
                cleaned_information = clean_string(information)
                cleaned_type = clean_string(type_str)

                try:
                    category = Category.objects.get(pk=category_id)

                    try:
                        brand = Brand.objects.get(pk=brand_id)
                    except Brand.DoesNotExist:
                        messages.error(request, "Brand not found.")
                        return redirect(admin_add_product)

                    if Products.objects.filter(name__iexact=name).exists():
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Product name already exists, try with another name.",
                        )

                    elif not min_length <= len(name) <= max_length:
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Product name must be between 10 and 100 characters long.",
                        )

                    elif not min_length <= len(cleaned_name) <= max_length:
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Product name should not consist solely of special characters or be blank.",
                        )

                    elif name.isspace():
                        is_every_field_valid = False
                        messages.error(request, "Product name should not be blank.")

                    elif not product_name_pattern.match(name):
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Product name should only contain letters, numbers, spaces, hyphens, and underscores.",
                        )

                    elif not min_length <= len(description) <= 500:
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Description must be between 10 and 500 characters long.",
                        )

                    elif not min_length <= len(cleaned_description) <= 500:
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Description should not consist solely of special characters or be blank.",
                        )

                    elif not min_length <= len(information) <= 1000:
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "More information must be between 10 and 1000 characters long.",
                        )

                    elif not min_length <= len(cleaned_information) <= 1000:
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "More Information field should not consist solely of special characters or be blank.",
                        )

                    elif not 5 <= len(cleaned_type) <= 100:
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Product Type should not consist solely of special characters or be blank.",
                        )

                    elif not product_name_pattern.match(type_str):
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Product type should only contain letters, numbers, spaces, periods, commas, hyphens, and underscores.",
                        )

                    if is_every_field_valid:
                        if Products.objects.filter(name__iexact=name).exists():
                            messages.error(request, "Product already exists!")
                            return redirect(admin_add_product)
                        else:
                            try:
                                product = Products.objects.create(
                                    name=name,
                                    description=description,
                                    information=information,
                                    type=type_str,
                                    category=category,
                                    brand=brand,
                                )
                                product.save()
                                messages.success(
                                    request,
                                    "New Product was created, Add product image",
                                )
                                return redirect(admin_add_image_page)
                            except:
                                messages.error(
                                    request, "Currently unable to add a product."
                                )
                    return redirect(admin_add_product)
                except Category.DoesNotExist:
                    messages.error(request, "Category not found.")
                return redirect(admin_add_product)
            else:
                messages.error(request, "Please fill all the fields.")
                return redirect(admin_add_product)
    else:
        return redirect("admin_login_page")


# EDIT PRODUCT VIEW PAGE FUNCTION


@never_cache
@clear_old_messages
def edit_product_page(request, p_id):
    if request.user.is_superuser:
        try:
            product_color_image = ProductColorImage.objects.get(id=p_id)
            product = product_color_image.products
            product_sizes = ProductSize.objects.filter(
                product_color_image=product_color_image
            )
        except ProductColorImage.DoesNotExist:
            return HttpResponse("One or more objects do not exist.", status=404)

        category_list = Category.objects.all()
        brand_list = Brand.objects.all()

        context = {
            "category_list": category_list,
            "brand_list": brand_list,
            "product": product,
            "product_color_image": product_color_image,
            "product_sizes": product_sizes,
            "is_active_product": is_active_product,
        }
        return render(request, "pages/products/edit_product.html", context)
    else:
        return redirect("admin_login_page")


# EDIT PRODUCT VIEW FUNCTION


@never_cache
@clear_old_messages
def edit_product_update(request, p_id):
    if request.user.is_superuser:
        if request.method == "POST":
            name = request.POST.get("product_name")
            description = request.POST.get("description")
            information = request.POST.get("information")
            type_str = request.POST.get("type")
            category_id = request.POST.get("category")
            brand_id = request.POST.get("brand")

            is_every_field_valid = True

            min_length = 10
            max_length = 100

            try:
                product = Products.objects.get(pk=p_id)

                if (
                    name
                    and description
                    and information
                    and type_str
                    and category_id
                    and brand_id
                ):
                    cleaned_name = clean_string(name)
                    cleaned_description = clean_string(description)
                    cleaned_information = clean_string(information)
                    cleaned_type = clean_string(type_str)

                    try:
                        category = Category.objects.get(pk=category_id)
                    except Category.DoesNotExist:
                        messages.error(
                            request, "Currently the selected category is not available."
                        )
                        return redirect("list_product_page")

                    try:
                        brand = Brand.objects.get(pk=brand_id)
                    except Brand.DoesNotExist:
                        messages.error(
                            request, "Currently the selected brand is not available."
                        )
                        return redirect("list_product_page")

                    if (
                        Products.objects.filter(name__iexact=name)
                        .exclude(pk=p_id)
                        .exists()
                    ):
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Product name already exists, try with another name.",
                        )

                    elif not min_length <= len(name) <= max_length:
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Product name must be between 10 and 100 characters long.",
                        )

                    elif not min_length <= len(cleaned_name) <= max_length:
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Product Name should not consist solely of special characters or be blank.",
                        )

                    elif not product_name_pattern.match(name):
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Product name should only contain letters, numbers, spaces, hyphens, and underscores.",
                        )

                    elif not min_length <= len(description) <= 500:
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Description must be between 10 and 500 characters long.",
                        )

                    elif not min_length <= len(cleaned_description) <= 500:
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Description should not consist solely of special characters or be blank.",
                        )

                    elif not min_length <= len(cleaned_information) <= 1000:
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "More Information field should not consist solely of special characters or be blank.",
                        )

                    elif not min_length <= len(information) <= 1000:
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "More information must be between 10 and 1000 characters long.",
                        )

                    elif not 5 <= len(cleaned_type) <= 100:
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Product Type should not consist solely of special characters or be blank.",
                        )

                    elif not product_name_pattern.match(type_str):
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Product type should only contain letters, numbers, spaces, periods, commas, hyphens, and underscores.",
                        )

                    if is_every_field_valid:
                        try:
                            product.name = name
                            product.description = description
                            product.information = information
                            product.category = category
                            product.brand = brand
                            product.save()
                            messages.success(request, "Product Updated successfully!")
                            return redirect("list_product_page")
                        except:
                            messages.error(
                                request, "Currently not able to update the product"
                            )
                    return redirect("list_product_page")
                else:
                    messages.error(request, "Please fill all the fields.")
                    return redirect("list_product_page")
            except Products.DoesNotExist:
                messages.error(request, "Product not found.")
                return redirect("list_product_page")
    else:
        return redirect("admin_login_page")


# DELETED PRODUCTS VIEW PAGE FUNCTION


@never_cache
def deleted_product_page(request):
    if request.user.is_superuser:
        deleted_product_colors = (
            ProductColorImage.objects.filter(is_deleted=True)
            .select_related("products__category", "products__brand")
            .annotate(total_quantity=Sum("productsize__quantity"))
        )
        return render(
            request,
            "pages/products/deleted_products.html",
            {
                "product_colors": deleted_product_colors,
                "is_active_product": is_active_product,
            },
        )
    else:
        return redirect("admin_login_page")


# RESTORE PRODUCT FUNCTION


@never_cache
def restore_product(request, pdt_id):
    if request.user.is_superuser:
        if pdt_id:
            product_to_delete = ProductColorImage.objects.get(pk=pdt_id)
            product_to_delete.is_deleted = False
            product_to_delete.save()
            messages.success(request, "Product have been restored!")
            return redirect(list_product_page)
        else:
            messages.error()
    else:
        return redirect("admin_login_page")


# ---------------------------------------------------------------- CC_ADMIN EDIT PRODUCT COLOR & IMAGE PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------


# EDIT PRODUCT COLOR PAGE VIEW FUNCTION


@never_cache
def edit_product_color_page(request, p_id):
    if request.user.is_superuser:
        try:
            product_color_image = ProductColorImage.objects.get(id=p_id)
            product = product_color_image.products
            product_sizes = ProductSize.objects.filter(
                product_color_image=product_color_image
            )
        except ProductColorImage.DoesNotExist:
            return HttpResponse("One or more objects do not exist.", status=404)

        category_list = Category.objects.all()
        brand_list = Brand.objects.all()

        context = {
            "category_list": category_list,
            "brand_list": brand_list,
            "product": product,
            "product_color_image": product_color_image,
            "product_sizes": product_sizes,
            "is_active_product": is_active_product,
        }
        return render(request, "pages/products/edit_product_color.html", context)
    else:
        return redirect("admin_login_page")


# EDIT PRODUCT COLOR FUNCTION


@never_cache
def edit_product_color(request, p_id):
    if request.user.is_superuser:
        if request.method == "POST":
            color = request.POST.get("color")
            price = request.POST.get("price")
            main_image = request.FILES.get("main_image")
            side_image = request.FILES.get("side_image")
            top_image = request.FILES.get("top_image")
            back_image = request.FILES.get("back_image")

            if color and price:
                try:
                    product_color_image = ProductColorImage.objects.get(pk=p_id)
                except ProductColorImage.DoesNotExist:
                    messages.error(request, "Product color not found.")
                    return redirect("list_product_page")

                is_every_field_valid = True

                try:
                    if main_image:
                        validate_image(main_image)
                    if side_image:
                        validate_image(side_image)
                    if top_image:
                        validate_image(top_image)
                    if back_image:
                        validate_image(back_image)
                except:
                    messages.error(request, "Image files should be in valid format.")
                    return redirect("list_product_page")

                try:
                    price = int(price)
                except ValueError:
                    messages.error(request, "Price should be a valid whole number.")
                    return redirect("list_product_page")

                cleaned_color = clean_string(color)

                if not 3 <= len(cleaned_color) <= 30 and not alphabets_pattern.match(
                    color
                ):
                    is_every_field_valid = False
                    messages.error(
                        request,
                        "Color should only consist of characters and it should not be blank.",
                    )

                elif not 3 <= len(color) <= 30:
                    is_every_field_valid = False
                    messages.error(
                        request,
                        "The color name should be between 3 and 30 characters long.",
                    )

                elif not 500 <= price <= 100000:
                    is_every_field_valid = False
                    messages.error(
                        request, "Price should be between ₹500 and ₹100,000."
                    )

                if is_every_field_valid:
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

                    messages.success(
                        request, "Product color & images have been updated successfully"
                    )
                    return redirect("list_product_page")
                else:
                    return redirect("list_product_page")
            else:
                messages.error(request, "Please fill all the fields to continue.")
                return redirect("list_product_page")
        else:
            return render(
                request,
                "edit_product_color.html",
                {
                    "product_color_image": product_color_image,
                    "is_active_product": is_active_product,
                },
            )
    else:
        return redirect(admin_login_page)


# For list_product function


@never_cache
def list_product(request, pdt_id):
    if request.user.is_superuser:
        if pdt_id:
            product_to_list = ProductColorImage.objects.get(pk=pdt_id)
            if (
                product_to_list.products.brand.is_listed
                and product_to_list.products.category.is_listed
            ):
                product_to_list.is_listed = True
                product_to_list.save()
                messages.success(request, "Product updated successfully!")
            else:
                if (
                    product_to_list.products.brand.is_listed == False
                    and product_to_list.products.category.is_listed == False
                ):
                    messages.error(
                        request,
                        "Cannot list product: Brand and Category is not listed.",
                    )
                elif product_to_list.products.brand.is_listed == False:
                    messages.error(request, "Cannot list product: Brand is not listed.")
                else:
                    messages.error(
                        request, "Cannot list product: Category is not listed."
                    )
            return redirect(list_product_page)
        else:
            messages.error(request, "ID cannot be found.")
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
            messages.success(request, "Product updated successfully!")
            return redirect(list_product_page)
        else:
            messages.error(request, "id cannot be found.")
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
            messages.success(request, "Product have been deleted!")
            return redirect(list_product_page)
        else:
            messages.error()
    else:
        return redirect("admin_login_page")


# ---------------------------------------------------------------- CC_ADMIN EDIT PRODUCT SIZE PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------


# EDIT PRODUCT SIZE PAGE VIEW FUNCTION


@never_cache
def edit_product_size_page(request, p_id):
    if request.user.is_superuser:
        try:
            product_color_image = ProductColorImage.objects.get(id=p_id)
            product = product_color_image.products
            product_sizes = ProductSize.objects.filter(
                product_color_image=product_color_image
            )
        except ProductColorImage.DoesNotExist:
            return HttpResponse("One or more objects do not exist.", status=404)

        category_list = Category.objects.all()
        brand_list = Brand.objects.all()
        context = {
            "category_list": category_list,
            "brand_list": brand_list,
            "product": product,
            "product_color_image": product_color_image,
            "product_sizes": product_sizes,
        }

        return render(request, "pages/products/edit_variant_page.html", context)
    else:
        return redirect("admin_login_page")


# EDIT PRODUCT SIZE FUNCTION


@never_cache
def edit_product_size(request, p_id):
    if request.user.is_superuser:
        if request.method == "POST":
            size = request.POST.get("product_size")
            quantity = request.POST.get("product_quantity")

            try:
                product_size = ProductSize.objects.get(pk=p_id)
            except ProductSize.DoesNotExist:
                messages.error(request, """Product Variant doesn't exists!""")
                return redirect("list_product_page")

            if size and quantity:
                is_every_field_valid = True

                try:
                    quantity = int(quantity)
                except ValueError:
                    messages.error(request, "Quantity must be a whole number.")
                    return redirect("list_product_page")

                if (
                    ProductSize.objects.filter(
                        product_color_image=product_size.product_color_image, size=size
                    )
                    .exclude(pk=p_id)
                    .exists()
                ):
                    is_every_field_valid = False
                    messages.error(
                        request, "A same product variant already exists with this size."
                    )

                elif not 0 <= quantity <= 500:
                    is_every_field_valid = False
                    messages.error(request, "Quantity should be between 0 and 500.")

                if is_every_field_valid:
                    try:
                        product_size.size = size
                        product_size.quantity = quantity
                        product_size.save()

                        messages.success(request, "Product sizes & quantity updated")
                        return redirect("list_product_page")
                    except:
                        messages.error(
                            request, "Currently not able to update the product size."
                        )
                        return redirect("list_product_page")
                else:
                    return redirect("list_product_page")
            else:
                messages.error(request, "Size or quantity is empty")
                return redirect("list_product_page")
        else:
            return redirect("list_product_page")
    else:
        return redirect(admin_login_page)


# ---------------------------------------------------------------- CC_ADMIN ADD PRODUCT IMAGE PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------


# ADD PRODUCT IMAGE PAGE VIEW FUNCTION


@never_cache
def admin_add_image_page(request):
    if request.user.is_superuser:
        brand_list = Brand.objects.all().order_by("name")
        if request.method == "GET":
            brand_name = request.GET.get("brand_id")
            product_list = Products.objects.filter(brand__name=brand_name).order_by(
                "name"
            )
        else:
            brand_name = None
            product_list = None
        context = {
            "brand_name": brand_name,
            "product_list": product_list,
            "is_active_product": is_active_product,
            "brand_list": brand_list,
        }
        return render(request, "pages/products/add_product_image.html", context)
    else:
        return redirect(admin_login_page)


# ADD PRODUCT IMAGE FUNCTION
@never_cache
@clear_old_messages
def add_product_image(request):
    if request.user.is_superuser:
        if request.method == "POST":
            product_id = request.POST.get("product")
            color = request.POST.get("color")
            price = request.POST.get("price")
            main_image = request.FILES.get("main_image")
            side_image = request.FILES.get("side_image")
            top_image = request.FILES.get("top_image")
            back_image = request.FILES.get("back_image")

            cleaned_color = clean_string(color)

            is_every_field_valid = True

            if (
                product_id
                and color
                and price
                and main_image
                and side_image
                and top_image
                and back_image
            ):

                cleaned_color = clean_string(color)

                try:
                    validate_image(main_image)
                    validate_image(side_image)
                    validate_image(top_image)
                    validate_image(back_image)
                except:
                    messages.error(request, "Image files should be in valid format.")
                    return redirect("admin_add_image_page")

                try:
                    products = Products.objects.get(pk=product_id)

                    try:
                        price = int(price)
                    except ValueError:
                        messages.error(request, "Price should be a valid whole number.")
                        return redirect("admin_add_image_page")

                    existing_color = ProductColorImage.objects.filter(
                        products=products, color=color
                    ).exists()
                    if existing_color:
                        messages.error(
                            request,
                            f"A product image with the color '{
                                       color}' already exists for this product.",
                        )
                        return redirect("admin_add_image_page")
                    else:

                        if not 3 <= len(
                            cleaned_color
                        ) <= 30 and not alphabets_pattern.match(color):
                            is_every_field_valid = False
                            messages.error(
                                request,
                                "Color should only consist of characters and it should not be blank.",
                            )

                        elif not 3 <= len(color) <= 30:
                            is_every_field_valid = False
                            messages.error(
                                request,
                                "The color name should be between 3 and 30 characters long.",
                            )

                        elif not 500 <= price <= 100000:
                            is_every_field_valid = False
                            messages.error(
                                request, "Price should be between ₹500 and ₹100,000."
                            )

                        if is_every_field_valid:
                            product_color_image = ProductColorImage.objects.create(
                                color=color,
                                price=price,
                                main_image=main_image,
                                side_image=side_image,
                                top_image=top_image,
                                back_image=back_image,
                                products=products,
                            )
                            product_color_image.save()
                            messages.success(
                                request,
                                "Product Color and Image was added, now add product size",
                            )
                            return redirect(admin_add_variants)
                        else:
                            return redirect("admin_add_image_page")
                except Products.DoesNotExist:
                    messages.error(request, "Product does not exist")
                    return redirect("admin_add_image_page")
            else:
                messages.error(request, "Please fill all the fields.")
                return redirect("admin_add_image_page")
        else:
            return redirect("admin_add_image_page")
    else:
        return redirect("admin_login_page")


# ---------------------------------------------------------------- CC_ADMIN PRODUCT VARIANTS PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------


adult_sizes = [6, 7, 8, 9, 10, 11, 12]
kids_sizes = ["8C", "9C", "10C", "11C", "12C", "13C"]

# PRODUCT SIZE ADD PAGE VIEW PAGE FUNCTION


@never_cache
def admin_add_variants(request):
    if request.user.is_superuser:
        sizes = adult_sizes
        products = Products.objects.all().order_by("name")
        product_color = ProductColorImage.objects.all().order_by("-created_at")
        return render(
            request,
            "pages/products/add_product_variant.html",
            {
                "products": products,
                "product_color": product_color,
                "sizes": sizes,
                "is_active_product": is_active_product,
            },
        )
    else:
        return redirect(admin_login_page)


# GET COLOR FUNCTION


@never_cache
def get_colors(request):
    if request.user.is_superuser:
        if (
            request.method == "GET"
            and request.headers.get("x-requested-with") == "XMLHttpRequest"
        ):
            product_id = request.GET.get("product_id")
            if product_id:
                colors = (
                    ProductColorImage.objects.filter(products_id=product_id)
                    .order_by("color")
                    .values("id", "color")
                )
                return JsonResponse({"colors": list(colors)})
        return JsonResponse({}, status=400)


# GET SIZES FUNCTION


@never_cache
@require_GET
def get_sizes_view(request):
    if request.user.is_superuser:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            product_id = request.GET.get("product_id")
            if product_id:
                try:
                    product = Products.objects.get(pk=product_id)
                    if product.category.name.lower() == "kids":
                        sizes = ["8C", "9C", "10C", "11C", "12C", "13C"]
                    else:
                        sizes = ["6", "7", "8", "9", "10", "11", "12"]
                    return JsonResponse({"sizes": sizes})
                except Products.DoesNotExist:
                    pass
            return JsonResponse({"error": "Invalid request"}, status=400)


# ADD PRODUCT SIZE FUNCTION


@never_cache
def add_size(request):
    if request.user.is_superuser:
        if request.method == "POST":
            product_id = request.POST.get("product")
            color_id = request.POST.get("color")
            size = request.POST.get("size")
            quantity = request.POST.get("quantity")

            is_everything_valid = True

            if product_id and color_id and size and quantity:
                product_color_image = ProductColorImage.objects.get(pk=color_id)

                try:
                    quantity = int(quantity)
                except ValueError:
                    messages.error(
                        request, "Size Quantity should be a valid whole number."
                    )
                    return redirect("admin_add_variants")

                existing_size = ProductSize.objects.filter(
                    product_color_image=product_color_image, size=size
                ).exists()

                if existing_size:
                    messages.error(request, "This size already exists.")
                    return redirect("admin_add_variants")
                else:

                    if not 10 <= quantity <= 500:
                        is_everything_valid = False
                        messages.error(
                            request, "Quantity should be between 10 and 500 units."
                        )

                    if is_everything_valid:
                        try:
                            product_size = ProductSize.objects.create(
                                product_color_image=product_color_image,
                                size=size,
                                quantity=quantity,
                            )
                            product_size.save()
                            messages.success(
                                request,
                                f"Successfully added a new size for {
                                             product_color_image.products.name} ({product_color_image.color})",
                            )
                            return redirect(list_product_page)
                        except:
                            messages.error(
                                request, "Currently facing problems to add a variant."
                            )
                        return redirect(admin_add_variants)
                    else:
                        return redirect(admin_add_variants)
            else:
                messages.error(request, "Please fill all the fields.")
                return redirect("admin_add_variants")
        else:
            return redirect("admin_add_variants")
    else:
        return redirect("admin_login_page")


# ---------------------------------------------------------------- CC_ADMIN BRAND PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------

# BRAND PAGE FUNCTION


@never_cache
def list_brand_page(request):
    if request.user.is_superuser:
        brand_list = Brand.objects.filter(is_deleted=False).order_by("name").values()
        return render(
            request,
            "pages/brands/brand.html",
            {"brand_list": brand_list, "is_active_brand": is_active_brand},
        )
    else:
        return redirect("admin_login_page")


countries = [
    "Select a country",
    "Afghanistan",
    "Albania",
    "Algeria",
    "Andorra",
    "Angola",
    "Antigua and Barbuda",
    "Argentina",
    "Armenia",
    "Australia",
    "Austria",
    "Azerbaijan",
    "Bahamas",
    "Bahrain",
    "Bangladesh",
    "Barbados",
    "Belarus",
    "Belgium",
    "Belize",
    "Benin",
    "Bhutan",
    "Bolivia",
    "Bosnia and Herzegovina",
    "Botswana",
    "Brazil",
    "Brunei",
    "Bulgaria",
    "Burkina Faso",
    "Burundi",
    "Cabo Verde",
    "Cambodia",
    "Cameroon",
    "Canada",
    "Central African Republic",
    "Chad",
    "Chile",
    "China",
    "Colombia",
    "Comoros",
    "Congo (Congo-Brazzaville)",
    "Costa Rica",
    "Croatia",
    "Cuba",
    "Cyprus",
    "Czechia (Czech Republic)",
    "Democratic Republic of the Congo",
    "Denmark",
    "Djibouti",
    "Dominica",
    "Dominican Republic",
    "Ecuador",
    "Egypt",
    "El Salvador",
    "Equatorial Guinea",
    "Eritrea",
    "Estonia",
    "Eswatini (fmr. 'Swaziland')",
    "Ethiopia",
    "Fiji",
    "Finland",
    "France",
    "Gabon",
    "Gambia",
    "Georgia",
    "Germany",
    "Ghana",
    "Greece",
    "Grenada",
    "Guatemala",
    "Guinea",
    "Guinea-Bissau",
    "Guyana",
    "Haiti",
    "Holy See",
    "Honduras",
    "Hungary",
    "Iceland",
    "India",
    "Indonesia",
    "Iran",
    "Iraq",
    "Ireland",
    "Israel",
    "Italy",
    "Jamaica",
    "Japan",
    "Jordan",
    "Kazakhstan",
    "Kenya",
    "Kiribati",
    "Kuwait",
    "Kyrgyzstan",
    "Laos",
    "Latvia",
    "Lebanon",
    "Lesotho",
    "Liberia",
    "Libya",
    "Liechtenstein",
    "Lithuania",
    "Luxembourg",
    "Madagascar",
    "Malawi",
    "Malaysia",
    "Maldives",
    "Mali",
    "Malta",
    "Marshall Islands",
    "Mauritania",
    "Mauritius",
    "Mexico",
    "Micronesia",
    "Moldova",
    "Monaco",
    "Mongolia",
    "Montenegro",
    "Morocco",
    "Mozambique",
    "Myanmar (formerly Burma)",
    "Namibia",
    "Nauru",
    "Nepal",
    "Netherlands",
    "New Zealand",
    "Nicaragua",
    "Niger",
    "Nigeria",
    "North Korea",
    "North Macedonia (formerly Macedonia)",
    "Norway",
    "Oman",
    "Pakistan",
    "Palau",
    "Palestine State",
    "Panama",
    "Papua New Guinea",
    "Paraguay",
    "Peru",
    "Philippines",
    "Poland",
    "Portugal",
    "Qatar",
    "Romania",
    "Russia",
    "Rwanda",
    "Saint Kitts and Nevis",
    "Saint Lucia",
    "Saint Vincent and the Grenadines",
    "Samoa",
    "San Marino",
    "Sao Tome and Principe",
    "Saudi Arabia",
    "Senegal",
    "Serbia",
    "Seychelles",
    "Sierra Leone",
    "Singapore",
    "Slovakia",
    "Slovenia",
    "Solomon Islands",
    "Somalia",
    "South Africa",
    "South Korea",
    "South Sudan",
    "Spain",
    "Sri Lanka",
    "Sudan",
    "Suriname",
    "Sweden",
    "Switzerland",
    "Syria",
    "Tajikistan",
    "Tanzania",
    "Thailand",
    "Timor-Leste",
    "Togo",
    "Tonga",
    "Trinidad and Tobago",
    "Tunisia",
    "Turkey",
    "Turkmenistan",
    "Tuvalu",
    "Uganda",
    "Ukraine",
    "United Arab Emirates",
    "United Kingdom",
    "United States of America",
    "Uruguay",
    "Uzbekistan",
    "Vanuatu",
    "Venezuela",
    "Vietnam",
    "Yemen",
    "Zambia",
    "Zimbabwe",
]


# ADD BRAND PAGE FUNCTION


@never_cache
def admin_add_brand(request):
    if request.user.is_superuser:
        return render(
            request,
            "pages/brands/add_brand.html",
            {"countries": countries, "is_active_brand": is_active_brand},
        )
    else:
        return redirect("admin_login_page")


# ADD BRAND FUNCTION


@never_cache
@clear_old_messages
def add_brand(request):
    if request.user.is_superuser:
        if request.method == "POST":
            name = request.POST["name"]
            country_of_origin = request.POST["country_of_origin"]
            manufacturer_details = request.POST["manufacturer_details"]

            is_every_field_valid = True

            if name and country_of_origin and manufacturer_details:
                cleaned_name = clean_string(name)
                cleaned_manufacturer = clean_string(manufacturer_details)

                if not 2 <= len(cleaned_name) <= 30:
                    is_every_field_valid = False
                    messages.error(
                        request,
                        "Brand name should be between 2 and 30 characters long, and it should not be blank.",
                    )

                elif not alphabets_pattern.match(name):
                    is_every_field_valid
                    messages.error(
                        request,
                        "Brand name should contain only alphabetical characters & should not contain any spaces",
                    )

                elif Brand.objects.filter(
                    manufacturer_details__iexact=manufacturer_details
                ).exists():
                    is_every_field_valid = False
                    messages.error(request, "Manufacturer already exists.")

                elif not 10 <= len(cleaned_manufacturer) <= 300:
                    is_every_field_valid = False
                    messages.error(
                        request,
                        "Manufacturer details should be between 10 and 300 characters long, and it should not be blank.",
                    )

                if is_every_field_valid:
                    name = name.title()
                    if not Brand.objects.filter(name__iexact=name).exists():
                        try:
                            brand = Brand.objects.create(
                                name=name,
                                country_of_origin=country_of_origin,
                                manufacturer_details=manufacturer_details,
                            )
                            brand.save()
                            messages.success(request, "New brand added!")
                            return redirect(list_brand_page)
                        except:
                            messages.error(
                                request,
                                "Currently not able to create a brand, try again after some time.",
                            )
                            return redirect("admin_add_brand")
                    else:
                        messages.error(request, "Brand already exits, add new brand")
                        return redirect("admin_add_brand")
                else:
                    return redirect("admin_add_brand")
            else:
                messages.error(request, "Please fill all the fields.")
                return redirect("admin_add_brand")
        else:
            return redirect("admin_add_brand")
    else:
        return redirect("admin_login_page")


# EDIT BRAND PAGE FUNCTION


@never_cache
def edit_brand_page(request, brand_id):
    if request.user.is_superuser:
        brand = get_object_or_404(Brand, id=brand_id)
        selected_country = (
            brand.country_of_origin if brand.country_of_origin in countries else None
        )
        return render(
            request,
            "pages/brands/edit_brand.html",
            {
                "brand": brand,
                "countries": countries,
                "selected_country": selected_country,
                "is_active_brand": is_active_brand,
            },
        )
    else:
        return redirect("admin_login_page")


# EDIT BRAND FUNCTION


@never_cache
def edit_brand(request, brand_id):
    if request.user.is_superuser:
        if request.method == "POST":
            name = request.POST["name"]
            country_of_origin = request.POST["country_of_origin"]
            manufacturer_details = request.POST["manufacturer_details"]

            is_every_field_valid = True

            try:
                brand = Brand.objects.get(id=brand_id)
            except Brand.DoesNotExist:
                messages.error(request, "Brand not found.")
                return redirect("list_brand_page")

            if name and country_of_origin and manufacturer_details:
                cleaned_name = clean_string(name)
                cleaned_manufacturer = clean_string(manufacturer_details)

                if not 2 <= len(cleaned_name) <= 30:
                    is_every_field_valid = False
                    messages.error(
                        request,
                        "Brand name should be between 2 and 30 characters long, and it should not be blank.",
                    )

                elif not alphabets_pattern.match(name):
                    is_every_field_valid = False
                    messages.error(
                        request,
                        "Brand name should contain only alphabetical characters & should not contain any spaces",
                    )

                elif (
                    Brand.objects.filter(
                        manufacturer_details__iexact=manufacturer_details
                    )
                    .exclude(pk=brand_id)
                    .exists()
                ):
                    is_every_field_valid = False
                    messages.error(request, "Manufacturer already exists.")

                elif not 10 <= len(cleaned_manufacturer) <= 300:
                    is_every_field_valid = False
                    messages.error(
                        request,
                        "Manufacturer details should be between 10 and 300 characters long, and it should not be blank.",
                    )

                if is_every_field_valid:
                    name = name.title()
                    if (
                        not Brand.objects.filter(name__iexact=name)
                        .exclude(pk=brand_id)
                        .exists()
                    ):
                        brand.name = name
                        brand.country_of_origin = country_of_origin
                        brand.manufacturer_details = manufacturer_details
                        brand.save()
                        messages.success(request, "Brand updated successfully!")
                        return redirect("list_brand_page")
                    else:
                        messages.error(
                            request,
                            "Another brand exists with the same name, try a different name.",
                        )
                        return redirect("edit_brand_page", brand_id)
                else:
                    return redirect("edit_brand_page", brand_id)
            else:
                messages.error(request, "Please fill all the fields.")
                return redirect("edit_brand_page", brand_id)
        else:
            return redirect("list_brand_page")
    else:
        return redirect("admin_login_page")


# DELETE BRAND FUNCTION


@never_cache
def delete_brand(request, brand_id):
    if request.user.is_superuser:
        if brand_id:
            brand_to_delete = Brand.objects.get(id=brand_id)
            brand_to_delete.is_deleted = True
            brand_to_delete.save()
            messages.success(request, "Brand has been deleted!")
            return redirect(list_brand_page)
        else:
            messages.error(request, "id cannot be found!")
            return redirect(list_brand_page)
    else:
        return redirect("admin_login_page")


#  RESTORE BRAND FUNCTION


@never_cache
def restore_brand(request, brand_id):
    if request.user.is_superuser:
        if brand_id:
            brand_to_restore = Brand.objects.get(id=brand_id)
            brand_to_restore.is_deleted = False
            brand_to_restore.save()
            messages.success(request, "Brand has been restored!")
            return redirect(list_brand_page)
        else:
            messages.error(request, "id cannot be found!")
            return redirect(list_brand_page)
    else:
        return redirect("admin_login_page")


#  DELETED BRAND VIEW PAGE


@never_cache
def deleted_brand_view(request):
    if request.user.is_superuser:
        brand_list = Brand.objects.filter(is_deleted=True).order_by("name").values()
        return render(
            request,
            "pages/brands/deleted_brand.html",
            {"brand_list": brand_list, "is_active_brand": is_active_brand},
        )
    else:
        return redirect("admin_login_page")


# LIST BRAND FUNCTION


@never_cache
def list_the_brand(request, brand_id):
    if request.user.is_superuser:
        if brand_id:
            brand_to_list = Brand.objects.get(id=brand_id)
            brand_to_list.is_listed = True
            brand_to_list.save()
            messages.success(request, "Brand updated successfully!")
            return redirect(list_brand_page)
        else:
            messages.error(request, "id cannot be found!")
            return redirect(list_brand_page)
    else:
        return redirect("admin_login_page")


# UNLIST BRAND FUNCTION


@never_cache
def un_list_the_brand(request, brand_id):
    if request.user.is_superuser:
        if brand_id:
            brand_to_un_list = Brand.objects.get(id=brand_id)
            brand_to_un_list.is_listed = False
            brand_to_un_list.save()
            messages.success(request, "Brand updated successfully!")
            return redirect(list_brand_page)
        else:
            messages.error(request, "id cannot be found!")
            return redirect(list_brand_page)
    else:
        return redirect("admin_login_page")


# ---------------------------------------------------------------- CC_ADMIN ORDER PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------


@never_cache
def orders_view_page(request):
    if request.user.is_superuser:
        orders = Orders.objects.all().order_by("customer").values()
        order_item = OrderItem.objects.all().order_by("-order__placed_at")
        context = {
            "order_item": order_item,
            "orders": orders,
            "is_active_order": is_active_order,
        }
        return render(request, "pages/orders/orders_view_page.html", context)
    else:
        return redirect("admin_login_page")


@never_cache
def order_detailed_view(request, order_id):
    if request.user.is_superuser:
        order_item = OrderItem.objects.get(pk=order_id)
        context = {
            "is_active_order": is_active_order,
            "order_item": order_item,
        }
        return render(request, "pages/orders/single order_view_page.html", context)
    else:
        return redirect("admin_login_page")


@never_cache
def change_order_status(request, order_id):
    if request.user.is_superuser:
        order_status = request.POST.get("order_status")
        order_item = OrderItem.objects.get(pk=order_id)

        if order_item:
            order = order_item.order
            order_products = OrderItem.objects.filter(
                order=order,
                request_cancel=False,
                cancel_product=False,
                request_return=False,
                return_product=False,
            )

            order_item.order_status = order_status
            order_item.save()

            if order_status == "Delivered":
                if order_item.order.payment.method_name == "Cash On Delivery":
                    order_item.order.paid = True
                    order_item.order.save()

                    order_item.order.payment.pending = False
                    order_item.order.payment.success = True
                    order_item.order.payment.save()

                order_item.delivery_date = date.today()
                order_item.save()

            count = sum(
                1 for item in order_products if item.order_status == order_status
            )
            status = True if count == order.number_of_orders else None

            if status == True:
                order.order_status = order_status
                order.save()

            if order.order_status == "Delivered":
                order.delivery_date = date.today()
                order.save()

            messages.success(request, "Order Status Updated")
            return redirect("orders_view_page")
    else:
        return redirect("admin_login_page")


@never_cache
@clear_old_messages
def cancel_product(request, order_items_id):
    if request.user.is_superuser:
        try:
            try:
                order_item = OrderItem.objects.get(pk=order_items_id)
            except OrderItem.DoesNotExist:
                return redirect("orders_view_page")
            product_size = order_item.product
            order = order_item.order
            user = order.customer.user
            wallet = Wallet.objects.get(user=user)
            with transaction.atomic():
                if order.payment.method_name in ["Razorpay", "Wallet"]:
                    refund_money = 0
                    other_item_price = 0
                    sum_of_all_other = 0
                    refund_money = 0
                    other_item_price = 0
                    sum_of_all_other = 0
                    if order.number_of_orders > 1:
                        if order_item.order.coupon_applied:
                            minimum_amount = order.coupon_minimum_amount
                            maximum_amount = order.coupon_maximum_amount
                            other_order_items = OrderItem.objects.filter(
                                order=order, return_product=False, cancel_product=False
                            ).exclude(order_items_id=order_items_id)
                            total_of_other_order = 0
                            for item in other_order_items:
                                total_of_other_order += item.each_price

                            item_price = order_item.each_price

                            total_after_reducing = (
                                order.total_charge - order_item.each_price
                            )

                            if minimum_amount <= total_of_other_order <= maximum_amount:

                                if other_order_items:
                                    if total_after_reducing > 0:
                                        order.total_charge = total_after_reducing
                                        order.save()

                                refund_money = order_item.each_price

                                wallet_transaction = WalletTransaction.objects.create(
                                    wallet=wallet,
                                    order_item=order_item,
                                    money_deposit=refund_money,
                                )
                                wallet_transaction.save()

                            else:
                                order_total = order.total_charge
                                sum_of_all_other = 0
                                for item in other_order_items:
                                    other_item_price = item.each_price
                                    sum_of_all_other += other_item_price

                                refund_money = int(order_total - sum_of_all_other)

                                wallet_transaction = WalletTransaction.objects.create(
                                    wallet=wallet,
                                    order_item=order_item,
                                    money_deposit=refund_money,
                                )
                                wallet_transaction.save()

                                order_item.each_price = refund_money
                                order_item.save()

                                order.total_charge = sum_of_all_other
                                order.coupon_applied = False
                                order.coupon_name = None
                                order.discount_price = None
                                order.coupon_discount_percent = None
                                order.coupon_minimum_amount = None
                                order.coupon_maximum_amount = None
                                order.save()
                        else:
                            item_price = order_item.each_price
                            refund_money = item_price
                            wallet_transaction = WalletTransaction.objects.create(
                                wallet=wallet,
                                order_item=order_item,
                                money_deposit=refund_money,
                            )
                            wallet_transaction.save()

                            order_total = order.total_charge
                            order.total_charge = order_total - refund_money
                            order.save()
                    else:
                        refund_money = order.total_charge
                        wallet_transaction = WalletTransaction.objects.create(
                            wallet=wallet,
                            order_item=order_item,
                            money_deposit=refund_money,
                        )
                        wallet_transaction.save()

                        order_total = order.total_charge
                        order.total_charge = order_total - refund_money
                        order.save()

                    new_wallet_balance = wallet.balance + refund_money
                    wallet.balance = new_wallet_balance
                    wallet.save()

                product_size.quantity += order_item.quantity
                product_size.save()

                if order.payment.method_name not in ["Razorpay", "Wallet"]:
                    order.total_charge -= order_item.each_price
                    if order.total_charge < 0:
                        order.total_charge = 0
                    order.save()
                order_item.cancel_product = True
                order_item.order_status = "Cancelled"
                order_item.save()
                time.sleep(1)
                return redirect("order_detailed_view", order_items_id)
        except:
            return redirect("order_detailed_view", order_items_id)
    else:
        return redirect("admin_dashboard")


@never_cache
def return_product(request, order_items_id):
    if request.user.is_superuser:
        try:
            with transaction.atomic():
                order_item = OrderItem.objects.get(pk=order_items_id)
                product_size = order_item.product
                order = order_item.order
                user = order.customer.user
                wallet = Wallet.objects.get(user=user)
                refund_money = 0
                other_item_price = 0
                sum_of_all_other = 0
                if order.number_of_orders > 1:
                    if order_item.order.coupon_applied:
                        minimum_amount = order.coupon_minimum_amount
                        maximum_amount = order.coupon_maximum_amount
                        other_order_items = OrderItem.objects.filter(
                            order=order, return_product=False, cancel_product=False
                        ).exclude(order_items_id=order_items_id)
                        total_of_other_order = 0
                        for item in other_order_items:
                            total_of_other_order += item.each_price

                        item_price = order_item.each_price

                        total_after_reducing = (
                            order.total_charge - order_item.each_price
                        )

                        if minimum_amount <= total_of_other_order <= maximum_amount:

                            if other_order_items:
                                if total_after_reducing > 0:
                                    order.total_charge = total_after_reducing
                                    order.save()

                            refund_money = order_item.each_price

                            wallet_transaction = WalletTransaction.objects.create(
                                wallet=wallet,
                                order_item=order_item,
                                money_deposit=refund_money,
                            )
                            wallet_transaction.save()

                        else:
                            order_total = order.total_charge
                            sum_of_all_other = 0
                            for item in other_order_items:
                                other_item_price = item.each_price
                                sum_of_all_other += other_item_price

                            refund_money = int(order_total - sum_of_all_other)

                            wallet_transaction = WalletTransaction.objects.create(
                                wallet=wallet,
                                order_item=order_item,
                                money_deposit=refund_money,
                            )
                            wallet_transaction.save()

                            order_item.each_price = refund_money
                            order_item.save()

                            order.total_charge = sum_of_all_other
                            order.coupon_applied = False
                            order.coupon_name = None
                            order.discount_price = None
                            order.coupon_discount_percent = None
                            order.coupon_minimum_amount = None
                            order.coupon_maximum_amount = None
                            order.save()
                    else:
                        item_price = order_item.each_price
                        refund_money = item_price
                        wallet_transaction = WalletTransaction.objects.create(
                            wallet=wallet,
                            order_item=order_item,
                            money_deposit=refund_money,
                        )
                        wallet_transaction.save()

                        order_total = order.total_charge
                        order.total_charge = order_total - refund_money
                        order.save()
                else:
                    refund_money = order.total_charge
                    wallet_transaction = WalletTransaction.objects.create(
                        wallet=wallet,
                        order_item=order_item,
                        money_deposit=refund_money,
                    )
                    wallet_transaction.save()

                    order_item.each_price = refund_money
                    order_item.save()

                new_wallet_balance = wallet.balance + refund_money
                wallet.balance = new_wallet_balance
                wallet.save()

                product_size.quantity += order_item.quantity
                product_size.save()

                order_item.return_product = True
                order_item.order_status = "Returned"
                order_item.save()

                time.sleep(2)

                return redirect("order_detailed_view", order_items_id)
        except Exception as e:
            return redirect(admin_login_page)
    else:
        return redirect(admin_login_page)


# ----------------------------------------------------------------  CC_SALES REPORT PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------


current_date = timezone.now().date()
start_date = current_date - timedelta(days=current_date.weekday())
end_date = start_date + timedelta(days=6)

start_date = timezone.make_aware(
    datetime.combine(start_date, datetime.min.time()), pytz.utc
)


end_date = timezone.make_aware(
    datetime.combine(end_date, datetime.max.time()), pytz.utc
)


now = timezone.now()


current_year = now.strftime("%Y")
custom_start_date = None
custom_end_date = None


@never_cache
@clear_old_messages
def sales_report_page(request):
    if request.user.is_superuser:
        global current_year, start_date, end_date

        today = timezone.now()

        sales_data = None

        if request.method == "GET":
            filter_option = request.GET.get("filter")

            if filter_option == "weekly":
                sales_data = OrderItem.objects.filter(
                    Q(cancel_product=False)
                    & Q(return_product=False)
                    & Q(order_status="Delivered")
                    & Q(order__placed_at__range=(start_date, end_date))
                )
                request.session["start_date"] = start_date.strftime("%Y-%m-%d %H:%M:%S")
                request.session["end_date"] = end_date.strftime("%Y-%m-%d %H:%M:%S")

            if filter_option == "monthly":
                current_year_and_month = request.GET.get("year_month")

                if current_year_and_month:
                    year, month = map(int, current_year_and_month.split("-"))
                    first_day_of_month = timezone.datetime(year, month, 1).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    last_day_of_month = timezone.datetime(
                        year,
                        month,
                        calendar.monthrange(year, month)[1],
                        23,
                        59,
                        59,
                        999999,
                    )

                    first_day_of_month = make_aware(first_day_of_month)
                    last_day_of_month = make_aware(last_day_of_month)

                    sales_data = OrderItem.objects.filter(
                        Q(cancel_product=False)
                        & Q(return_product=False)
                        & Q(order_status="Delivered")
                        & Q(
                            order__placed_at__range=(
                                first_day_of_month,
                                last_day_of_month,
                            )
                        )
                    )
                    request.session["start_date"] = first_day_of_month.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    request.session["end_date"] = last_day_of_month.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                else:
                    messages.error(request, "Please select a month to continue")
                    return redirect("sales_report_page")

            if filter_option == "yearly":
                filter_year = request.GET.get("year")

                if filter_year:
                    year = int(filter_year)

                    start_date_of_year = datetime(year, 1, 1, 0, 0, 0)

                    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                        end_date_of_year = datetime(year, 12, 31, 23, 59, 59)
                    else:
                        end_date_of_year = datetime(year, 12, 31, 23, 59, 59)

                    start_date_of_year = make_aware(start_date_of_year)
                    end_date_of_year = make_aware(end_date_of_year)

                    sales_data = OrderItem.objects.filter(
                        Q(cancel_product=False)
                        & Q(return_product=False)
                        & Q(order_status="Delivered")
                        & Q(
                            order__placed_at__range=(
                                start_date_of_year,
                                end_date_of_year,
                            )
                        )
                    )
                    request.session["start_date"] = start_date_of_year.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    request.session["end_date"] = end_date_of_year.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                else:
                    messages.error(request, "Please select a year to continue.")
                    return redirect("sales_report_page")

            if filter_option == "custom":
                custom_start_date = request.GET.get("start_date")
                custom_end_date = request.GET.get("end_date")

                if custom_start_date and custom_end_date:
                    start_datetime = datetime.strptime(custom_start_date, "%Y-%m-%d")
                    end_datetime = datetime.strptime(custom_end_date, "%Y-%m-%d")

                    start_datetime = make_aware(start_datetime)
                    end_datetime = make_aware(end_datetime)

                    if start_datetime < end_datetime and start_datetime <= today:
                        start_datetime = start_datetime.replace(
                            hour=0, minute=0, second=0, microsecond=0
                        )

                        end_datetime = end_datetime.replace(
                            hour=23, minute=59, second=59, microsecond=999999
                        )

                        sales_data = OrderItem.objects.filter(
                            Q(cancel_product=False)
                            & Q(return_product=False)
                            & Q(order_status="Delivered")
                            & Q(order__placed_at__range=(start_datetime, end_datetime))
                        )
                        request.session["start_date"] = start_datetime.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        request.session["end_date"] = end_datetime.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    else:
                        messages.error(request, "Please select a valid date range.")
                        return redirect("sales_report_page")
                else:
                    messages.error(
                        request, "Please select all the required fields to continue"
                    )
                    return redirect("sales_report_page")

        if sales_data is not None:
            sales_data = sales_data.annotate(
                order_item_count=Subquery(
                    OrderItem.objects.filter(
                        order=OuterRef("order"),
                        cancel_product=False,
                        return_product=False,
                    )
                    .values("order")
                    .annotate(item_count=Count("order_id"))
                    .values("item_count")[:1],
                    output_field=IntegerField(),
                )
            )

            sales_data = sales_data.annotate(
                discount_amount=Case(
                    When(
                        order__coupon_applied=True,
                        then=ExpressionWrapper(
                            F("order__discount_price") / F("order_item_count"),
                            output_field=DecimalField(max_digits=10, decimal_places=2),
                        ),
                    ),
                    default=Value(None),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                )
            )

        overall_sales_count = sales_data.count() if sales_data else 0
        overall_order_amount = (
            sales_data.aggregate(total_amount=Sum("each_price"))["total_amount"]
            if sales_data
            else 0
        )
        overall_discount = (
            sales_data.aggregate(total_discount=Sum("discount_amount"))[
                "total_discount"
            ]
            if sales_data
            else 0
        )

        if sales_data:
            overall_order_amount = float(
                sales_data.aggregate(total_amount=Sum("each_price"))["total_amount"]
                or 0
            )
            overall_discount = float(
                sales_data.aggregate(total_discount=Sum("discount_amount"))[
                    "total_discount"
                ]
                or 0
            )
            request.session["overall_sales_count"] = overall_sales_count
            request.session["overall_order_amount"] = overall_order_amount
            request.session["overall_discount"] = overall_discount
        context = {
            "sales_data": sales_data,
            "is_active_sales": is_active_sales,
            "overall_sales_count": overall_sales_count,
            "overall_order_amount": overall_order_amount,
            "overall_discount": overall_discount,
        }
        return render(request, "admin_sales_report.html", context)
    else:
        return redirect("admin_login_page")


@never_cache
@clear_old_messages
def download_sales_report(request):
    if request.user.is_superuser:
        if request.method == "POST":

            start_date_str = request.session.get("start_date")
            end_date_str = request.session.get("end_date")

            start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")

            sales_data = OrderItem.objects.filter(
                Q(cancel_product=False)
                & Q(return_product=False)
                & Q(order_status="Delivered")
                & Q(order__placed_at__range=(start_date, end_date))
            )

            overall_sales_count = request.session.get("overall_sales_count")
            overall_order_amount = request.session.get("overall_order_amount")
            overall_discount = request.session.get("overall_discount")

            if "sales_report" in request.POST and request.POST["sales_report"] == "pdf":
                buffer = BytesIO()

                doc = SimpleDocTemplate(buffer, pagesize=letter)

                styles = getSampleStyleSheet()
                centered_style = ParagraphStyle(
                    name="Centered", parent=styles["Heading1"], alignment=1
                )

                today_date = datetime.now().strftime("%Y-%m-%d")

                content = []

                company_details = f"<b>SneakerHeads</b><br/>Email: sneakerheadsweb@email.com<br/>Date: {
                    today_date}"
                content.append(Paragraph(company_details, styles["Normal"]))
                content.append(Spacer(1, 0.5 * inch))

                content.append(Paragraph("<b>Sales Report</b>", centered_style))
                content.append(Spacer(1, 0.5 * inch))

                data = [["Product", "Quantity", "Total Price", "Date"]]
                for sale in sales_data:
                    formatted_date = sale.order.placed_at.strftime("%a, %d %b %Y")
                    data.append(
                        [sale.product, sale.quantity, sale.each_price, formatted_date]
                    )

                table = Table(data, repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("TOPPADDING", (0, 0), (-1, 0), 12),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ]
                    )
                )

                content.append(table)

                content.append(Spacer(1, 0.5 * inch))

                overall_sales_count_text = f"<b>Overall Sales Count:</b> {
                    overall_sales_count}"
                overall_order_amount_text = f"<b>Overall Order Amount:</b> {
                    overall_order_amount}"
                overall_discount_amount_text = f"<b>Overall Discount:</b> {
                    overall_discount}"

                content.append(Paragraph(overall_sales_count_text, styles["Normal"]))
                content.append(Paragraph(overall_order_amount_text, styles["Normal"]))
                content.append(
                    Paragraph(overall_discount_amount_text, styles["Normal"])
                )

                doc.build(content)

                current_time = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
                file_name = f"Sales_Report_{current_time}.pdf"

                response = HttpResponse(
                    buffer.getvalue(), content_type="application/pdf"
                )
                response["Content-Disposition"] = (
                    f'attachment; filename="{
                    file_name}"'
                )

                return response

            elif (
                "sales_report" in request.POST
                and request.POST["sales_report"] == "excel"
            ):
                output = BytesIO()
                workbook = xlsxwriter.Workbook(output, {"in_memory": True})
                worksheet = workbook.add_worksheet("Sales Report")

                headings = [
                    "Product",
                    "Color",
                    "Quantity",
                    "Total Price",
                    "Date",
                    "Size",
                ]
                header_format = workbook.add_format({"border": 1, "bold": True})
                for col, heading in enumerate(headings):
                    worksheet.write(0, col, heading, header_format)

                for row, sale in enumerate(sales_data, start=1):
                    formatted_date = sale.order.placed_at.strftime("%a, %d %b %Y")
                    color = sale.product.product_color_image.color
                    size = sale.product.size

                    worksheet.write(
                        row, 0, sale.product.product_color_image.products.name
                    )
                    worksheet.write(row, 1, color)
                    worksheet.write(row, 2, sale.quantity)
                    worksheet.write(row, 3, sale.each_price)
                    worksheet.write(row, 4, formatted_date)
                    worksheet.write(row, 5, size)

                overall_row = len(sales_data) + 2
                worksheet.write(overall_row, 0, "Overall Sales Count:")
                worksheet.write(overall_row, 1, overall_sales_count)
                worksheet.write(overall_row + 1, 0, "Overall Order Amount:")
                worksheet.write(overall_row + 1, 1, overall_order_amount)
                worksheet.write(overall_row + 2, 0, "Overall Discount:")
                worksheet.write(overall_row + 2, 1, overall_discount)

                for i, heading in enumerate(headings):
                    max_length = max(
                        [
                            len(str(getattr(row, heading.lower(), "")))
                            for row in sales_data
                        ]
                        + [len(heading)]
                    )
                    worksheet.set_column(i, i, max_length + 2)

                date_width = max(
                    [
                        len(sale.order.placed_at.strftime("%a, %d %b %Y"))
                        for sale in sales_data
                    ]
                )
                worksheet.set_column(4, 4, date_width + 2)
                color_width = max(
                    [
                        len(color)
                        for color in [
                            sale.product.product_color_image.color
                            for sale in sales_data
                        ]
                    ]
                )
                worksheet.set_column(1, 1, color_width + 2)

                workbook.close()

                output.seek(0)
                response = HttpResponse(
                    output.getvalue(),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                current_time = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
                file_name = f"Sales Report {current_time}.xlsx"
                response["Content-Disposition"] = (
                    f'attachment; filename="{
                    file_name}"'
                )

                return response
        else:
            return redirect("admin_dashboard")
    else:
        return redirect("admin_login_page")


# ---------------------------------------------------------------- CC_PRODUCT OFFER MODULE PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------


@never_cache
@clear_old_messages
def product_offer_module_view(request):
    if request.user.is_superuser:
        product_offer = ProductOffer.objects.all().order_by("start_date", "end_date")
        context = {
            "today": today,
            "product_offer": product_offer,
            "is_active_product_offer": is_active_product_offer,
        }
        return render(request, "pages/offers/product_offer_modules.html", context)
    else:
        return redirect("admin_login_page")


@never_cache
@clear_old_messages
def product_offer_edit_page(request, product_color_image_name, color):
    if request.user.is_superuser:
        try:
            product_offer = ProductOffer.objects.get(
                product_color_image__products__name=product_color_image_name,
                product_color_image__color=color,
            )
            product_color = ProductColorImage.objects.all().order_by("products__name")
            context = {
                "product_offer": product_offer,
                "product_color": product_color,
                "is_active_product_offer": is_active_product_offer,
            }
            return render(request, "pages/offers/product_offer_edit_page.html", context)
        except ProductOffer.DoesNotExist:
            messages.error(request, "Product Offer not found")
            return redirect("product_offer_module_view")
    else:
        return redirect("admin_login_page")


@never_cache
@clear_old_messages
def product_offer_update(request, product_offer_id):
    if request.user.is_superuser:
        try:
            product_offer = ProductOffer.objects.get(pk=product_offer_id)

            if request.method == "POST":
                discount_percentage_str = request.POST.get("offer_discount")
                start_date_str = request.POST.get("offer_start_date")
                end_date_str = request.POST.get("offer_end_date")

                valid_product = True
                valid_discount_percentage = True
                valid_start_date = True
                valid_end_date = True

                today = timezone.now().date()
                offer_start_date = product_offer.start_date
                offer_end_date = product_offer.end_date

                if discount_percentage_str and start_date_str and end_date_str:
                    try:
                        discount_percentage = int(discount_percentage_str)
                    except ValueError:
                        messages.error(
                            request,
                            "Discount percentage should be a number without decimals or symbols.",
                        )
                        return redirect(
                            "product_offer_edit_page",
                            product_offer.product_color_image.products.name,
                            product_offer.product_color_image.color,
                        )

                    try:
                        start_date = datetime.strptime(
                            start_date_str, "%Y-%m-%d"
                        ).date()
                        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                    except ValueError:
                        messages.error(
                            request, "Please enter the dates in the format YYYY-MM-DD."
                        )
                        return redirect(
                            "product_offer_edit_page",
                            product_offer.product_color_image.products.name,
                            product_offer.product_color_image.color,
                        )

                    if not 5 <= discount_percentage <= 70:
                        valid_discount_percentage = False
                        messages.error(
                            request,
                            "Discount percentage should be minimum of 5%, and maximum of 70%.",
                        )

                    elif start_date < today and start_date != offer_start_date:
                        valid_start_date = False
                        messages.error(
                            request,
                            "Please select today's date or a future date for the start date.",
                        )

                    elif (
                        end_date <= start_date
                        and end_date <= today
                        and end_date != offer_end_date
                    ):
                        valid_end_date = False
                        messages.error(
                            request,
                            "Please select a future date for the offer end date, ensuring it is greater than today's date and the start date.",
                        )

                    if (
                        valid_product
                        and valid_discount_percentage
                        and valid_start_date
                        and valid_end_date
                    ):
                        try:
                            product_offer.discount_percentage = discount_percentage
                            product_offer.start_date = start_date
                            product_offer.end_date = end_date
                            product_offer.save()

                            messages.success(
                                request, "Product Offer Updated Successfully!"
                            )
                            return redirect("product_offer_module_view")
                        except:
                            messages.error(
                                request,
                                "Currently unable to update the product offer, try again after sometime.",
                            )
                            return redirect(
                                "product_offer_edit_page",
                                product_offer.product_color_image.products.name,
                                product_offer.product_color_image.color,
                            )
                    else:
                        return redirect(
                            "product_offer_edit_page",
                            product_offer.product_color_image.products.name,
                            product_offer.product_color_image.color,
                        )

                else:
                    messages.error(request, "Please fill in all required fields.")
                    return redirect(
                        "product_offer_edit_page",
                        product_offer.product_color_image.products.name,
                        product_offer.product_color_image.color,
                    )
            else:
                return redirect("product_offer_module_view")
        except ProductOffer.DoesNotExist:
            messages.error(request, "Product Offer not found.")
        return redirect(
            "product_offer_edit_page",
            product_offer.product_color_image.products.name,
            product_offer.product_color_image.color,
        )
    else:
        return redirect("admin_login_page")


@never_cache
@clear_old_messages
def product_offer_add_page(request):
    if request.user.is_superuser:
        product_color = ProductColorImage.objects.all().order_by("products__name")
        context = {
            "product_color": product_color,
            "is_active_product_offer": is_active_product_offer,
        }
        return render(request, "pages/offers/product_offer_add_page.html", context)
    else:
        return redirect("admin_login_page")


@never_cache
@clear_old_messages
def add_product_offer(request):
    if request.user.is_superuser:
        if request.method == "POST":
            product_color_image_id = request.POST.get("offer_name")
            discount_percentage_str = request.POST.get("offer_discount")
            end_date_str = request.POST.get("offer_end_date")

            valid_product = True
            valid_discount_percentage = True
            valid_end_date = True

            today = timezone.now().date()

            if product_color_image_id and discount_percentage_str and end_date_str:
                try:
                    discount_percentage = int(discount_percentage_str)
                except ValueError:
                    messages.error(
                        request,
                        "Discount percentage should be a number without decimals or symbols.",
                    )
                    return redirect("product_offer_add_page")
                try:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                except ValueError:
                    messages.error(
                        request, "Please enter the dates in the format YYYY-MM-DD."
                    )
                    return redirect("product_offer_add_page")
                try:
                    product_color_image = ProductColorImage.objects.get(
                        pk=product_color_image_id
                    )

                    if ProductOffer.objects.filter(
                        product_color_image=product_color_image, end_date__gte=today
                    ).exists():
                        valid_product = False
                        messages.error(request, "Product already have an offer")

                    elif not 5 <= discount_percentage <= 70:
                        valid_discount_percentage = False
                        messages.error(
                            request,
                            "Discount percentage should be minimum of 5%, and maximum of 70%.",
                        )

                    elif end_date <= today:
                        valid_end_date = False
                        messages.error(
                            request,
                            "Please select a future date for the offer end date.",
                        )

                    if valid_product and valid_discount_percentage and valid_end_date:
                        try:
                            ProductOffer.objects.create(
                                product_color_image=product_color_image,
                                discount_percentage=int(discount_percentage),
                                end_date=end_date,
                            )
                            messages.success(
                                request, "Offer Module Added Successfully!"
                            )
                            return redirect("product_offer_module_view")
                        except:
                            messages.error(
                                request,
                                "Unable to create a product offer at this moment,",
                            )
                            return redirect("product_offer_add_page")
                    else:
                        return redirect("product_offer_add_page")

                except ProductColorImage.DoesNotExist:
                    messages.error(request, "Selected product not found")
                    return redirect("product_offer_add_page")
            else:
                messages.error(request, "Please fill in all required fields")
            return redirect("product_offer_add_page")
        else:
            return redirect("product_offer_add_page")
    else:
        return redirect("admin_login_page")


@never_cache
@clear_old_messages
def delete_offer(request, product_offer_id):
    if request.user.is_superuser:
        try:
            product_offer = ProductOffer.objects.get(pk=product_offer_id)
            product_offer.delete()
            messages.success(request, "Product Offer have been successfully deleted!")
        except ProductOffer.DoesNotExist:
            messages.error(request, "Product offer not found")
        return redirect("product_offer_module_view")
    else:
        return redirect("admin_login_page")


# ---------------------------------------------------------------- CC_PRODUCT OFFER MODULE PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------


@never_cache
@clear_old_messages
def category_offer_module_view(request):
    if request.user.is_superuser:
        category_offers = CategoryOffer.objects.all().order_by("start_date", "end_date")
        context = {
            "today": today,
            "category_offers": category_offers,
            "is_active_product_offer": is_active_product_offer,
        }
        return render(request, "pages/offers/category_offer_module.html", context)
    else:
        return redirect("admin_login_page")


@never_cache
@clear_old_messages
def category_offers_add_page(request):
    if request.user.is_superuser:
        categories = Category.objects.all().order_by("name")
        context = {
            "categories": categories,
            "is_active_product_offer": is_active_product_offer,
        }
        return render(request, "pages/offers/category_offer_add_page.html", context)
    else:
        return redirect("admin_login_page")


@never_cache
@clear_old_messages
def add_category_offer(request):
    if request.user.is_superuser:
        if request.method == "POST":
            category_id = request.POST.get("category_id")
            discount_percentage_str = request.POST.get("offer_discount")
            end_date_str = request.POST.get("offer_end_date")

            is_every_field_valid = True

            today = timezone.now().date()

            if category_id and discount_percentage_str and end_date_str:
                try:
                    discount_percentage = int(discount_percentage_str)
                except ValueError:
                    messages.error(
                        request,
                        "Discount percentage should be a number without decimals or symbols.",
                    )
                    return redirect("category_offers_add_page")
                try:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                except ValueError:
                    messages.error(
                        request, "Please enter the dates in the format YYYY-MM-DD."
                    )
                    return redirect("category_offers_add_page")

                try:
                    category = Category.objects.get(pk=category_id)

                    if CategoryOffer.objects.filter(
                        category=category, end_date__gte=today
                    ).exists():
                        is_every_field_valid = False
                        messages.error(
                            request, "Offer already exist for this category."
                        )

                    elif not 5 <= discount_percentage <= 30:
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Discount percentage should be minimum of 5%, and maximum of 30%.",
                        )

                    elif end_date <= today:
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Please select a future date for the offer end date.",
                        )

                    if is_every_field_valid:
                        try:
                            CategoryOffer.objects.create(
                                category=category,
                                discount_percentage=discount_percentage,
                                end_date=end_date,
                            )
                            messages.success(
                                request,
                                f"Successfully added offer for {
                                             category.name} category",
                            )
                            return redirect("category_offer_module_view")

                        except:
                            messages.error(
                                request,
                                "Unable to create a category offer at this moment.",
                            )
                            return redirect("category_offers_add_page")
                    else:
                        return redirect("category_offers_add_page")
                except Category.DoesNotExist:
                    messages.error(request, "Selected category not found.")
                    return redirect("category_offers_add_page")
            else:
                messages.error(request, "Please fill all the fields.")
                return redirect("category_offers_add_page")
        else:
            return redirect("category_offers_add_page")
    else:
        return redirect("admin_login_page")


@never_cache
@clear_old_messages
def category_offer_edit_page(request, category_name):
    if request.user.is_superuser:
        try:
            category_offer = CategoryOffer.objects.get(category__name=category_name)
            categories = Category.objects.all().order_by("name")
            context = {
                "category_offer": category_offer,
                "categories": categories,
                "is_active_product_offer": is_active_product_offer,
            }
            return render(
                request, "pages/offers/category_offer_edit_page.html", context
            )
        except CategoryOffer.DoesNotExist:
            messages.error("Category Offer not found.")
            return redirect("category_offer_module_view")
    else:
        return redirect("admin_login_page")


@never_cache
@clear_old_messages
def category_offer_update(request, category_offer_id):
    if request.user.is_superuser:
        if request.method == "POST":
            try:
                category_offer = CategoryOffer.objects.get(pk=category_offer_id)

                discount_percentage_str = request.POST.get("offer_discount")
                start_date_str = request.POST.get("offer_start_date")
                end_date_str = request.POST.get("offer_end_date")

                is_every_field_valid = True

                offer_start_date = category_offer.start_date
                offer_end_date = category_offer.end_date

                if discount_percentage_str and start_date_str and end_date_str:
                    try:
                        discount_percentage = int(discount_percentage_str)
                    except ValueError:
                        messages.error(
                            request,
                            "Discount percentage should be a number without decimals or symbols.",
                        )
                        return redirect(
                            "category_offer_edit_page", category_offer.category.name
                        )
                    try:
                        start_date = datetime.strptime(
                            start_date_str, "%Y-%m-%d"
                        ).date()
                        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                    except ValueError:
                        messages.error(
                            request, "Please enter the dates in the format YYYY-MM-DD."
                        )
                        return redirect(
                            "category_offer_edit_page", category_offer.category.name
                        )

                    if not 5 <= discount_percentage <= 70:
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Discount percentage should be minimum of 5%, and maximum of 70%.",
                        )

                    elif start_date < today and start_date != offer_start_date:
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Please select today's date or a future date for the start date.",
                        )

                    elif (
                        end_date <= start_date
                        and end_date <= today
                        and end_date != offer_end_date
                    ):
                        is_every_field_valid = False
                        messages.error(
                            request,
                            "Please select a future date for the offer end date, ensuring it is greater than today's date and the start date.",
                        )

                    if is_every_field_valid:
                        try:
                            category_offer.discount_percentage = discount_percentage
                            category_offer.start_date = start_date
                            category_offer.end_date = end_date
                            category_offer.save()

                            messages.success(
                                request, "Category Offer Updated Successfully!"
                            )
                            return redirect("category_offer_module_view")
                        except:
                            messages.error(
                                request,
                                "Currently unable to update the product offer, try again after sometime.",
                            )
                            return redirect(
                                "category_offer_edit_page", category_offer.category.name
                            )
                    else:
                        return redirect(
                            "category_offer_edit_page", category_offer.category.name
                        )

            except CategoryOffer.DoesNotExist:
                messages.error(request, "Category Offer not found.")
                return redirect("category_offer_module_view")
        else:
            return redirect("category_offer_module_view")
    else:
        return redirect("admin_login_page")


@never_cache
@clear_old_messages
def delete_category_offer(request, category_offer_id):
    if request.user.is_superuser:
        try:
            category_offer = CategoryOffer.objects.get(pk=category_offer_id)
            category_offer.delete()
            messages.success(request, "Category Offer have been deleted!")
            return redirect("category_offer_module_view")
        except CategoryOffer.DoesNotExist:
            messages.error(request, "Category Offer not found.")
            return redirect("category_offer_module_view")
    else:
        return redirect("admin_login_page")


# ----------------------------------------------------------------  CC_COUPON PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------


@never_cache
@clear_old_messages
def coupon_page_view(request):
    if request.user.is_superuser:
        coupons = Coupon.objects.all()
        context = {"coupons": coupons, "is_active_coupon": is_active_coupon}
        return render(request, "pages/coupons/coupon.html", context)
    else:
        return redirect("admin_login_page")


@never_cache
@clear_old_messages
def add_coupon_page(request):
    if request.user.is_superuser:
        context = {"is_active_coupon": is_active_coupon}
        return render(request, "pages/coupons/add_coupon.html", context)
    else:
        return redirect("admin_login_page")


@never_cache
@clear_old_messages
def add_coupon(request):
    if request.user.is_superuser:
        if request.method == "POST":
            name_str = request.POST.get("coupon_name")
            discount_percentage_str = request.POST.get("offer_discount")
            end_date_str = request.POST.get("offer_end_date")
            minimum_amount_str = request.POST.get("minimum_amount")
            maximum_amount_str = request.POST.get("maximum_amount")

            valid_coupon_name = True
            valid_discount_percentage = True
            valid_end_date = True
            valid_min_max = True

            today = timezone.now().date()

            if (
                name_str
                and discount_percentage_str
                and end_date_str
                and minimum_amount_str
                and maximum_amount_str
            ):

                if not alphabets_pattern.match(name_str):
                    valid_coupon_name = False
                    messages.error(
                        request,
                        "Coupon name should contain only alphabetical characters & should not contain any spaces",
                    )
                    return redirect("add_coupon_page")

                name = name_str.upper()

                try:
                    discount_percentage = int(discount_percentage_str)
                except ValueError:
                    messages.error(
                        request,
                        "Discount percentage should be a number without decimals or symbols.",
                    )
                    return redirect("add_coupon_page")

                try:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                except ValueError:
                    messages.error(
                        request, "Please enter the dates in the format YYYY-MM-DD."
                    )
                    return redirect("add_coupon_page")

                try:
                    minimum_amount = int(minimum_amount_str)
                    maximum_amount = int(maximum_amount_str)
                except:
                    valid_min_max = False
                    messages.error(
                        request,
                        "Minimum and Maximum amounts should be a number without decimals or symbols.",
                    )
                    return redirect("add_coupon_page")

                if not (
                    2500 <= minimum_amount <= 35000 and 3000 <= maximum_amount <= 25000
                ):
                    valid_min_max = False
                    messages.error(
                        request,
                        "Both the minimum and maximum amounts should be between ₹2500 and ₹25000",
                    )
                    return redirect("add_coupon_page")

                elif maximum_amount <= minimum_amount:
                    valid_min_max = False
                    messages.error(
                        request, "Maximum amount should be greater than minimum amount."
                    )

                elif not 5 <= discount_percentage <= 20:
                    valid_discount_percentage = False
                    messages.error(
                        request,
                        "Discount percentage should be minimum of 5%, and maximum of 20%.",
                    )

                elif end_date <= today:
                    valid_end_date = False
                    messages.error(
                        request, "Please select a future date for the offer end date."
                    )

                try:
                    if (
                        valid_coupon_name
                        and valid_discount_percentage
                        and valid_end_date
                        and valid_min_max
                    ):
                        Coupon.objects.create(
                            name=name,
                            discount_percentage=discount_percentage,
                            end_date=end_date,
                            minimum_amount=minimum_amount,
                            maximum_amount=maximum_amount,
                        )
                        messages.success(request, "Coupon Added Successfully")
                        return redirect("coupon_page_view")
                except:
                    messages.error(
                        request,
                        "Unable to create a coupon at this moment, try after sometime.",
                    )
            else:
                messages.error(request, "Please fill in all the required fields")
        return redirect("add_coupon_page")
    else:
        return redirect("admin_login_page")


@never_cache
@clear_old_messages
def coupon_edit_page(request, coupon_id):
    if request.user.is_superuser:
        try:
            coupon = Coupon.objects.get(pk=coupon_id)
            context = {
                "coupon": coupon,
            }
            return render(request, "pages/coupons/coupon_edit_page.html", context)
        except Coupon.DoesNotExist:
            messages.error(request, "Coupon not found")
            return redirect("admin_dashboard")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect("admin_dashboard")
    else:
        return redirect("admin_login_page")


@never_cache
@clear_old_messages
def update_coupon(request, coupon_id):
    if request.user.is_superuser:
        try:
            coupon = Coupon.objects.get(pk=coupon_id)

            if request.method == "POST":

                coupon_start_date = coupon.start_date
                coupon_end_date = coupon.end_date

                name_str = request.POST.get("coupon_name")
                discount_percentage_str = request.POST.get("offer_discount")
                start_date_str = request.POST.get("offer_start_date")
                end_date_str = request.POST.get("offer_end_date")
                minimum_amount_str = request.POST.get("minimum_amount")
                maximum_amount_str = request.POST.get("maximum_amount")

                valid_name = True
                valid_discount_percentage = True
                valid_start_date = True
                valid_end_date = True
                valid_min_max = True

                today = timezone.now().date()

                if (
                    name_str
                    and discount_percentage_str
                    and end_date_str
                    and minimum_amount_str
                    and maximum_amount_str
                ):

                    if not alphabets_pattern.match(name_str):
                        valid_name = False
                        messages.error(
                            request,
                            "Coupon name should contain only alphabetical characters & should not contain any spaces",
                        )

                    else:
                        name = name_str.upper()

                        if (
                            Coupon.objects.filter(name=name)
                            .exclude(pk=coupon_id)
                            .exists()
                        ):
                            valid_name = False
                            messages.error(
                                request,
                                "A coupon with the same name already exists. Please choose a different name.",
                            )

                        try:
                            discount_percentage = int(discount_percentage_str)
                        except ValueError:
                            valid_discount_percentage = False
                            messages.error(
                                request,
                                "Discount percentage should be a number without decimals or symbols.",
                            )

                        try:
                            start_date = datetime.strptime(
                                start_date_str, "%Y-%m-%d"
                            ).date()
                            end_date = datetime.strptime(
                                end_date_str, "%Y-%m-%d"
                            ).date()
                        except ValueError:
                            valid_start_date = False
                            messages.error(
                                request,
                                "Please enter the dates in the format YYYY-MM-DD.",
                            )

                        try:
                            minimum_amount = int(minimum_amount_str)
                            maximum_amount = int(maximum_amount_str)
                        except:
                            valid_min_max = False
                            messages.error(
                                request,
                                "Minimum and Maximum amounts should be a number without decimals or symbols.",
                            )

                        if not 5 <= discount_percentage <= 20:
                            valid_discount_percentage = False
                            messages.error(
                                request,
                                "Discount percentage should be minimum of 5%, and maximum of 20%.",
                            )

                        elif start_date < today and start_date != coupon_start_date:
                            valid_start_date = False
                            messages.error(
                                request,
                                "Please select today's date or a future date for the start date.",
                            )

                        elif (
                            end_date <= start_date
                            or end_date <= today
                            and end_date != coupon_end_date
                        ):
                            valid_end_date = False
                            messages.error(
                                request,
                                "Please select a future date for the offer end date, ensuring it is greater than today's date and the start date.",
                            )

                        elif not (
                            2500 <= minimum_amount <= 35000
                            and 3000 <= maximum_amount <= 25000
                        ):
                            valid_min_max = False
                            messages.error(
                                request,
                                "Both the minimum and maximum amounts should be between ₹2500 and ₹25000",
                            )

                        elif maximum_amount <= minimum_amount:
                            valid_min_max = False
                            messages.error(
                                request,
                                "The maximum amount should be greater than the minimum amount.",
                            )

                        if (
                            valid_name
                            and valid_discount_percentage
                            and valid_start_date
                            and valid_end_date
                            and valid_min_max
                        ):
                            coupon.name = name
                            coupon.discount_percentage = discount_percentage
                            coupon.start_date = start_date
                            coupon.end_date = end_date
                            coupon.minimum_amount = minimum_amount
                            coupon.maximum_amount = maximum_amount
                            coupon.save()

                            messages.success(
                                request, "Coupon has been updated successfully"
                            )
                            return redirect("coupon_page_view")
                else:
                    messages.error(request, "Please fill in all required fields.")

            return redirect("coupon_edit_page", coupon_id)

        except Coupon.DoesNotExist:
            messages.error(request, "Coupon is not found")
            return redirect("coupon_page_view")
    else:
        return redirect("admin_login_page")


@never_cache
@clear_old_messages
def delete_coupon(request, coupon_id):
    if request.user.is_superuser:
        try:
            coupon = Coupon.objects.get(coupon_code=coupon_id)
            coupon.delete()
            messages.success(request, "Coupon have been deleted!")
        except Coupon.DoesNotExist:
            messages.error(request, "Coupon not found.")
        return redirect("coupon_page_view")
    else:
        return redirect("admin_login_page")


# ----------------------------------------------------------------  CC_BANNER PAGE FUNCTIONS STARTING FROM HERE ----------------------------------------------------------------


@never_cache
@clear_old_messages
def banner_view_page(request):
    if request.user.is_superuser:
        context = {
            "is_active_banner": is_active_banner,
        }
        return render(request, "pages/banner/banner_page.html", context)
    else:
        return redirect("admin_login_page")


@never_cache
@clear_old_messages
def banner_add_page_view(request):
    if request.user.is_superuser:
        context = {"is_active_banner": is_active_banner}
        return render(request, "pages/banner/banner_add_page.html", context)
    else:
        return redirect("admin_login_page")
