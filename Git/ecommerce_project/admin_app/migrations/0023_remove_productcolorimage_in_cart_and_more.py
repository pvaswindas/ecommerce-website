# Generated by Django 5.0.2 on 2024-04-04 05:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0022_productcolorimage_in_cart'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productcolorimage',
            name='in_cart',
        ),
        migrations.RemoveField(
            model_name='productcolorimage',
            name='in_wishlist',
        ),
    ]