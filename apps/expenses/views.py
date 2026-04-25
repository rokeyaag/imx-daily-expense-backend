from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q
from .models import Expense, Category, Budget
from .serializers import ExpenseSerializer, CategorySerializer, BudgetSerializer
import django_filters


class ExpenseFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to   = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    month     = django_filters.NumberFilter(field_name='date', lookup_expr='month')
    year      = django_filters.NumberFilter(field_name='date', lookup_expr='year')
    type      = django_filters.CharFilter(field_name='type')
    category  = django_filters.UUIDFilter(field_name='category__id')

    class Meta:
        model  = Expense
        fields = ['type', 'category', 'date_from', 'date_to', 'month', 'year']


class ExpenseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = ExpenseSerializer
    filterset_class    = ExpenseFilter
    search_fields      = ['note']
    ordering_fields    = ['date', 'amount', 'created_at']
    ordering           = ['-date']

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user).select_related('category')

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Monthly summary — total income, expense, balance"""
        month = request.query_params.get('month')
        year  = request.query_params.get('year')
        qs    = self.get_queryset()

        if month and year:
            qs = qs.filter(date__month=month, date__year=year)

        total_expense = qs.filter(type='expense').aggregate(t=Sum('amount'))['t'] or 0
        total_income  = qs.filter(type='income').aggregate(t=Sum('amount'))['t'] or 0

        return Response({
            'total_expense': float(total_expense),
            'total_income':  float(total_income),
            'balance':       float(total_income) - float(total_expense),
            'month':         month,
            'year':          year,
        })

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Category breakdown for chart"""
        month = request.query_params.get('month')
        year  = request.query_params.get('year')
        qs    = self.get_queryset().filter(type='expense')

        if month and year:
            qs = qs.filter(date__month=month, date__year=year)

        data = (
            qs.values('category__name', 'category__color', 'category__icon')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')
        )
        return Response(list(data))


class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = CategorySerializer

    def get_queryset(self):
        # user's own categories + default system categories
        return Category.objects.filter(
            Q(user=self.request.user) | Q(is_default=True)
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BudgetViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = BudgetSerializer

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user).select_related('category')
