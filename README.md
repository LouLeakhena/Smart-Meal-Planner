# 🍽 Smart Meal Planner

A Flask web application that calculates personalized daily calorie targets and builds optimized meal plans using a knapsack algorithm to maximize protein within a given calorie budget.

---

##  Features

- **Calorie Calculator** — Uses the Mifflin-St Jeor formula based on weight, height, age, gender, activity level, and goal
- **Meal Optimizer** — Knapsack algorithm selects the best food combination to maximize protein within your calorie limit
- **Progress Tracker** — Stores up to 7 days of meal history in the session
- **Pie Chart Visualization** — Visual breakdown of your last optimized meal plan that persists across server restarts
- **Responsive UI** — Mobile-friendly design with a hamburger menu

---

## 📁 Project Structure

```
SMART MEAL PLANNER
├──website
|    ├── __init__.py          # App factory — creates and configures the Flask app
|    ├── views.py             # Main route handlers (home, optimizer)
|    ├── auth.py              # Auth blueprint (login/register pages)
|    ├── models.py            # Core logic: User, Food, Tracker, Optimizer classes
|    ├── app_data.json        # Persisted food library + last meal plan (auto-generated at runtime)
|    │
|    ├── templates/
|    │   ├── base.html        # Shared layout with navbar, flash messages, fonts
|    │   ├── dashboard.html   # Home page: calorie calculator + pie chart
|    │   ├── optimizer.html   # Meal optimizer: food library + knapsack results
|    │   ├── login.html       # Login form
|    │   └── register.html    # Registration form
|    │
|    └── static/
|        └── style.css        # All styles: layout, cards, tables, responsive rules
├──main.py                    # Run the web 

```
---

## 🚀 How to Run

### 1. Clone the repository

```bash
git clone https://github.com/your-username/meal-planner.git
cd meal-planner
```

### 2. Create and activate a virtual environment

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install flask pandas
```

### 4. Run the app

Simply run:

```bash
python main.py
```
Open your browser at **http://127.0.0.1:5000**

---

## Code Overview

### `__init__.py` — App Factory

Creates the Flask app, registers the `views` and `auth` blueprints.

```python
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "mealplanner-dev-secret"
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")

    return app
```

---

### `models.py` — Core Logic

Contains four classes that handle all business logic.

**`User`** — Stores user profile data and calculates BMR and daily calorie target.

```python
class User:
    def calculate_bmr(self):
        """Mifflin-St Jeor formula."""
        base = 10 * self.weight + 6.25 * self.height - 5 * self.age
        return base + 5 if self.gender == 'male' else base - 161

    def calculate_daily_calories(self):
        bmr = self.calculate_bmr()
        maintenance = bmr * ACTIVITY_MAP[self.activity]
        daily_adjust = (7700 * self.rate) / 7
        # ... applies goal adjustment and enforces MIN_CALORIES = 1000
```

**`Food`** — Represents a food item with name, calories, protein, and meal type.

```python
class Food:
    def __init__(self, name, calories, protein, meal_type):
        self.name = name.strip()
        self.calories = int(calories)
        self.protein = int(protein)
        self.meal_type = meal_type
```

**`Tracker`** — Maintains a rolling 7-day log of daily calorie and protein totals.

```python
class Tracker:
    def add_day(self, cal, pro):
        if len(self.data) >= 7:
            self.data.pop(0)
        self.data.append({'calories': cal, 'protein': pro})
```

**`Optimizer`** — Implements the 0/1 knapsack algorithm to maximize protein within a calorie budget.

```python
class Optimizer:
    def knapsack(self, foods, max_cal):
        # dp[i][w] = max protein using first i foods with calorie budget w
        dp = [[0] * (cap + 1) for _ in range(n + 1)]
        for i in range(1, n + 1):
            for w in range(cap + 1):
                dp[i][w] = dp[i - 1][w]
                if food_cal <= w:
                    with_food = dp[i - 1][w - food_cal] + food_pro
                    if with_food > dp[i][w]:
                        dp[i][w] = with_food
        # ... traces back selected foods
```

---

### `views.py` — Route Handlers

Handles `GET`/`POST` for the two main pages. Both the food library and the last optimized result are persisted to a single `app_data.json` file so all data survives server restarts.

| Route | Method | Description |
|---|---|---|
| `/` | GET, POST | Calorie calculator + last meal plan chart |
| `/optimizer` | GET, POST | Food library management + knapsack optimizer |

Key session keys used:
- `foods` — list of food dicts in the user's library (backed by `app_data.json`)
- `tracker_data` — rolling 7-day history
- `last_optimized` — most recent knapsack result (backed by `app_data.json`)

`app_data.json` structure:
```json
{
  "foods": [...],
  "last_optimized": [...]
}
```

The optimizer page handles four POST actions:

```python
@views.route('/optimizer', methods=['GET', 'POST'])
def optimizer_page():
    if 'food' in request.form:
        # Add a new food to the library
    elif 'delete_index' in request.form:
        # Remove a single food by its index
    elif 'clear' in request.form:
        # Wipe the entire food library and last optimized result
    elif 'optimize' in request.form:
        # Run knapsack, save result, log to tracker
```

---

### `auth.py` — Authentication Blueprint

Currently renders login and register pages. Backend auth logic (password hashing, database) can be added here.

```python
auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/register')
def register():
    return render_template('register.html')
```

---

### `templates/base.html` — Base Layout

Shared shell for all pages. Includes Google Fonts (`DM Sans`, `DM Serif Display`), sticky navbar, mobile hamburger menu, and Jinja2 flash message rendering.

---

### `templates/dashboard.html` — Home Page

- Calorie calculator form with dynamic rate options (JavaScript updates dropdown based on selected goal)
- Pie chart rendered with **Chart.js** from the last optimized meal plan
- CTA button linking to the optimizer

---

### `templates/optimizer.html` — Optimizer Page

- Add food form (name, calories, protein, meal type)
- Food library table with a **✕ button on each row** to remove individual items, and a **Clear All** button to wipe the entire list
- Optimizer form with a calorie budget input
- Results table showing the optimal food combination with totals

---

### `static/style.css` — Stylesheet

Uses CSS custom properties for theming. Key layout classes:

| Class | Purpose |
|---|---|
| `.card` | White rounded content block with shadow |
| `.grid-3` / `.grid-4` | Responsive CSS grid layouts |
| `.food-table` | Styled data table |
| `.tag` | Pill badge for meal type labels |
| `.btn-delete` | Small outlined red button for per-row deletion |
| `.chart-layout` | Side-by-side pie chart + table |
| `.optimizer-section` | Centered CTA block |

Responsive breakpoints: **768px** (collapses grids, shows hamburger) and **480px** (single-column grid-4).

---

## Configuration

| Config Key | Default | Description |
|---|---|---|
| `SECRET_KEY` | `mealplanner-dev-secret` | Change to a random string in production |
| `SESSION_COOKIE_SAMESITE` | `Lax` | CSRF protection setting |
| `MIN_CALORIES` | `1000` | Floor for calculated daily calorie target |

---

## Dependencies

| Package | Purpose |
|---|---|
| `flask` | Web framework, routing, sessions, templating |
| `pandas` | DataFrame support in the `Tracker` class |

> Chart.js is loaded from CDN in `dashboard.html` — no installation needed.
