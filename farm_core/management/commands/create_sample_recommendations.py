import random
from django.core.management.base import BaseCommand
from farm_core.models import Product, ProductRecommendation

class Command(BaseCommand):
    help = 'Creates sample product recommendations based on complementary products'

    def handle(self, *args, **options):
        # Get all products
        products = list(Product.objects.all())
        
        if len(products) < 2:
            self.stdout.write(self.style.WARNING('Not enough products to create recommendations'))
            return
        
        # Clear existing recommendations
        ProductRecommendation.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Cleared existing recommendations'))
        
        # Dictionary to track complementary categories
        complementary_categories = {
            'Vegetables': ['Spices', 'Oils', 'Fruits'],
            'Fruits': ['Dairy', 'Honey', 'Nuts'],
            'Dairy': ['Fruits', 'Baked Goods', 'Beverages'],
            'Grains': ['Vegetables', 'Dairy', 'Pulses'],
            'Pulses': ['Grains', 'Spices', 'Vegetables'],
            'Spices': ['Vegetables', 'Pulses', 'Meat'],
            'Meat': ['Vegetables', 'Spices', 'Grains'],
            'Oils': ['Vegetables', 'Spices', 'Baked Goods'],
            'Nuts': ['Fruits', 'Honey', 'Baked Goods'],
            'Honey': ['Fruits', 'Dairy', 'Baked Goods'],
            'Baked Goods': ['Dairy', 'Fruits', 'Honey'],
            'Beverages': ['Fruits', 'Dairy', 'Baked Goods'],
        }
        
        recommendations_created = 0
        
        # Create recommendations
        for primary_product in products:
            # Get category name
            category_name = primary_product.category.name if primary_product.category else None
            
            # Find complementary categories
            complementary_category_names = []
            if category_name and category_name in complementary_categories:
                complementary_category_names = complementary_categories[category_name]
            
            # Get potential products
            potential_products = []
            
            # Add products from complementary categories
            for complementary_category in complementary_category_names:
                category_products = [p for p in products if p.category and p.category.name == complementary_category and p != primary_product]
                potential_products.extend(category_products)
            
            # If not enough complementary category products, add some random products
            if len(potential_products) < 3:
                random_products = [p for p in products if p != primary_product and p not in potential_products]
                random.shuffle(random_products)
                potential_products.extend(random_products[:5])
            
            # Create recommendations (up to 5)
            num_recommendations = min(5, len(potential_products))
            recommended_products = random.sample(potential_products, num_recommendations)
            
            for recommended_product in recommended_products:
                # Create recommendation with random strength
                strength = random.randint(1, 10)
                ProductRecommendation.objects.create(
                    primary_product=primary_product,
                    recommended_product=recommended_product,
                    strength=strength
                )
                recommendations_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {recommendations_created} product recommendations')) 