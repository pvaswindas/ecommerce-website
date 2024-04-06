from django.db import models



class Banner(models.Model):
    name = models.CharField(max_length = 200)
    image_video = models.FileField(upload_to= 'banner_images/')
    target_id = models.IntegerField()
    target_name = models.CharField()
    start_date = models.DateField()
    expiry_date = models.DateField()
    is_listed = models.BooleanField()
    
    def __str__(self):
        return self.name