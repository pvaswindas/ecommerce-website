from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings
from django.contrib.auth.models import User



class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(regex=r'^\d{10}$', message='Phone number must have 10 digits.')
        ]
    )
    
    class Gender(models.IntegerChoices):
        MALE = 1, 'Male'
        FEMALE = 2, 'Female'
        OTHER = 3, 'Other'
        
    gender = models.IntegerField(choices=Gender.choices, default=Gender.OTHER)
    dob = models.DateField(null=True)
    
    def __str__(self):
        return self.user.email


class Address(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    country = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    street_address = models.CharField(max_length=50)
    pin_code = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.country}, {self.state}, {self.city}, {self.street_address}, {self.pin_code}"

