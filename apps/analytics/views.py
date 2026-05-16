from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from django.db.models.functions import TruncDay, TruncMonth
from apps.expenses.models import Expense, Category
from datetime import date, datetime, timedelta
import calendar


class MonthlyTrendView(APIView):
    """Last 6 months income vs expense - for line/bar chart"""
    permission_classes = [IsAuthenticated]
    def get(self, request):
        today  = date.today()
        months = []
        for i in range(5, -1, -1):
            month = today.month - i
            year  = today.year
            while month <= 0:
                month += 12
                year  -= 1
            qs = Expense.objects.filter(
                user=request.user,
                date__month=month,
                date__year=year,
            )
            expense = qs.filter(type='expense').aggregate(t=Sum('amount'))['t'] or 0
            income  = qs.filter(type='income').aggregate(t=Sum('amount'))['t'] or 0
            months.append({
                'month':   month,
                'year':    year,
                'label':   calendar.month_abbr[month],
                'expense': float(expense),
                'income':  float(income),
                'balance': float(income) - float(expense),
            })
        return Response(months)


class DailyBreakdownView(APIView):
    """Daily expenses for current month - for calendar/bar chart"""
    permission_classes = [IsAuthenticated]
    def get(self, request):
        month = request.query_params.get('month', date.today().month)
        year  = request.query_params.get('year', date.today().year)
        data = (
            Expense.objects.filter(
                user=request.user,
                date__month=month,
                date__year=year,
                type='expense',
            )
            .annotate(day=TruncDay('date'))
            .values('day')
            .annotate(total=Sum('amount'))
            .order_by('day')
        )
        return Response([
            {'date': str(d['day'].date()), 'total': float(d['total'])}
            for d in data
        ])


class ReportView(APIView):
    """Filtered report for PDF generation"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            today = date.today()
            preset = request.query_params.get('preset', 'this_month')
            start_str = request.query_params.get('start_date')
            end_str = request.query_params.get('end_date')
            txn_type = request.query_params.get('type', 'all')

            if start_str and end_str:
                start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
            elif preset == 'this_month':
                start_date = today.replace(day=1)
                end_date = today
            elif preset == 'last_month':
                first_this = today.replace(day=1)
                last_month_end = first_this - timedelta(days=1)
                start_date = last_month_end.replace(day=1)
                end_date = last_month_end
            elif preset == 'last_7_days':
                start_date = today - timedelta(days=6)
                end_date = today
            elif preset == 'last_30_days':
                start_date = today - timedelta(days=29)
                end_date = today
            elif preset == 'all_time':
                start_date = date(2000, 1, 1)
                end_date = today
            else:
                start_date = today.replace(day=1)
                end_date = today

            qs = Expense.objects.filter(
                user=request.user,
                date__gte=start_date,
                date__lte=end_date,
            )

            if txn_type in ['income', 'expense']:
                qs = qs.filter(type=txn_type)

            qs = qs.select_related('category').order_by('-date', '-created_at')

            total_income = qs.filter(type='income').aggregate(t=Sum('amount'))['t'] or 0
            total_expense = qs.filter(type='expense').aggregate(t=Sum('amount'))['t'] or 0
            balance = float(total_income) - float(total_expense)
            count = qs.count()

            category_breakdown = []
            cat_data = (
                qs.filter(type='expense')
                .values('category__name')
                .annotate(total=Sum('amount'))
                .order_by('-total')
            )
            for c in cat_data:
                category_breakdown.append({
                    'name': c['category__name'] or 'Uncategorized',
                    'total': float(c['total'] or 0),
                })

            transactions = []
            for e in qs[:500]:
                transactions.append({
                    'id': str(e.id),
                    'date': str(e.date),
                    'type': e.type,
                    'amount': float(e.amount),
                    'note': e.note or '',
                    'category': e.category.name if e.category else 'Uncategorized',
                })

            return Response({
                'success': True,
                'period': {
                    'preset': preset,
                    'start_date': str(start_date),
                    'end_date': str(end_date),
                },
                'summary': {
                    'total_income': float(total_income),
                    'total_expense': float(total_expense),
                    'balance': balance,
                    'transaction_count': count,
                },
                'category_breakdown': category_breakdown,
                'transactions': transactions,
            })
        except Exception as e:
            return Response({'error': str(e)}, status=400)