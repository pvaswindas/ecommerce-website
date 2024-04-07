# Generated by Django 5.0.2 on 2024-04-06 11:39

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('value', models.BigIntegerField()),
                ('starting_date', models.DateField()),
                ('expiry_date', models.DateField()),
                ('is_listed', models.BooleanField(default=True)),
            ],
        ),
    ]