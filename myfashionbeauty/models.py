from django.db import models
from django.conf import settings
from django.contrib.auth.models import User, AbstractUser
import uuid

# Create your models here.


class Customer(AbstractUser):
    email = models.CharField(max_length=200)

    is_customer=models.BooleanField("is_customer", default=True)
    is_vendor=models.BooleanField("is_vendor", default=False)


    def __str__(self):
        return self.username


class Product(models.Model):
    vendor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200)
    price = models.FloatField(max_length=7, default=0.00)
    description = models.TextField(default="")
    type=models.CharField(default="none", max_length=50)
    image = models.ImageField(null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField(max_length=1000, blank=True)
    rating = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s review of {self.product.name}"

class Order(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True, blank=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    def __str__(self):
        return str(self.customer)+ " " + (str(self.paid))

    @property
    def shipping(self):
        shipping = True
        order_items = self.orderitem_set.all()
        return shipping

    @property
    def get_cart_total(self):
      orderitems = self.orderitem_set.all()
      if orderitems:
        total = sum([item.get_total for item in orderitems])
        return total
      return 0
    

    @property
    def get_cart_items(self):
     orderitems = self.orderitem_set.all()
     if orderitems:
        total = sum([item.quantity for item in orderitems])
        return total
     return 0


class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=0)
    date_added = models.DateTimeField(auto_now_add=True)

    @property
    def get_total(self):
        total = self.product.price * self.quantity
        return total


class ShippingAddress(models.Model):
    customer = models.ForeignKey(
    Customer, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    address = models.CharField(max_length=200, null=False)
    city = models.CharField(max_length=200, null=False)
    state = models.CharField(max_length=200, null=False)
    zipcode = models.CharField(max_length=200, null=False)
    country = models.CharField(max_length=200, null=False)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address
    

