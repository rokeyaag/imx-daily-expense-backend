from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.expenses.models import Expense, Category
from django.conf import settings
from groq import Groq
import json
import base64
from datetime import date
from django.db.models import Sum

class AIExpenseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = request.data.get("text", "")
        action = request.data.get("action", "parse")

        if action == "confirm":
            return self.confirm_expense(request)
        elif action == "chat":
            return self.ai_chat(request, text)

        if not text:
            return Response({"error": "Text is required"}, status=400)

        client = Groq(api_key=settings.GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a financial assistant. Extract expense/income details from text. Always respond with valid JSON only."},
                {"role": "user", "content": f"""Extract expense details from this text: "{text}"
Return ONLY this JSON format:
{{
  "type": "expense" or "income",
  "amount": number,
  "note": "short description in English",
  "category_hint": "food" or "transport" or "shopping" or "health" or "education" or "bills" or "rent" or "salary" or "games" or "travel" or "other",
  "confidence": "high" or "medium" or "low"
}}"""}
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

            hint = result.get("category_hint", "").lower()
            all_cats = list(Category.objects.filter(user=request.user))
            category = None
            category_id = None

            for cat in all_cats:
                if hint in cat.name.lower() or cat.name.lower() in hint:
                    category = cat
                    category_id = str(cat.id)
                    break

            if not category and all_cats:
                name_map = {
                    "food": ["food", "bazar", "lunch", "dinner", "breakfast"],
                    "transport": ["transport", "rickshaw", "bus", "uber"],
                    "shopping": ["shopping", "clothes"],
                    "health": ["health", "medicine", "doctor"],
                    "bills": ["bills", "electricity", "water", "internet"],
                    "rent": ["rent"],
                    "salary": ["salary", "income"],
                }
                for cat in all_cats:
                    cat_lower = cat.name.lower()
                    for key, keywords in name_map.items():
                        if key == hint or any(k in cat_lower for k in keywords):
                            category = cat
                            category_id = str(cat.id)
                            break
                    if category:
                        break

            return Response({
                "success": True,
                "action": "preview",
                "parsed": {
                    "type": result.get("type", "expense"),
                    "amount": result.get("amount", 0),
                    "note": result.get("note", text),
                    "category_hint": hint,
                    "category_id": category_id,
                    "category_name": category.name if category else None,
                    "confidence": result.get("confidence", "medium"),
                },
            })

        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def confirm_expense(self, request):
        try:
            parsed = request.data.get("parsed", {})
            category_id = parsed.get("category_id")
            category = None
            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                except:
                    pass

            expense = Expense.objects.create(
                user=request.user,
                type=parsed.get("type", "expense"),
                amount=parsed.get("amount", 0),
                note=parsed.get("note", ""),
                date=date.today(),
                category=category,
            )

            return Response({
                "success": True,
                "message": f"Added: {parsed.get('note')} - Tk {parsed.get('amount')}",
                "expense_id": str(expense.id),
            })
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def ai_chat(self, request, text):
        try:
            user = request.user
            today = date.today()
            month_start = today.replace(day=1)

            expenses = Expense.objects.filter(user=user, date__gte=month_start)
            total_income = expenses.filter(type="income").aggregate(Sum("amount"))["amount__sum"] or 0
            total_expense = expenses.filter(type="expense").aggregate(Sum("amount"))["amount__sum"] or 0
            balance = total_income - total_expense

            category_breakdown = []
            for cat in Category.objects.filter(user=user):
                cat_total = expenses.filter(type="expense", category=cat).aggregate(Sum("amount"))["amount__sum"] or 0
                if cat_total > 0:
                    category_breakdown.append(f"{cat.name}: Tk {cat_total}")

            recent = expenses.order_by("-date")[:5]
            recent_list = [f"{e.note} - Tk {e.amount} ({e.type})" for e in recent]

            context = f"""
User Financial Summary for {today.strftime("%B %Y")}:
- Total Income: Tk {total_income}
- Total Expense: Tk {total_expense}
- Current Balance: Tk {balance}
- Category Breakdown: {", ".join(category_breakdown) if category_breakdown else "No expenses yet"}
- Recent Transactions: {", ".join(recent_list) if recent_list else "No transactions yet"}
"""

            client = Groq(api_key=settings.GROQ_API_KEY)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"""You are a helpful personal finance assistant for IMX Daily Expense app.
You have access to the user financial data. Answer questions about their finances, give advice, and help them understand their spending.
Keep responses concise, friendly, and in the same language the user writes in (Bengali or English).
{context}"""},
                    {"role": "user", "content": text}
                ],
                max_tokens=500,
            )

            reply = completion.choices[0].message.content
            return Response({"success": True, "reply": reply})

        except Exception as e:
            return Response({"error": str(e)}, status=400)


class ReceiptScanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        image_base64 = request.data.get("image", "")
        if not image_base64:
            return Response({"error": "Image is required"}, status=400)

        try:
            client = Groq(api_key=settings.GROQ_API_KEY)
            completion = client.chat.completions.create(
                model="llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": """Look at this receipt/bill image and extract the expense details.
Return ONLY this JSON format:
{
  "type": "expense",
  "amount": total amount as number,
  "note": "short description of what was purchased",
  "category_hint": "food" or "transport" or "shopping" or "health" or "education" or "bills" or "rent" or "other",
  "confidence": "high" or "medium" or "low"
}
If you cannot read the receipt clearly, return {"error": "Cannot read receipt"}"""
                            }
                        ]
                    }
                ],
                max_tokens=300,
            )

            result_text = completion.choices[0].message.content
            import re
            json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
            if not json_match:
                return Response({"error": "Cannot read receipt"}, status=400)

            result = json.loads(json_match.group())
            if "error" in result:
                return Response({"error": result["error"]}, status=400)

            hint = result.get("category_hint", "").lower()
            all_cats = list(Category.objects.filter(user=request.user))
            category = None
            category_id = None

            for cat in all_cats:
                if hint in cat.name.lower() or cat.name.lower() in hint:
                    category = cat
                    category_id = str(cat.id)
                    break

            return Response({
                "success": True,
                "parsed": {
                    "type": result.get("type", "expense"),
                    "amount": result.get("amount", 0),
                    "note": result.get("note", "Receipt"),
                    "category_hint": hint,
                    "category_id": category_id,
                    "category_name": category.name if category else None,
                    "confidence": result.get("confidence", "medium"),
                }
            })

        except Exception as e:
            return Response({"error": str(e)}, status=400)


class BudgetPredictionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            today = date.today()
            month_start = today.replace(day=1)
            days_passed = today.day
            import calendar
            days_in_month = calendar.monthrange(today.year, today.month)[1]
            days_remaining = days_in_month - days_passed

            expenses = Expense.objects.filter(user=user, date__gte=month_start, type="expense")
            total_expense = expenses.aggregate(Sum("amount"))["amount__sum"] or 0
            total_income = Expense.objects.filter(user=user, date__gte=month_start, type="income").aggregate(Sum("amount"))["amount__sum"] or 0

            daily_avg = float(total_expense) / days_passed if days_passed > 0 else 0
            predicted_total = daily_avg * days_in_month

            category_breakdown = []
            for cat in Category.objects.filter(user=user):
                cat_total = expenses.filter(category=cat).aggregate(Sum("amount"))["amount__sum"] or 0
                if cat_total > 0:
                    category_breakdown.append({"name": cat.name, "total": float(cat_total)})

            last_month_start = (month_start - __import__("datetime").timedelta(days=1)).replace(day=1)
            last_month_expense = Expense.objects.filter(user=user, date__gte=last_month_start, date__lt=month_start, type="expense").aggregate(Sum("amount"))["amount__sum"] or 0

            client = Groq(api_key=settings.GROQ_API_KEY)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a personal finance advisor. Give concise, actionable advice in 3-4 sentences."},
                    {"role": "user", "content": f"""
Based on this financial data:
- Days passed: {days_passed}/{days_in_month}
- Current expense: Tk {total_expense}
- Daily average: Tk {daily_avg:.0f}
- Predicted month total: Tk {predicted_total:.0f}
- Current income: Tk {total_income}
- Last month expense: Tk {last_month_expense}
- Top categories: {", ".join([f"{c['name']}: Tk {c['total']}" for c in category_breakdown[:3]])}

Give a brief financial analysis and 2-3 saving tips. Be friendly and specific.
"""}
                ],
                max_tokens=300,
            )

            advice = completion.choices[0].message.content

            return Response({
                "success": True,
                "prediction": {
                    "days_passed": days_passed,
                    "days_remaining": days_remaining,
                    "days_in_month": days_in_month,
                    "current_expense": float(total_expense),
                    "current_income": float(total_income),
                    "daily_average": round(daily_avg, 2),
                    "predicted_total": round(predicted_total, 2),
                    "last_month_expense": float(last_month_expense),
                    "category_breakdown": category_breakdown,
                    "ai_advice": advice,
                }
            })

        except Exception as e:
            return Response({"error": str(e)}, status=400)

