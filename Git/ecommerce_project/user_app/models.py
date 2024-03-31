from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver



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
        return f"{self.user.first_name} {self.user.last_name}"
    
    
@receiver(post_save, sender=User)
def create_customer(sender, instance, created, **kwargs):
    if created:
        Customer.objects.create(user=instance)



class Address(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    name = models.CharField(max_length = 100, default = "")
    phone_number = models.CharField(
        max_length=10,
        default = "",
        validators=[
            RegexValidator(regex=r'^\d{10}$', message='Phone number must have 10 digits.')
        ]
    )
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    street_address = models.CharField(max_length=200)
    pin_code = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.name}, {self.country}, {self.state}, {self.city}, {self.street_address}, {self.pin_code}"

