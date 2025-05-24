import socket
import smtplib
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.views.generic import DetailView
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, ProductImage, Order, OrderItem, PaymentSettings

class SuccessView(DetailView):
    model = Order
    template_name = 'store/success.html'
    context_object_name = 'order'

    def get_object(self):
        return get_object_or_404(Order, id=self.kwargs['order_id'])
        
    def get(self, request, *args, **kwargs):
        # إذا كان الطلب قادمًا من عملية الدفع، عرض صفحة النجاح
        if request.GET.get('from_payment') == 'true':
            return super().get(request, *args, **kwargs)
        # وإلا، توجيه المستخدم إلى صفحة الدفع
        order = self.get_object()
        return redirect('store:payment_info', order_id=order.id)


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
    
    # الحصول على المنتجات المشابهة من نفس الفئة إذا لم تكن هناك منتجات مرتبطة محددة
    if product.related_products.exists():
        # إذا كانت هناك منتجات مرتبطة محددة، فسنستخدمها
        similar_products = product.related_products.all()
    else:
        # البحث عن منتجات مشابهة بناءً على الفئة والجنس والعلامات
        similar_products = Product.objects.filter(category=product.category, gender=product.gender)
        
        # استبعاد المنتج الحالي
        similar_products = similar_products.exclude(id=product.id)
        
        # إذا كان للمنتج علامات، نحاول العثور على منتجات بنفس العلامات
        if product.tags.exists():
            # الحصول على منتجات لها نفس العلامات
            tagged_products = Product.objects.filter(tags__in=product.tags.all()).exclude(id=product.id).distinct()
            
            # دمج النتائج مع إزالة التكرار
            similar_products = (similar_products | tagged_products).distinct()[:6]
        else:
            similar_products = similar_products[:6]
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'similar_products': similar_products
    })

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    
    # Get form data
    quantity = int(request.POST.get('quantity', 1))
    size = request.POST.get('size', '')
    color = request.POST.get('color', '')
    
    # Create a unique key for this product+size+color combination
    cart_key = str(product.id)
    if size:
        cart_key += f"_size_{size}"
    if color:
        cart_key += f"_color_{color}"
    
    # Get current quantity in cart
    current_quantity = cart.get(cart_key, 0)
    
    # Check if we have enough stock
    if current_quantity + quantity > product.quantity:
        messages.error(request, f"Not enough stock for {product.name}")
        return redirect('product_detail', product_id=product_id)
    
    # Add to cart
    cart[cart_key] = current_quantity + quantity
    
    # Store size and color information
    if 'item_details' not in request.session:
        request.session['item_details'] = {}
    
    request.session['item_details'][cart_key] = {
        'product_id': product.id,
        'size': size,
        'color': color
    }
    
    # Save to session
    request.session['cart'] = cart
    request.session.modified = True
    
    messages.success(request, f"Added {quantity} × {product.name} to cart!")
    return redirect('store:view_cart')


def cart_increase(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    item_details = request.session.get('item_details', {})
    
    # Find the cart key for this product
    cart_key = None
    for key in cart.keys():
        if key == str(product_id) or key.startswith(f"{product_id}_"):
            cart_key = key
            break
    
    if not cart_key:
        messages.error(request, f"Product not found in cart")
        return redirect('store:view_cart')
    
    current_quantity = cart.get(cart_key, 0)
    
    if current_quantity < product.quantity:
        cart[cart_key] = current_quantity + 1
        messages.success(request, f"Increased quantity of {product.name}")
    else:
        messages.error(request, f"Cannot increase quantity, not enough stock of {product.name}")
    
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('store:view_cart')


def cart_decrease(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    item_details = request.session.get('item_details', {})
    
    # Find the cart key for this product
    cart_key = None
    for key in cart.keys():
        if key == str(product_id) or key.startswith(f"{product_id}_"):
            cart_key = key
            break
    
    if not cart_key:
        messages.error(request, f"Product not found in cart")
        return redirect('store:view_cart')
    
    current_quantity = cart.get(cart_key, 0)
    
    if current_quantity > 1:
        cart[cart_key] = current_quantity - 1
        messages.info(request, f"Decreased quantity of {product.name}")
    else:
        del cart[cart_key]
        # Also remove from item_details if it exists
        if cart_key in item_details:
            del item_details[cart_key]
            request.session['item_details'] = item_details
        messages.info(request, f"Removed {product.name} from cart")
    
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('store:view_cart')


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
    item_details = request.session.get('item_details', {})
    
    if not cart:
        return render(request, 'store/cart.html', {
            'cart_items': [],
            'total_price': 0
        })
    
    # Get all product IDs from the cart keys
    product_ids = set()
    for cart_key in cart.keys():
        # Extract product ID from the cart key
        if '_size_' in cart_key or '_color_' in cart_key:
            product_id = int(cart_key.split('_')[0])
        else:
            product_id = int(cart_key)
        product_ids.add(product_id)
    
    # Get all products in one query
    products = {str(p.id): p for p in Product.objects.filter(id__in=product_ids)}
    
    cart_items = []
    total_price = 0
    
    for cart_key, quantity in cart.items():
        # Get product ID from cart key
        if '_size_' in cart_key or '_color_' in cart_key:
            product_id = cart_key.split('_')[0]
        else:
            product_id = cart_key
        
        # Get product
        product = products.get(product_id)
        if not product:
            continue
        
        # Get size and color
        size = ''
        color = ''
        if cart_key in item_details:
            details = item_details[cart_key]
            size = details.get('size', '')
            color = details.get('color', '')
        
        # Calculate subtotal
        subtotal = product.price * quantity
        total_price += subtotal
        
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
            'size': size,
            'color': color
        })
    
    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })


