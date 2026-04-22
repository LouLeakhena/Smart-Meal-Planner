import json
import os

from flask import Blueprint, render_template, request, session, flash
from .models import User, Food, Tracker, Optimizer

_OPTIMIZED_FILE = os.path.join(os.path.dirname(__file__), 'last_optimized.json')
_FOODS_FILE     = os.path.join(os.path.dirname(__file__), 'last_foods.json')


def _load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f)


views = Blueprint('views', __name__)
optimizer_engine = Optimizer()


def _get_foods():
    """Load foods from session; fall back to disk so they survive restarts."""
    raw = session.get('foods')
    if raw is None:
        raw = _load_json(_FOODS_FILE)
        session['foods'] = raw          # re-sync session from disk
    return [Food(i['name'], i['calories'], i['protein'], i['meal_type']) for i in raw]


def _save_foods(foods):
    """Persist food list to both session and disk."""
    data = [
        {'name': f.name, 'calories': f.calories,
         'protein': f.protein, 'meal_type': f.meal_type}
        for f in foods
    ]
    session['foods'] = data
    session.modified = True
    _save_json(_FOODS_FILE, data)


def _get_tracker():
    tracker = Tracker()
    tracker.data = session.get('tracker_data', [])
    return tracker


def _save_tracker(tracker):
    session['tracker_data'] = tracker.data
    session.modified = True


def _build_chart():
    """Returns chart data; survives server restarts via disk."""
    last = session.get('last_optimized') or _load_json(_OPTIMIZED_FILE)
    if not last:
        return {'foods': []}
    session['last_optimized'] = last   # re-sync if loaded from disk
    return {'foods': last}


# ============
# HOME PAGE
# ============

@views.route('/', methods=['GET', 'POST'])
def home():
    calories = None
    chart = _build_chart()

    if request.method == 'POST' and 'calculate' in request.form:
        try:
            user = User(
                request.form['weight'],
                request.form['height'],
                request.form['age'],
                request.form['gender'],
                request.form['activity'],
                request.form['goal'],
                request.form['rate']
            )
            errors = user.validate()
            if errors:
                for e in errors:
                    flash(e, 'error')
            else:
                calories = user.calculate_daily_calories()
        except (ValueError, KeyError):
            flash("Please fill in all fields with valid numbers.", 'error')

    return render_template('dashboard.html', calories=calories, chart=chart)


# ===============
# OPTIMIZER PAGE
# ===============

@views.route('/optimizer', methods=['GET', 'POST'])
def optimizer_page():
    foods = _get_foods()
    optimized_raw = session.get('last_optimized', [])
    optimized = [Food(f['name'], f['calories'], f['protein'], f['meal_type'])
                 for f in optimized_raw]

    if request.method == 'POST':

        # ── Add food
        if 'food' in request.form:
            try:
                f = Food(
                    request.form['name'],
                    request.form['cal'],
                    request.form['protein'],
                    request.form['meal']
                )
                errors = f.validate()
                if errors:
                    for e in errors:
                        flash(e, 'error')
                else:
                    foods.append(f)
                    _save_foods(foods)
                    flash(f'"{f.name}" added successfully.', 'success')
            except (ValueError, KeyError):
                flash("Please fill in all food fields with valid values.", 'error')

        # ── Delete one food by index 
        elif 'delete_index' in request.form:
            try:
                idx = int(request.form['delete_index'])
                if 0 <= idx < len(foods):
                    removed = foods.pop(idx)
                    _save_foods(foods)
                    flash(f'"{removed.name}" removed.', 'success')
                else:
                    flash("Invalid item index.", 'error')
            except (ValueError, KeyError):
                flash("Could not delete that item.", 'error')

        # ── Clear all 
        elif 'clear' in request.form:
            session.pop('foods', None)
            session.pop('last_optimized', None)
            _save_json(_FOODS_FILE, [])
            _save_json(_OPTIMIZED_FILE, [])
            flash("Food list cleared.", 'success')
            foods = []
            optimized = []

        # ── Run optimizer
        elif 'optimize' in request.form:
            try:
                max_cal = int(request.form['max_cal'])
                if max_cal <= 0:
                    flash("Maximum calories must be a positive number.", 'error')
                elif not foods:
                    flash("Add some foods first before optimizing.", 'error')
                else:
                    optimized = optimizer_engine.knapsack(foods, max_cal)
                    if not optimized:
                        flash("No foods fit within that calorie budget. Try a higher limit.", 'warning')
                    else:
                        data = [
                            {'name': f.name, 'calories': f.calories,
                             'protein': f.protein, 'meal_type': f.meal_type}
                            for f in optimized
                        ]
                        session['last_optimized'] = data
                        _save_json(_OPTIMIZED_FILE, data)
                        tracker = _get_tracker()
                        tracker.add_day(
                            sum(f.calories for f in optimized),
                            sum(f.protein for f in optimized)
                        )
                        _save_tracker(tracker)
                        flash(f"Optimal plan found: {len(optimized)} food(s) selected.", 'success')
            except (ValueError, KeyError):
                flash("Please enter a valid number for the calorie limit.", 'error')

    return render_template('optimizer.html', foods=foods, optimized=optimized)