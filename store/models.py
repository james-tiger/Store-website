from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# ==============================
# Category Model
# ==============================
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Category Name")
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ==============================
# Section Model
# ==============================
class Section(models.Model):
    name = models.CharField(max_length=100, verbose_name="Section Name")
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Section"
        verbose_name_plural = "Sections"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ==============================
# Product Model
# ==============================
class ProductSize(models.Model):
    name = models.CharField(max_length=50, verbose_name="اسم المقاس")
    code = models.CharField(max_length=10, verbose_name="كود المقاس", blank=True)

    def __str__(self):
        return self.name

class ProductColor(models.Model):
    name = models.CharField(max_length=50, verbose_name="اسم اللون")
    hex_code = models.CharField(max_length=7, verbose_name="كود اللون", blank=True)

    def __str__(self):
        return self.name

class ProductTag(models.Model):
    name = models.CharField(max_length=50, verbose_name="اسم العلامة")
    slug = models.SlugField(max_length=60, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    sizes = models.ManyToManyField(ProductSize, verbose_name="المقاسات المتاحة", blank=True)
    colors = models.ManyToManyField(ProductColor, verbose_name="الألوان المتاحة", blank=True)
    
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('U', 'Unisex'),
    )
    
    GENDER_FILTER_CHOICES = (
        ('M', 'Men\'s Collection'),
        ('F', 'Women\'s Collection'),
        ('U', 'Unisex Collection'),
    )

    STATUS_CHOICES = (
        ('in_stock', 'In Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('on_sale', 'On Sale'),
        ('new_arrival', 'New Arrival'),
    )
    
    RATING_CHOICES = (
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    )
    
    rating = models.PositiveIntegerField(choices=RATING_CHOICES, null=True, blank=True, verbose_name="Rating")
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, verbose_name="متوسط التقييم")
    total_reviews = models.PositiveIntegerField(default=0, verbose_name="عدد التقييمات")

    name = models.CharField(max_length=200, verbose_name="Product Name")
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Section")
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(verbose_name="Description")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Discount Price")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name="Gender")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Category")
    quantity = models.PositiveIntegerField(default=0, verbose_name="Available Quantity")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_stock', verbose_name="Status")
    is_featured = models.BooleanField(default=False, verbose_name="منتج مميز")
    tags = models.ManyToManyField(ProductTag, verbose_name="العلامات", blank=True)
    meta_title = models.CharField(max_length=100, verbose_name="عنوان SEO", blank=True)
    meta_description = models.TextField(verbose_name="وصف SEO", blank=True)
    related_products = models.ManyToManyField('self', blank=True, verbose_name="منتجات ذات صلة")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if self.quantity <= 0:
            self.status = 'out_of_stock'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    rating = models.PositiveIntegerField(choices=((1, '1 نجوم'), (2, '2 نجوم'), (3, '3 نجوم'), (4, '4 نجوم'), (5, '5 نجوم')))
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


# ==============================
# ProductImage Model
# ==============================
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/', null=True, blank=True, verbose_name="Image File")
    image_url = models.URLField(null=True, blank=True, verbose_name="Image URL")
    alt_text = models.CharField(max_length=100, blank=True, verbose_name="Alt Text")
    is_primary = models.BooleanField(default=False, verbose_name="Primary Image")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.image and not self.image_url:
            raise ValidationError("Either image file or image URL must be provided")
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"
        ordering = ['-is_primary', 'created_at']

    def __str__(self):
        return f"Image for {self.product.name}"


# ==============================
# Order Model
# ==============================
class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    PAYMENT_CHOICES = (
        ('cod', 'الدفع عند الاستلام'),
        ('card', 'بطاقة ائتمانية'),
        ('instapay', 'إنستاباي'),
        ('vodafone_cash', 'فودافون كاش'),
    )

    customer_name = models.CharField(max_length=200, verbose_name="اسم العميل")
    customer_email = models.EmailField(verbose_name="البريد الإلكتروني للعميل")
    customer_phone = models.CharField(max_length=20, verbose_name="رقم هاتف العميل")
    shipping_address = models.TextField(verbose_name="عنوان الشحن")
    order_notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات الطلب")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ الإجمالي")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="حالة الطلب")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod', verbose_name="طريقة الدفع")
    is_paid = models.BooleanField(default=False, verbose_name="تم الدفع")
    transaction_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="رقم العملية")
    sender_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم هاتف المرسل")
    receipt_url = models.CharField(max_length=255, blank=True, null=True, verbose_name="رابط إيصال الدفع")
    payment_receipt = models.ImageField(upload_to='payment_receipts/', blank=True, null=True, verbose_name="إيصال الدفع")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"


# ==============================
# OrderItem Model
# ==============================
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=10, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def subtotal(self):
        return self.price * self.quantity


# ==============================
# PaymentSettings Model
# ==============================
class PaymentSettings(models.Model):
    """نموذج لتخزين إعدادات الدفع التي يمكن تعديلها من لوحة الإدارة"""
    instapay_number = models.CharField(max_length=20, verbose_name="رقم إنستاباي", default="01XXXXXXXXX")
    vodafone_cash_number = models.CharField(max_length=20, verbose_name="رقم فودافون كاش", default="01XXXXXXXXX")
    bank_account_details = models.TextField(verbose_name="تفاصيل الحساب البنكي", blank=True, null=True)
    is_card_enabled = models.BooleanField(default=True, verbose_name="تفعيل الدفع بالبطاقة")
    is_instapay_enabled = models.BooleanField(default=True, verbose_name="تفعيل الدفع بإنستاباي")
    is_vodafone_cash_enabled = models.BooleanField(default=True, verbose_name="تفعيل الدفع بفودافون كاش")
    is_cod_enabled = models.BooleanField(default=True, verbose_name="تفعيل الدفع عند الاستلام")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "إعدادات الدفع"
        verbose_name_plural = "إعدادات الدفع"

    def save(self, *args, **kwargs):
        # التأكد من وجود سجل واحد فقط من إعدادات الدفع
        if not self.pk and PaymentSettings.objects.exists():
            # إذا كان هناك سجل موجود بالفعل، قم بتحديثه بدلاً من إنشاء سجل جديد
            return PaymentSettings.objects.first().save()
        return super(PaymentSettings, self).save(*args, **kwargs)

    def __str__(self):
        return "إعدادات الدفع"