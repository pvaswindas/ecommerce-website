# Generated by Django 5.0.2 on 2024-04-16 06:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0056_coupon"),
    ]

    operations = [
        migrations.RenameField(
            model_name="coupon",
            old_name="coupon",
            new_name="coupon_code",
        ),
        migrations.AlterField(
            model_name="productoffer",
            name="start_date",
            field=models.DateField(auto_now_add=True),
        ),
    ]
