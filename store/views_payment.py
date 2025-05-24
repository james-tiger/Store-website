from django.contrib import messages
from django.views.generic import DetailView
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, get_object_or_404
from .models import Order, OrderItem, Product, ProductRating, PaymentSettings

def payment_info(request, order_id):
    """عرض معلومات الدفع بناءً على طريقة الدفع المختارة"""
    order = get_object_or_404(Order, id=order_id)
    payment_method = request.session.get('payment_method', 'cod')
    
    # الحصول على معلومات الدفع من إعدادات الدفع
    try:
        payment_settings = PaymentSettings.objects.first()
        if not payment_settings:
            # إنشاء إعدادات افتراضية إذا لم تكن موجودة
            payment_settings = PaymentSettings.objects.create()
    except Exception:
        # إنشاء كائن بقيم افتراضية في حالة حدوث خطأ
        payment_settings = type('PaymentSettings', (), {
            'instapay_number': '01XXXXXXXXX',
            'vodafone_cash_number': '01XXXXXXXXX',
            'bank_account_details': '',
            'is_card_enabled': True,
            'is_instapay_enabled': True,
            'is_vodafone_cash_enabled': True,
            'is_cod_enabled': True
        })
    
    # معلومات الدفع التي يمكن تعديلها من لوحة الإدارة
    payment_info = {
        'instapay_number': payment_settings.instapay_number,
        'vodafone_number': payment_settings.vodafone_cash_number,
        'bank_account_details': payment_settings.bank_account_details,
        'is_card_enabled': payment_settings.is_card_enabled,
        'is_instapay_enabled': payment_settings.is_instapay_enabled,
        'is_vodafone_cash_enabled': payment_settings.is_vodafone_cash_enabled,
        'is_cod_enabled': payment_settings.is_cod_enabled
    }
    
    return render(request, 'store/payment.html', {
        'order': order,
        'payment_method': payment_method,
        'payment_info': payment_info
    })

def complete_payment(request, order_id):
    """إكمال عملية الدفع ورفع إيصال الدفع"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        # حفظ معلومات الدفع
        order.payment_method = payment_method
        
        # معالجة رفع إيصال الدفع إذا تم تقديمه
        if 'payment_receipt' in request.FILES:
            receipt = request.FILES['payment_receipt']
            # استخدام حقل payment_receipt مباشرة بدلاً من FileSystemStorage المخصص
            # هذا سيضمن أن Django يتعامل مع الملف بشكل صحيح ويحفظه في المسار المحدد في نموذج Order
            order.payment_receipt = receipt
            # حفظ رابط الإيصال أيضًا للاستخدام المستقبلي إذا لزم الأمر
            order.receipt_url = f"/media/payment_receipts/receipt_{order.id}_{receipt.name}"
        
        # حفظ معلومات إضافية حسب طريقة الدفع
        if payment_method == 'card':
            # حفظ معلومات البطاقة (لا نخزن معلومات البطاقة الكاملة لأسباب أمنية)
            # يمكن تخزين الأرقام الأخيرة فقط من البطاقة إذا لزم الأمر
            card_last_digits = request.POST.get('card_number', '')[-4:] if request.POST.get('card_number') else ''
            order.transaction_id = f"CARD-{card_last_digits}"
            # تعيين حالة الدفع
            order.is_paid = True
        elif payment_method == 'instapay':
            transaction_id = request.POST.get('transaction_id')
            # حفظ رقم العملية
            order.transaction_id = transaction_id
            # تعيين حالة الدفع بناءً على وجود إيصال
            order.is_paid = bool(order.payment_receipt)
        elif payment_method == 'vodafone_cash':
            sender_phone = request.POST.get('sender_phone')
            transaction_id = request.POST.get('transaction_id')
            # حفظ رقم الهاتف المرسل ورقم العملية
            order.sender_phone = sender_phone
            order.transaction_id = transaction_id
            # تعيين حالة الدفع بناءً على وجود إيصال
            order.is_paid = bool(order.payment_receipt)
        elif payment_method == 'cod':
            # الدفع عند الاستلام، لا يتم تعيين حالة الدفع كمدفوع
            order.is_paid = False
        
        # تحديث حالة الطلب والدفع بناءً على وجود إيصال
        if payment_method in ['instapay', 'vodafone_cash']:
            # إذا كان هناك إيصال دفع، نعتبر الطلب مدفوعًا
            if order.payment_receipt:
                order.is_paid = True
                order.status = 'processing'
        
        # تحديث حالة الطلب للطرق الأخرى
        elif order.is_paid:
            order.status = 'processing'
        
        order.save()
        
        # إضافة رسالة نجاح
        messages.success(request, 'تم تسجيل معلومات الدفع بنجاح!')
        
        # توجيه المستخدم إلى صفحة تقييم المنتج
        return redirect('store:rate_products', order_id=order.id)
    
    # إذا لم تكن طريقة الطلب POST، إعادة توجيه المستخدم إلى صفحة معلومات الدفع
    return redirect('payment_info', order_id=order.id)

def rate_products(request, order_id):
    """عرض صفحة تقييم المنتجات بعد إتمام عملية الدفع"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/rate_product.html', {'order': order})

