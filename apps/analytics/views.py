from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from django.db.models.functions import TruncDay, TruncMonth
from apps.expenses.models import Expense
from datetime import date
import calendar


class MonthlyTrendView(APIView):
    """Last 6 months income vs expense — for line/bar chart"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today  = date.today()
        months = []

        for i in range(5, -1, -1):
            # go back i months from today
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
    """Daily expenses for current month — for calendar/bar chart"""
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
