from django.urls import path
from . import views

urlpatterns = [
        #Leave as empty string for base url
	path('register/', views.registerPage, name="register"),
    path('login/', views.loginPage, name="login"),	
    path('logout/', views.logoutUser, name="logout"),
    
	path('', views.store, name="store"),
	path('cart/', views.cart, name="cart"),
	path('checkout/', views.checkout, name="checkout"),

    path('add_product/', views.add_product, name="add_product"),
    path('search/', views.product_search, name="product_search"),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name="product_view"),
    path('product/<int:product_id>/', views.product_detail, name="product_detail"),
    path('add_review/<int:product_id>/', views.add_review, name="add_review"),
    
	path('update_item/', views.updateItem, name="update_item"),
    path('add_cart/<int:pk>', views.add_cart, name="add_item"),
    path('update_add_cart/<int:pk>', views.update_add_cart, name="update_add_item"),
    path('update_remove_cart/<int:pk>', views.update_remove_cart, name="update_remove_item"),
    path('delete_item/<int:pk>', views.delete_item, name="delete_item"),
    path('process_order/', views.processOrder, name="process_order"),
    path('edit_product/<int:product_id>/', views.edit_product, name="edit_product"),

        
    path('payment', views.payment, name="payment"),
    path('vendor/', views.vendor, name="vendor"),
    path('vendor/delete/<int:pk>', views.delete_product, name="delete_product"),
    
    path('appointments/', views.list_scheduled_appointments, name="appointments"),
    path('categories/<str:category>', views.categories, name="categories"),
    path('delivered/<int:order_id>/', views.order_delivered, name='order_delivered'),
    path('paid_orders/', views.paid_orders, name="paid_orders"),

    ]
