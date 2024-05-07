# Generated by Django 5.0.2 on 2024-04-19 06:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0062_alter_cart_coupon"),
    ]

    operations = [
        migrations.AddField(
            model_name="orders",
            name="coupon_applied",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="orders",
            name="coupon_discount_percent",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="orders",
            name="coupon_maximum_amount",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="orders",
            name="coupon_minimum_amount",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="orders",
            name="coupon_name",
            field=models.CharField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="orders",
            name="discount_price",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
    ]
