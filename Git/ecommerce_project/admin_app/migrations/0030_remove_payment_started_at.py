# Generated by Django 5.0.2 on 2024-04-07 10:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0029_alter_payment_paid_at"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="payment",
            name="started_at",
        ),
    ]
