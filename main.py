import telebot
from telebot import types
import sqlite3
import json
from datetime import datetime
 
TOKEN = "8844022654:AAFZt7DXdHWoORHlGrFSi0rMyX7BUYBzUR8"
bot = telebot.TeleBot(TOKEN)
 
# ─────────────────────────────────────────
#  БАЗА КАЛОРИЙНОСТИ
# ─────────────────────────────────────────
 
KCAL_PER_100G = {
    "куриная грудка": 110, "куриное бедро": 185, "индейка": 115,
    "говядина": 187, "яйцо": 155,
    "гречка": 313, "бурый рис": 337, "булгур": 342, "овсянка": 352, "макароны": 350,
    "болгарский перец": 27, "морковь": 35, "шпинат": 23,
    "стручковая фасоль": 31, "брокколи": 34, "огурец": 15, "помидор": 18,
    "миндаль": 576, "грецкий орех": 654, "кешью": 553, "тыквенные семечки": 559,
    "яблоко": 52, "груша": 57, "ягоды": 45,
}
 
FOOD_GROUPS = {
    "белок":    ["куриная грудка", "куриное бедро", "индейка", "говядина"],
    "углеводы": ["гречка", "бурый рис", "булгур", "овсянка", "макароны"],
    "овощи":    ["болгарский перец", "морковь", "шпинат", "стручковая фасоль", "брокколи", "огурец", "помидор"],
    "орехи":    ["миндаль", "грецкий орех", "кешью", "тыквенные семечки"],
    "фрукты":   ["яблоко", "груша", "ягоды"],
}
 
# Продукты по приёмам пищи (что можно заменять в каждом)
MEAL_FOODS = {
    "🍳 Завтрак":  {"белок": ["яйцо"], "углеводы": ["овсянка"], "овощи": ["огурец", "помидор"]},
    "🍗 Обед":     {"белок": ["куриная грудка", "куриное бедро", "индейка", "говядина"],
                    "углеводы": ["гречка", "бурый рис", "булгур", "макароны"],
                    "овощи": ["болгарский перец", "морковь", "шпинат", "огурец"]},
    "🍎 Полдник":  {"белок": ["куриная грудка", "индейка"],
                    "орехи": ["миндаль", "грецкий орех", "кешью", "тыквенные семечки"],
                    "фрукты": ["яблоко", "груша", "ягоды"]},
    "🌙 Ужин":     {"белок": ["куриная грудка", "куриное бедро", "индейка", "говядина"],
                    "овощи": ["болгарский перец", "морковь", "шпинат", "стручковая фасоль", "брокколи"]},
}
 
DEFAULT_PORTIONS = {
    "куриная грудка": 230, "куриное бедро": 230, "индейка": 230, "говядина": 200,
    "яйцо": 186,  # 3 яйца
    "гречка": 65, "бурый рис": 65, "булгур": 65, "овсянка": 60, "макароны": 85,
    "болгарский перец": 200, "морковь": 200, "шпинат": 200,
    "стручковая фасоль": 200, "брокколи": 200, "огурец": 100, "помидор": 100,
    "миндаль": 20, "грецкий орех": 20, "кешью": 20, "тыквенные семечки": 20,
    "яблоко": 150, "груша": 150, "ягоды": 100,
}
 
def calc_equivalent(from_food, to_food, from_grams=None):
    if from_grams is None:
        from_grams = DEFAULT_PORTIONS.get(from_food, 100)
    kcal = KCAL_PER_100G[from_food] * from_grams / 100
    grams_to = round(kcal / KCAL_PER_100G[to_food] * 100)
    return grams_to, round(kcal)
 
def find_group(food):
    for g, items in FOOD_GROUPS.items():
        if food in items:
            return g
    return None
 
# ─────────────────────────────────────────
#  БАЗА ДАННЫХ
# ─────────────────────────────────────────
 
