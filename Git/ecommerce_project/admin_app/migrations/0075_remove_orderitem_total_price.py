# Generated by Django 5.0.2 on 2024-04-28 09:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0074_alter_categoryoffer_category'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderitem',
            name='total_price',
        ),
    ]
