# Generated by Django 5.0.2 on 2024-04-01 06:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0011_remove_orders_coupon'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='each_price',
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='orders',
            name='number_of_orders',
            field=models.PositiveBigIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='orders',
            name='shipping_charge',
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='orders',
            name='subtotal',
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='orders',
            name='total_charge',
            field=models.PositiveBigIntegerField(default=0),
        ),
    ]
