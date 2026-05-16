from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from apps.users.views import RegisterView, LoginView, ProfileView, LogoutView
from apps.expenses.views import ExpenseViewSet, CategoryViewSet, BudgetViewSet
from apps.analytics.views import MonthlyTrendView, DailyBreakdownView, ReportView
from apps.ai_engine.views import AIExpenseView, ReceiptScanView, BudgetPredictionView

router = DefaultRouter()
router.register(r"expenses",   ExpenseViewSet,  basename="expense")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"budgets",    BudgetViewSet,   basename="budget")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/register/",      RegisterView.as_view(),     name="register"),
    path("api/auth/login/",         LoginView.as_view(),        name="login"),
    path("api/auth/logout/",        LogoutView.as_view(),       name="logout"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/profile/",       ProfileView.as_view(),      name="profile"),
    path("api/", include(router.urls)),
    path("api/analytics/monthly-trend/",   MonthlyTrendView.as_view(),   name="monthly-trend"),
    path("api/analytics/daily-breakdown/", DailyBreakdownView.as_view(), name="daily-breakdown"),
    path("api/analytics/report/",          ReportView.as_view(),         name="report"),
    path("api/ai/add-expense/",            AIExpenseView.as_view(),       name="ai-add-expense"),
    path("api/ai/scan-receipt/",           ReceiptScanView.as_view(),     name="ai-scan-receipt"),
    path("api/ai/budget-prediction/",      BudgetPredictionView.as_view(), name="ai-budget-prediction"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)