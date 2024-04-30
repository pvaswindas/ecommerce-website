from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
import string


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(
        max_length=10, null=True, blank=True,
        validators=[
            RegexValidator(regex=r'^\d{10}$',
                           message='Phone number must have 10 digits.')
        ]
    )

    class Gender(models.IntegerChoices):
        MALE = 1, 'Male'
        FEMALE = 2, 'Female'
        OTHER = 3, 'Other'

    gender = models.IntegerField(choices=Gender.choices, default=Gender.OTHER,
                                 null=True, blank=True)
    dob = models.DateField(null=True, blank=True)

    referral_code = models.CharField(default='', blank=True, null=True,
                                     max_length=10)

    used_referral_code = models.CharField(default='', blank=True, null=True,
                                          max_length=10)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def generate_referral_code(self):
        while True:
            user_username = self.user.username.upper()[:4]
            random_chars = ''.join(random.choices(
                string.ascii_uppercase + string.digits, k=6))
            code = user_username + random_chars
            if not Customer.objects.filter(referral_code=code).exists():
                return code


@receiver(post_save, sender=User)
def create_customer(sender, instance, created, **kwargs):
    if created:
        Customer.objects.create(user=instance)


class Address(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="")
    phone_number = models.CharField(
        max_length=10,
        default="",
        validators=[
            RegexValidator(regex=r'^\d{10}$',
                           message='Phone number must have 10 digits.')
        ]
    )
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    street_address = models.CharField(max_length=500)
    pin_code = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name}, {self.state}, {self.city}, {self.street_address}"
