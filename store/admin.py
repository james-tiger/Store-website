# store/admin.py

from django.contrib import admin
from .models import Product, Category, ProductImage, Order, OrderItem, Section

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    verbose_name = "Product Image"
    verbose_name_plural = "Product Images"
    fields = ('image', 'image_url', 'alt_text', 'is_primary')
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields['image_url'].required = False
        formset.form.base_fields['image'].required = False
        return formset





@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'discount_price', 'gender', 'category', 'section', 'quantity', 'status', 'is_featured', 'created_at']
    list_filter = ['category', 'gender', 'status', 'is_featured', 'created_at', 'section']
    search_fields = ['name', 'description']
    list_editable = ['price', 'discount_price', 'quantity', 'status', 'is_featured']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        gender = request.GET.get('gender', None)
        if gender:
            qs = qs.filter(gender=gender)
        return qs
    fieldsets = [
        ('Basic Information', {'fields': ['name', 'description', 'price', 'discount_price']}),
        ('Classification', {'fields': ['category', 'gender', 'section']}),
        ('Inventory', {'fields': ['quantity', 'status']}),
        ('Display Options', {'fields': ['is_featured']}),
        ('Metadata', {'fields': ['created_at', 'updated_at'], 'classes': ['collapse']}),
    ]
    
    def get_form(self, request, obj=None, **kwargs):
        return super().get_form(request, obj, **kwargs)
    inlines = [ProductImageInline]
    list_per_page = 20


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price', 'subtotal']
    can_delete = False
    
    def subtotal(self, obj):
        if obj.price is None:
            return 0
        return obj.price * obj.quantity
    subtotal.short_description = 'Subtotal'


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug']
    list_editable = ['is_active']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        ('Basic Information', {'fields': ['name', 'slug']}),
        ('Status', {'fields': ['is_active']}),
        ('Metadata', {'fields': ['created_at', 'updated_at'], 'classes': ['collapse']}),
    ]
    list_per_page = 20


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'customer_email', 'total_amount', 'status', 'payment_method', 'is_paid', 'created_at']
    list_filter = ['status', 'payment_method', 'is_paid', 'created_at']
    search_fields = ['customer_name', 'customer_email', 'customer_phone']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['status', 'is_paid']
    fieldsets = [
        ('Customer Information', {'fields': ['customer_name', 'customer_email', 'customer_phone']}),
        ('Shipping Information', {'fields': ['shipping_address', 'order_notes']}),
        ('Order Details', {'fields': ['total_amount', 'status', 'payment_method', 'is_paid']}),
        ('Metadata', {'fields': ['created_at', 'updated_at'], 'classes': ['collapse']}),
    ]
    inlines = [OrderItemInline]
    list_per_page = 20