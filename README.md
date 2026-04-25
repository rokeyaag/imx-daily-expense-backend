# Daily Expense App — Django Backend

## Setup

```bash
# 1. Virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 2. Install packages
pip install -r requirements.txt

# 3. Environment variables
cp .env.example .env
# .env ফাইলে তোমার Railway DATABASE_URL দাও

# 4. Migrations
python manage.py makemigrations users
python manage.py makemigrations expenses
python manage.py migrate

# 5. Default categories seed করো
python manage.py seed_categories

# 6. Superuser বানাও
python manage.py createsuperuser

# 7. Run server
python manage.py runserver
```

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | /api/auth/register/ | নতুন account |
| POST | /api/auth/login/ | Login → tokens |
| POST | /api/auth/token/refresh/ | Token refresh |
| GET/PUT | /api/auth/profile/ | Profile |
| GET/POST | /api/expenses/ | Expense list/create |
| GET/PUT/DELETE | /api/expenses/{id}/ | Single expense |
| GET | /api/expenses/summary/ | Monthly summary |
| GET | /api/expenses/by_category/ | Category chart data |
| GET/POST | /api/categories/ | Categories |
| GET/POST | /api/budgets/ | Budgets |
| GET | /api/analytics/monthly-trend/ | 6 months trend |
| GET | /api/analytics/daily-breakdown/ | Daily chart |

## Railway Deploy

```bash
railway up
```
