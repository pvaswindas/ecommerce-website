# Generated by Django 5.0.2 on 2024-04-18 15:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0061_alter_coupon_coupon_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cart",
            name="coupon",
            field=models.CharField(blank=True, null=True),
        ),
    ]
