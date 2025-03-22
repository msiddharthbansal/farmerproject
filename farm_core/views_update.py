from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.db import connection
import sqlite3
import json

def update_product_model(request):
    if request.GET.get('run') != 'true':
        # Just render the template the first time
        return render(request, 'farm_core/product_update.html')
    
    try:
        # Check if the database needs update
        cursor = connection.cursor()
        
        # Check if the new fields exist in the product table
        cursor.execute("PRAGMA table_info(farm_core_product)")
        columns = {row[1] for row in cursor.fetchall()}
        
        # List of new fields we added to the Product model
        new_fields = [
            'discount_price', 'unit', 'is_organic', 'is_available', 
            'harvest_date', 'expiry_date', 'nutritional_info'
        ]
        
        missing_fields = [field for field in new_fields if field not in columns]
        
        if not missing_fields:
            return render(request, 'farm_core/product_update.html', {
                'migration_result': "Product model is already up to date! No changes needed."
            })
        
        # Add the missing columns manually through SQL
        for field in missing_fields:
            try:
                if field in ['harvest_date', 'expiry_date']:
                    # Date fields
                    cursor.execute(f"ALTER TABLE farm_core_product ADD COLUMN {field} date NULL")
                elif field in ['discount_price']:
                    # Decimal fields
                    cursor.execute(f"ALTER TABLE farm_core_product ADD COLUMN {field} decimal(10, 2) NULL")
                elif field in ['is_organic', 'is_available']:
                    # Boolean fields with default
                    default_value = 'false'
                    if field == 'is_available':
                        default_value = 'true'
                    cursor.execute(f"ALTER TABLE farm_core_product ADD COLUMN {field} bool NOT NULL DEFAULT {default_value}")
                elif field in ['nutritional_info']:
                    # Text fields
                    cursor.execute(f"ALTER TABLE farm_core_product ADD COLUMN {field} text NULL")
                elif field == 'unit':
                    # Char field with default
                    cursor.execute(f"ALTER TABLE farm_core_product ADD COLUMN {field} varchar(10) NOT NULL DEFAULT 'kg'")
            except sqlite3.OperationalError as e:
                # If the column already exists, ignore the error
                if 'duplicate column name' not in str(e).lower():
                    raise
        
        # Create initial categories
        from farm_core.models import ProductCategory
        
        categories = [
            ('Vegetables', 'Fresh vegetables directly from farms'),
            ('Fruits', 'Seasonal and exotic fruits'),
            ('Dairy', 'Fresh milk, cheese, butter, and other dairy products'),
            ('Grains', 'Rice, wheat, barley, and other grains'),
            ('Pulses', 'Beans, lentils, and other legumes'),
            ('Nuts and Seeds', 'Almonds, walnuts, chia seeds, and more'),
            ('Herbs and Spices', 'Fresh and dried herbs and spices'),
            ('Honey and Preserves', 'Natural honey and homemade preserves'),
            ('Oils', 'Cold-pressed oils and traditional extracts'),
            ('Organic Products', 'Certified organic farm products'),
        ]
        
        created_count = 0
        for name, description in categories:
            try:
                # Check if category exists and create if not
                category, created = ProductCategory.objects.get_or_create(
                    name=name,
                    defaults={'description': description}
                )
                if created:
                    created_count += 1
            except Exception as e:
                return render(request, 'farm_core/product_update.html', {
                    'migration_result': f"Error creating category {name}: {str(e)}"
                })
        
        return render(request, 'farm_core/product_update.html', {
            'migration_result': f"Database updated successfully! Added fields to the Product model: {', '.join(missing_fields)}. Created {created_count} new product categories."
        })
    
    except Exception as e:
        return render(request, 'farm_core/product_update.html', {
            'migration_result': f"Error updating database: {str(e)}. Try restarting the server."
        })

def create_categories(request):
    """View to create default product categories if they don't exist yet"""
    if request.GET.get('run') != 'true':
        # Just render the template the first time
        return render(request, 'farm_core/category_setup.html')
    
    try:
        # Import models
        from farm_core.models import ProductCategory
        
        categories = [
            ('Vegetables', 'Fresh vegetables directly from farms'),
            ('Fruits', 'Seasonal and exotic fruits'),
            ('Dairy', 'Fresh milk, cheese, butter, and other dairy products'),
            ('Grains', 'Rice, wheat, barley, and other grains'),
            ('Pulses', 'Beans, lentils, and other legumes'),
            ('Nuts and Seeds', 'Almonds, walnuts, chia seeds, and more'),
            ('Herbs and Spices', 'Fresh and dried herbs and spices'),
            ('Honey and Preserves', 'Natural honey and homemade preserves'),
            ('Oils', 'Cold-pressed oils and traditional extracts'),
            ('Organic Products', 'Certified organic farm products'),
        ]
        
        created_count = 0
        for name, description in categories:
            try:
                # Check if category exists and create if not
                category, created = ProductCategory.objects.get_or_create(
                    name=name,
                    defaults={'description': description}
                )
                if created:
                    created_count += 1
            except Exception as e:
                return render(request, 'farm_core/category_setup.html', {
                    'result': f"Error creating category {name}: {str(e)}"
                })
        
        if created_count > 0:
            result = f"Successfully created {created_count} new product categories. You can now add products with these categories."
        else:
            result = "All categories already exist. You can now add products with these categories."
        
        return render(request, 'farm_core/category_setup.html', {
            'result': result
        })
    
    except Exception as e:
        return render(request, 'farm_core/category_setup.html', {
            'result': f"Error creating categories: {str(e)}"
        }) 