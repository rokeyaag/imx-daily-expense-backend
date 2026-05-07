from rest_framework import serializers
from .models import Expense, Category, Budget

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = Category
        fields = ["id", "name", "icon", "color", "is_default"]
        read_only_fields = ["id"]

class ExpenseSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source="category", read_only=True)
    class Meta:
        model  = Expense
        fields = ["id", "type", "amount", "category", "category_detail", "note", "date", "created_at"]
        read_only_fields = ["id", "created_at"]
    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

class BudgetSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source="category", read_only=True)
    spent           = serializers.SerializerMethodField()
    remaining       = serializers.SerializerMethodField()
    percentage      = serializers.SerializerMethodField()
    class Meta:
        model  = Budget
        fields = ["id", "category", "category_detail", "amount", "month", "year", "spent", "remaining", "percentage"]
        read_only_fields = ["id"]
    def _get_spent(self, obj):
        from django.db.models import Sum
        result = Expense.objects.filter(
            user=obj.user, category=obj.category,
            type="expense", date__month=obj.month, date__year=obj.year,
        ).aggregate(total=Sum("amount"))
        return result["total"] or 0
    def get_spent(self, obj):     return float(self._get_spent(obj))
    def get_remaining(self, obj): return float(obj.amount) - float(self._get_spent(obj))
    def get_percentage(self, obj):
        spent = float(self._get_spent(obj))
        if float(obj.amount) == 0: return 0
        return round((spent / float(obj.amount)) * 100, 1)
    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
