# Generated by Django 5.0.4 on 2024-05-08 07:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0083_orders_delivery_date"),
    ]

    operations = [
        migrations.DeleteModel(
            name="WalletTransaction",
        ),
    ]
