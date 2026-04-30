from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.expenses.models import Expense, Category
from django.conf import settings
import anthropic
import json
from datetime import date


class AIExpenseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = request.data.get("text", "")
        if not text:
            return Response({"error": "Text is required"}, status=400)

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": f"Extract expense details from: {text}\nReturn ONLY JSON: {{\"type\": \"expense\" or \"income\", \"amount\": number, \"note\": \"description\", \"category_hint\": \"food/transport/shopping/health/education/bills/rent/salary/other\"}}"
                }
            ]
        )

        try:
            result = json.loads(message.content[0].text)
            category = None
            hint = result.get("category_hint", "")
            all_cats = list(Category.objects.filter(user=request.user)) + list(Category.objects.filter(is_default=True))
            for cat in all_cats:
                if hint in cat.icon.lower():
                    category = cat
                    break
            expense = Expense.objects.create(
                user=request.user,
                type=result.get("type", "expense"),
                amount=result.get("amount", 0),
                note=result.get("note", ""),
                date=date.today(),
                category=category,
            )
            return Response({
                "success": True,
                "message": f"Added: {result.get('note')} - Tk {result.get('amount')}",
                "expense_id": str(expense.id),
                "parsed": result,
            })
        except Exception as e:
            return Response({"error": str(e)}, status=400)
