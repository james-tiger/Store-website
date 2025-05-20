from django.db import models
from django.utils.text import slugify


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
class Product(models.Model):
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
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, verbose_name="Average Rating")

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
    is_featured = models.BooleanField(default=False, verbose_name="Featured Product")
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
        ('cash_on_delivery', 'Cash on Delivery'),
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
    )

    customer_name = models.CharField(max_length=200, verbose_name="Customer Name")
    customer_email = models.EmailField(verbose_name="Customer Email")
    customer_phone = models.CharField(max_length=20, verbose_name="Customer Phone")
    shipping_address = models.TextField(verbose_name="Shipping Address")
    order_notes = models.TextField(blank=True, null=True, verbose_name="Order Notes")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Amount")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Order Status")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash_on_delivery', verbose_name="Payment Method")
    is_paid = models.BooleanField(default=False, verbose_name="Is Paid")
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

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def subtotal(self):
        return self.price * self.quantity