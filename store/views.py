import smtplib
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.views.generic import DetailView
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, ProductImage, Order, OrderItem

class SuccessView(DetailView):
    model = Order
    template_name = 'store/success.html'
    context_object_name = 'order'

    def get_object(self):
        return get_object_or_404(Order, id=self.kwargs['order_id'])





def index(request):
    categories = Category.objects.all()
    return render(request, 'store/index.html', {'categories': categories})


def product_list(request):
    category_slug = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_rating = request.GET.get('min_rating')
    gender = request.GET.get('gender', 'all')
    
    products = Product.objects.all()
    
    if category_slug:
        products = products.filter(category__name=category_slug)
        
    if min_price:
        products = products.filter(price__gte=min_price)
        
    if max_price:
        products = products.filter(price__lte=max_price)
        
    if min_rating:
        products = products.filter(average_rating__gte=min_rating)
    
    if gender and gender != 'all':
        # تحويل قيمة gender من الرابط إلى القيمة المناسبة في قاعدة البيانات
        gender_mapping = {
            'men': 'M',
            'women': 'F',
            'unisex': 'U'
        }
        # استخدام القيمة المحولة إذا كانت موجودة في التعيين، وإلا استخدام القيمة الأصلية
        db_gender = gender_mapping.get(gender.lower(), gender)
        products = products.filter(gender=db_gender)
    
    return render(request, 'store/products.html', {
        'products': products,
        'current_category': category_slug,
        'min_price': min_price,
        'max_price': max_price,
        'min_rating': min_rating,
        'gender_filter': gender
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'store/product_detail.html', {'product': product})


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})

    if str(product.id) in cart:
        cart_quantity = cart[str(product.id)]
    else:
        cart_quantity = 0

    # التأكد من أن الكمية المطلوبة لا تتجاوز المتوفر
    if cart_quantity + 1 > product.quantity:
        messages.error(request, f"عذرًا، لا يوجد كمية كافية من {product.name}")
        return redirect('product_detail', product_id=product_id)

    cart[product_id] = cart.get(product_id, 0) + 1
    request.session['cart'] = cart
    return redirect('view_cart')


def cart_increase(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})

    current_quantity = cart.get(str(product.id), 0)

    if current_quantity < product.quantity:
        cart[str(product.id)] = current_quantity + 1
        messages.success(request, f"تم زيادة عدد {product.name}")
    else:
        messages.error(request, f"لا يمكن زيادة العدد، لا يوجد رصيد كافٍ من {product.name}")

    request.session['cart'] = cart
    return redirect('view_cart')


def cart_decrease(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})

    current_quantity = cart.get(str(product.id), 0)

    if current_quantity > 1:
        cart[str(product.id)] = current_quantity - 1
        messages.info(request, f"تم تقليل عدد {product.name}")
    else:
        del cart[str(product.id)]
        messages.info(request, f"تم إزالة {product.name} من العربة")

    request.session['cart'] = cart
    return redirect('view_cart')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        # يمكنك هنا إرسال البريد أو حفظه
        return render(request, 'store/contact_success.html')
    return render(request, 'store/contact.html')

def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, 'الرجاء إدخال بريد إلكتروني صحيح.')
            return redirect('index')
            
        subject = 'شكرًا على الاشتراك في نشرتنا البريدية'
        message = 'شكرًا لك على الاشتراك في نشرتنا البريدية. سنقوم بإعلامك بأحدث المنتجات والعروض.'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email]
        
        try:
            send_mail(subject, message, email_from, recipient_list)
            messages.success(request, 'تم الاشتراك بنجاح! شكرًا لك.')
        except smtplib.SMTPException as e:
            messages.error(request, f'حدث خطأ في الاتصال بخادم البريد: {str(e)}. الرجاء المحاولة لاحقًا.')
        except socket.error as e:
            messages.error(request, f'تعذر الاتصال بخادم البريد: {str(e)}. الرجاء المحاولة لاحقًا.')
        except Exception as e:
            messages.error(request, 'حدث خطأ غير متوقع أثناء إرسال بريد التأكيد. الرجاء المحاولة لاحقًا.')
            
        return redirect('index')
    
    return redirect('index')


def view_cart(request):
    cart = request.session.get('cart', {})
    product_ids = cart.keys()

    if not product_ids:
        return render(request, 'store/cart.html', {
            'cart_items': [],
            'total_price': 0
        })

    products = Product.objects.filter(id__in=product_ids)
    cart_items = []
    total_price = 0

    for product in products:
        quantity = cart.get(str(product.id), 0)
        subtotal = product.price * quantity
        total_price += subtotal
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal
        })

    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })


def checkout(request):
    cart = request.session.get('cart', {})
    product_ids = cart.keys()

    if not product_ids:
        messages.error(request, "Your cart is empty. Please add items before checkout.")
        return redirect('view_cart')

    products = Product.objects.filter(id__in=product_ids)
    cart_items = []
    total_price = 0

    for product in products:
        quantity = cart.get(str(product.id), 0)
        subtotal = product.price * quantity
        total_price += subtotal
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal
        })

    if request.method == 'POST':
        # Validate required fields
        required_fields = ['customer_name', 'customer_phone', 'shipping_address', 'payment_method']
        missing_fields = [field for field in required_fields if not request.POST.get(field)]
        
        if missing_fields:
            messages.error(request, f'Missing required fields: {", ".join(missing_fields)}')
            return redirect('checkout')

        # Create a new order
        order = Order(
            customer_name=request.POST.get('customer_name'),
            customer_email=request.POST.get('customer_email', ''),
            customer_phone=request.POST.get('customer_phone'),
            shipping_address=request.POST.get('shipping_address'),
            order_notes=request.POST.get('order_notes'),
            total_amount=total_price,
            payment_method=request.POST.get('payment_method')
        )

        order.save()
        
        # Create order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price
            )
            
            # Update product quantity
            product = item['product']
            product.quantity -= item['quantity']
            product.save()
        
        # Clear the cart and show success message
        request.session['cart'] = {}
        messages.success(request, "Your order has been placed successfully!")
        return redirect('success', order_id=order.id)

    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })


class SuccessView(DetailView):
    model = Order
    template_name = 'store/success.html'
    context_object_name = 'order'

    def get_object(self):
        return get_object_or_404(Order, id=self.kwargs['order_id'])