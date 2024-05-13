import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Banner, ProductColorImage

class BannerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product_color_image'].queryset = ProductColorImage.objects.order_by('products__name')

    class Meta:
        model = Banner
        fields = ['banner_name', 'banner_image', 'product_color_image', 'title', 'subtitle', 'price_text']
    
    def clean_banner_name(self):
        banner_name = self.cleaned_data.get('banner_name')
        if re.match(r'^[!@#$%^&*()_+\-=\[\]{};\'\\:"|,.<>\/?]*$', banner_name) or banner_name.strip() == '':
            raise forms.ValidationError("Banner name must contain at least one alphanumeric character.")
        return banner_name
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if re.match(r'^[!@#$%^&*()_+\-=\[\]{};\'\\:"|,.<>\/?]*$', title) or title.strip() == '':
            raise forms.ValidationError("Title must contain at least one alphanumeric character.")
        return title

    def clean_subtitle(self):
        subtitle = self.cleaned_data.get('subtitle')
        if re.match(r'^[!@#$%^&*()_+\-=\[\]{};\'\\:"|,.<>\/?]*$', subtitle) or subtitle.strip() == '':
            raise forms.ValidationError("Subtitle must contain at least one alphanumeric character.")
        return subtitle
    
    def clean_price_text(self):
        price_text = self.cleaned_data.get('price_text')
        if re.match(r'^[!@#$%^&*()_+\-=\[\]{};\'\\:"|,.<>\/?]*$', price_text) or price_text.strip() == '':
            raise forms.ValidationError("Price text must contain at least one alphanumeric character.")
        return price_text
    
    def clean_banner_image(self):
        banner_image = self.cleaned_data.get('banner_image')
        
        if not banner_image:
            if self.instance and self.instance.banner_image:
                return self.instance.banner_image
            else:
                raise forms.ValidationError("Banner image is required.")
        
        allowed_extensions = ['jpg', 'jpeg', 'png', 'svg']
        if not banner_image.name.lower().endswith(tuple(allowed_extensions)):
            raise forms.ValidationError("Only JPG, JPEG, PNG, and SVG formats are allowed.")
        
        return banner_image

    def clean_product_color_image(self):
        product_color_image = self.cleaned_data.get('product_color_image')
        if product_color_image:
            banners_with_product_color_image = Banner.objects.filter(product_color_image=product_color_image)
            if self.instance:
                banners_with_product_color_image = banners_with_product_color_image.exclude(pk=self.instance.pk)
            if banners_with_product_color_image.exists():
                raise forms.ValidationError("This product is already used in another banner.")
        return product_color_image