def process_payment(request, order_id):
    """معالجة عملية الدفع بناءً على طريقة الدفع المختارة"""
    order = get_object_or_404(Order, id=order_id)
    payment_method = request.session.get('payment_method', 'cod')
    
    # التحقق من إعدادات الدفع المفعلة
    try:
        payment_settings = PaymentSettings.objects.first()
        if not payment_settings:
            messages.error(request, 'لم يتم تهيئة إعدادات الدفع بعد')
            return redirect('payment_info', order_id=order_id)
            
        # التحقق من صحة طريقة الدفع المختارة
        payment_enabled = {
            'card': payment_settings.is_card_enabled,
            'instapay': payment_settings.is_instapay_enabled,
            'vodafone_cash': payment_settings.is_vodafone_cash_enabled,
            'cod': payment_settings.is_cod_enabled
        }.get(payment_method, False)
        
        if not payment_enabled:
            messages.error(request, 'طريقة الدفع المختارة غير مفعلة أو غير صحيحة')
            return redirect('payment_info', order_id=order_id)
    except Exception as e:
        messages.error(request, f'خطأ في التحقق من إعدادات الدفع: {str(e)}')
        return redirect('payment_info', order_id=order_id)
    
    # معالجة الدفع بناءً على الطريقة المختارة
    if payment_method == 'card':
        # معالجة الدفع بالبطاقة
        order.is_paid = True
        order.status = 'processing'
    elif payment_method == 'instapay':
        # معالجة الدفع عبر Instapay
        order.is_paid = True
        order.status = 'processing'
    elif payment_method == 'vodafone_cash':
        # معالجة الدفع عبر Vodafone Cash
        order.is_paid = True
        order.status = 'processing'
    elif payment_method == 'cod':
        # الدفع عند الاستلام
        order.is_paid = False
        order.status = 'pending'
    
    order.save()
    
    # توجيه المستخدم إلى صفحة إتمام الدفع
    return redirect('store:complete_payment', order_id=order.id)


def rate_product(request, order_id, product_id):
    """معالجة تقييم منتج محدد"""
    order = get_object_or_404(Order, id=order_id)
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        rating_value = int(request.POST.get('rating', 5))  # القيمة الافتراضية هي 5 نجوم
        comment = request.POST.get('comment', '')
        
        # إنشاء تقييم جديد
        rating = ProductRating(
            product=product,
            user=request.user if request.user.is_authenticated else None,
            rating=rating_value,
            comment=comment
        )
        rating.save()
        
        # تحديث متوسط تقييم المنتج
        ratings = product.ratings.all()
        total_ratings = ratings.count()
        average = sum(r.rating for r in ratings) / total_ratings if total_ratings > 0 else 0
        
        product.average_rating = average
        product.total_reviews = total_ratings
        product.save()
        
        messages.success(request, f'شكراً لتقييمك لمنتج {product.name}!')
    
    # إعادة توجيه المستخدم إلى صفحة تقييم المنتجات
    return redirect('store:rate_products', order_id=order.id)

# تعديل وظيفة checkout لدعم المراحل الثلاث
def checkout_updated(request):
    # استخدام نفس منطق معالجة السلة كما في وظيفة view_cart
    cart = request.session.get('cart', {})
    item_details = request.session.get('item_details', {})
    
    if not cart:
        messages.error(request, "سلة التسوق فارغة. يرجى إضافة منتجات قبل متابعة عملية الدفع.")
        return redirect('view_cart')
    
    # الحصول على جميع معرفات المنتجات من مفاتيح السلة
    product_ids = set()
    for cart_key in cart.keys():
        # استخراج معرف المنتج من مفتاح السلة
        if '_size_' in cart_key or '_color_' in cart_key:
            product_id = int(cart_key.split('_')[0])
        else:
            product_id = int(cart_key)
        product_ids.add(product_id)
    
    # الحصول على جميع المنتجات في استعلام واحد
    products = {str(p.id): p for p in Product.objects.filter(id__in=product_ids)}
    
    cart_items = []
    total_price = 0
    
    for cart_key, quantity in cart.items():
        # الحصول على معرف المنتج من مفتاح السلة
        if '_size_' in cart_key or '_color_' in cart_key:
            product_id = cart_key.split('_')[0]
        else:
            product_id = cart_key
        
        # الحصول على المنتج
        product = products.get(product_id)
        if not product:
            continue
        
        # الحصول على المقاس واللون
        size = ''
        color = ''
        if cart_key in item_details:
            details = item_details[cart_key]
            size = details.get('size', '')
            color = details.get('color', '')
        
        # حساب المجموع الفرعي
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
        # التحقق من الحقول المطلوبة
        required_fields = ['customer_name', 'customer_phone', 'shipping_address', 'payment_method']
        missing_fields = [field for field in required_fields if not request.POST.get(field)]
        
        if missing_fields:
            messages.error(request, f'الحقول التالية مطلوبة: {", ".join(missing_fields)}')
            return redirect('checkout')

        # إنشاء طلب جديد
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
        
        # إنشاء عناصر الطلب
        for item in cart_items:
            # إنشاء عنصر طلب مع المقاس/اللون
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price,
                size=item.get('size', ''),
                color=item.get('color', '')
            )
            
            # تحديث كمية المنتج
            product = item['product']
            product.quantity -= item['quantity']
            product.save()
        
        # حفظ طريقة الدفع في الجلسة للاستخدام في الخطوة التالية
        request.session['payment_method'] = request.POST.get('payment_method')
        
        # توجيه المستخدم إلى صفحة معلومات الدفع
        return redirect('payment_info', order_id=order.id)

    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })