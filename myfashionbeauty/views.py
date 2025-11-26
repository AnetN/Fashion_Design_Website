from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.http import JsonResponse
import json
import datetime 
from django.db.models import Q
from .models import * 
import requests
from requests.auth import HTTPBasicAuth
import base64
from django.views.generic import DetailView
from .forms import ReviewForm, ProductForm
from .utils import cookieCart, cartData, guestOrder, paidcartData
from django.contrib.auth.forms import UserCreationForm
from .forms import CreateUserForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
import uuid


def registerPage(request):
    if request.user.is_authenticated:
        return redirect('store')
    else:
        customer_data=Customer()
        form = CreateUserForm()
        
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():
                user_type=request.POST['user-type']

                new=form.save(commit=False)
                if user_type == "customer":
                    new.is_customer=True
                    new.is_vendor=False
                else:
                    new.is_customer=False
                    new.is_vendor=True
                new.save()
                user = form.cleaned_data.get('username')
                messages.success(request, 'Account was created for ' + user)
                return redirect('login')

    context= {'form' :form}
    return render(request, 'register.html',context)


def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_customer:
                return redirect('store')  #    customer page URL name
            elif user.is_vendor:
                return redirect('vendor')  #   vendor page URL name
        else:
            messages.error(request, 'Invalid login credentials')
    return render(request, 'login.html')


def logoutUser(request):
	logout(request)
	return redirect('login')


@login_required(login_url='login')
def store(request):
    data = cartData(request)
    cartItems = data['cartItems']
    products = Product.objects.all()
    reviews = Review.objects.all()
    context = {'products': products, 'reviews': reviews, 'cartItems':cartItems}
    return render(request, 'store.html', context)


@login_required(login_url='login')
def cart(request):

    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items':items, 'order':order, 'cartItems':cartItems}
    return render(request, 'cart.html', context)




@login_required(login_url='login')
def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']

    # Get the customer and product objects
    customer = request.user.customer
    product = Product.objects.get(id=productId)

    # Get the order and order item for the customer and product
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    # Update the order item quantity based on the action
    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    # Save the updated order item
    orderItem.save()

    # If the order item quantity is 0, delete it
    if orderItem.quantity <= 0:
        orderItem.delete()

    # Return a JSON response indicating the item was added or removed
    if action == 'add':
        message = 'Item was added'
    elif action == 'remove':
        message = 'Item was removed'
    return JsonResponse(message, safe=False)


@login_required(login_url='login')
def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('vendor')
    else:
        form = ProductForm(instance=product)
    return render(request, 'edit_product.html', {'form': form})


@login_required(login_url='login')
def delete_item(request, pk):

    order = get_object_or_404(OrderItem, id=pk)

    if order.quantity > 1:
        order.quantity -= 1
        order.save()
        return redirect('cart')
    else:
        order.delete()
        return redirect('cart')


@login_required(login_url='login')
def processOrder(request):
    data = {}
    #mpesa code for stkpush'
    mpesa_express_shortcode="174379"
    mpesa_passkey="bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
    mpesa_consumer_key="UskIemRd2rJ8OdWjIA0Mz8qUGEWtuq6D"
    mpesa_consumer_secret="DghV05qhSqmcO6Pd"
    timestamp=datetime.datetime.now().strftime("%Y%m%d%H%M%S")#get timestamp in fom of string

    #get password
    data_to_encode=mpesa_express_shortcode +mpesa_passkey+ timestamp
    encoded=base64.b64encode(data_to_encode.encode())
    decoded_password=encoded.decode('utf-8')

    #auth credentials ur to get an access token
    auth_url ="https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r=requests.get(auth_url, auth=HTTPBasicAuth(mpesa_consumer_key,mpesa_consumer_secret))

    access_token=r.json()['access_token']

    #stk push url
    api_url="https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers={
        "Authorization":"Bearer %s" % access_token
    }
# get data from request
    data = json.loads(request.body)
    print(data)
    shipping_data = data.get('shipping', {})
    print(shipping_data)
    
