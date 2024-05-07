# Generated by Django 5.0.2 on 2024-03-27 08:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("user_app", "__first__"),
    ]

    operations = [
        migrations.CreateModel(
            name="Banner",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                ("image_video", models.FileField(upload_to="banner_images/")),
                ("target_id", models.IntegerField()),
                ("target_name", models.CharField()),
                ("start_date", models.DateField()),
                ("expiry_date", models.DateField()),
                ("is_listed", models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name="Brand",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                ("country_of_origin", models.CharField(max_length=100)),
                ("manufacturer_details", models.TextField()),
                ("is_deleted", models.BooleanField(default=False)),
                ("is_listed", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                ("description", models.TextField()),
                ("is_deleted", models.BooleanField(default=False)),
                ("is_listed", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Coupon",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                ("value", models.BigIntegerField()),
                ("starting_date", models.DateField()),
                ("expiry_date", models.DateField()),
                ("is_listed", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("method_name", models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="Products",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField()),
                ("information", models.TextField()),
                ("type", models.CharField(max_length=50)),
                ("is_deleted", models.BooleanField(default=False)),
                ("is_listed", models.BooleanField(default=True)),
                (
                    "brand",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="admin_app.brand",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="admin_app.category",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ProductColorImage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("color", models.CharField(max_length=50)),
                ("price", models.PositiveBigIntegerField()),
                ("main_image", models.FileField(upload_to=" product_all_images/")),
                ("side_image", models.FileField(upload_to=" product_all_images/")),
                ("top_image", models.FileField(upload_to=" product_all_images/")),
                ("back_image", models.FileField(upload_to=" product_all_images/")),
                ("is_deleted", models.BooleanField(default=False)),
                ("is_listed", models.BooleanField(default=True)),
                (
                    "products",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="admin_app.products",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("order_status", models.CharField(max_length=100)),
                (
                    "address",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="user_app.address",
                    ),
                ),
                (
                    "coupon",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="admin_app.coupon",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="user_app.customer",
                    ),
                ),
                (
                    "payment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="admin_app.payment",
                    ),
                ),
                (
                    "products",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="admin_app.products",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Cart",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("in_stock", models.BooleanField(default=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="user_app.customer",
                    ),
                ),
                (
                    "products",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="admin_app.products",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ProductSize",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("size", models.CharField(max_length=50)),
                ("quantity", models.BigIntegerField()),
                ("is_listed", models.BooleanField(default=True)),
                ("is_deleted", models.BooleanField(default=False)),
                (
                    "product_color_image",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="admin_app.productcolorimage",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Review",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("rating", models.BigIntegerField()),
                ("review_text", models.TextField()),
                ("review_date", models.DateField()),
                ("verified_purchase", models.BooleanField(default=False)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="user_app.customer",
                    ),
                ),
                (
                    "products",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="admin_app.products",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Wishlist",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("in_stock", models.BooleanField(default=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="user_app.customer",
                    ),
                ),
                (
                    "products",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="admin_app.products",
                    ),
                ),
            ],
        ),
    ]
