from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.forms.widgets import TextInput
from .models import Customer,Review , Product, ShippingAddress

class CreateUserForm(UserCreationForm):
    class Meta:
        model = Customer
        fields = ('username', 'email', 'password1', 'password2', 'is_customer','is_vendor')
     



class ReviewForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    rating = forms.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = Review
        fields = ['text', 'rating']




class ProductForm(forms.ModelForm):
    description = forms.CharField(widget=TextInput(attrs={'style': 'height: 100px;'}))
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'type', 'image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pre-populate form with existing product data
        instance = kwargs.get('instance')
        if instance:
            self.initial['name'] = instance.name
            self.initial['description'] = instance.description
            self.initial['price'] = instance.price
            self.initial['type'] = instance.type
            self.initial['image'] = instance.image
            
    

class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ['address', 'city', 'state', 'zipcode', 'country']

