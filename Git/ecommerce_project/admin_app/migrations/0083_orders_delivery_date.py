# Generated by Django 5.0.2 on 2024-05-05 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0082_orders_order_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="orders",
            name="delivery_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
