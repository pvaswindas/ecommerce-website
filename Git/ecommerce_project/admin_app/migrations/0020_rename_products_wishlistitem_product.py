# Generated by Django 5.0.2 on 2024-04-03 15:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "admin_app",
            "0019_remove_wishlist_in_stock_remove_wishlist_products_and_more",
        ),
    ]

    operations = [
        migrations.RenameField(
            model_name="wishlistitem",
            old_name="products",
            new_name="product",
        ),
    ]
