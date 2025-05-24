from . import views
from . import views_payment
from django.urls import path

# store/urls.py
app_name = 'store'

urlpatterns = [
    # الصفحات الرئيسية
    path('', views.index, name='index'),
    path('products/', views.product_list, name='product_list'),
    path('products/<str:gender>/', views.product_list, name='product_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('contact/', views.contact, name='contact'),
    
    # سلة التسوق
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/increase/<int:product_id>/', views.cart_increase, name='cart_increase'),
    path('cart/decrease/<int:product_id>/', views.cart_decrease, name='cart_decrease'),
    
    # الشحن والدفع
    path('checkout/', views.checkout, name='checkout'),
    path('success/<int:order_id>/', views.SuccessView.as_view(), name='success'),
    
    # صفحات الدفع والتقييم
    path('payment/<int:order_id>/', views_payment.payment_info, name='payment_info'),
    path('payment/<int:order_id>/complete/', views_payment.complete_payment, name='complete_payment'),
    path('order/<int:order_id>/rate/', views_payment.rate_products, name='rate_products'),
    path('order/<int:order_id>/rate/<int:product_id>/', views_payment.rate_product, name='rate_product'),
    
    # أخرى
    path('subscribe/', views.subscribe, name='subscribe'),
    path('payment/<int:order_id>/process/', views_payment.process_payment, name='process_payment'),
]