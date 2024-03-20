from django.db import models




class Category(models.Model):
    name = models.CharField(max_length = 50)
    description = models.TextField()
    is_deleted = models.BooleanField(default = False)
    is_listed = models.BooleanField(default = True)
    
    def __str__(self):
        return self.name
    
    
    
class Brand(models.Model):
     name = models.CharField(max_length = 50)
     country_of_origin = models.CharField(max_length = 100)
     manufacturer_details = models.TextField()
     is_deleted = models.BooleanField(default = False)
     is_listed = models.BooleanField(default = True)
     
     
     def __str__(self):
        return self.name
        
    
    
    
class Product(models.Model):
    name = models.CharField(max_length = 100)
    description = models.TextField()
    price = models.BigIntegerField()
    category = models.ForeignKey(Category, on_delete = models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete = models.CASCADE)
    is_deleted = models.BooleanField(default = False)
    is_listed = models.BooleanField(default = True)
    
    
    def __str__(self):
        return self.name
    
    

    

class ProductColorImage(models.Model):
    product = models.ForeignKey(Product, on_delete = models.CASCADE)
    color = models.CharField(max_length = 50)
    
    main_image =  models.FileField(upload_to= ' product_all_images/')
    side_image = models.FileField(upload_to= ' product_all_images/')
    top_image = models.FileField(upload_to= ' product_all_images/')
    back_image = models.FileField(upload_to= ' product_all_images/')
    
    

    
class ProductVariant(models.Model):
    size = models.CharField(max_length = 50)
    quantity = models.BigIntegerField()
    is_listed = models.BooleanField(default = True)
    is_deleted = models.BooleanField(default = False)
    
    def __str__(self):
        return self.size

 
    
    
    

    
    
    
    
    # //hello