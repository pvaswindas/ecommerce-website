# Generated by Django 5.0.2 on 2024-04-21 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0063_orders_coupon_applied_orders_coupon_discount_percent_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='total_price',
            field=models.PositiveBigIntegerField(default=0),
        ),
    ]