def init_db():
    conn = sqlite3.connect("weight_tracker.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS weights (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        weight_value REAL, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        step_count INTEGER, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_state (
        user_id INTEGER PRIMARY KEY, state TEXT DEFAULT "idle", extra TEXT DEFAULT "")''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_profile (
        user_id INTEGER PRIMARY KEY,
        current_weight REAL, target_weight REAL, height INTEGER, age INTEGER,
        gym_days INTEGER, workout_pref TEXT, deadline_weeks INTEGER,
        is_sick INTEGER DEFAULT 0, sick_since TEXT DEFAULT "")''')
    conn.commit(); conn.close()
 
def get_profile(user_id):
    conn = sqlite3.connect("weight_tracker.db")
    row = conn.execute("SELECT * FROM user_profile WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    if not row:
        return None
    keys = ["user_id","current_weight","target_weight","height","age",
            "gym_days","workout_pref","deadline_weeks","is_sick","sick_since"]
    return dict(zip(keys, row))
 
def save_profile(user_id, **kwargs):
    conn = sqlite3.connect("weight_tracker.db")
    existing = conn.execute("SELECT user_id FROM user_profile WHERE user_id=?", (user_id,)).fetchone()
    if existing:
        sets = ", ".join(f"{k}=?" for k in kwargs)
        conn.execute(f"UPDATE user_profile SET {sets} WHERE user_id=?",
                     (*kwargs.values(), user_id))
    else:
        kwargs["user_id"] = user_id
        cols = ", ".join(kwargs.keys())
        vals = ", ".join("?" * len(kwargs))
        conn.execute(f"INSERT INTO user_profile ({cols}) VALUES ({vals})", list(kwargs.values()))
    conn.commit(); conn.close()
 
def add_weight(user_id, weight):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("INSERT INTO weights (user_id, weight_value, date) VALUES (?,?,?)",
                 (user_id, weight, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit(); conn.close()
 
def get_weights(user_id):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute("SELECT weight_value, date FROM weights WHERE user_id=? ORDER BY id ASC", (user_id,)).fetchall()
    conn.close()
    return rows
 
def add_steps(user_id, steps):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("INSERT INTO steps (user_id, step_count, date) VALUES (?,?,?)",
                 (user_id, steps, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit(); conn.close()
 
def get_steps(user_id, limit=14):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute("SELECT step_count, date FROM steps WHERE user_id=? ORDER BY id DESC LIMIT ?",
                        (user_id, limit)).fetchall()
    conn.close()
    return list(reversed(rows))
 
def set_state(user_id, state, extra=""):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("INSERT INTO user_state (user_id, state, extra) VALUES (?,?,?) "
                 "ON CONFLICT(user_id) DO UPDATE SET state=excluded.state, extra=excluded.extra",
                 (user_id, state, extra))
    conn.commit(); conn.close()
 
def get_state(user_id):
    conn = sqlite3.connect("weight_tracker.db")
    row = conn.execute("SELECT state, extra FROM user_state WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return (row[0], row[1]) if row else ("idle", "")
 
# ─────────────────────────────────────────
#  РАСЧЁТ ПЛАНА ПО ПРОФИЛЮ
# ─────────────────────────────────────────
 
def calc_plan(profile):
    """Рассчитывает BMR, TDEE, дефицит и темп по данным профиля"""
    w  = profile["current_weight"]
    h  = profile["height"]
    a  = profile["age"] or 24
    gd = profile["gym_days"] or 3
 
    # BMR Миффлин
    bmr = 10 * w + 6.25 * h - 5 * a + 5
 
    # Множитель активности
    multipliers = {1: 1.30, 2: 1.35, 3: 1.45, 4: 1.50, 5: 1.55}
    mult = multipliers.get(gd, 1.45)
    tdee = round(bmr * mult)
 
    # Дефицит ~30% от TDEE но не более 1200 ккал
    deficit = min(round(tdee * 0.30), 1200)
    calories = tdee - deficit
 
    # Темп в неделю
    weekly = round(deficit * 7 / 7700, 2)
 
    # Срок до цели
    to_lose = w - profile["target_weight"]
    weeks_needed = round(to_lose / weekly) if weekly > 0 else 999
 
    return {
        "bmr": round(bmr),
        "tdee": tdee,
        "calories": calories,
        "deficit": deficit,
        "protein": round(w * 1.8),  # 1.8г на кг веса
        "weekly_loss": weekly,
        "weeks_needed": weeks_needed,
    }
 
def get_portions(calories, protein):
    """Подбирает порции под калораж"""
    # Масштабируем от базы 1950 ккал
    scale = calories / 1950
    return {
        "breast":  round(230 * scale),
        "carb":    round(65  * scale),
        "snack":   round(130 * scale),
        "dinner":  "300г тушёных овощей" if scale >= 1 else "только овощи без гарнира",
    }
 
def analyze_progress(weights_data):
    if len(weights_data) < 2:
        return None
    prev_w, prev_d = weights_data[-2]
    curr_w, curr_d = weights_data[-1]
    try:
        days = max((datetime.strptime(curr_d[:10], "%Y-%m-%d") -
                    datetime.strptime(prev_d[:10], "%Y-%m-%d")).days, 1)
    except Exception:
        days = 7
    delta = round(prev_w - curr_w, 2)
    weekly_rate = round(delta / days * 7, 2)
    if weekly_rate > 2.0:
        return {"status": "fast",    "rate": weekly_rate, "cal_change": +150,
                "advice": f"⚡ Темп слишком высокий ({weekly_rate} кг/нед). *Добавь 150 ккал* углеводами к обеду."}
    elif weekly_rate >= 0.7:
        return {"status": "good",    "rate": weekly_rate, "cal_change": 0,
                "advice": f"✅ Идеальный темп ({weekly_rate} кг/нед). Ничего не меняй!"}
    elif weekly_rate >= 0.1:
        return {"status": "slow",    "rate": weekly_rate, "cal_change": -150,
                "advice": f"🐢 Темп медленный ({weekly_rate} кг/нед). *Убери гарнир на ужин* (−150 ккал)."}
    elif weekly_rate >= -0.1:
        return {"status": "plateau", "rate": weekly_rate, "cal_change": -200,
                "advice": f"🪨 Плато. *Убери 200 ккал* и добавь одно кардио на этой неделе."}
    else:
        return {"status": "gain",    "rate": weekly_rate, "cal_change": -250,
                "advice": f"🚨 Вес растёт ({abs(weekly_rate)} кг/нед). *Убери полдник* (−250 ккал)."}
 
# ─────────────────────────────────────────
#  ТРЕНИРОВКИ ПО ПРЕДПОЧТЕНИЯМ
# ─────────────────────────────────────────
 
WORKOUTS = {
    "силовые": {
        "А": ("Грудь + Спина + Бицепс",
              "1. Жим гантелей на наклонной лавке — 4×12\n"
              "2. Тяга верхнего блока широким хватом — 4×12\n"
              "3. Горизонтальная тяга в блоке — 3×12\n"
              "4. Сгибание рук с гантелями — 3×12\n"
              "5. Планка на предплечьях — 3×45 сек"),
        "Б": ("Ноги + Плечи + Трицепс",
              "1. Жим ногами в тренажёре — 4×12\n"
              "2. Разгибание ног в тренажёре — 3×15\n"
              "3. Жим гантелей сидя на плечи — 4×12\n"
              "4. Отжимания в гравитроне — 3×10\n"
              "5. Подъём ног в висе — 4×12"),
        "В": ("Спина + Кор",
              "1. Гиперэкстензия без веса — 4×15\n"
              "2. Тяга нижнего блока узким хватом — 4×12\n"
              "3. Жим гантелей лёжа — 3×12\n"
              "4. Боковая планка — 3×30 сек каждая сторона\n"
              "5. Скручивания на пресс — 3×20"),
    },
    "кардио": {
        "К": ("Кардио 45 минут",
              "• Эллипс (пульс 120-135 уд/мин)\n"
              "• ИЛИ ходьба на дорожке: наклон 8%, скорость 5.5 км/ч\n"
              "• НЕ бегать при весе >100 кг"),
    },
}
 
def get_week_schedule(profile, gym_days):
    """
    Бот сам подбирает расписание:
    кардио_акцент: упор на кардио, 1 силовая для защиты мышц
    баланс: 2 кардио + 2-3 силовых
    """
    mode = auto_select_workout(profile) if profile else "кардио_акцент"
    gd   = min(gym_days, 5)
 
    if mode == "кардио_акцент":
        # Приоритет кардио, минимум силовых (1-2 раза)
        schedules = {
            1: {1: "К"},
            2: {1: "К", 4: "К"},
            3: {1: "К", 3: "К", 5: "А"},          # 2К + 1С
            4: {0: "К", 2: "К", 4: "К", 5: "А"},   # 3К + 1С
            5: {0: "К", 1: "К", 2: "А", 3: "К", 4: "К"},  # 3К + 2С(+кардио)
        }
    else:  # баланс
        schedules = {
            1: {2: "А"},
            2: {1: "К", 3: "А"},
            3: {0: "А", 2: "К", 4: "Б"},           # 1К + 2С
            4: {0: "А", 1: "К", 3: "Б", 4: "К"},   # 2К + 2С
            5: {0: "А", 1: "К", 2: "Б", 3: "К", 4: "В"},  # 2К + 3С
        }
    return schedules.get(gd, schedules.get(3, {}))
 
# ─────────────────────────────────────────
#  МЕНЮ
# ─────────────────────────────────────────
 
def main_menu(user_id=None):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    profile = get_profile(user_id) if user_id else None
 
    # Кнопка болезни
    if profile and profile.get("is_sick"):
        m.add(types.KeyboardButton("💊 Я болею (активно)"),
              types.KeyboardButton("✅ Я выздоровел"))
    else:
        m.add(types.KeyboardButton("🤒 Я заболел"))
 
    m.add(
        types.KeyboardButton("🟢 Тренировка сегодня"),
        types.KeyboardButton("🍽️ Рацион сегодня"),
        types.KeyboardButton("🔄 Заменить блюдо"),
        types.KeyboardButton("⚖️ Внести вес"),
        types.KeyboardButton("👟 Внести шаги"),
        types.KeyboardButton("📈 Мой прогресс"),
        types.KeyboardButton("👣 Мои шаги"),
        types.KeyboardButton("🕐 Расписание дня"),
        types.KeyboardButton("🍫 Сладкое"),
        types.KeyboardButton("🔥 Жиросжигающие продукты"),
        types.KeyboardButton("👤 Мой профиль"),
        types.KeyboardButton("⚙️ Изменить профиль"),
    )
    return m
 
def cancel_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(types.KeyboardButton("❌ Отмена"))
    return m
 
def foods_keyboard(foods_list):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for f in foods_list:
        m.add(types.KeyboardButton(f))
    m.add(types.KeyboardButton("❌ Отмена"))
    return m
 
# ─────────────────────────────────────────
#  ОНБОРДИНГ — НАСТРОЙКА ПРОФИЛЯ
# ─────────────────────────────────────────
 
ONBOARDING_STEPS = [
    ("setup_weight",   "⚖️ Введи свой *текущий вес* (кг), например: `107`"),
    ("setup_target",   "🎯 Введи *желаемый вес* (кг), например: `92`"),
    ("setup_height",   "📏 Введи свой *рост* (см), например: `194`"),
    ("setup_age",      "🎂 Введи свой *возраст* (лет), например: `24`"),
    ("setup_gymdays",  "🏋️ Сколько дней в неделю готов ходить в зал?\nВведи число от 1 до 5"),
    ("setup_pref",     "💬 Что тебе больше нравится в зале?\n\n1 — Кардио (эллипс, дорожка)\n2 — Силовые (тренажёры, веса)\n3 — Без разницы, пусть бот решает"),
    ("setup_deadline", "📅 За сколько *недель* хочешь достичь цели?\nНапример: `12` (3 месяца)"),
]
 
def auto_select_workout(profile):
    """
    Подбирает баланс с учётом:
    1. Пожелания пользователя (кардио / силовые / авто)
    2. Количества дней в зале
    3. Срочности (нужный темп похудения)
 
    Правило: пожелание учитывается, но не в ущерб здоровью.
    Даже при "только кардио" оставляем 1 силовую — защита мышц обязательна.
    """
    to_lose   = (profile.get("current_weight") or 107) - (profile.get("target_weight") or 92)
    gym_days  = profile.get("gym_days") or 3
    weeks     = profile.get("deadline_weeks") or 12
    user_pref = profile.get("workout_pref") or "авто"
    weekly_needed = to_lose / max(weeks, 1)
    urgent = weekly_needed > 1.5
 
    # Пользователь хочет кардио → даём кардио, но 1 силовая всегда
    if user_pref == "кардио":
        return "кардио_акцент"
 
    # Пользователь хочет силовые → даём силовые, но кардио не убираем
    # (при большом весе кардио обязательно для сердца)
    if user_pref == "силовые":
        if gym_days <= 2:
            return "кардио_акцент"   # мало дней — кардио важнее
        else:
            return "баланс"          # силовых больше
 
    # Авто — бот решает по математике
    if gym_days <= 2:
        return "кардио_акцент"
    elif gym_days == 3:
        return "кардио_акцент"
    elif gym_days == 4:
        return "кардио_акцент" if urgent else "баланс"
    else:
        return "кардио_акцент" if urgent else "баланс"
 
def auto_workout_label(profile):
    """Текстовое описание подобранного плана для профиля"""
    if not profile:
        return "автоподбор"
    mode     = auto_select_workout(profile)
    gym_days = profile.get("gym_days") or 3
    if mode == "кардио_акцент":
        if gym_days <= 2:   return "только кардио"
        elif gym_days == 3: return "2 кардио + 1 силовая"
        elif gym_days == 4: return "3 кардио + 1 силовая"
        else:               return "3 кардио + 2 силовых"
    else:
        if gym_days <= 2:   return "1 кардио + 1 силовая"
        elif gym_days == 3: return "1 кардио + 2 силовых"
        elif gym_days == 4: return "2 кардио + 2 силовых"
        else:               return "2 кардио + 3 силовых"
 
 
def start_onboarding(chat_id, edit=False):
    prefix = "✏️ Обновляем профиль!\n\n" if edit else "👤 *Настройка профиля*\n\nОтвечай на вопросы по очереди.\n\n"
    set_state(chat_id, "setup_weight", extra="edit" if edit else "new")
    bot.send_message(chat_id, prefix + ONBOARDING_STEPS[0][1],
                     parse_mode="Markdown", reply_markup=cancel_menu())
 
def handle_onboarding(chat_id, state, text, extra):
    """Обрабатывает шаги онбординга. Возвращает True если онбординг завершён."""
    steps = [s[0] for s in ONBOARDING_STEPS]
    idx   = steps.index(state) if state in steps else -1
    if idx == -1:
        return False
 
    # Валидация и сохранение текущего шага
    try:
        if state == "setup_weight":
            val = float(text.replace(",", "."))
            if not (30 < val < 300): raise ValueError
            save_profile(chat_id, current_weight=val)
 
        elif state == "setup_target":
            val = float(text.replace(",", "."))
            if not (30 < val < 300): raise ValueError
            save_profile(chat_id, target_weight=val)
 
        elif state == "setup_height":
            val = int(text)
            if not (100 < val < 250): raise ValueError
            save_profile(chat_id, height=val)
 
        elif state == "setup_age":
            val = int(text)
            if not (10 < val < 100): raise ValueError
            save_profile(chat_id, age=val)
 
        elif state == "setup_gymdays":
            val = int(text)
            if not (1 <= val <= 5): raise ValueError
            save_profile(chat_id, gym_days=val)
 
        elif state == "setup_pref":
            if text not in ("1", "2", "3"): raise ValueError
            pref_map = {"1": "кардио", "2": "силовые", "3": "авто"}
            save_profile(chat_id, workout_pref=pref_map[text])
 
        elif state == "setup_deadline":
            val = int(text)
            if not (1 <= val <= 104): raise ValueError
            save_profile(chat_id, deadline_weeks=val)
 
    except (ValueError, TypeError):
        hints = {
            "setup_weight":   "Введи вес числом, например: 107",
            "setup_target":   "Введи желаемый вес числом, например: 92",
            "setup_height":   "Введи рост числом в см, например: 194",
            "setup_age":      "Введи возраст числом, например: 24",
            "setup_gymdays":  "Введи число от 1 до 5",
            "setup_pref":     "Введи 1, 2 или 3",
            "setup_deadline": "Введи число недель, например: 12",
        }
        bot.send_message(chat_id, f"⚠️ {hints.get(state, 'Некорректный ввод')}",
                         reply_markup=cancel_menu())
        return False
 
    # Следующий шаг или завершение
    if idx + 1 < len(ONBOARDING_STEPS):
        next_state, next_prompt = ONBOARDING_STEPS[idx + 1]
        set_state(chat_id, next_state, extra=extra)
        bot.send_message(chat_id, next_prompt, parse_mode="Markdown", reply_markup=cancel_menu())
        return False
    else:
        # Онбординг завершён — показываем план
        set_state(chat_id, "idle")
        profile = get_profile(chat_id)
        plan    = calc_plan(profile)
        pref_ru = {"силовые": "только силовые", "кардио": "только кардио",
                   "чередование": "силовые + кардио"}
        msg = (
            f"🎉 *Профиль настроен!*\n\n"
            f"📊 *Твой персональный план:*\n\n"
            f"⚖️ Текущий вес: *{profile['current_weight']} кг*\n"
            f"🎯 Цель: *{profile['target_weight']} кг*\n"
            f"📉 Сбросить: *{round(profile['current_weight'] - profile['target_weight'], 1)} кг*\n\n"
            f"🔥 Калории/день: *{plan['calories']} ккал*\n"
            f"💪 Белок/день: *{plan['protein']}г*\n"
            f"📉 Дефицит: *{plan['deficit']} ккал/день*\n"
            f"📈 Темп: *~{plan['weekly_loss']} кг/нед*\n\n"
            f"🏋️ Зал: *{profile['gym_days']} дней/нед* ({auto_workout_label(profile)})\n"
            f"⏱️ Расчётный срок: *~{plan['weeks_needed']} недель*\n"
            f"📅 Твой срок: *{profile['deadline_weeks']} недель*\n\n"
        )
        if plan['weeks_needed'] > profile['deadline_weeks']:
            gap = plan['weeks_needed'] - profile['deadline_weeks']
            msg += (f"⚠️ *Внимание:* при текущем плане цель достигается за "
                    f"{plan['weeks_needed']} нед, а не {profile['deadline_weeks']}. "
                    f"Разница {gap} нед. Можно добавить +1 день в зале или немного снизить калории.\n\n")
        msg += "Используй кнопки меню для ежедневного плана!"
        bot.send_message(chat_id, msg, parse_mode="Markdown", reply_markup=main_menu(chat_id))
 
        # Сохраняем стартовый вес
        if not get_weights(chat_id):
            add_weight(chat_id, profile["current_weight"])
        return True
 
# ─────────────────────────────────────────
#  ГЕНЕРАТОР РАЦИОНА
# ─────────────────────────────────────────
 
def build_ration(user_id):
    profile = get_profile(user_id)
    if not profile:
        return "Сначала настрой профиль кнопкой *⚙️ Изменить профиль*", 0
 
    plan    = calc_plan(profile)
    cal     = plan["calories"]
    weights = get_weights(user_id)
    analysis = analyze_progress(weights) if len(weights) >= 2 else None
 
    # Корректировка по динамике
    if analysis:
        cal += analysis["cal_change"]
 
    p = get_portions(cal, plan["protein"])
 
    status = ""
    if analysis:
        icons = {"fast": "📈", "good": "✅", "slow": "📉", "plateau": "🪨", "gain": "🚨"}
        status = f"{icons.get(analysis['status'], '')} {analysis['advice']}\n\n"
 
    ration = (
        f"{status}"
        f"🍳 *Завтрак:* 3 яйца + 60г овсянки на воде + помидор/огурец\n"
        f"🍗 *Обед:* {p['breast']}г куриной грудки + {p['carb']}г гречки + салат\n"
        f"🍎 *Полдник:* {p['snack']}г куриного филе + 1 фрукт + 20г орехов\n"
        f"🌙 *Ужин:* 180г запечённой курицы + {p['dinner']}\n\n"
        f"🎯 *~{cal} ккал* | 💪 *~{plan['protein']}г белка*\n"
        f"🚶 +1 500 шагов сверх нормы (~15 мин прогулки)"
    )
    return ration, cal
 
def build_sick_ration():
    return (
        "🤒 *РАЦИОН ПРИ БОЛЕЗНИ*\n\n"
        "⚠️ Дефицит калорий отменяется — иммунитет важнее!\n\n"
        "🍳 *Завтрак:* 2 варёных яйца + 60г овсянки на воде + мёд 1 ч.л.\n"
        "🍗 *Обед:* куриный бульон 400мл + 150г куриной грудки + 60г риса\n"
        "🍎 *Полдник:* 1 банан + 20г грецких орехов + зелёный чай\n"
        "🌙 *Ужин:* 150г куриной грудки варёной + 200г шпината тушёного\n\n"
        "💧 *Вода:* минимум 3.5л + имбирный чай\n"
        "🌡️ *Калории:* ~2 000 ккал (поддерживающие)\n\n"
        "✅ Когда выздоровеешь — нажми «Я выздоровел» и план восстановится."
    )
 
# ─────────────────────────────────────────
#  ТРЕНИРОВКА СЕГОДНЯ
# ─────────────────────────────────────────
 
def get_today_workout(user_id):
    profile = get_profile(user_id)
    if not profile:
        return "Сначала настрой профиль кнопкой *⚙️ Изменить профиль*"
 
    if profile.get("is_sick"):
        return (
            "🤒 *Ты болеешь — тренировка отменена!*\n\n"
            "Любая нагрузка при болезни замедляет выздоровление и может дать осложнения.\n\n"
            "Сегодня: максимум лёгкая прогулка 15-20 мин на свежем воздухе если самочувствие позволяет.\n\n"
            "✅ Нажми «Я выздоровел» когда восстановишься."
        )
 
    weekday  = datetime.now().weekday()  # 0=пн
    pref     = profile.get("workout_pref", "чередование")
    gym_days = profile.get("gym_days", 3)
    schedule = get_week_schedule(profile, gym_days)
 
    workout_key = schedule.get(weekday)
    if not workout_key:
        return (
            "🛌 *Сегодня день отдыха*\n\n"
            "Мышцы растут во время восстановления, не на тренировке.\n"
            "Если менее 7 000 шагов — выйди на прогулку 30 мин.\n\n"
            "🍽️ Нажми «Рацион сегодня» для актуальных порций."
        )
 
    # Определяем тип тренировки
    if workout_key == "К":
        name, exercises = WORKOUTS["кардио"]["К"]
        return (
            f"🔵 *ТРЕНИРОВКА СЕГОДНЯ — {name}*\n\n"
            f"📱 Если уже >12 000 шагов — в зал не идёшь!\n\n"
            f"{exercises}\n\n"
            f"🍽️ Нажми «Рацион сегодня» для актуальных порций."
        )
    else:
        name, exercises = WORKOUTS["силовые"][workout_key]
        return (
            f"🟢 *ТРЕНИРОВКА СЕГОДНЯ — Комплекс {workout_key}: {name}*\n\n"
            f"🏋️ *Упражнения:*\n{exercises}\n\n"
            f"⏰ Рекомендуемое время: 18:40-20:00\n\n"
            f"🍽️ Нажми «Рацион сегодня» для актуальных порций."
        )
 
# ─────────────────────────────────────────
#  ХЭНДЛЕРЫ
# ─────────────────────────────────────────
 
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id
    profile = get_profile(chat_id)
    if not profile:
        bot.send_message(
            chat_id,
            "👋 Привет! Я *Инженерный трекер жиросжигания PRO v6*\n\n"
            "Давай настроим твой персональный план — это займёт 1 минуту.\n"
            "Отвечай на вопросы по очереди 👇",
            parse_mode="Markdown"
        )
        start_onboarding(chat_id)
    else:
        plan = calc_plan(profile)
        bot.send_message(
            chat_id,
            f"👋 С возвращением!\n\n"
            f"🎯 Цель: *{profile['current_weight']} → {profile['target_weight']} кг*\n"
            f"🔥 Калории/день: *{plan['calories']} ккал*\n"
            f"📈 Темп: *~{plan['weekly_loss']} кг/нед*",
            parse_mode="Markdown",
            reply_markup=main_menu(chat_id)
        )
 
@bot.message_handler(func=lambda m: True)
def router(message):
    chat_id = message.chat.id
    text    = message.text.strip()
    state, extra = get_state(chat_id)
 
    # ── Отмена ──
    if text == "❌ Отмена":
        set_state(chat_id, "idle")
        bot.send_message(chat_id, "Отменено.", reply_markup=main_menu(chat_id))
        return
 
    # ── Онбординг ──
    onboarding_states = [s[0] for s in ONBOARDING_STEPS]
    if state in onboarding_states:
        handle_onboarding(chat_id, state, text, extra)
        return
 
    # ── Ожидание веса ──
    if state == "waiting_weight":
        try:
            w = float(text.replace(",", "."))
            if not (30 < w < 300): raise ValueError
            add_weight(chat_id, w)
            save_profile(chat_id, current_weight=w)
            set_state(chat_id, "idle")
            weights_data = get_weights(chat_id)
            profile = get_profile(chat_id)
            start_w   = weights_data[0][0]
            target    = profile["target_weight"] if profile else 92.0
            loss      = round(start_w - w, 2)
            remaining = round(w - target, 1)
            pct = round((start_w - w) / (start_w - target) * 100, 1) if start_w != target else 100.0
            resp = (
                f"✅ Вес *{w} кг* сохранён! ({datetime.now().strftime('%d.%m.%Y')})\n\n"
                f"📉 Сброшено: *{loss} кг* | До цели: *{remaining} кг* | Прогресс: *{pct}%*"
            )
            if len(weights_data) >= 2:
                a = analyze_progress(weights_data)
                if a:
                    resp += f"\n\n─────────────\n🤖 {a['advice']}"
                    if a["cal_change"] != 0:
                        d = "увеличен" if a["cal_change"] > 0 else "снижен"
                        resp += f"\n\n📋 Рацион автоматически {d} на *{abs(a['cal_change'])} ккал*."
            bot.send_message(chat_id, resp, parse_mode="Markdown", reply_markup=main_menu(chat_id))
        except ValueError:
            bot.send_message(chat_id, "Введи число, например: 105.7")
        return
 
    # ── Ожидание шагов ──
    if state == "waiting_steps":
        try:
            steps = int(text.replace(" ", "").replace(",", ""))
            if not (0 < steps < 100000): raise ValueError
            add_steps(chat_id, steps)
            set_state(chat_id, "idle")
            if steps >= 12000:   verdict = "🔥 Отличный день! Кардио в зале можно пропустить."
            elif steps >= 8000:  verdict = "✅ Хороший уровень активности."
            elif steps >= 5000:  verdict = "🟡 Средняя активность. Добавь вечернюю прогулку."
            else:                verdict = "🔴 Малоподвижный день. Выйди на прогулку или сделай кардио."
            bot.send_message(chat_id,
                f"👟 *{steps:,} шагов* сохранено!\n\n{verdict}".replace(",", " "),
                parse_mode="Markdown", reply_markup=main_menu(chat_id))
        except ValueError:
            bot.send_message(chat_id, "Введи число шагов, например: 8500")
        return
 
    # ── Замена блюда: выбор приёма пищи ──
    if state == "subst_choose_meal":
        meals = list(MEAL_FOODS.keys())
        if text in meals:
            set_state(chat_id, "subst_choose_from", extra=text)
            meal_foods_flat = [f for group in MEAL_FOODS[text].values() for f in group]
            bot.send_message(
                chat_id,
                f"Выбран приём: *{text}*\n\nТеперь выбери *какой продукт заменить*:",
                parse_mode="Markdown",
                reply_markup=foods_keyboard(meal_foods_flat)
            )
        else:
            bot.send_message(chat_id, "Выбери приём пищи из кнопок.")
        return
 
    # ── Замена блюда: выбор исходного продукта ──
    if state == "subst_choose_from":
        meal = extra
        meal_foods_flat = [f for group in MEAL_FOODS.get(meal, {}).values() for f in group]
        if text in meal_foods_flat:
            group = find_group(text)
            from_grams = DEFAULT_PORTIONS.get(text, 100)
            kcal = round(KCAL_PER_100G[text] * from_grams / 100)
            # Доступные замены — та же группа, кроме самого продукта
            alternatives = [f for f in FOOD_GROUPS.get(group, []) if f != text]
            set_state(chat_id, "subst_choose_to", extra=f"{meal}|{text}")
            bot.send_message(
                chat_id,
                f"Заменяем: *{text}* ({from_grams}г = {kcal} ккал)\n"
                f"Приём пищи: *{meal}*\n\n"
                f"Выбери *чем заменить* (та же группа — {group}):",
                parse_mode="Markdown",
                reply_markup=foods_keyboard(alternatives)
            )
        else:
            bot.send_message(chat_id, "Выбери продукт из кнопок.")
        return
 
    # ── Замена блюда: выбор замены ──
    if state == "subst_choose_to":
        parts     = extra.split("|", 1)
        meal      = parts[0]
        from_food = parts[1] if len(parts) > 1 else ""
        all_foods = [f for g in FOOD_GROUPS.values() for f in g]
        if text in all_foods:
            if text == from_food:
                bot.send_message(chat_id, "Это тот же продукт 😄 Выбери другой.")
                return
            from_grams = DEFAULT_PORTIONS.get(from_food, 100)
            to_grams, kcal = calc_equivalent(from_food, text, from_grams)
            set_state(chat_id, "idle")
            bot.send_message(
                chat_id,
                f"✅ *Эквивалентная замена в {meal}:*\n\n"
                f"❌ {from_grams}г *{from_food}*\n"
                f"✅ {to_grams}г *{text}*\n\n"
                f"🔁 Калорийность приёма сохранена: *{kcal} ккал*\n"
                f"Дефицит и темп похудения не изменятся.",
                parse_mode="Markdown",
                reply_markup=main_menu(chat_id)
            )
        else:
            bot.send_message(chat_id, "Выбери продукт из кнопок.")
        return
 
    # ════════════════════════════════════════
    #  КНОПКИ ГЛАВНОГО МЕНЮ
    # ════════════════════════════════════════
 
    # ── Болезнь ──
    if text == "🤒 Я заболел":
        save_profile(chat_id, is_sick=1, sick_since=datetime.now().strftime("%Y-%m-%d"))
        bot.send_message(
            chat_id,
            "🤒 *Режим болезни активирован*\n\n"
            "• Тренировки автоматически отменены\n"
            "• Дефицит калорий снят — питание поддерживающее\n"
            "• Рацион переключён на лёгкую еду\n\n"
            "Скорейшего выздоровления! 💊\n"
            "Нажми «Рацион сегодня» для меню при болезни.",
            parse_mode="Markdown",
            reply_markup=main_menu(chat_id)
        )
 
    elif text in ("✅ Я выздоровел", "💊 Я болею (активно)") and text == "✅ Я выздоровел":
        profile = get_profile(chat_id)
        if profile:
            sick_since = profile.get("sick_since", "")
            days_sick = 0
            if sick_since:
                try:
                    days_sick = (datetime.now() - datetime.strptime(sick_since, "%Y-%m-%d")).days
                except Exception:
                    pass
            save_profile(chat_id, is_sick=0, sick_since="")
            bot.send_message(
                chat_id,
                f"✅ *Отлично, рад что выздоровел!*\n\n"
                f"{'Болел ' + str(days_sick) + ' дн. ' if days_sick else ''}"
                f"Возвращаемся к плану!\n\n"
                f"⚠️ *Первые 1-2 дня после болезни:*\n"
                f"• Снизь нагрузку на 30% — не форсируй\n"
                f"• Начни с кардио, потом силовые\n"
                f"• Пей воду как обычно — 3л\n\n"
                f"Нажми «Рацион сегодня» — план восстановлен.",
                parse_mode="Markdown",
                reply_markup=main_menu(chat_id)
            )
 
    # ── Тренировка сегодня ──
    elif text == "🟢 Тренировка сегодня":
        bot.send_message(chat_id, get_today_workout(chat_id),
                         parse_mode="Markdown")
 
    # ── Рацион сегодня ──
    elif text == "🍽️ Рацион сегодня":
        profile = get_profile(chat_id)
        if profile and profile.get("is_sick"):
            bot.send_message(chat_id, build_sick_ration(), parse_mode="Markdown")
        else:
            ration, cal = build_ration(chat_id)
            cal_label = {"low": "📉 Порции снижены", "medium": "✅ Стандарт", "high": "📈 Порции увеличены"}
            weights = get_weights(chat_id)
            a = analyze_progress(weights) if len(weights) >= 2 else None
            level = "medium"
            if a:
                level = "high" if a["cal_change"] > 0 else ("low" if a["cal_change"] < 0 else "medium")
            bot.send_message(
                chat_id,
                f"🍽️ *РАЦИОН НА СЕГОДНЯ*\n{cal_label.get(level, '')}\n─────────────\n{ration}\n\n"
                f"💡 Для замены продукта нажми «🔄 Заменить блюдо»",
                parse_mode="Markdown"
            )
 
    # ── Замена блюда ──
    elif text == "🔄 Заменить блюдо":
        set_state(chat_id, "subst_choose_meal")
        m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for meal in MEAL_FOODS.keys():
            m.add(types.KeyboardButton(meal))
        m.add(types.KeyboardButton("❌ Отмена"))
        bot.send_message(
            chat_id,
            "🔄 *Замена продукта с сохранением калорийности*\n\n"
            "В каком приёме пищи хочешь заменить продукт?",
            parse_mode="Markdown",
            reply_markup=m
        )
 
    # ── Внести вес ──
    elif text == "⚖️ Внести вес":
        set_state(chat_id, "waiting_weight")
        bot.send_message(chat_id, "⚖️ Введи текущий вес (например: *105.7*)\n\nЛучше утром натощак.",
                         parse_mode="Markdown", reply_markup=cancel_menu())
 
    # ── Внести шаги ──
    elif text == "👟 Внести шаги":
        set_state(chat_id, "waiting_steps")
        bot.send_message(chat_id, "👟 Введи количество шагов за сегодня (например: *8500*)",
                         parse_mode="Markdown", reply_markup=cancel_menu())
 
    # ── Прогресс ──
    elif text == "📈 Мой прогресс":
        weights_data = get_weights(chat_id)
        profile = get_profile(chat_id)
        if not weights_data:
            bot.send_message(chat_id, "История пуста. Внеси первый вес кнопкой «⚖️ Внести вес»")
            return
        lines = [f"• {d[:10]}: *{w} кг*" for w, d in weights_data]
        start_w = weights_data[0][0]
        curr_w  = weights_data[-1][0]
        target  = profile["target_weight"] if profile else 92.0
        loss    = round(start_w - curr_w, 2)
        remaining = round(curr_w - target, 1)
        pct = round((start_w - curr_w) / (start_w - target) * 100, 1) if start_w != target else 100.0
        msg = (
            "📋 *История взвешиваний:*\n\n" + "\n".join(lines) +
            f"\n\n🔥 Сброшено: *{loss} кг*\n"
            f"🎯 До цели ({target} кг): *{remaining} кг*\n"
            f"📊 Прогресс: *{pct}%*"
        )
        if len(weights_data) >= 2:
            a = analyze_progress(weights_data)
            if a:
                msg += f"\n\n─────────────\n🤖 {a['advice']}"
        bot.send_message(chat_id, msg, parse_mode="Markdown")
 
    # ── Мои шаги ──
    elif text == "👣 Мои шаги":
        steps_data = get_steps(chat_id)
        if not steps_data:
            bot.send_message(chat_id, "Нет данных. Нажми «👟 Внести шаги».")
            return
        lines = []
        total = 0
        for s, d in steps_data:
            bar   = "█" * (s // 2000) + "░" * max(0, 6 - s // 2000)
            emoji = "🔥" if s >= 12000 else ("✅" if s >= 8000 else ("🟡" if s >= 5000 else "🔴"))
            lines.append(f"{emoji} {d[:10]}: *{s:,}* {bar}".replace(",", " "))
            total += s
        avg = round(total / len(steps_data))
        goal_days = sum(1 for s, _ in steps_data if s >= 8000)
        bot.send_message(chat_id,
            "👣 *Статистика шагов (2 недели):*\n\n" + "\n".join(lines) +
            f"\n\n📊 Среднее: *{avg:,}* шагов/день".replace(",", " ") +
            f"\n🎯 Дней с нормой (≥8 000): *{goal_days}* из {len(steps_data)}",
            parse_mode="Markdown")
 
    # ── Расписание дня ──
    elif text == "🕐 Расписание дня":
        now  = datetime.now()
        hour = now.hour
        weekday = now.weekday()
        profile = get_profile(chat_id)
        gym_days = profile["gym_days"] if profile else 3
        pref = profile["workout_pref"] if profile else "чередование"
        schedule = get_week_schedule(profile, gym_days)
        is_gym_today = weekday in schedule
 
        if is_gym_today:
            wk = schedule[weekday]
            if wk == "К":
                gym_block = "🏃 *18:40* — Кардио в зале (45 мин)\n🚿 *19:45* — Душ, дорога домой"
            else:
                gym_block = "🏋️ *18:40* — Силовая тренировка (60 мин)\n🚿 *20:00* — Душ, дорога домой"
            dinner_time = "20:30-21:00"
        else:
            gym_block   = "🛌 Сегодня *день отдыха* — зал не нужен"
            dinner_time = "19:30-20:00"
 
        if 6 <= hour < 7:      current = "⏰ Время вставать!"
        elif 7 <= hour < 8:    current = "🍳 Время завтрака!"
        elif 8 <= hour < 12:   current = "💼 Рабочее утро. Следующий приём — обед в 12:00."
        elif 12 <= hour < 14:  current = "🍗 Время обеда!"
        elif 14 <= hour < 16:  current = "💼 Рабочий день. Полдник в 16:00."
        elif 16 <= hour < 17:  current = "🍎 Время полдника!"
        elif 17 <= hour < 19:  current = "🏃 Скоро зал / активность."
        elif 19 <= hour < 21:  current = "🏋️ Время тренировки или ужина!"
        elif 21 <= hour < 23:  current = "🌙 Время ужина. После — только вода."
        else:                  current = "😴 Пора спать! Цель — 23:00."
 
        bot.send_message(chat_id,
            f"🕐 *РАСПИСАНИЕ ДНЯ*\n\n📍 Сейчас: {current}\n\n"
            f"⏰ *06:45* — Подъём\n"
            f"🍳 *07:10* — Завтрак\n"
            f"💼 *07:30-12:00* — Работа\n"
            f"🍗 *12:00-13:00* — Обед\n"
            f"💼 *13:00-16:00* — Работа\n"
            f"🍎 *16:00-16:30* — Полдник ⚠️ не позже!\n"
            f"💼 *16:30-18:40* — Работа / дорога\n"
            f"{gym_block}\n"
            f"🌙 *{dinner_time}* — Ужин\n"
            f"💧 *До 23:00* — только вода\n"
            f"😴 *23:00* — Сон ✅",
            parse_mode="Markdown")
 
    # ── Профиль ──
    elif text == "👤 Мой профиль":
        profile = get_profile(chat_id)
        if not profile:
            bot.send_message(chat_id, "Профиль не настроен. Нажми *⚙️ Изменить профиль*",
                             parse_mode="Markdown")
            return
        plan    = calc_plan(profile)
        pref_ru = {"силовые": "только силовые", "кардио": "только кардио",
                   "чередование": "силовые + кардио"}
        weights = get_weights(chat_id)
        curr_w  = weights[-1][0] if weights else profile["current_weight"]
        loss    = round(profile["current_weight"] - curr_w, 1)
        bot.send_message(chat_id,
            f"👤 *МОЙ ПРОФИЛЬ*\n\n"
            f"⚖️ Стартовый вес: *{profile['current_weight']} кг*\n"
            f"📉 Текущий вес: *{curr_w} кг*\n"
            f"🔥 Сброшено: *{loss} кг*\n"
            f"🎯 Цель: *{profile['target_weight']} кг*\n"
            f"📏 Рост: *{profile['height']} см*\n"
            f"🎂 Возраст: *{profile['age']} лет*\n\n"
            f"🏋️ Зал: *{profile['gym_days']} дней/нед*\n"
            f"💪 Тренировки: *{auto_workout_label(profile)}*\n"
            f"📅 Срок: *{profile['deadline_weeks']} недель*\n\n"
            f"📊 *Расчётный план:*\n"
            f"• Калории: *{plan['calories']} ккал/день*\n"
            f"• Белок: *{plan['protein']}г/день*\n"
            f"• Дефицит: *{plan['deficit']} ккал/день*\n"
            f"• Темп: *~{plan['weekly_loss']} кг/нед*\n"
            f"• Расчётный срок: *~{plan['weeks_needed']} нед*",
            parse_mode="Markdown")
 
    # ── Изменить профиль ──
    elif text == "⚙️ Изменить профиль":
        start_onboarding(chat_id, edit=True)
 
    # ── Сладкое ──
    elif text == "🍫 Сладкое":
        hour = datetime.now().hour
        if 12 <= hour < 17:   timing = "✅ Сейчас хорошее время — после обеда или полдника!"
        elif 17 <= hour < 20: timing = "🟡 Ещё можно — но это последний шанс на сегодня."
        else:                  timing = "🚫 После 20:00 не стоит — потерпи до завтра!"
        bot.send_message(chat_id,
            f"🍫 *СЛАДКОЕ БЕЗ ВРЕДА ДЛЯ ПОХУДЕНИЯ*\n\n{timing}\n\n"
            f"─────────────────\n"
            f"✅ *Разрешено (150-200 ккал бюджет):*\n"
            f"• Горький шоколад 70%+ — 25г = *138 ккал* ⭐\n"
            f"• Зефир — 1 шт (25г) = *75 ккал*\n"
            f"• Финики — 3 шт (30г) = *82 ккал*\n"
            f"• Мёд — 1 ч.л. (7г) = *23 ккал*\n"
            f"• Сухофрукты — 30г = *70 ккал*\n\n"
            f"🚫 *Исключить полностью:*\n"
            f"• Сладкие напитки/соки\n"
            f"• Торты, пирожные\n"
            f"• Конфеты с начинкой\n\n"
            f"📌 *Правила:* только после еды · не позже 20:00 · 3-4 раза в неделю",
            parse_mode="Markdown")
 
    # ── Жиросжигающие продукты ──
    elif text == "🔥 Жиросжигающие продукты":
        bot.send_message(chat_id,
            "🔥 *ПРОДУКТЫ ДЛЯ УСКОРЕНИЯ ЖИРОСЖИГАНИЯ*\n\n"
            "⚡ *Ускоряют метаболизм:*\n"
            "• Зелёный чай без сахара — 2-3 чашки в день\n"
            "• Кофе без сахара — за 30 мин до тренировки\n"
            "• Острый перец (чили) — добавляй в еду\n"
            "• Имбирь — в чай, снижает инсулин\n\n"
            "💪 *Снижают кортизол (висцеральный жир):*\n"
            "• Тёмный шоколад 70%+ — 25г после обеда\n"
            "• Грецкие орехи — омега-3, снижают воспаление\n"
            "• Черника/голубика — 50г в день\n"
            "• Бананы — калий + магний (1-2 раза в неделю)\n\n"
            "💧 *Самый недооценённый инструмент:*\n"
            "• 3л воды в день = +30% к скорости жиросжигания\n"
            "  (печень лучше перерабатывает жир)\n\n"
            "⚠️ Ни один продукт не заменит дефицит калорий.\n"
            "Но зелёный чай + кофе до тренировки + грецкие орехи\n"
            "дадут реальный дополнительный эффект.",
            parse_mode="Markdown")
 
    else:
        bot.send_message(chat_id, "Используй кнопки меню.", reply_markup=main_menu(chat_id))
 
if __name__ == '__main__':
    init_db()
    print("Бот v6 запущен! Профиль + болезнь + умные замены активированы.")
    bot.infinity_polling()
