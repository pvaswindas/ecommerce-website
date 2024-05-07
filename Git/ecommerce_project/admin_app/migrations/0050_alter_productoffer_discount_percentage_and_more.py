# Generated by Django 5.0.2 on 2024-04-13 04:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0049_alter_productoffer_offer_price"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productoffer",
            name="discount_percentage",
            field=models.PositiveBigIntegerField(),
        ),
        migrations.AlterField(
            model_name="productoffer",
            name="offer_price",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
    ]
