import uuid
from django.db import models
from django.conf import settings

class Category(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories", null=True, blank=True)
    name       = models.CharField(max_length=100)
    icon       = models.CharField(max_length=10, blank=True, default="")
    color      = models.CharField(max_length=20, blank=True, default="#6366F1")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

class Expense(models.Model):
    TYPE_CHOICES = [("income", "Income"), ("expense", "Expense")]
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="expenses")
    category   = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="expenses")
    type       = models.CharField(max_length=10, choices=TYPE_CHOICES, default="expense")
    amount     = models.DecimalField(max_digits=12, decimal_places=2)
    note       = models.CharField(max_length=255, blank=True, default="")
    date       = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.type} - {self.amount}"

class Budget(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets")
    category   = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="budgets")
    amount     = models.DecimalField(max_digits=12, decimal_places=2)
    month      = models.IntegerField()
    year       = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"Budget {self.month}/{self.year} - {self.amount}"

