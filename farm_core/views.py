from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count, Avg
from django.contrib.auth import logout as auth_logout
from django.utils import timezone
from django.http import HttpResponse
from .models import User, Product, ProductCategory, Order, CartItem, PaymentTransaction, ProductReview
from .forms import UserSignupForm, ProductForm, OrderForm, UserProfileForm, ProductReviewForm, FarmerProfileForm
from django.utils.safestring import mark_safe

# Temporary migration view
def run_migrations(request):
    from django.core.management import call_command
    from django.db import connection
    import sqlite3
    
    try:
        # Check if the database needs migration
        cursor = connection.cursor()
        
        # Check if the cancellation_reason field exists in the order table
        cursor.execute("PRAGMA table_info(farm_core_order)")
        columns = {row[1] for row in cursor.fetchall()}
        
        # List of new fields we added to the Order model
        new_fields = ['cancellation_reason', 'tracking_number', 'notes', 
                     'processing_date', 'shipped_date', 'delivered_date', 'cancelled_date']
        
        missing_fields = [field for field in new_fields if field not in columns]
        
        if not missing_fields:
            return render(request, 'farm_core/migrations.html', {
                'migration_result': "Database is already up to date! No migrations needed."
            })
        
        # Add the missing columns manually through SQL
        for field in missing_fields:
            try:
                if field in ['processing_date', 'shipped_date', 'delivered_date', 'cancelled_date']:
                    # Date fields
                    cursor.execute(f"ALTER TABLE farm_core_order ADD COLUMN {field} datetime NULL")
                elif field in ['cancellation_reason', 'notes']:
                    # Text fields
                    cursor.execute(f"ALTER TABLE farm_core_order ADD COLUMN {field} text NULL")
                elif field == 'tracking_number':
                    # String field
                    cursor.execute(f"ALTER TABLE farm_core_order ADD COLUMN {field} varchar(100) NULL")
            except sqlite3.OperationalError as e:
                # If the column already exists, ignore the error
                if 'duplicate column name' not in str(e).lower():
                    raise
        
        return render(request, 'farm_core/migrations.html', {
            'migration_result': f"Database updated successfully! Added the following fields to the Order model: {', '.join(missing_fields)}"
        })
    
    except Exception as e:
        return render(request, 'farm_core/migrations.html', {
            'migration_result': f"Error updating database: {str(e)}. Try restarting the server."
        })

class MigrationPageView(TemplateView):
    template_name = 'farm_core/migrations.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if the database needs migration
        from django.db import connection
        cursor = connection.cursor()
        
        try:
            # Check if the cancellation_reason field exists in the order table
            cursor.execute("PRAGMA table_info(farm_core_order)")
            columns = {row[1] for row in cursor.fetchall()}
            
            # List of new fields we added to the Order model
            new_fields = ['cancellation_reason', 'tracking_number', 'notes', 
                         'processing_date', 'shipped_date', 'delivered_date', 'cancelled_date']
            
            missing_fields = [field for field in new_fields if field not in columns]
            
            if missing_fields:
                context['status'] = 'needs_migration'
                context['missing_fields'] = missing_fields
            else:
                context['status'] = 'up_to_date'
        except Exception as e:
            context['status'] = 'error'
            context['error_message'] = str(e)
        
        return context

# Home and static pages
class HomeView(ListView):
    model = Product
    template_name = 'farm_core/home.html'
    context_object_name = 'products'
    queryset = Product.objects.all().order_by('-created_at')[:6]  # Show latest 6 products
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ProductCategory.objects.all()
        return context

class AboutView(TemplateView):
    template_name = 'farm_core/about.html'

class ContactView(TemplateView):
    template_name = 'farm_core/contact.html'

# Authentication
class SignupView(CreateView):
    model = User
    form_class = UserSignupForm
    template_name = 'farm_core/signup.html'
    success_url = reverse_lazy('farm_core:login')
    
    def form_valid(self, form):
        user_type = form.instance.user_type
        if user_type == 'farmer':
            messages.success(self.request, _('Your farmer account has been created successfully. Please log in to start selling your products.'))
        else:
            messages.success(self.request, _('Your consumer account has been created successfully. Please log in to start shopping.'))
        return super().form_valid(form)