def checkout(request):
    # Use the same cart processing logic as view_cart
    cart = request.session.get('cart', {})
    item_details = request.session.get('item_details', {})
    
    if not cart:
        messages.error(request, "Your cart is empty. Please add items before checkout.")
        return redirect('store:view_cart')
    
    # Get all product IDs from the cart keys
    product_ids = set()
    for cart_key in cart.keys():
        # Extract product ID from the cart key
        if '_size_' in cart_key or '_color_' in cart_key:
            product_id = int(cart_key.split('_')[0])
        else:
            product_id = int(cart_key)
        product_ids.add(product_id)
    
    # Get all products in one query
    products = {str(p.id): p for p in Product.objects.filter(id__in=product_ids)}
    
    cart_items = []
    total_price = 0
    
    for cart_key, quantity in cart.items():
        # Get product ID from cart key
        if '_size_' in cart_key or '_color_' in cart_key:
            product_id = cart_key.split('_')[0]
        else:
            product_id = cart_key
        
        # Get product
        product = products.get(product_id)
        if not product:
            continue
        
        # Get size and color
        size = ''
        color = ''
        if cart_key in item_details:
            details = item_details[cart_key]
            size = details.get('size', '')
            color = details.get('color', '')
        
        # Calculate subtotal
        subtotal = product.price * quantity
        total_price += subtotal
        
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
            'size': size,
            'color': color
        })

    if request.method == 'POST':
        # Validate required fields
        required_fields = ['customer_name', 'customer_phone', 'shipping_address', 'payment_method']
        missing_fields = [field for field in required_fields if not request.POST.get(field)]
        
        if missing_fields:
            messages.error(request, f'Missing required fields: {", ".join(missing_fields)}')
            return redirect('store:checkout')
        
        # Get payment method from POST data
        payment_method = request.POST.get('payment_method')
        
        # التحقق من صحة طريقة الدفع المختارة
        try:
            payment_settings = PaymentSettings.objects.first()
            if payment_method not in ['card', 'instapay', 'vodafone_cash', 'cod'] \
                or not getattr(payment_settings, f'is_{payment_method}_enabled', False):
                messages.error(request, 'طريقة الدفع المختارة غير مدعومة أو غير مفعلة')
                return redirect('store:checkout')
        
            # حفظ طريقة الدفع في الجلسة بعد التحقق
            request.session['payment_method'] = payment_method
        except Exception as e:
            messages.error(request, f'خطأ في التحقق من إعدادات الدفع: {str(e)}')
            return redirect('store:checkout')
        
        # حفظ طريقة الدفع في الجلسة بعد التحقق
        request.session['payment_method'] = payment_method

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
            # Create order item with size/color
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price,
                size=item.get('size', ''),
                color=item.get('color', '')
            )
            
            # Update product quantity
            product = item['product']
            product.quantity -= item['quantity']
            product.save()
        
        # Clear the cart and show success message
        request.session['cart'] = {}
        messages.success(request, "Your order has been placed successfully!")
        return redirect('store:payment_info', order_id=order.id)

    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })