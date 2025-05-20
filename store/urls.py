from . import views
from . import views
from django.urls import path

# store/urls.py

urlpatterns = [

    path('', views.index, name='index'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('contact/', views.contact, name='contact'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/increase/<int:product_id>/', views.cart_increase, name='cart_increase'),
    path('cart/decrease/<int:product_id>/', views.cart_decrease, name='cart_decrease'),
    path('checkout/', views.checkout, name='checkout'),
    path('success/<int:order_id>/', views.SuccessView.as_view(), name='success'),
    path('subscribe/', views.subscribe, name='subscribe'),
]