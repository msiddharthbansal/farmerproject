from django.core.management.base import BaseCommand
from farm_core.models import ProductCategory

class Command(BaseCommand):
    help = 'Creates default product categories'

    def handle(self, *args, **kwargs):
        categories = [
            {
                'name': 'Vegetables',
                'description': 'Fresh vegetables directly from farms'
            },
            {
                'name': 'Fruits',
                'description': 'Seasonal and exotic fruits'
            },
            {
                'name': 'Dairy',
                'description': 'Fresh milk, cheese, butter, and other dairy products'
            },
            {
                'name': 'Grains',
                'description': 'Rice, wheat, barley, and other grains'
            },
            {
                'name': 'Pulses',
                'description': 'Beans, lentils, and other legumes'
            },
            {
                'name': 'Nuts and Seeds',
                'description': 'Almonds, walnuts, chia seeds, and more'
            },
            {
                'name': 'Herbs and Spices',
                'description': 'Fresh and dried herbs and spices'
            },
            {
                'name': 'Honey and Preserves',
                'description': 'Natural honey and homemade preserves'
            },
            {
                'name': 'Oils',
                'description': 'Cold-pressed oils and traditional extracts'
            },
            {
                'name': 'Organic Products',
                'description': 'Certified organic farm products'
            },
        ]

        created_count = 0
        existing_count = 0

        for category_data in categories:
            category, created = ProductCategory.objects.get_or_create(
                name=category_data['name'],
                defaults={'description': category_data['description']}
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
            else:
                existing_count += 1
                self.stdout.write(self.style.WARNING(f'Category already exists: {category.name}'))

        self.stdout.write(self.style.SUCCESS(
            f'Finished creating categories. Created: {created_count}, Already existing: {existing_count}'
        )) 