# get data from phone

    request_payment={
        "BusinessShortCode":mpesa_express_shortcode,
        "Password": decoded_password,
        "Timestamp":timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount":{order.get_cart_total},
        "PartyA":f"254796258358",
        "PartyB":mpesa_express_shortcode,
        "PhoneNumber":f"254796258358",
        "CallBackURL":"https://darajambili.herokuapp.com/express-payment",
        "AccountReference":"BeautyNfashion",
        "TransactionDesc":"order payment"
    }

    response=requests.post(api_url, json=request_payment, headers=headers)

    transaction_id = datetime.datetime.now().timestamp()
    
    if request.user.is_authenticated:
        customer = request.user.is_customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        data["form"] = request.POST
    else:
        customer, order = guestOrder(request, data)
    
    try:
        total = float(data['total'])
    except KeyError:
        return JsonResponse({'error': 'Invalid request data. Please provide a valid total amount.'}, status=400)
    
    except ValueError:
        return JsonResponse({'error': 'Invalid total amount. Please provide a valid number.'}, status=400)
    
    order.transaction_id = transaction_id
    if total == order.get_cart_total():
        if response:
         order.complete = True
         order.save()

    if request.method == "POST":
        address=request.POST['address']
        city=request.POST['city']
        state=request.POST['state']
        zipcode=request.POST['zipcode']
        country=request.POST['country']

        print(address)

        s=ShippingAddress.objects.create(
            customer=get_object_or_404(Customer,username=request.user.username),
            order =get_object_or_404(Order, customer=get_object_or_404(Customer,username=request.user.username)),
            address=address,
            city =city, 
            state =state,
            zipcode=zipcode,
            country=country
        )
        s.save()


# Save shipping address if shipping is True

    if True:
        print("data is saving......")
        shipping_data = data.get("shippingData")
        s=ShippingAddress.objects.create(
        customer=customer,
        order=order,
        address=shipping_data['address'],
        city=shipping_data['city'],
        state=shipping_data['state'],
        zipcode=shipping_data['zipcode'],
        country=shipping_data['country'],
        )
        s.save()
        print("data saved")
    

    return JsonResponse('Payment submitted..', safe=False)


def vendor(request):
    if request.user.is_authenticated and request.user.is_vendor:
        products = Product.objects.filter(vendor=request.user)
        context = {'products': products}
        return render(request, 'vendor.html', context)
    else:
        return redirect('login')


def delete_product(request, pk):
     data=Product.objects.get(id=pk)
     data.delete()
     return redirect("vendor")

# product review view function
@login_required
def add_review(request, product_id):
    transaction_id_str=request.session.get('transaction_id')
    transaction_id = uuid.UUID(transaction_id_str)

    order = get_object_or_404(Order, transaction_id=transaction_id)
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            return redirect('product_detail', product_id)

    else:
        form = ReviewForm()

    return render(request, 'add_review.html', {'product': product, 'form': form})

def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    reviews = Review.objects.filter(product=product).order_by('-created_at')
    return render(request, 'product_detail.html', {'product': product, 'reviews': reviews})


def update_add_cart(request, pk):
     # Get the customer and product objects
    customer = get_object_or_404(Customer, username=request.user.username)
    product = Product.objects.get(id=pk)

    # Get the order and order item for the customer and product
    order= Order.objects.get(customer=customer)
    if OrderItem.objects.filter(order=order, product=product).exists():
        orderItem= OrderItem.objects.get(order=order, product=product)
        orderItem.quantity += 1
        orderItem.save()

     # Save the updated order item
    return redirect('cart')


def add_cart(request, pk):
     # Get the customer and product objects
    customer = get_object_or_404(Customer, username=request.user.username)
    product = Product.objects.get(id=pk)

    # Get the order and order item for the customer and product
    # order= Order.objects.get(customer=customer)
    order = Order.objects.filter(customer=customer).latest('id')
    if OrderItem.objects.filter(order=order, product=product).exists():
        orderItem= OrderItem.objects.get(order=order, product=product)
        orderItem.quantity += 1
        orderItem.save()
    else:
       orderitem=OrderItem()
       orderitem.product=product
       orderitem.order=order
       orderitem.quantity = 1
       orderitem.save()


     # Save the updated order item
    return redirect('store')


def update_remove_cart(request, pk):
     # Get the customer and product objects
    customer = get_object_or_404(Customer, username=request.user.username)
    product = Product.objects.get(id=pk)

    # Get the order and order item for the customer and product
    # order= Order.objects.get(customer=customer)
    
    order = Order.objects.filter(customer=customer).latest('id')
    if OrderItem.objects.filter(order=order, product=product).exists():
        orderItem= OrderItem.objects.get(order=order, product=product)
        orderItem.quantity -= 1
        orderItem.save()



     # Save the updated order item
    return redirect('cart')



@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = request.user
            product.save()
            return redirect('vendor')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})



class ProductDetailView(DetailView):
    model = Product
    template_name = 'product_view.html'

def product_search(request):
    query = request.GET.get('q')
    if query:
        products = Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query))
    else:
        products = Product.objects.all()
    context = {'products': products, 'query': query}
    return render(request, 'product_search.html', context)    



