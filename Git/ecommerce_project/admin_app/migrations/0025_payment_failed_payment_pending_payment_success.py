# Generated by Django 5.0.2 on 2024-04-05 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0024_orders_paid_orders_razorpay_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="failed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="payment",
            name="pending",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="payment",
            name="success",
            field=models.BooleanField(default=False),
        ),
    ]
