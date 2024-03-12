from django.db import models


class Category(models.Model):
    name = models.CharField(max_length = 50)
    description = models.TextField()
    is_deleted = models.BooleanField(default = False)
    is_listed = models.BooleanField(default = False)
    
    def __str__(self):
        return self.name
    