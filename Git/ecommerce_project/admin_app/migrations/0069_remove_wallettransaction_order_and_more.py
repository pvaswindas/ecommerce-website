# Generated by Django 5.0.2 on 2024-04-22 11:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0068_alter_wallettransaction_order"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="wallettransaction",
            name="order",
        ),
        migrations.AddField(
            model_name="wallettransaction",
            name="order_item",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="admin_app.orderitem",
            ),
        ),
    ]