# Farmer views
class FarmerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'farmer'

class FarmerDashboardView(LoginRequiredMixin, FarmerRequiredMixin, TemplateView):
    template_name = 'farm_core/farmer_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        try:
            # Get products for this farmer
            products = Product.objects.filter(farmer=user)
            context['products'] = products
            context['products_count'] = products.count()
            
            # Get orders for this farmer's products
            orders = Order.objects.filter(product__farmer=user)
            context['orders'] = orders
            context['orders_count'] = orders.count()
            
            # Check if database needs updating
            from django.db import connection
            cursor = connection.cursor()
            
            # Check if orders table has the new fields
            order_fields_need_update = False
            try:
                cursor.execute("SELECT cancellation_reason FROM farm_core_order LIMIT 1")
            except:
                order_fields_need_update = True
            
            # Check if product table has new fields
            product_fields_need_update = False
            try:
                cursor.execute("SELECT unit FROM farm_core_product LIMIT 1")
            except:
                product_fields_need_update = True
                
            # Check if categories exist
            categories_need_creation = False
            try:
                cursor.execute("SELECT COUNT(*) FROM farm_core_productcategory")
                count = cursor.fetchone()[0]
                if count == 0:
                    categories_need_creation = True
            except:
                categories_need_creation = True
            
            # Set context flags
            context['order_fields_need_update'] = order_fields_need_update
            context['product_fields_need_update'] = product_fields_need_update
            context['categories_need_creation'] = categories_need_creation
            
            # Add message about database needs
            if order_fields_need_update:
                context['warning_message'] = mark_safe('Your order database needs to be updated. <a href="/run-migrations/">Click here</a> to update it.')
            
            if product_fields_need_update:
                context['info_message'] = mark_safe('You can enhance your product features by <a href="/update-product-model/">updating your product model</a>.')
                
            if categories_need_creation:
                context['category_message'] = mark_safe('No product categories found. You need to <a href="/create-categories/">create default categories</a> before adding products.')
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error loading dashboard data: {str(e)}")
            context['error_message'] = "Error loading dashboard data"
            
        return context

class FarmerProductListView(LoginRequiredMixin, FarmerRequiredMixin, ListView):
    model = Product
    template_name = 'farm_core/farmer/products.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        try:
            return Product.objects.filter(farmer=self.request.user)
        except Exception as e:
            # If there's a database error (like missing columns), log it and return an empty queryset
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in FarmerProductListView.get_queryset: {str(e)}")
            
            # Show an error message to the user
            from django.contrib import messages
            messages.error(self.request, _('There was an error loading your products. Please update your product model.'))
            
            # Return an empty queryset
            from django.db.models.query import EmptyQuerySet
            return EmptyQuerySet(model=Product)

