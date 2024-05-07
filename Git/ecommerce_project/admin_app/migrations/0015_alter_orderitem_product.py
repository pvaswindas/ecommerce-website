# Generated by Django 5.0.2 on 2024-04-01 06:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0014_alter_orders_payment"),
    ]

    operations = [
        migrations.AlterField(
            model_name="orderitem",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="admin_app.productsize"
            ),
        ),
    ]
