from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('farmer', 'Farmer'),
        ('consumer', 'Consumer'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='consumer')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    # NPOP Certificate fields
    npop_certificate_number = models.CharField(max_length=100, blank=True, null=True)
    npop_certificate_issue_date = models.DateField(blank=True, null=True)
    npop_certificate_expiry_date = models.DateField(blank=True, null=True)
    npop_certificate_file = models.FileField(upload_to='npop_certificates/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    @property
    def is_npop_verified(self):
        """Check if the farmer has a valid NPOP certificate"""
        from datetime import date
        if self.user_type != 'farmer':
            return False
        if not self.npop_certificate_number or not self.npop_certificate_expiry_date:
            return False
        # Check if certificate is still valid
        return self.npop_certificate_expiry_date >= date.today()


class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Product Categories"


class Product(models.Model):
    UNIT_CHOICES = (
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('l', 'Liter'),
        ('ml', 'Milliliter'),
        ('piece', 'Piece'),
        ('dozen', 'Dozen'),
        ('bundle', 'Bundle'),
        ('box', 'Box'),
        ('bag', 'Bag'),
        ('packet', 'Packet'),
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    quantity_available = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='kg')
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_organic = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    harvest_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    nutritional_info = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

    @property
    def avg_rating(self):
        """Calculate the average rating for this product"""
        reviews = self.reviews.all()
        if reviews.exists():
            return reviews.aggregate(models.Avg('rating'))['rating__avg']
        return 0
    
    @property
    def review_count(self):
        """Count the number of reviews for this product"""
        return self.reviews.count()
    
    @property
    def latest_reviews(self):
        """Return the 5 most recent reviews"""
        return self.reviews.all()[:5]
    
    def get_recommended_products(self, limit=5):
        """Get the best 5 products that are recommended to use with this product"""
        # Get directly linked recommendations ordered by strength
        direct_recommendations = ProductRecommendation.objects.filter(
            primary_product=self
        ).select_related('recommended_product').order_by('-strength')[:limit]
        
        recommended_products = [rec.recommended_product for rec in direct_recommendations]
        
        # If we don't have enough direct recommendations, get complementary category products
        if len(recommended_products) < limit:
            # Get complementary categories (this mapping could be moved to a separate model)
            complementary_categories = {
                'Vegetables': ['Spices', 'Oils'],
                'Fruits': ['Dairy', 'Honey'],
                'Dairy': ['Fruits', 'Beverages'],
                'Grains': ['Vegetables', 'Dairy'],
                'Pulses': ['Grains', 'Spices'],
                'Spices': ['Vegetables', 'Pulses'],
            }
            
            # Get the current product's category name
            current_category = self.category.name if self.category else None
            
            # Find complementary categories for the current product
            target_categories = []
            if current_category and current_category in complementary_categories:
                target_categories = complementary_categories[current_category]
            
            # Get highly-rated products from complementary categories
            if target_categories:
                category_products = Product.objects.filter(
                    category__name__in=target_categories,
                    is_available=True
                ).exclude(
                    id=self.id
                ).exclude(
                    id__in=[p.id for p in recommended_products]
                ).annotate(
                    avg_rating=models.Avg('reviews__rating'),
                    num_reviews=models.Count('reviews')
                ).order_by('-avg_rating', '-num_reviews')[:limit-len(recommended_products)]
                
                recommended_products.extend(list(category_products))
        
        # If we still don't have enough recommendations, add top-rated products
        if len(recommended_products) < limit:
            # Get popular products based on ratings and review count
            popular_products = Product.objects.filter(
                is_available=True
            ).exclude(
                id=self.id
            ).exclude(
                id__in=[p.id for p in recommended_products]
            ).annotate(
                avg_rating=models.Avg('reviews__rating'),
                num_reviews=models.Count('reviews')
            ).order_by('-avg_rating', '-num_reviews')[:limit-len(recommended_products)]
            
            recommended_products.extend(list(popular_products))
            
        # Limit to exactly the requested number of products
        return recommended_products[:limit]


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    
    consumer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shipping_address = models.TextField()
    order_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional fields for order management
    cancellation_reason = models.TextField(blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Status update timestamps
    processing_date = models.DateTimeField(blank=True, null=True)
    shipped_date = models.DateTimeField(blank=True, null=True)
    delivered_date = models.DateTimeField(blank=True, null=True)
    cancelled_date = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Order #{self.id} - {self.consumer.username} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Calculate total price based on product price and quantity
        if not self.total_price:
            self.total_price = self.product.price * self.quantity
        super().save(*args, **kwargs)


class CartItem(models.Model):
    """
    Model to store cart items for users
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name} in {self.user.username}'s cart"
    
    @property
    def subtotal(self):
        return self.product.price * self.quantity


class PaymentTransaction(models.Model):
    """
    Model to store payment transaction information
    """
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('cod', 'Cash on Delivery'),
        ('upi', 'UPI'),
        ('card', 'Credit/Debit Card'),
        ('netbanking', 'Net Banking'),
        ('wallet', 'Wallet'),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payment_transactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cod')
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    gateway_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment #{self.id} - {self.order.id} - {self.payment_status}"


class ProductReview(models.Model):
    RATING_CHOICES = (
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_reviews')
    rating = models.IntegerField(choices=RATING_CHOICES)
    review_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'user')  # One review per product per user
    
    def __str__(self):
        return f"{self.user.username}'s {self.rating}-star review on {self.product.name}"


class ProductRecommendation(models.Model):
    """
    Model to store product recommendations for complementary products
    """
    primary_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recommendations_as_primary')
    recommended_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recommendations_as_secondary')
    strength = models.IntegerField(default=1, help_text="Higher value means stronger recommendation")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('primary_product', 'recommended_product')
        ordering = ['-strength']
    
    def __str__(self):
        return f"{self.primary_product.name} → {self.recommended_product.name}"
    
    def clean(self):
        # Prevent self-recommendation
        if self.primary_product == self.recommended_product:
            from django.core.exceptions import ValidationError
            raise ValidationError("A product cannot recommend itself.")
