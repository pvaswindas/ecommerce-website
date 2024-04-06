from django.db import models



class Coupon(models.Model):
    name = models.CharField(max_length = 200)
    value = models.BigIntegerField()
    starting_date = models.DateField()
    expiry_date = models.DateField()
    is_listed = models.BooleanField(default = True)
    
    def __str__(self):
        return self.name