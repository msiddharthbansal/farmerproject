from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ProductCategory, Product, Order, CartItem, PaymentTransaction, ProductReview, ProductRecommendation

# Register custom User model with UserAdmin
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone', 'address', 'profile_pic')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone', 'address', 'profile_pic')}),
    )

admin.site.register(User, CustomUserAdmin)

# Register ProductCategory model
@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

# Register Product model
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'quantity_available', 'category', 'farmer', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'

# Register Order model
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'consumer', 'product', 'quantity', 'total_price', 'status', 'order_date')
    list_filter = ('status', 'order_date')
    search_fields = ('consumer__username', 'product__name')
    date_hierarchy = 'order_date'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'added_at', 'updated_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'product__name')

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'user', 'amount', 'payment_method', 'payment_status', 'created_at')
    list_filter = ('payment_status', 'payment_method', 'created_at')
    search_fields = ('user__username', 'order__id', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'review_text')
    readonly_fields = ('created_at',)

@admin.register(ProductRecommendation)
class ProductRecommendationAdmin(admin.ModelAdmin):
    list_display = ('primary_product', 'recommended_product', 'strength', 'created_at')
    list_filter = ('strength', 'created_at')
    search_fields = ('primary_product__name', 'recommended_product__name')
    autocomplete_fields = ['primary_product', 'recommended_product']
