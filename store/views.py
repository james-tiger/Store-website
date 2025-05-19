from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, ProductImage
from django.contrib import messages


def index(request):
    categories = Category.objects.all()
    return render(request, 'store/index.html', {'categories': categories})


def product_list(request):
    category_slug = request.GET.get('category')
    if category_slug:
        products = Product.objects.filter(category__name=category_slug)
    else:
        products = Product.objects.all()
    return render(request, 'store/products.html', {'products': products})


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