class ProductCreateView(LoginRequiredMixin, FarmerRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'farm_core/farmer/product_form.html'
    success_url = reverse_lazy('farm_core:farmer_products')
    
    def get(self, request, *args, **kwargs):
        categories_count = ProductCategory.objects.count()
        if categories_count == 0:
            from django.utils.safestring import mark_safe
            messages.warning(
                request,
                mark_safe('No product categories found. Please <a href="/create-categories/">create default categories</a> before adding products.')
            )
            return redirect('farm_core:farmer_products')
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.farmer = self.request.user
        messages.success(self.request, _('Product added successfully.'))
        return super().form_valid(form)

class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'farm_core/farmer/product_form.html'
    success_url = reverse_lazy('farm_core:farmer_products')
    
    def test_func(self):
        product = self.get_object()
        return self.request.user.user_type == 'farmer' and self.request.user == product.farmer
    
    def form_valid(self, form):
        messages.success(self.request, _('Product updated successfully.'))
        return super().form_valid(form)

class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Product
    template_name = 'farm_core/farmer/product_confirm_delete.html'
    success_url = reverse_lazy('farm_core:farmer_products')
    
    def test_func(self):
        product = self.get_object()
        return self.request.user == product.farmer
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Product deleted successfully.'))
        return super().delete(request, *args, **kwargs)

class BulkProductActionView(LoginRequiredMixin, FarmerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        selected_products = request.POST.getlist('selected_products')
        action = request.POST.get('action')
        
        if not selected_products:
            messages.error(request, _('No products selected.'))
            return redirect('farm_core:farmer_products')
        
        products = Product.objects.filter(id__in=selected_products, farmer=request.user)
        
        if action == 'delete':
            count = products.count()
            products.delete()
            messages.success(request, _('%(count)d products deleted successfully.') % {'count': count})
        
        elif action == 'mark_in_stock':
            for product in products:
                if product.quantity_available == 0:
                    product.quantity_available = 10
                    product.save()
            messages.success(request, _('Selected products marked as in stock.'))
        
        elif action == 'mark_out_of_stock':
            products.update(quantity_available=0)
            messages.success(request, _('Selected products marked as out of stock.'))
        
        else:
            messages.error(request, _('Invalid action.'))
        
        return redirect('farm_core:farmer_products')

class FarmerOrderListView(LoginRequiredMixin, FarmerRequiredMixin, ListView):
    model = Order
    template_name = 'farm_core/farmer/orders.html'
    context_object_name = 'orders'
    
    def get_queryset(self):
        try:
            # Check for migration-dependent fields
            from django.db import connection
            cursor = connection.cursor()
            # Check if the cancellation_reason field exists
            cursor.execute("PRAGMA table_info(farm_core_order)")
            has_new_fields = any(row[1] == 'cancellation_reason' for row in cursor.fetchall())
            
            if has_new_fields:
                # Use the full query with all fields
                return Order.objects.filter(product__farmer=self.request.user).order_by('-order_date')
            else:
                # Empty queryset if fields are missing
                messages.warning(self.request, _('Database needs to be updated. Please run the migrations at /run-migrations/'))
                return Order.objects.none()
                
        except Exception as e:
            # Handle any database-related exceptions
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in FarmerOrderListView: {str(e)}")
            
            # Display error message to user
            messages.error(self.request, _('There was an error loading your orders. Please try running the migrations.'))
            return Order.objects.none()

class UpdateOrderStatusView(LoginRequiredMixin, FarmerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            order = Order.objects.get(pk=pk, product__farmer=request.user)
            
            status = request.POST.get('status')
            if status and status in dict(Order.STATUS_CHOICES):
                # Set the old status to track changes
                old_status = order.status
                order.status = status
                
                # Update timestamps based on status
                now = timezone.now()
                
                # Only update timestamp if status is changing
                if old_status != status:
                    if status == 'processing':
                        order.processing_date = now
                    elif status == 'shipped':
                        order.shipped_date = now
                    elif status == 'delivered':
                        order.delivered_date = now
                    elif status == 'cancelled':
                        order.cancelled_date = now
                
                # If the order is cancelled, get the cancellation reason
                if status == 'cancelled':
                    order.cancellation_reason = request.POST.get('cancellation_reason', '')
                
                # If the order is shipped, save tracking info
                if status == 'shipped':
                    order.tracking_number = request.POST.get('tracking_number', '')
                
                # Save any notes
                if request.POST.get('notes'):
                    order.notes = request.POST.get('notes')
                
                order.save()
                messages.success(request, _('Order status updated successfully.'))
            else:
                messages.error(request, _('Invalid status.'))
                
        except Order.DoesNotExist:
            messages.error(request, _('Order not found.'))
        
        return redirect('farm_core:farmer_orders')

class ContactBuyerView(LoginRequiredMixin, FarmerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            order = Order.objects.get(pk=pk, product__farmer=request.user)
            subject = request.POST.get('subject', '')
            message = request.POST.get('message', '')
            
            if not subject or not message:
                messages.error(request, _('Subject and message are required.'))
                return redirect('farm_core:farmer_orders')
            
            # Here you would implement the actual email sending functionality
            # For example, using Django's send_mail function
            
            messages.success(
                request, 
                _('Your message has been sent to %(name)s.') % {
                    'name': order.consumer.get_full_name() or order.consumer.username
                }
            )
            
        except Order.DoesNotExist:
            messages.error(request, _('Order not found.'))
        
        return redirect('farm_core:farmer_orders')

# Consumer views
class ProductListView(ListView):
    model = Product
    template_name = 'farm_core/products/list.html'
    context_object_name = 'products'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = Product.objects.all().order_by('-created_at')
        
        # Search functionality
        search_query = self.request.GET.get('search_query')
        if search_query:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(name__icontains=search_query) |  # Search by product name
                Q(farmer__first_name__icontains=search_query) |  # Search by farmer first name
                Q(farmer__last_name__icontains=search_query) |  # Search by farmer last name
                Q(farmer__username__icontains=search_query)  # Search by farmer username
            )
        
        # Apply filters
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
            
        min_price = self.request.GET.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
            
        max_price = self.request.GET.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
            
        in_stock = self.request.GET.get('in_stock')
        if in_stock:
            queryset = queryset.filter(quantity_available__gt=0)
            
        # Apply sorting
        sort = self.request.GET.get('sort')
        if sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort == 'rating':
            queryset = queryset.order_by('-avg_rating')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ProductCategory.objects.all()
        context['featured_farmers'] = User.objects.filter(user_type='farmer').order_by('-date_joined')[:3]
        
        # Get current category for display
        category_id = self.request.GET.get('category')
        if category_id:
            try:
                context['current_category'] = ProductCategory.objects.get(id=category_id)
            except ProductCategory.DoesNotExist:
                pass
                
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'farm_core/products/detail.html'
    context_object_name = 'product'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # Add review form and user's existing review (if any)
        context['form'] = ProductReviewForm()
        if self.request.user.is_authenticated:
            try:
                user_review = ProductReview.objects.get(product=product, user=self.request.user)
                context['user_review'] = user_review
                context['form'] = ProductReviewForm(instance=user_review)
            except ProductReview.DoesNotExist:
                pass
        
        # Get all reviews for the product
        context['reviews'] = product.reviews.all()
        
        # Get complementary products (frequently bought together)
        context['complementary_products'] = product.get_recommended_products(limit=4)
        
        # Add cart info
        cart = self.request.session.get('cart', {})
        context['cart_count'] = sum(int(quantity) for quantity in cart.values())
        
        return context
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, _('You must be logged in to submit a review.'))
            return redirect('farm_core:login')
            
        self.object = self.get_object()
        
        # Check if user already reviewed this product
        user_review = ProductReview.objects.filter(
            product=self.object, 
            user=request.user
        ).first()
        
        if user_review:
            # Update existing review
            form = ProductReviewForm(request.POST, instance=user_review)
            success_message = _('Your review has been updated.')
        else:
            # Create new review
            form = ProductReviewForm(request.POST)
            success_message = _('Thank you for your review!')
        
        if form.is_valid():
            review = form.save(commit=False)
            review.product = self.object
            review.user = request.user
            review.save()
            
            messages.success(request, success_message)
        else:
            messages.error(request, _('There was an error with your review. Please try again.'))
            
        return redirect('farm_core:product_detail', pk=self.object.pk)

class CategoryProductListView(ListView):
    model = Product
    template_name = 'farm_core/products/list.html'
    context_object_name = 'products'
    paginate_by = 9
    
    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        queryset = Product.objects.filter(category_id=category_id)
        
        # Search functionality
        search_query = self.request.GET.get('search_query')
        if search_query:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(name__icontains=search_query) |  # Search by product name
                Q(farmer__first_name__icontains=search_query) |  # Search by farmer first name
                Q(farmer__last_name__icontains=search_query) |  # Search by farmer last name
                Q(farmer__username__icontains=search_query)  # Search by farmer username
            )
            
        # Apply additional filters
        min_price = self.request.GET.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
            
        max_price = self.request.GET.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
            
        in_stock = self.request.GET.get('in_stock')
        if in_stock:
            queryset = queryset.filter(quantity_available__gt=0)
            
        # Apply sorting
        sort = self.request.GET.get('sort')
        if sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort == 'rating':
            queryset = queryset.order_by('-avg_rating')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ProductCategory.objects.all()
        context['current_category'] = get_object_or_404(ProductCategory, pk=self.kwargs.get('category_id'))
        context['featured_farmers'] = User.objects.filter(user_type='farmer').order_by('-date_joined')[:3]
        return context

# Shopping cart views
class CartView(LoginRequiredMixin, TemplateView):
    template_name = 'farm_core/cart/cart.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get cart items from the database model instead of session
        cart_items = CartItem.objects.filter(user=self.request.user).select_related('product')
        total = sum(item.subtotal for item in cart_items)
        
        context['cart_items'] = cart_items
        context['total'] = total
        context['item_count'] = cart_items.count()
        
        return context

class AddToCartView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        if product_id:
            try:
                product = Product.objects.get(id=product_id)
                
                # Check if the product is available
                if not product.is_available or product.quantity_available < quantity:
                    messages.error(request, _('Sorry, this product is not available in the requested quantity.'))
                    return redirect('farm_core:product_detail', pk=product_id)
                
                # Check if the product is already in the cart
                cart_item, created = CartItem.objects.get_or_create(
                    user=request.user,
                    product=product,
                    defaults={'quantity': quantity}
                )
                
                # If the product already exists in the cart, update the quantity
                if not created:
                    cart_item.quantity += quantity
                    # Check if quantity exceeds available stock
                    if cart_item.quantity > product.quantity_available:
                        cart_item.quantity = product.quantity_available
                        messages.warning(request, _('We have adjusted the quantity to the maximum available stock.'))
                    cart_item.save()
                
                messages.success(request, _('Product added to your cart successfully.'))
                
            except Product.DoesNotExist:
                messages.error(request, _('Product not found.'))
            except Exception as e:
                messages.error(request, _('An error occurred while adding the product to your cart.'))
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in AddToCartView: {str(e)}")
        
        return redirect('farm_core:cart')

class RemoveFromCartView(LoginRequiredMixin, View):
    def post(self, request, item_id, *args, **kwargs):
        try:
            cart_item = CartItem.objects.get(id=item_id, user=request.user)
            cart_item.delete()
            messages.success(request, _('Product removed from your cart.'))
        except CartItem.DoesNotExist:
            messages.error(request, _('Item not found in your cart.'))
        except Exception as e:
            messages.error(request, _('An error occurred while removing the product from your cart.'))
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in RemoveFromCartView: {str(e)}")
        
        return redirect('farm_core:cart')

class UpdateCartView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            item_id = request.POST.get('item_id')
            quantity = int(request.POST.get('quantity', 1))
            
            if quantity <= 0:
                return redirect('farm_core:remove_from_cart', item_id=item_id)
            
            cart_item = CartItem.objects.get(id=item_id, user=request.user)
            
            # Check if requested quantity exceeds available quantity
            if quantity > cart_item.product.quantity_available:
                quantity = cart_item.product.quantity_available
                messages.warning(request, _('We have adjusted the quantity to the maximum available stock.'))
            
            cart_item.quantity = quantity
            cart_item.save()
            
            messages.success(request, _('Cart updated successfully.'))
            
        except CartItem.DoesNotExist:
            messages.error(request, _('Item not found in your cart.'))
        except Exception as e:
            messages.error(request, _('An error occurred while updating your cart.'))
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in UpdateCartView: {str(e)}")
        
        return redirect('farm_core:cart')

# Order management
class CreateOrderView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'farm_core/orders/create.html'
    success_url = reverse_lazy('farm_core:order_list')
    
    def get_initial(self):
        initial = super().get_initial()
        product_id = self.kwargs.get('product_id')
        product = get_object_or_404(Product, pk=product_id)
        initial['product'] = product
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.kwargs.get('product_id')
        context['product'] = get_object_or_404(Product, pk=product_id)
        return context
    
    def form_valid(self, form):
        form.instance.consumer = self.request.user
        form.instance.product = get_object_or_404(Product, pk=self.kwargs.get('product_id'))
        
        # Check if there's enough quantity available
        product = form.instance.product
        if form.instance.quantity > product.quantity_available:
            form.add_error('quantity', _('Not enough quantity available'))
            return self.form_invalid(form)
        
        # Update product quantity
        product.quantity_available -= form.instance.quantity
        product.save()
        
        messages.success(self.request, _('Order placed successfully.'))
        return super().form_valid(form)

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'farm_core/orders/list.html'
    context_object_name = 'orders'
    
    def get_queryset(self):
        try:
            # Check for migration-dependent fields
            from django.db import connection
            cursor = connection.cursor()
            # Check if the cancellation_reason field exists
            cursor.execute("PRAGMA table_info(farm_core_order)")
            has_new_fields = any(row[1] == 'cancellation_reason' for row in cursor.fetchall())
            
            if has_new_fields:
                # Use the full query with all fields
                return Order.objects.filter(consumer=self.request.user).order_by('-order_date')
            else:
                # Empty queryset if fields are missing
                messages.warning(self.request, _('Database needs to be updated. Please run the migrations at /run-migrations/'))
                return Order.objects.none()
                
        except Exception as e:
            # Handle any database-related exceptions
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in OrderListView: {str(e)}")
            
            # Display error message to user
            messages.error(self.request, _('There was an error loading your orders. Please try running the migrations.'))
            return Order.objects.none()

class OrderDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Order
    template_name = 'farm_core/orders/detail.html'
    context_object_name = 'order'
    
    def test_func(self):
        try:
            order = self.get_object()
            return (self.request.user == order.consumer or 
                   (self.request.user.user_type == 'farmer' and self.request.user == order.product.farmer))
        except Exception:
            return False
            
    def get(self, request, *args, **kwargs):
        try:
            # Check for migration-dependent fields
            from django.db import connection
            cursor = connection.cursor()
            # Check if the cancellation_reason field exists
            cursor.execute("PRAGMA table_info(farm_core_order)")
            has_new_fields = any(row[1] == 'cancellation_reason' for row in cursor.fetchall())
            
            if not has_new_fields:
                # Redirect or show message if fields are missing
                from django.contrib import messages
                from django.utils.translation import gettext_lazy as _
                from django.shortcuts import redirect
                messages.warning(request, _('Database needs to be updated. Please run the migrations at /run-migrations/'))
                
                # Redirect to the appropriate list view based on user type
                if request.user.user_type == 'farmer':
                    return redirect('farm_core:farmer_orders')
                else:
                    return redirect('farm_core:order_list')
                
            return super().get(request, *args, **kwargs)
                
        except Exception as e:
            # Handle any database-related exceptions
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in OrderDetailView: {str(e)}")
            
            # Display error message to user
            from django.contrib import messages
            from django.utils.translation import gettext_lazy as _
            from django.shortcuts import redirect
            messages.error(request, _('There was an error loading the order details. Please try running the migrations.'))
            
            # Redirect to the appropriate list view based on user type
            if request.user.user_type == 'farmer':
                return redirect('farm_core:farmer_orders')
            else:
                return redirect('farm_core:order_list')

# User profile
class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'farm_core/profile/view.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Common data for both user types
        cart = self.request.session.get('cart', {})
        context['cart_count'] = sum(int(quantity) for quantity in cart.values())
        
        try:
            if user.user_type == 'farmer':
                # Farmer specific data
                context['products_count'] = Product.objects.filter(farmer=user).count()
                
                # Check for migration-dependent fields
                from django.db import connection
                cursor = connection.cursor()
                # Check if the cancellation_reason field exists
                cursor.execute("PRAGMA table_info(farm_core_order)")
                has_new_fields = any(row[1] == 'cancellation_reason' for row in cursor.fetchall())
                
                if has_new_fields:
                    # Use the full query with all fields
                    context['orders_count'] = Order.objects.filter(product__farmer=user).count()
                    context['recent_orders'] = Order.objects.filter(
                        product__farmer=user
                    ).order_by('-order_date')[:5]
                    
                    # Calculate total sales
                    sales = Order.objects.filter(product__farmer=user)
                    context['sales_total'] = sales.aggregate(total=Sum('total_price'))['total'] or 0
                else:
                    # Use a simpler query without accessing the new fields
                    context['orders_count'] = 0
                    context['recent_orders'] = []
                    context['sales_total'] = 0
                    
                    # Redirect to migration page with a message
                    from django.shortcuts import redirect
                    messages.warning(self.request, _('Database needs to be updated. Please run the migrations.'))
                    
            else:
                # Consumer specific data
                try:
                    context['orders_count'] = Order.objects.filter(consumer=user).count()
                    context['recent_orders'] = Order.objects.filter(
                        consumer=user
                    ).order_by('-order_date')[:5]
                except Exception:
                    # If there's an error (likely due to missing fields), provide defaults
                    context['orders_count'] = 0
                    context['recent_orders'] = []
                
                # For wishlist count (placeholder for now)
                context['wishlist_count'] = 0
        
        except Exception as e:
            # Handle any database-related exceptions
            context['error_message'] = str(e)
            context['products_count'] = 0
            context['orders_count'] = 0
            context['recent_orders'] = []
            context['sales_total'] = 0
            context['wishlist_count'] = 0
            
            # Log the error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in ProfileView: {str(e)}")
            
            # Display error message to user
            messages.error(self.request, _('There was an error loading your profile data. Please try running the migrations.'))
        
        return context

class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'farm_core/profile/edit.html'
    success_url = reverse_lazy('farm_core:profile')
    
    def get_object(self):
        return self.request.user
    
    def get_form_class(self):
        # Use different form class based on user type
        if self.request.user.user_type == 'farmer':
            from .forms import FarmerProfileForm
            return FarmerProfileForm
        else:
            from .forms import UserProfileForm
            return UserProfileForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add user to context explicitly
        context['user'] = self.request.user
        
        # Add NPOP certificate expiry warning for farmers if certificate is about to expire
        if self.request.user.user_type == 'farmer' and self.request.user.npop_certificate_expiry_date:
            from datetime import date, timedelta
            today = date.today()
            # If certificate expires within 30 days, add warning message
            if self.request.user.npop_certificate_expiry_date - today <= timedelta(days=30):
                days_remaining = (self.request.user.npop_certificate_expiry_date - today).days
                context['npop_expiry_warning'] = True
                context['days_until_expiry'] = days_remaining
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Profile updated successfully.'))
        return super().form_valid(form)

class CheckoutView(LoginRequiredMixin, TemplateView):
    template_name = 'farm_core/cart/checkout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get cart items from the database model
        cart_items = CartItem.objects.filter(user=self.request.user).select_related('product')
        
        if not cart_items:
            messages.warning(self.request, _('Your cart is empty. Add some products before checkout.'))
            return context
        
        total = sum(item.subtotal for item in cart_items)
        
        context['cart_items'] = cart_items
        context['total'] = total
        context['item_count'] = cart_items.count()
        
        return context
    
    def get(self, request, *args, **kwargs):
        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items.exists():
            messages.warning(request, _('Your cart is empty. Add some products before checkout.'))
            return redirect('farm_core:product_list')
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        
        if not cart_items.exists():
            messages.warning(request, _('Your cart is empty. Add some products before checkout.'))
            return redirect('farm_core:product_list')
        
        try:
            # Process the orders
            orders = []
            payment_method = request.POST.get('payment_method', 'cod')
            address = request.POST.get('address', '')
            address2 = request.POST.get('address2', '')
            city = request.POST.get('city', '')
            state = request.POST.get('state', '')
            zip_code = request.POST.get('zip', '')
            shipping_address = f"{address}\n{address2}\n{city}, {state} {zip_code}"
            
            for cart_item in cart_items:
                product = cart_item.product
                
                # Check if product is still available
                if product.quantity_available < cart_item.quantity:
                    messages.error(
                        request, 
                        _('Sorry, %(product)s is out of stock or has insufficient quantity.') % {
                            'product': product.name
                        }
                    )
                    return redirect('farm_core:cart')
                
                # Create the order
                total_price = product.price * cart_item.quantity
                order = Order.objects.create(
                    product=product,
                    consumer=request.user,
                    quantity=cart_item.quantity,
                    status='pending',
                    total_price=total_price,
                    shipping_address=shipping_address
                )
                orders.append(order)
                
                # Create payment transaction
                PaymentTransaction.objects.create(
                    order=order,
                    user=request.user,
                    amount=total_price,
                    payment_method=payment_method,
                    payment_status='pending'
                )
                
                # Update product quantity
                product.quantity_available -= cart_item.quantity
                product.save()
            
            # Clear the user's cart
            cart_items.delete()
            
            # Redirect to payment page if needed
            if payment_method == 'cod':
                messages.success(request, _('Your order has been placed successfully! You will pay on delivery.'))
                return redirect('farm_core:order_list')
            else:
                # For other payment methods, redirect to payment gateway
                return redirect('farm_core:payment_gateway', order_ids=','.join(str(order.id) for order in orders))
            
        except Exception as e:
            messages.error(request, _('Error creating order. Please try again later.'))
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating order in CheckoutView: {str(e)}")
            return redirect('farm_core:cart')

# Custom logout view
def logout_view(request):
    username = request.user.username
    auth_logout(request)
    messages.success(request, _('You have been successfully logged out.'))
    return redirect('farm_core:home')

# Payment Processing
class PaymentGatewayView(LoginRequiredMixin, TemplateView):
    template_name = 'farm_core/payment/gateway.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_ids = self.kwargs.get('order_ids', '').split(',')
        
        try:
            # Get orders and associated payment transactions
            orders = Order.objects.filter(id__in=order_ids, consumer=self.request.user)
            payment_transactions = PaymentTransaction.objects.filter(order__in=orders)
            
            # Calculate total amount
            total_amount = sum(transaction.amount for transaction in payment_transactions)
            
            context['orders'] = orders
            context['payment_transactions'] = payment_transactions
            context['total_amount'] = total_amount
            context['payment_reference'] = f"FARM-{int(timezone.now().timestamp())}"
            
            # Get payment method from the first transaction (should be the same for all)
            if payment_transactions.exists():
                context['payment_method'] = payment_transactions.first().payment_method
            else:
                context['payment_method'] = 'cod'
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in PaymentGatewayView: {str(e)}")
            messages.error(self.request, _('An error occurred while loading payment information.'))
            context['error'] = True
            
        return context
    
    def post(self, request, *args, **kwargs):
        order_ids = self.kwargs.get('order_ids', '').split(',')
        payment_method = request.POST.get('payment_method')
        card_number = request.POST.get('card_number', '').replace(' ', '')
        expiry_date = request.POST.get('expiry_date', '')
        cvv = request.POST.get('cvv', '')
        cardholder_name = request.POST.get('cardholder_name', '')
        
        # Simple validation (in a real app, you'd use a payment processor API)
        if payment_method == 'card':
            if not (card_number and expiry_date and cvv and cardholder_name):
                messages.error(request, _('Please fill in all card details.'))
                return redirect('farm_core:payment_gateway', order_ids=','.join(order_ids))
            
            if not card_number.isdigit() or len(card_number) < 13:
                messages.error(request, _('Invalid card number.'))
                return redirect('farm_core:payment_gateway', order_ids=','.join(order_ids))
        
        try:
            # Update payment transactions
            payment_transactions = PaymentTransaction.objects.filter(
                order_id__in=order_ids,
                user=request.user
            )
            
            # In a real app, this is where you'd integrate with a payment gateway API
            # Here we're just simulating a successful payment
            transaction_id = f"TXN-{int(timezone.now().timestamp())}"
            
            for transaction in payment_transactions:
                transaction.payment_method = payment_method
                transaction.transaction_id = transaction_id
                transaction.payment_status = 'completed'  # Assuming payment is always successful
                transaction.gateway_response = "Payment processed successfully"
                transaction.save()
            
            messages.success(request, _('Payment processed successfully. Thank you for your order!'))
            return redirect('farm_core:order_list')
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error processing payment: {str(e)}")
            messages.error(request, _('An error occurred while processing your payment. Please try again.'))
            return redirect('farm_core:payment_gateway', order_ids=','.join(order_ids))
