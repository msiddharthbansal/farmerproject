from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count
from django.contrib.auth import logout as auth_logout
from django.utils import timezone
from django.http import HttpResponse
from .models import User, Product, ProductCategory, Order
from .forms import UserSignupForm, ProductForm, OrderForm, UserProfileForm
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
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'farm_core/products/detail.html'
    context_object_name = 'product'

class CategoryProductListView(ListView):
    model = Product
    template_name = 'farm_core/products/list.html'
    context_object_name = 'products'
    paginate_by = 9
    
    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        return Product.objects.filter(category_id=category_id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ProductCategory.objects.all()
        context['current_category'] = get_object_or_404(ProductCategory, pk=self.kwargs.get('category_id'))
        context['featured_farmers'] = User.objects.filter(user_type='farmer').order_by('-date_joined')[:3]
        return context

# Shopping cart views
class CartView(TemplateView):
    template_name = 'farm_core/cart/cart.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.request.session.get('cart', {})
        cart_items = []
        total = 0
        
        for product_id, quantity in cart.items():
            try:
                product = Product.objects.get(id=product_id)
                item_total = product.price * int(quantity)
                total += item_total
                cart_items.append({
                    'id': product_id,
                    'product': product,
                    'quantity': quantity,
                    'subtotal': item_total
                })
            except Product.DoesNotExist:
                pass
        
        context['cart_items'] = cart_items
        context['total'] = total
        context['item_count'] = sum(int(quantity) for quantity in cart.values())
        
        return context

class AddToCartView(View):
    def post(self, request, *args, **kwargs):
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        try:
            product = Product.objects.get(id=product_id)
            if product.quantity_available < quantity:
                messages.error(request, _('Not enough stock available.'))
                return redirect('farm_core:product_detail', pk=product_id)
            
            # Initialize or get the cart from session
            cart = request.session.get('cart', {})
            
            # Add or update item in cart
            if product_id in cart:
                cart[product_id] += quantity
            else:
                cart[product_id] = quantity
            
            request.session['cart'] = cart
            messages.success(request, _('Product added to cart.'))
            
            # Redirect to referer or products list if referer is not available
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect(referer)
            return redirect('farm_core:product_list')
            
        except Product.DoesNotExist:
            messages.error(request, _('Product not found.'))
            return redirect('farm_core:product_list')

class RemoveFromCartView(View):
    def post(self, request, item_id, *args, **kwargs):
        cart = request.session.get('cart', {})
        if str(item_id) in cart:
            del cart[str(item_id)]
            request.session['cart'] = cart
            messages.success(request, _('Item removed from cart.'))
        
        referer = request.META.get('HTTP_REFERER')
        if referer and 'cart' in referer:
            return redirect('farm_core:cart')
        return redirect('farm_core:product_list')

class UpdateCartView(View):
    def post(self, request, *args, **kwargs):
        product_ids = request.POST.getlist('product_id')
        quantities = request.POST.getlist('quantity')
        
        cart = request.session.get('cart', {})
        
        for product_id, quantity in zip(product_ids, quantities):
            try:
                qty = int(quantity)
                if qty > 0:
                    product = Product.objects.get(id=product_id)
                    if product.quantity_available >= qty:
                        cart[str(product_id)] = qty
                    else:
                        messages.error(
                            request, 
                            _('Only %(available)s units of %(product)s available.') % {
                                'available': product.quantity_available,
                                'product': product.name
                            }
                        )
                else:
                    if str(product_id) in cart:
                        del cart[str(product_id)]
            except (ValueError, Product.DoesNotExist):
                pass
        
        request.session['cart'] = cart
        messages.success(request, _('Cart updated successfully.'))
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
    form_class = UserProfileForm
    template_name = 'farm_core/profile/edit.html'
    success_url = reverse_lazy('farm_core:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, _('Profile updated successfully.'))
        return super().form_valid(form)

class CheckoutView(LoginRequiredMixin, TemplateView):
    template_name = 'farm_core/cart/checkout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.request.session.get('cart', {})
        
        if not cart:
            messages.warning(self.request, _('Your cart is empty. Add some products before checkout.'))
            return context  # Just return the context, redirect will happen in get()
        
        cart_items = []
        total = 0
        
        for product_id, quantity in cart.items():
            try:
                product = Product.objects.get(id=product_id)
                item_total = product.price * int(quantity)
                total += item_total
                cart_items.append({
                    'id': product_id,
                    'product': product,
                    'quantity': quantity,
                    'subtotal': item_total
                })
            except Product.DoesNotExist:
                pass
        
        context['cart_items'] = cart_items
        context['total'] = total
        context['item_count'] = sum(int(quantity) for quantity in cart.values())
        
        return context
    
    def get(self, request, *args, **kwargs):
        cart = request.session.get('cart', {})
        if not cart:
            messages.warning(request, _('Your cart is empty. Add some products before checkout.'))
            return redirect('farm_core:product_list')
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        cart = request.session.get('cart', {})
        
        if not cart:
            messages.warning(request, _('Your cart is empty. Add some products before checkout.'))
            return redirect('farm_core:product_list')
        
        # Check for migration-dependent fields
        try:
            from django.db import connection
            cursor = connection.cursor()
            cursor.execute("PRAGMA table_info(farm_core_order)")
            has_new_fields = any(row[1] == 'cancellation_reason' for row in cursor.fetchall())
            
            if not has_new_fields:
                messages.warning(request, _('Database needs to be updated. Please run the migrations at /run-migrations/ before checkout.'))
                return redirect('farm_core:cart')
        except Exception as e:
            messages.error(request, _('There was an error checking the database. Please try again later.'))
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error checking database in CheckoutView: {str(e)}")
            return redirect('farm_core:cart')
        
        # Process the order here (create Order objects)
        for product_id, quantity in cart.items():
            try:
                product = Product.objects.get(id=product_id)
                if product.quantity_available >= int(quantity):
                    # Calculate total price for this order
                    total_price = product.price * int(quantity)
                    
                    # Create the order
                    order = Order.objects.create(
                        product=product,
                        consumer=request.user,
                        quantity=quantity,
                        status='pending',  # Use the field name 'status', not 'order_status'
                        total_price=total_price,
                        shipping_address=request.POST.get('address', 'No address provided')
                    )
                    
                    # Update product quantity
                    product.quantity_available -= int(quantity)
                    product.save()
                else:
                    messages.error(
                        request, 
                        _('Sorry, %(product)s is out of stock or has insufficient quantity.') % {
                            'product': product.name
                        }
                    )
                    return redirect('farm_core:cart')
            except Product.DoesNotExist:
                pass
            except Exception as e:
                messages.error(request, _('Error creating order. Please try again later.'))
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating order in CheckoutView: {str(e)}")
                return redirect('farm_core:cart')
        
        # Clear the cart after successful checkout
        request.session['cart'] = {}
        messages.success(request, _('Your order has been placed successfully.'))
        return redirect('farm_core:order_list')

# Custom logout view
def logout_view(request):
    username = request.user.username
    auth_logout(request)
    messages.success(request, _('You have been successfully logged out.'))
    return redirect('farm_core:home')
