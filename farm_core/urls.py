from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views_update import update_product_model, create_categories

app_name = 'farm_core'

urlpatterns = [
    # Temporary migration URLs
    path('run-migrations/', views.run_migrations, name='run_migrations'),
    path('migrations/', views.MigrationPageView.as_view(), name='migrations_page'),
    path('update-product-model/', update_product_model, name='update_product_model'),
    path('create-categories/', create_categories, name='create_categories'),
    
    # Home and static pages
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    
    # Authentication
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='farm_core/login.html', next_page='farm_core:profile'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Farmer dashboard
    path('farmer/dashboard/', views.FarmerDashboardView.as_view(), name='farmer_dashboard'),
    path('farmer/products/', views.FarmerProductListView.as_view(), name='farmer_products'),
    path('farmer/products/add/', views.ProductCreateView.as_view(), name='add_product'),
    path('farmer/products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='edit_product'),
    path('farmer/products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='delete_product'),
    path('farmer/products/bulk-action/', views.BulkProductActionView.as_view(), name='bulk_product_action'),
    path('farmer/orders/', views.FarmerOrderListView.as_view(), name='farmer_orders'),
    path('farmer/orders/<int:pk>/update-status/', views.UpdateOrderStatusView.as_view(), name='update_order_status'),
    path('farmer/orders/<int:pk>/contact-buyer/', views.ContactBuyerView.as_view(), name='contact_buyer'),
    
    # Consumer views
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('categories/<int:category_id>/products/', views.CategoryProductListView.as_view(), name='category_products'),
    
    # Shopping cart
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('cart/update/', views.UpdateCartView.as_view(), name='update_cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    
    # Order management
    path('order/<int:product_id>/', views.CreateOrderView.as_view(), name='create_order'),
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    
    # User profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='edit_profile'),
] 