def checkout(request):
    if request.method == "POST":
        address=request.POST['address']
        city=request.POST['city']
        state=request.POST['state']
        zipcode=request.POST['zipcode']
        country=request.POST['country']

        print(address)
        customer = get_object_or_404(Customer, username=request.user.username)
        order = Order.objects.filter(customer=customer).first()
        s=ShippingAddress.objects.create(
            customer=customer,
            order = order,
            address=address,
            city =city, 
            state =state,
            zipcode=zipcode,
            country=country
        )
        s.save()
        data = cartData(request)
        order = data['order']
        request.session['order']=order.get_cart_total

        return redirect("payment")
    else:
        data = cartData(request)
        cartItems = data['cartItems']
        order = data['order']
        items = data['items']
        context = {'items':items, 'order':order, 'cartItems':cartItems}
        return render(request, "checkout.html", context)
    
def payment(request):
    order = None
    if request.method == "POST":
        number = request.POST['number']
        amount = request.POST['amount']
        email = request.POST['email']
        print(number)
        print(amount)
        print(email)
        data = cartData(request)
        cartItems = data['cartItems']
        order = data['order']
        items = data['items']

        # mpesa code for stkpush
        mpesa_express_shortcode = "174379"
        mpesa_passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
        mpesa_consumer_key = "UskIemRd2rJ8OdWjIA0Mz8qUGEWtuq6D"
        mpesa_consumer_secret = "DghV05qhSqmcO6Pd"
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # get timestamp in fom of string

        # get password
        data_to_encode = mpesa_express_shortcode + mpesa_passkey + timestamp
        encoded = base64.b64encode(data_to_encode.encode())
        decoded_password = encoded.decode('utf-8')

        # auth credentials ur to get an access token
        auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        r = requests.get(auth_url, auth=HTTPBasicAuth(mpesa_consumer_key, mpesa_consumer_secret))

        access_token = r.json()['access_token']

        # stk push url
        api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        headers = {"Authorization": "Bearer %s" % access_token}

        request_payment = {
            "BusinessShortCode": mpesa_express_shortcode,
            "Password": decoded_password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": float(amount),
            "PartyA": f"{number}",
            "PartyB": mpesa_express_shortcode,
            "PhoneNumber": f"{number}",
            "CallBackURL": "https://darajambili.herokuapp.com/express-payment",
            "AccountReference": "BeautyNfashion",
            "TransactionDesc": "order payment"
        }

       
        product_names = [(item.product.name, item.product.price, item.quantity) for item in items]
        product_strings = [f'{name} (Ksh {price}) x {quantity}' for name, price, quantity in product_names]
        message = 'Thank you for your order!  Your goods will arrive in 7 business days.  Your order details are as follows: ' + ', '.join(product_strings) +',' + 'total is ' + str(float(amount)),      
        send_mail(
                'Order Confirmation',
                f'{message}' ,
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
                
            )
        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            request.session['product_id']=item.product.id

        for item in order_items:
            item.delete()
    # Redirect the user to the order confirmation page
        response = requests.post(api_url, json=request_payment, headers=headers)
        if response:
            paid_order=get_object_or_404(Order, id=order.id)
            paid_order.paid=True
            paid_order.save()
            request.session['transaction_id'] = str(paid_order.transaction_id)
            print("saved")
            print(response.text)
            messages.info(request, "Payment has been processed")
            return redirect('store')

        else:
            order = request.session.get('order')
            print(order)
            return redirect('payment')
    else:
        data = cartData(request)
        cartItems = data['cartItems']
        order = data['order']
        items = data['items']
        return render(request, "mpesa.html", {'order': order.get_cart_total})
        
    
#My beauty_appointments api
token = "api1680016187dQzkiUl87PGu0IZChKMy214155"

#Appointment schedule view and api
def list_scheduled_appointments(request):
    list_scheduled_appointments_api = f'https://appointmentthing.com/api/v1/appointments/list/?token={token}&type=upcoming'
    try:
        response = requests.get(list_scheduled_appointments_api)
        data = response.json()
        return render(request, "appointments.html", {'data': data['appointments']})
    except:
        data = {}
        return render(request, "appointments.html",{'data':data})


# categories view
def categories(request, category):
    try:
        product=Product.objects.filter(type=category)
    except:
        product={}
    return render(request, "categories.html", {"products": product})


def paid_orders(request):
    
    transaction_id = request.session.get('transaction_id')
    order = get_object_or_404(Order, transaction_id=transaction_id)
    print(transaction_id)
    order_items = OrderItem.objects.filter(order=order)
    
    if request.method == 'POST':
        order.complete = True
        order.save()
        return redirect('add_review', transaction_id=transaction_id)

    return render(request, 'paid_orders.html', {'order': order, 'order_items': order_items})



def order_delivered(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.complete = True
    order.save()
    return redirect('add_review', product_id=request.session.get('product_id'))

