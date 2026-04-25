import uuid
from django.db import models
from django.conf import settings


class Category(models.Model):
    ICON_CHOICES = [
        ('food',        '🍽️ Food & Dining'),
        ('transport',   '🚗 Transport'),
        ('shopping',    '🛍️ Shopping'),
        ('health',      '💊 Health'),
        ('education',   '📚 Education'),
        ('bills',       '💡 Bills & Utilities'),
        ('rent',        '🏠 Rent'),
        ('salary',      '💰 Salary'),
        ('freelance',   '💻 Freelance'),
        ('bkash',       '📱 bKash / Nagad'),
        ('entertainment','🎬 Entertainment'),
        ('other',       '📦 Other'),
    ]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,  # null = default/system category
        related_name='categories'
    )
    name       = models.CharField(max_length=50)
    icon       = models.CharField(max_length=20, choices=ICON_CHOICES, default='other')
    color      = models.CharField(max_length=7, default='#6366F1')  # hex color
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'categories'
        ordering  = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Expense(models.Model):
    TYPE_CHOICES = [
        ('expense', 'Expense'),
        ('income',  'Income'),
    ]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='expenses'
    )
    type       = models.CharField(max_length=10, choices=TYPE_CHOICES, default='expense')
    amount     = models.DecimalField(max_digits=12, decimal_places=2)
    category   = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='expenses'
    )
    note       = models.TextField(blank=True, default='')
    date       = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'expenses'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'{self.type} | {self.amount} BDT | {self.date}'


class Budget(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='budgets'
    )
    category   = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='budgets'
    )
    amount     = models.DecimalField(max_digits=12, decimal_places=2)
    month      = models.IntegerField()   # 1–12
    year       = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'budgets'
        unique_together = ['user', 'category', 'month', 'year']

    def __str__(self):
        return f'{self.user} | {self.category} | {self.month}/{self.year}'
