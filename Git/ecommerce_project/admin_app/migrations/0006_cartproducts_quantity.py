# Generated by Django 5.0.2 on 2024-03-28 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0005_alter_cartproducts_product"),
    ]

    operations = [
        migrations.AddField(
            model_name="cartproducts",
            name="quantity",
            field=models.PositiveBigIntegerField(default=1),
        ),
    ]
