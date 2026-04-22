import pandas as pd

ACTIVITY_MAP = {
    'sedentary': 1.2,
    'light': 1.375,
    'moderate': 1.55,
    'active': 1.725
}

GOAL_OPTIONS = {'lose', 'maintain', 'gain'}
ACTIVITY_OPTIONS = set(ACTIVITY_MAP.keys())
MIN_CALORIES = 1000  


class User:
    def __init__(self, weight, height, age, gender, activity, goal, rate):
        self.weight = float(weight)
        self.height = float(height)
        self.age = int(age)
        self.gender = gender.lower()
        self.activity = activity.lower()
        self.goal = goal.lower()
        self.rate = float(rate)

    def validate(self):
        """Returns a list of error strings. Empty list = valid."""
        errors = []
        if self.weight <= 0 or self.weight > 500:
            errors.append("Weight must be between 1 and 500 kg.")
        if self.height <= 0 or self.height > 300:
            errors.append("Height must be between 1 and 300 cm.")
        if self.age < 5 or self.age > 120:
            errors.append("Age must be between 5 and 120.")
        if self.gender not in ('male', 'female'):
            errors.append("Gender must be male or female.")
        if self.activity not in ACTIVITY_OPTIONS:
            errors.append(f"Activity must be one of: {', '.join(ACTIVITY_OPTIONS)}.")
        if self.goal not in GOAL_OPTIONS:
            errors.append(f"Goal must be one of: {', '.join(GOAL_OPTIONS)}.")
        allowed_rates = {
            'lose':     {0.25, 0.5, 1.0},
            'maintain': {0.0},
            'gain':     {0.25, 0.5},
        }
        if self.goal in allowed_rates and self.rate not in allowed_rates[self.goal]:
            errors.append(f"Invalid rate for goal '{self.goal}'.")
        return errors

    def calculate_bmr(self):
        """Mifflin-St Jeor formula."""
        base = 10 * self.weight + 6.25 * self.height - 5 * self.age
        return base + 5 if self.gender == 'male' else base - 161

    def calculate_daily_calories(self):
        bmr = self.calculate_bmr()
        maintenance = bmr * ACTIVITY_MAP[self.activity]
        # 7700 kcal ≈ 1 kg of body weight
        daily_adjust = (7700 * self.rate) / 7

        if self.goal == 'lose':
            result = maintenance - daily_adjust
        elif self.goal == 'gain':
            result = maintenance + daily_adjust
        else:
            result = maintenance

        # Never return an unsafe or negative calorie target
        return max(int(result), MIN_CALORIES)


class Food:
    def __init__(self, name, calories, protein, meal_type):
        self.name = name.strip()
        self.calories = int(calories)
        self.protein = int(protein)
        self.meal_type = meal_type

    def validate(self):
        errors = []
        if not self.name:
            errors.append("Food name cannot be empty.")
        if self.calories <= 0 or self.calories > 5000:
            errors.append("Calories must be between 1 and 5000.")
        if self.protein < 0 or self.protein > 1000:
            errors.append("Protein must be between 0 and 1000 g.")
        return errors


class Tracker:
    def __init__(self):
        self.data = []

    def add_day(self, cal, pro):
        if len(self.data) >= 7:
            self.data.pop(0)
        self.data.append({'calories': cal, 'protein': pro})

    def to_df(self):
        if not self.data:
            # Return a properly structured empty DataFrame so callers don't crash
            return pd.DataFrame(columns=['calories', 'protein'])
        return pd.DataFrame(self.data)


class Optimizer:
    def knapsack(self, foods, max_cal):
        if not foods or max_cal <= 0:
            return []

        n = len(foods)
        cap = int(max_cal)
        # dp[i][w] = max protein using first i foods with calorie budget w
        dp = [[0] * (cap + 1) for _ in range(n + 1)]

        for i in range(1, n + 1):
            food_cal = int(foods[i - 1].calories)
            food_pro = foods[i - 1].protein
            for w in range(cap + 1):
                # Option 1: skip this food
                dp[i][w] = dp[i - 1][w]
                # Option 2: include this food (only if it fits)
                if food_cal <= w:
                    with_food = dp[i - 1][w - food_cal] + food_pro
                    if with_food > dp[i][w]:
                        dp[i][w] = with_food

        # Trace back which foods were selected
        selected = []
        w = cap
        for i in range(n, 0, -1):
            if dp[i][w] != dp[i - 1][w]:
                selected.append(foods[i - 1])
                w -= int(foods[i - 1].calories)

        return selected