# Generated by Django 5.0.2 on 2024-05-02 12:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0080_alter_productsize_product_color_image"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productcolorimage",
            name="products",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="product_color_image",
                to="admin_app.products",
            ),
        ),
        migrations.AlterField(
            model_name="products",
            name="brand",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="products",
                to="admin_app.brand",
            ),
        ),
        migrations.AlterField(
            model_name="products",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="products",
                to="admin_app.category",
            ),
        ),
    ]
