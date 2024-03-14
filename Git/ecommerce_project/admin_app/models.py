from django.db import models




class Category(models.Model):
    name = models.CharField(max_length = 50)
    description = models.TextField()
    is_deleted = models.BooleanField(default = False)
    is_listed = models.BooleanField(default = False)
    
    def __str__(self):
        return self.name
    
    
    
class Brand(models.Model):
     name = models.CharField(max_length = 50)
     country_of_origin = models.CharField(max_length = 100)
     manufacturer_details = models.TextField()
     is_deleted = models.BooleanField(default = False)
     is_listed = models.BooleanField(default = False)
     
     
     def __str__(self):
        return self.name
        
    
    
    
class Product(models.Model):
    name = models.CharField(max_length = 50)
    description = models.TextField()
    quantity = models.BigIntegerField()
    price = models.BigIntegerField()
    category = models.ForeignKey(Category, on_delete = models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete = models.CASCADE)
    main_image = models.FileField(upload_to = 'product_images/')
    side_view_image = models.FileField(upload_to = 'product_images/')
    back_view_image = models.FileField(upload_to = 'product_images/')
    is_deleted = models.BooleanField(default = False)
    is_listed = models.BooleanField(default = False)
    
    
    def __str__(self):
        return self.name
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    