from django.core.management.base import BaseCommand
from apps.expenses.models import Category


DEFAULT_CATEGORIES = [
    {'name': 'খাবার',          'icon': 'food',          'color': '#F97316'},
    {'name': 'যাতায়াত',        'icon': 'transport',     'color': '#3B82F6'},
    {'name': 'কেনাকাটা',       'icon': 'shopping',      'color': '#EC4899'},
    {'name': 'স্বাস্থ্য',       'icon': 'health',        'color': '#10B981'},
    {'name': 'শিক্ষা',          'icon': 'education',     'color': '#8B5CF6'},
    {'name': 'বিল / ইউটিলিটি', 'icon': 'bills',         'color': '#F59E0B'},
    {'name': 'বাড়িভাড়া',      'icon': 'rent',          'color': '#EF4444'},
    {'name': 'বেতন',            'icon': 'salary',        'color': '#22C55E'},
    {'name': 'ফ্রিল্যান্স',     'icon': 'freelance',     'color': '#06B6D4'},
    {'name': 'bKash / Nagad',   'icon': 'bkash',         'color': '#E91E8C'},
    {'name': 'বিনোদন',          'icon': 'entertainment', 'color': '#A855F7'},
    {'name': 'অন্যান্য',        'icon': 'other',         'color': '#6B7280'},
]


class Command(BaseCommand):
    help = 'Seed default categories for Bangladeshi users'

    def handle(self, *args, **kwargs):
        created = 0
        for cat in DEFAULT_CATEGORIES:
            _, was_created = Category.objects.get_or_create(
                name=cat['name'],
                is_default=True,
                defaults={
                    'icon':  cat['icon'],
                    'color': cat['color'],
                    'user':  None,
                }
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'✅ Done! {created} new categories created.'
        ))
