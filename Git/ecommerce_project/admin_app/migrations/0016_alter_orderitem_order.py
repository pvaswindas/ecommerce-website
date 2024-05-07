# Generated by Django 5.0.2 on 2024-04-01 06:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0015_alter_orderitem_product"),
    ]

    operations = [
        migrations.AlterField(
            model_name="orderitem",
            name="order",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="admin_app.orders"
            ),
        ),
    ]
