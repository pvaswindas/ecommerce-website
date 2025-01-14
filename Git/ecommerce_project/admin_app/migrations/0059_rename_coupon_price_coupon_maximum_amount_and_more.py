# Generated by Django 5.0.2 on 2024-04-18 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0058_cart_coupon_cart_coupon_applied"),
    ]

    operations = [
        migrations.RenameField(
            model_name="coupon",
            old_name="coupon_price",
            new_name="maximum_amount",
        ),
        migrations.RemoveField(
            model_name="coupon",
            name="product_color_image",
        ),
        migrations.AddField(
            model_name="coupon",
            name="minimum_amount",
            field=models.PositiveBigIntegerField(blank=True, default=0),
        ),
    ]
