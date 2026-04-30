from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.expenses.models import Expense, Category
from django.conf import settings
from groq import Groq
import json
from datetime import date


class AIExpenseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = request.data.get("text", "")
        if not text:
            return Response({"error": "Text is required"}, status=400)

        client = Groq(api_key=settings.GROQ_API_KEY)

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": f"Extract expense details from: {text}\nReturn ONLY JSON: {{\"type\": \"expense\" or \"income\", \"amount\": number, \"note\": \"description\", \"category_hint\": \"food/transport/shopping/health/education/bills/rent/salary/other\"}}"
                }
            ],
            max_tokens=200,
        )

        try:
            result_text = completion.choices[0].message.content
            import re
            json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                return Response({"error": "Could not parse AI response"}, status=400)

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
