# Generated by Django 5.0.2 on 2024-04-13 04:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0046_rename_product_productoffer_product_color_image"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="orders",
            name="delivery_date",
        ),
        migrations.AddField(
            model_name="orderitem",
            name="delivery_date",
            field=models.DateField(null=True),
        ),
    ]
