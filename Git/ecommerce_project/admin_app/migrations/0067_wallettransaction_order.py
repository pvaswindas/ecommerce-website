# Generated by Django 5.0.2 on 2024-04-22 07:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0066_alter_wallettransaction_money_deposit_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='wallettransaction',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='admin_app.orderitem'),
        ),
    ]