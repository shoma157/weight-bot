import telebot
from telebot import types
import sqlite3
import threading
import time
import csv
import io
from datetime import datetime, timezone, timedelta
import random

# Самарское время UTC+4
SAMARA_TZ = timezone(timedelta(hours=4))
def now_samara():
    return datetime.now(SAMARA_TZ)

TOKEN = "8844022654:AAFZt7DXdHWoORHlGrFSi0rMyX7BUYBzUR8"
bot = telebot.TeleBot(TOKEN)

# ─────────────────────────────────────────
#  КАЛОРИЙНОСТЬ И ПРОДУКТЫ
# ─────────────────────────────────────────

KCAL_PER_100G = {
    # Белки
    "куриная грудка": 110, "куриное бедро": 185, "индейка": 115,
    "говядина": 187, "яйцо": 155,
    # Углеводы
    "гречка": 313, "бурый рис": 337, "булгур": 342, "овсянка": 352, "макароны": 350,
    # Овощи
    "болгарский перец": 27, "морковь": 35, "шпинат": 23,
    "стручковая фасоль": 31, "брокколи": 34, "огурец": 15, "помидор": 18,
    # Орехи
    "миндаль": 576, "грецкий орех": 654, "кешью": 553, "тыквенные семечки": 559,
    # Фрукты — расширенный список
    "яблоко": 52, "груша": 57, "ягоды": 45,
    "банан": 89, "апельсин": 47, "мандарин": 38, "грейпфрут": 35,
    "киви": 61, "манго": 65, "персик": 39, "слива": 46,
    "виноград": 67, "арбуз": 30, "дыня": 33, "ананас": 50,
    "черника": 57, "клубника": 32, "малина": 53, "вишня": 52,
    # Спортивное питание
    "протеиновый батончик": 370,
    "протеиновое печенье": 390,
    "протеин сывороточный (порция 30г)": 115,
    "протеин казеиновый (порция 30г)": 110,
    "протеиновый йогурт": 75,
    "протеиновый пудинг": 95,
    "высокобелковый творог (0%)": 73,
    # Полуфабрикаты
    "куриные котлеты замороженные": 170,
    "куриные фрикадельки замороженные": 155,
    "готовая варёная курица": 135,
    "консервированная курица": 160,
    "консервированная индейка": 130,
    "замороженная овощная смесь": 40,
    "гречка в пакете": 310,
    "рис в пакете": 330,
    "куриные сосиски": 190,
    "куриные наггетсы запечённые": 195,
}

# ... тут ваш KCAL_PER_100G ...

# MACRO_PER_100G: белки, жиры, углеводы на 100г продукта
MACRO_PER_100G = {
    # Белковые продукты
    "куриная грудка": {"белки": 23, "жиры": 1, "углеводы": 0},
    "куриное бедро": {"белки": 19, "жиры": 12, "углеводы": 0}, 
    "индейка": {"белки": 22, "жиры": 7, "углеводы": 0},
    "говядина": {"белки": 26, "жиры": 15, "углеводы": 0},
    "яйцо": {"белки": 13, "жиры": 11, "углеводы": 1},
    
    # Углеводные продукты
    "гречка": {"белки": 13, "жиры": 3, "углеводы": 68},
    "бурый рис": {"белки": 7, "жиры": 3, "углеводы": 77},
    "булгур": {"белики": 12, "жиры": 1, "углеводы": 76},
    "овсянка": {"белки": 12, "жиры": 7, "углеводы": 66},
    "макароны": {"белки": 11, "жиры": 1, "углеводы": 75},
    
    # Овощи
    "болгарский перец": {"белки": 1, "жиры": 0, "углеводы": 6},
    "морковь": {"белки": 1, "жиры": 0, "углеводы": 10},
    "шпинат": {"белки": 3, "жиры": 0, "углеводы": 2},
    "брокколи": {"белки": 3, "жиры": 0, "углеводы": 7},
}

FOOD_GROUPS = {
    "белок":    ["куриная грудка", "куриное бедро", "индейка", "говядина",
                 "готовая варёная курица", "консервированная курица", "консервированная индейка",
                 "куриные котлеты замороженные", "куриные фрикадельки замороженные",
                 "куриные сосиски", "куриные наггетсы запечённые"],
    "углеводы": ["гречка", "бурый рис", "булгур", "овсянка", "макароны",
                 "гречка в пакете", "рис в пакете"],
    "овощи":    ["болгарский перец", "морковь", "шпинат", "стручковая фасоль",
                 "брокколи", "огурец", "помидор", "замороженная овощная смесь"],
    "орехи":    ["миндаль", "грецкий орех", "кешью", "тыквенные семечки"],
    "фрукты":   ["яблоко", "груша", "ягоды", "банан", "апельсин", "мандарин",
                 "грейпфрут", "киви", "манго", "персик", "слива",
                 "виноград", "арбуз", "дыня", "ананас",
                 "черника", "клубника", "малина", "вишня"],
    "спортпит": ["протеиновый батончик", "протеиновое печенье",
                 "протеин сывороточный (порция 30г)", "протеин казеиновый (порция 30г)",
                 "протеиновый йогурт", "протеиновый пудинг",
                 "высокобелковый творог (0%)"],
}

# Предупреждения о полуфабрикатах
SEMIFAB_WARNINGS = {
    "куриные котлеты замороженные": "⚠️ Выбирай без панировки, состав: только курица+специи",
    "куриные фрикадельки замороженные": "⚠️ Состав: курица >80%, без крахмала и сои",
    "куриные сосиски": "⚠️ Макс 2 раза в неделю. Состав: мясо >80%, соль <2г/100г",
    "куриные наггетсы запечённые": "⚠️ Только запечённые, не жареные! Макс 2 раза в неделю",
    "готовая варёная курица": "✅ Хороший вариант — снять кожу перед едой",
    "консервированная курица": "✅ В собственном соку, без масла",
    "консервированная индейка": "✅ В собственном соку, без масла",
    "замороженная овощная смесь": "✅ Без соусов и масла в составе",
    "гречка в пакете": "✅ Удобно — 1 пакет ≈ 80г сухой крупы",
    "рис в пакете": "✅ Бурый или пропаренный, не белый шлифованный",
    # Спортпит
    "протеиновый батончик": "⚠️ Состав: белок >20г/порцию, сахар <10г. Не более 1 шт/день",
    "протеиновое печенье": "⚠️ Состав: белок >15г/порцию, сахар <8г. Не более 1 шт/день",
    "протеин сывороточный (порция 30г)": "✅ На воде или миндальном молоке. После тренировки или утром",
    "протеин казеиновый (порция 30г)": "✅ На ночь — медленное усвоение, защищает мышцы во сне",
    "протеиновый йогурт": "✅ Без сахара, состав: белок >10г/100г",
    "протеиновый пудинг": "⚠️ Смотри состав: белок >15г/порцию, калории <200/порцию",
    "высокобелковый творог (0%)": "✅ Отличный вариант — 18г белка/100г, без лактозных проблем (уточни индивидуально)",
    # Фрукты
    "банан": "⚠️ Высокий ГИ — лучше до/после тренировки, не вечером",
    "виноград": "⚠️ Много сахара — не более 150г, не вечером",
    "манго": "⚠️ Много сахара — не более 150г, предпочтительно до 16:00",
    "дыня": "⚠️ Высокий ГИ — есть отдельно от другой еды",
    "арбуз": "✅ Много воды, низкая калорийность. Отличный перекус летом",
    "грейпфрут": "✅ Снижает инсулин, хорош утром. Не сочетать с некоторыми лекарствами",
    "киви": "✅ Много витамина C, низкий ГИ — отличный выбор",
    "черника": "✅ Антиоксиданты, снижает воспаление — лучший выбор для похудения",
    "клубника": "✅ Низкий ГИ, витамин C",
}

MEAL_FOODS = {
    "🍳 Завтрак": {
        "белок": ["яйцо", "готовая варёная курица", "консервированная курица",
                  "высокобелковый творог (0%)"],
        "углеводы": ["овсянка", "гречка в пакете"],
        "овощи": ["огурец", "помидор"],
        "спортпит": ["протеин сывороточный (порция 30г)", "протеиновый йогурт"],
    },
    "🍗 Обед": {
        "белок": ["куриная грудка", "куриное бедро", "индейка", "говядина",
                  "готовая варёная курица", "консервированная курица", "консервированная индейка",
                  "куриные котлеты замороженные", "куриные фрикадельки замороженные",
                  "куриские сосиски"],
        "углеводы": ["гречка", "бурый рис", "булгур", "макароны",
                     "гречка в пакете", "рис в пакете"],
        "овощи": ["болгарский перец", "морковь", "замороженная овощная смесь", "огурец"],
    },
    "🍎 Полдник": {
        "белок": ["куриная грудка", "индейка", "консервированная курица",
                  "высокобелковый творог (0%)"],
        "орехи": ["миндаль", "грецкий орех", "кешью", "тыквенные семечки"],
        "фрукты": ["яблоко", "груша", "ягоды", "банан", "апельсин", "мандарин",
                   "грейпфрут", "киви", "персик", "слива", "черника", "клубника", "малина"],
        "спортпит": ["протеиновый батончик", "протеиновое печенье",
                     "протеиновый йогурт", "протеиновый пудинг"],
    },
    "🌙 Ужин": {
        "белок": ["куриная грудка", "куриное бедро", "индейка", "говядина",
                  "готовая варёная курица", "куриные котлеты замороженные",
                  "куриные наггетсы запечённые"],
        "овощи": ["болгарский перец", "морковь", "шпинат", "стручковая фасоль",
                  "брокколи", "замороженная овощная смесь"],
    },
}

DEFAULT_PORTIONS = {
    "куриная грудка": 230, "куриное бедро": 230, "индейка": 230, "говядина": 200,
    "яйцо": 186, "гречка": 65, "бурый рис": 65, "булгур": 65, "овсянка": 60,
    "макароны": 85, "болгарский перец": 200, "морковь": 200, "шпинат": 200,
    "стручковая фасоль": 200, "брокколи": 200, "огурец": 100, "помидор": 100,
    "миндаль": 20, "грецкий орех": 20, "кешью": 20, "тыквенные семечки": 20,
    "яблоко": 150, "груша": 150, "ягоды": 100,
    "куриные котлеты замороженные": 200, "куриные фрикадельки замороженные": 200,
    "готовая варёная курица": 230, "консервированная курица": 185,
    "консервированная индейка": 185, "замороженная овощная смесь": 250,
    "гречка в пакете": 80, "рис в пакете": 80,
    "куриские сосиски": 160, "куриные сосиски": 160,
    "куриные наггетсы запечённые": 200,
    # Фрукты расширенные
    "банан": 120, "апельсин": 150, "мандарин": 100, "грейпфрут": 200,
    "киви": 100, "манго": 150, "персик": 130, "слива": 100,
    "виноград": 150, "арбуз": 300, "дыня": 200, "ананас": 150,
    "черника": 100, "клубника": 150, "малина": 100, "вишня": 120,
    # Спортпит
    "протеиновый батончик": 60,
    "протеиновое печенье": 60,
    "протеин сывороточный (порция 30г)": 30,
    "протеин казеиновый (порция 30г)": 30,
    "протеиновый йогурт": 150,
    "протеиновый пудинг": 150,
    "высокобелковый творог (0%)": 150,
}

MOTIVATIONAL_QUOTES = [
    "💪 Каждый день без срыва — это победа!",
    "🔥 Дефицит калорий сегодня — это твоё тело завтра.",
    "🎯 107 кг → 92 кг. Ты уже на пути!",
    "⚡ Тяжело в тренировке — легко в жизни.",
    "🌟 Прогресс, а не перфекционизм.",
    "💧 3 литра воды сегодня — подарок своим мышцам.",
    "🏃 Каждый шаг считается. Буквально.",
    "😴 Сон до 23:00 — это тоже тренировка.",
]

def calc_equivalent(from_food, to_food, from_grams=None):
    if from_grams is None:
        from_grams = DEFAULT_PORTIONS.get(from_food, 100)
    kcal = KCAL_PER_100G.get(from_food, 150) * from_grams / 100
    to_kcal = KCAL_PER_100G.get(to_food, 150)
    return round(kcal / to_kcal * 100), round(kcal)

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
    c.execute('''CREATE TABLE IF NOT EXISTS water (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        glasses INTEGER, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_state (
        user_id INTEGER PRIMARY KEY, state TEXT DEFAULT "idle", extra TEXT DEFAULT "")''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_profile (
        user_id INTEGER PRIMARY KEY,
        current_weight REAL, target_weight REAL, height INTEGER, age INTEGER,
        gym_days INTEGER, workout_pref TEXT, deadline_weeks INTEGER,
        is_sick INTEGER DEFAULT 0, sick_since TEXT DEFAULT "",
        fatigue INTEGER DEFAULT 0, last_workout_date TEXT DEFAULT "",
        next_workout_override TEXT DEFAULT "",
        reminders_enabled INTEGER DEFAULT 1,
        cheatmeal_used INTEGER DEFAULT 0,
        cheatmeal_week TEXT DEFAULT "",
        is_driver INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        workout_type TEXT, fatigue_after INTEGER DEFAULT 0, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sleep (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        sleep_time TEXT, wake_time TEXT,
        duration_hours REAL, quality INTEGER, date TEXT)''')
    # Миграция
    for col, dflt in [
        ("fatigue","0"), ("last_workout_date","''"), ("next_workout_override","''"),
        ("reminders_enabled","1"), ("cheatmeal_used","0"), ("cheatmeal_week","''"),
        ("is_driver","0"),
    ]:
        try:
            c.execute(f"ALTER TABLE user_profile ADD COLUMN {col} TEXT DEFAULT {dflt}")
        except Exception:
            pass
    conn.commit(); conn.close()

def get_profile(uid):
    conn = sqlite3.connect("weight_tracker.db")
    row = conn.execute("SELECT * FROM user_profile WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    if not row: return None
    keys = ["user_id","current_weight","target_weight","height","age",
            "gym_days","workout_pref","deadline_weeks","is_sick","sick_since",
            "fatigue","last_workout_date","next_workout_override",
            "reminders_enabled","cheatmeal_used","cheatmeal_week","is_driver"]
    d = dict(zip(keys, row))
    # Приводим типы
    for k in ("is_sick","fatigue","reminders_enabled","cheatmeal_used","is_driver"):
        d[k] = int(d[k]) if d[k] else 0
    return d

def save_profile(uid, **kw):
    conn = sqlite3.connect("weight_tracker.db")
    ex = conn.execute("SELECT user_id FROM user_profile WHERE user_id=?", (uid,)).fetchone()
    if ex:
        sets = ", ".join(f"{k}=?" for k in kw)
        conn.execute(f"UPDATE user_profile SET {sets} WHERE user_id=?", (*kw.values(), uid))
    else:
        kw["user_id"] = uid
        cols = ", ".join(kw.keys()); vals = ", ".join("?"*len(kw))
        conn.execute(f"INSERT INTO user_profile ({cols}) VALUES ({vals})", list(kw.values()))
    conn.commit(); conn.close()

def get_all_users():
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute("SELECT user_id FROM user_profile").fetchall()
    conn.close()
    return [r[0] for r in rows]

def add_weight(uid, w):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("INSERT INTO weights (user_id,weight_value,date) VALUES (?,?,?)",
                 (uid, w, now_samara().strftime("%Y-%m-%d %H:%M")))
    conn.commit(); conn.close()

def get_weights(uid):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute("SELECT weight_value,date FROM weights WHERE user_id=? ORDER BY id ASC", (uid,)).fetchall()
    conn.close()
    return rows

def get_weights_last_n_days(uid, days=14):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute(
        "SELECT weight_value,date FROM weights WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (uid, days)).fetchall()
    conn.close()
    return list(reversed(rows))

def add_steps(uid, s):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("INSERT INTO steps (user_id,step_count,date) VALUES (?,?,?)",
                 (uid, s, now_samara().strftime("%Y-%m-%d %H:%M")))
    conn.commit(); conn.close()

def get_steps(uid, limit=14):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute("SELECT step_count,date FROM steps WHERE user_id=? ORDER BY id DESC LIMIT ?",
                        (uid, limit)).fetchall()
    conn.close()
    return list(reversed(rows))

def add_water(uid, glasses):
    today = now_samara().strftime("%Y-%m-%d")
    conn  = sqlite3.connect("weight_tracker.db")
    ex = conn.execute("SELECT id,glasses FROM water WHERE user_id=? AND date=?", (uid, today)).fetchone()
    if ex:
        conn.execute("UPDATE water SET glasses=? WHERE id=?", (ex[1]+glasses, ex[0]))
    else:
        conn.execute("INSERT INTO water (user_id,glasses,date) VALUES (?,?,?)", (uid, glasses, today))
    conn.commit(); conn.close()

def get_water_today(uid):
    today = now_samara().strftime("%Y-%m-%d")
    conn  = sqlite3.connect("weight_tracker.db")
    row   = conn.execute("SELECT glasses FROM water WHERE user_id=? AND date=?", (uid, today)).fetchone()
    conn.close()
    return row[0] if row else 0

def log_workout(uid, wtype, fatigue=0):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("INSERT INTO workouts (user_id,workout_type,fatigue_after,date) VALUES (?,?,?,?)",
                 (uid, wtype, fatigue, now_samara().strftime("%Y-%m-%d %H:%M")))
    conn.commit(); conn.close()

def get_last_workout(uid):
    conn = sqlite3.connect("weight_tracker.db")
    row = conn.execute("SELECT workout_type,fatigue_after,date FROM workouts WHERE user_id=? ORDER BY id DESC LIMIT 1",
                       (uid,)).fetchone()
    conn.close()
    return row

# ─────────────────────────────────────────
#  СОН
# ─────────────────────────────────────────

def log_sleep(uid, sleep_time, wake_time, duration, quality):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute(
        "INSERT INTO sleep (user_id,sleep_time,wake_time,duration_hours,quality,date) VALUES (?,?,?,?,?,?)",
        (uid, sleep_time, wake_time, duration, quality, now_samara().strftime("%Y-%m-%d"))
    )
    conn.commit(); conn.close()

def get_sleep_history(uid, limit=7):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute(
        "SELECT sleep_time,wake_time,duration_hours,quality,date FROM sleep "
        "WHERE user_id=? ORDER BY id DESC LIMIT ?", (uid, limit)
    ).fetchall()
    conn.close()
    return list(reversed(rows))

def get_last_sleep(uid):
    conn = sqlite3.connect("weight_tracker.db")
    row = conn.execute(
        "SELECT sleep_time,wake_time,duration_hours,quality,date FROM sleep "
        "WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,)
    ).fetchone()
    conn.close()
    return row

def analyze_sleep(duration, quality):
    """Анализирует качество сна и даёт рекомендации"""
    if duration >= 7.5 and quality >= 4:
        status = "excellent"
        note   = "🌟 Отличный сон! Тело восстановилось полностью. Тренировка в полную силу."
        cal_adj = 0
        fat_adj = 1
    elif duration >= 7.0 and quality >= 3:
        status = "good"
        note   = "✅ Хороший сон. Восстановление нормальное."
        cal_adj = 0
        fat_adj = 2
    elif duration >= 6.0:
        status = "moderate"
        note   = ("🟡 Сон немного короткий ({:.1f} ч). Кортизол чуть повышен — "
                  "жиросжигание замедляется на ~10%. Добавь 100 ккал и снизь нагрузку на 20%.").format(duration)
        cal_adj = +100
        fat_adj = 3
    elif duration >= 5.0:
        status = "poor"
        note   = ("🔴 Плохой сон ({:.1f} ч)! Кортизол высокий — силовую лучше заменить "
                  "на лёгкое кардио. +150 ккал на восстановление.").format(duration)
        cal_adj = +150
        fat_adj = 4
    else:
        status = "critical"
        note   = ("😵 Критически мало сна ({:.1f} ч)! Тренировку пропусти — "
                  "риск травмы и потери мышц. +200 ккал, много воды.").format(duration)
        cal_adj = +200
        fat_adj = 5
    return {"status": status, "note": note, "cal_adj": cal_adj, "fat_adj": fat_adj}

def build_sleep_stats(uid):
    history = get_sleep_history(uid, limit=7)
    if not history:
        return None
    durations = [h[2] for h in history if h[2]]
    qualities  = [h[3] for h in history if h[3]]
    avg_dur  = round(sum(durations)/len(durations), 1) if durations else 0
    avg_qual = round(sum(qualities)/len(qualities), 1) if qualities else 0
    lines = []
    for st, wt, dur, qual, d in history:
        bar  = "🌙" * min(int(dur or 0), 10)
        stars= "⭐" * (qual or 0)
        lines.append(f"• {d}: *{dur:.1f}ч* {bar} {stars}")
    verdict = ("🌟 Отличный режим!" if avg_dur >= 7.5 else
               "✅ Хороший режим" if avg_dur >= 7.0 else
               "🟡 Немного недосыпаешь" if avg_dur >= 6.0 else
               "🔴 Серьёзный недосып — влияет на похудение!")
    return ("\n".join(lines) +
            f"\n\n📊 Среднее за неделю: *{avg_dur} ч* | Качество: *{avg_qual}/5*\n{verdict}")

def set_state(uid, state, extra=""):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("INSERT INTO user_state (user_id,state,extra) VALUES (?,?,?) "
                 "ON CONFLICT(user_id) DO UPDATE SET state=excluded.state, extra=excluded.extra",
                 (uid, state, extra))
    conn.commit(); conn.close()

def get_state(uid):
    conn = sqlite3.connect("weight_tracker.db")
    row = conn.execute("SELECT state,extra FROM user_state WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return (row[0], row[1]) if row else ("idle", "")

# ─────────────────────────────────────────
#  РАСЧЁТ ПЛАНА
# ─────────────────────────────────────────

def calc_plan(profile):
    w  = profile.get("current_weight") or 107
    h  = profile.get("height") or 194
    a  = profile.get("age") or 24
    gd = profile.get("gym_days") or 3
    is_driver = int(profile.get("is_driver") or 0)
    bmr  = 10*w + 6.25*h - 5*a + 5
    base_mult = {1:1.30,2:1.35,3:1.45,4:1.50,5:1.55}.get(min(gd,5), 1.45)
    mult = base_mult - (0.05 if is_driver else 0)
    tdee = round(bmr * mult)
    deficit  = min(round(tdee*0.30), 1200)
    calories = tdee - deficit
    weekly   = round(deficit*7/7700, 2)
    to_lose  = w - (profile.get("target_weight") or 92)
    weeks_needed = round(to_lose/weekly) if weekly > 0 else 999
    return {"bmr":round(bmr),"tdee":tdee,"calories":calories,
            "deficit":deficit,"protein":round(w*1.8),
            "weekly_loss":weekly,"weeks_needed":weeks_needed}

def get_portions(calories):
    s = calories / 1950
    return {
        "breast": round(230*s), "carb": round(65*s), "snack": round(130*s),
        "dinner": "300г тушёных овощей" if s >= 1 else "только овощи без гарнира",
    }

def analyze_progress(wd):
    if len(wd) < 2: return None
    prev_w,prev_d = wd[-2]; curr_w,curr_d = wd[-1]
    try:
        days = max((datetime.strptime(curr_d[:10],"%Y-%m-%d") -
                    datetime.strptime(prev_d[:10],"%Y-%m-%d")).days, 1)
    except Exception:
        days = 7
    rate = round((prev_w-curr_w)/days*7, 2)
    if rate > 2.0:
        return {"status":"fast","rate":rate,"cal_change":+150,
                "advice":f"⚡ Темп высокий ({rate} кг/нед). *+150 ккал* к обеду."}
    elif rate >= 0.7:
        return {"status":"good","rate":rate,"cal_change":0,
                "advice":f"✅ Идеальный темп ({rate} кг/нед). Ничего не меняй!"}
    elif rate >= 0.1:
        return {"status":"slow","rate":rate,"cal_change":-150,
                "advice":f"🐢 Медленно ({rate} кг/нед). *Убери гарнир на ужин* (−150 ккал)."}
    elif rate >= -0.1:
        return {"status":"plateau","rate":rate,"cal_change":-200,
                "advice":f"🪨 Плато. *−200 ккал* + кардио на этой неделе."}
    else:
        return {"status":"gain","rate":rate,"cal_change":-250,
                "advice":f"🚨 Вес растёт ({abs(rate)} кг/нед). *Убери полдник* (−250 ккал)."}

def compare_weeks(uid):
    """Сравнивает текущую и прошлую неделю по шагам и весу"""
    wd = get_weights(uid)
    sd = get_steps(uid, limit=14)
    if len(wd) < 2 or len(sd) < 2:
        return None
    mid = len(sd) // 2
    avg_steps_this  = round(sum(s for s,_ in sd[mid:]) / max(len(sd)-mid, 1))
    avg_steps_last  = round(sum(s for s,_ in sd[:mid]) / max(mid, 1))
    steps_diff = avg_steps_this - avg_steps_last
    weight_diff = round(wd[-1][0] - wd[max(-3,-len(wd))][0], 2) if len(wd) >= 2 else 0
    return {"steps_this": avg_steps_this, "steps_last": avg_steps_last,
            "steps_diff": steps_diff, "weight_diff": weight_diff}

# ─────────────────────────────────────────
#  ASCII ГРАФИК ВЕСА
# ─────────────────────────────────────────

def build_weight_chart(uid):
    wd = get_weights_last_n_days(uid, 10)
    if len(wd) < 2:
        return None
    weights = [w for w,_ in wd]
    dates   = [d[:10] for _,d in wd]
    mn, mx  = min(weights), max(weights)
    rng     = mx - mn if mx != mn else 1
    height  = 5
    lines   = []
    for row in range(height, -1, -1):
        threshold = mn + (rng * row / height)
        line = f"{threshold:5.1f} |"
        for w in weights:
            if w >= threshold - rng/(height*2):
                line += " ●"
            else:
                line += "  "
        lines.append(line)
    lines.append("       " + "──" * len(weights))
    # Даты (только день)
    day_line = "       " + " ".join(d[8:] for d in dates)
    lines.append(day_line)
    return "\n".join(lines)

# ─────────────────────────────────────────
#  ТРЕНИРОВКИ
# ─────────────────────────────────────────

WORKOUTS = {
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
    "К": ("Кардио 45 минут",
          "• Эллипс (пульс 120-135 уд/мин)\n"
          "• ИЛИ ходьба на дорожке: наклон 8%, скорость 5.5 км/ч"),
    "И": ("Интимная близость (замена кардио)",
          "• Засчитывается как лёгкое кардио: ~200-350 ккал\n"
          "• Длительность: от 20 мин\n"
          "• Пульс 90-130 уд/мин — зона жиросжигания\n"
          "• После: выпей 500мл воды + лёгкий белковый перекус"),
}

def auto_select_workout(profile):
    if not profile: return "кардио_акцент"
    to_lose   = (profile.get("current_weight") or 107) - (profile.get("target_weight") or 92)
    gym_days  = profile.get("gym_days") or 3
    weeks     = profile.get("deadline_weeks") or 12
    user_pref = profile.get("workout_pref") or "авто"
    urgent    = (to_lose / max(weeks,1)) > 1.5
    if user_pref == "кардио": return "кардио_акцент"
    if user_pref == "силовые": return "баланс" if gym_days >= 3 else "кардио_акцент"
    return "кардио_акцент" if (gym_days <= 3 or urgent) else "баланс"

def auto_workout_label(profile):
    if not profile: return "автоподбор"
    mode = auto_select_workout(profile)
    gd   = profile.get("gym_days") or 3
    if mode == "кардио_акцент":
        return {1:"только кардио",2:"только кардио",3:"2 кардио + 1 силовая",
                4:"3 кардио + 1 силовая"}.get(gd, "3 кардио + 2 силовых")
    return {1:"1 силовая",2:"1 кардио + 1 силовая",3:"1 кардио + 2 силовых",
            4:"2 кардио + 2 силовых"}.get(gd, "2 кардио + 3 силовых")

def get_week_schedule(profile, gym_days):
    mode = auto_select_workout(profile)
    gd   = min(gym_days, 5)
    if mode == "кардио_акцент":
        s = {1:{2:"К"},2:{1:"К",4:"К"},3:{1:"К",3:"К",5:"А"},
             4:{0:"К",2:"К",4:"К",5:"А"},5:{0:"К",1:"К",2:"А",3:"К",4:"К"}}
    else:
        s = {1:{2:"А"},2:{1:"К",3:"А"},3:{0:"А",2:"К",4:"Б"},
             4:{0:"А",1:"К",3:"Б",4:"К"},5:{0:"А",1:"К",2:"Б",3:"К",4:"В"}}
    return s.get(gd, s.get(3, {}))

def hours_since_last_workout(profile):
    last = profile.get("last_workout_date") or ""
    if not last: return 999
    try:
        last_dt = datetime.strptime(last[:16],"%Y-%m-%d %H:%M").replace(tzinfo=SAMARA_TZ)
        return (now_samara()-last_dt).total_seconds()/3600
    except Exception:
        return 999

def adjust_workout_for_fatigue(wkey, fatigue):
    if fatigue <= 2: return wkey, "💪 Полная тренировка!"
    elif fatigue == 3:
        return wkey, ("🟡 Снизь веса на 20%, 3 подхода вместо 4." if wkey != "К"
                      else "🟡 Снизь темп кардио.")
    else:
        if wkey in ("А","Б","В"):
            return "К", "🔴 Высокая усталость — заменяю силовую на *лёгкое кардио 30 мин*!"
        return wkey, "🔴 Высокая усталость — сократи до 20 мин, пульс не выше 120."

def get_today_workout(uid):
    profile = get_profile(uid)
    if not profile: return "Сначала настрой профиль.", None
    if profile.get("is_sick"):
        return ("🤒 *Болезнь — тренировка отменена!*\n\nМаксимум: прогулка 15-20 мин.\n\n"
                "✅ Нажми «Я выздоровел» когда восстановишься."), None
    weekday  = now_samara().weekday()
    gym_days = profile.get("gym_days") or 3
    schedule = get_week_schedule(profile, gym_days)
    override = profile.get("next_workout_override") or ""
    wkey     = override if override else schedule.get(weekday)
    if not wkey:
        return ("🛌 *Сегодня день отдыха*\n\nМышцы растут во время восстановления.\n"
                "Если <7 000 шагов — выйди на прогулку 30 мин."), None
    fatigue = int(profile.get("fatigue") or 0)
    adj_key, fnote = adjust_workout_for_fatigue(wkey, fatigue)
    if override: save_profile(uid, next_workout_override="")
    name, exercises = WORKOUTS.get(adj_key, WORKOUTS["К"])
    tag  = "🔵" if adj_key == "К" else "🟢"
    orig = f" *(заменена с {wkey} из-за усталости)*" if adj_key != wkey else ""
    text = (f"{tag} *ТРЕНИРОВКА СЕГОДНЯ{orig}*\n*{name}*\n\n"
            f"{fnote}\n\n🏋️ *Упражнения:*\n{exercises}\n\n"
            f"⏰ 18:40-20:00\n\nПосле нажми *«✅ Тренировка завершена»*.")
    return text, adj_key

# ─────────────────────────────────────────
#  РАЦИОН И ПОЛУФАБРИКАТЫ
# ─────────────────────────────────────────

def build_ration(uid, for_tomorrow=False):
    profile = get_profile(uid)
    if not profile: return "Сначала настрой профиль.", 0
    if profile.get("is_sick") and not for_tomorrow:
        return build_sick_ration(), 0
    plan    = calc_plan(profile)
    cal     = plan["calories"]
    weights = get_weights(uid)
    analysis = analyze_progress(weights) if len(weights) >= 2 else None
    if analysis: cal += analysis["cal_change"]
    fatigue = int(profile.get("fatigue") or 0)
    fat_note = ""
    if fatigue >= 4: cal += 100; fat_note = "\n🔴 *+100 ккал на восстановление* (высокая усталость)"
    elif fatigue == 3: fat_note = "\n🟡 Умеренная усталость — не пропускай приёмы"
    p = get_portions(cal)
 # --- НАЧАЛО БЛОКА РАСЧЕТА БЖУ ---
    total_protein = plan['protein']  # Используем запланированный белок как основу
    total_fat = 0
    total_carbs = 0

    # Расчет БЖУ для обеда (Куриная грудка + Гречка)
    breast_grams = p['breast']
    carb_grams = p['carb']
    
if "куриная грудка" in MACRO_PER_100G and breast_grams > 0:
    macro = MACRO_PER_100G["куриная грудка"]
    total_protein += macro.get("белки", 0) * breast_grams / 100
    total_fat += macro.get("жиры", 0) * breast_grams / 100
    total_carbs += macro.get("углеводы", 0) * breast_grams / 100

if "гречка" in MACRO_PER_100G and carb_grams > 0:
    macro = MACRO_PER_100G["гречка"]
    total_protein += macro.get("белки", 0) * carb_grams / 100
    total_fat += macro.get("жиры", 0) * carb_grams / 100
    total_carbs += macro.get("углеводы", 0) * carb_grams / 100
# --- КОНЕЦ БЛОКА РАСЧЕТА БЖУ ---
    status = ""
    if analysis and not for_tomorrow:
        icons = {"fast":"📈","good":"✅","slow":"📉","plateau":"🪨","gain":"🚨"}
        status = f"{icons.get(analysis['status'],'')} {analysis['advice']}\n\n"
    prefix = "📅 *РАЦИОН НА ЗАВТРА*\n" if for_tomorrow else ""
    ration = (
        f"{prefix}{status}"
        f"🍳 *Завтрак:* 3 яйца + 60г овсянки на воде + помидор/огурец\n"
        f"🍗 *Обед:* {p['breast']}г куриной грудки + {p['carb']}г гречки + салат\n"
        f"  💡 Быстро: готовая курица из магазина + гречка в пакете\n"
        f"🍎 *Полдник:* {p['snack']}г куриного филе + 1 фрукт + 20г орехов\n"
        f"  💡 Быстро: консервированная курица + яблоко\n"
        f"🌙 *Ужин:* 180г курицы + {p['dinner']}\n"
        f"  💡 Быстро: замороженные котлеты (без панировки) + замороженные овощи\n\n"
        f"🎯 *~{cal} ккал* | 💪 *~{round(total_protein)}г белка* | ⚖️ *~{round(total_fat)}г жиров* | 🍞 *~{round(total_carbs)}г углеводов*"
        f"{fat_note}\n"
        f"🚶 +1 500 шагов сверх нормы"
    )
    return ration, cal

def build_tomorrow_plan(uid):
    ration, cal = build_ration(uid, for_tomorrow=True)
    profile  = get_profile(uid)
    if not profile: return ration
    tomorrow_wd = (now_samara().weekday() + 1) % 7
    gym_days    = profile.get("gym_days") or 3
    schedule    = get_week_schedule(profile, gym_days)
    wkey        = schedule.get(tomorrow_wd)
    if wkey:
        name = WORKOUTS.get(wkey, WORKOUTS["К"])[0]
        workout_note = f"\n\n🏋️ *Завтра тренировка:* {name} (18:40)\n"
    else:
        workout_note = "\n\n🛌 *Завтра день отдыха* — зал не нужен\n"
    plan = calc_plan(profile)
    p    = get_portions(cal)
    shopping = (
        f"\n\n🛒 *СПИСОК ПОКУПОК НА ЗАВТРА:*\n"
        f"• Куриная грудка/готовая курица — {p['breast']}г\n"
        f"• Яйца — 3 шт\n"
        f"• Овсянка — 60г\n"
        f"• Гречка/гречка в пакете — {p['carb']}г\n"
        f"• Свежие/замороженные овощи — 400г\n"
        f"• Фрукт (яблоко/груша) — 1 шт\n"
        f"• Орехи — 20г\n\n"
        f"⏱️ *Что приготовить заранее сегодня вечером:*\n"
        f"• Отвари {p['breast']+p['snack']}г куриной грудки\n"
        f"• Свари {p['carb']}г гречки или поставь пакет\n"
        f"• Нарежь овощи для салата\n"
        f"• Разложи порции по контейнерам"
    )
    return ration + workout_note + shopping

def build_sick_ration():
    return (
        "🤒 *РАЦИОН ПРИ БОЛЕЗНИ*\n\n"
        "⚠️ Дефицит отменяется — иммунитет важнее!\n\n"
        "🍳 *Завтрак:* 2 яйца + 60г овсянки + мёд 1 ч.л.\n"
        "🍗 *Обед:* куриный бульон 400мл + 150г куриной грудки + 60г риса\n"
        "  💡 Быстро: консервированная курица в бульоне + рис в пакете\n"
        "🍎 *Полдник:* 1 банан + 20г грецких орехов + зелёный чай\n"
        "🌙 *Ужин:* 150г куриной грудки + 200г шпината тушёного\n\n"
        "💧 Минимум 3.5л + имбирный чай\n"
        "🌡️ ~2 000 ккал (поддерживающие)"
    )

def build_cheatmeal_plan(uid):
    profile = get_profile(uid)
    if not profile: return "Сначала настрой профиль."
    plan    = calc_plan(profile)
    # После читмила компенсируем лишние калории на оставшиеся дни
    extra_kcal = 800  # примерный читмил
    compensate = round(extra_kcal / 6)  # на 6 оставшихся дней
    new_cal    = plan["calories"] - compensate
    return (
        f"🍕 *ЧИТМИЛ — ПЛАН*\n\n"
        f"✅ Раз в неделю — можно! Это не срыв, это стратегия.\n\n"
        f"📋 *Правила читмила:*\n"
        f"• Один приём пищи (обед или ужин) — ешь что хочешь\n"
        f"• Общий объём: не более 1 000 ккал за этот приём\n"
        f"• Не делай это два дня подряд\n"
        f"• Пей 3л воды сегодня и завтра\n\n"
        f"📊 *Компенсация на следующие 6 дней:*\n"
        f"Снижаем калории на *{compensate} ккал/день* ({new_cal} вместо {plan['calories']})\n"
        f"Дефицит за неделю сохраняется — похудение не остановится!\n\n"
        f"⚠️ После читмила обязательно тренировка или длинная прогулка."
    )

# ─────────────────────────────────────────
#  ЕЖЕНЕДЕЛЬНЫЙ ОТЧЁТ
# ─────────────────────────────────────────

def build_weekly_report(uid):
    profile = get_profile(uid)
    if not profile: return None
    wd = get_weights(uid)
    sd = get_steps(uid, limit=7)
    if not wd: return None
    plan     = calc_plan(profile)
    curr_w   = wd[-1][0]
    start_w  = wd[0][0]
    target   = profile.get("target_weight") or 92
    loss_total = round(start_w - curr_w, 2)
    remain     = round(curr_w - target, 1)
    pct        = round((start_w-curr_w)/(start_w-target)*100,1) if start_w != target else 100.0
    avg_steps  = round(sum(s for s,_ in sd)/len(sd)) if sd else 0
    weeks_done = round(loss_total / plan["weekly_loss"]) if plan["weekly_loss"] > 0 else 0
    analysis   = analyze_progress(wd) if len(wd) >= 2 else None
    a_text     = analysis["advice"] if analysis else "Недостаточно данных"

    # Сравнение недель
    comp = compare_weeks(uid)
    comp_text = ""
    if comp:
        steps_emoji = "📈" if comp["steps_diff"] >= 0 else "📉"
        comp_text = (f"\n📊 *Сравнение с прошлой неделей:*\n"
                     f"Шаги: {steps_emoji} {'+' if comp['steps_diff']>=0 else ''}{comp['steps_diff']}/день\n"
                     f"Вес: {'📉' if comp['weight_diff']<=0 else '📈'} {comp['weight_diff']:+.1f} кг\n")

    chart = build_weight_chart(uid)
    chart_text = f"\n```\n{chart}\n```\n" if chart else ""

    return (
        f"📬 *ЕЖЕНЕДЕЛЬНЫЙ ОТЧЁТ*\n"
        f"{'─'*20}\n\n"
        f"⚖️ Текущий вес: *{curr_w} кг*\n"
        f"🔥 Сброшено всего: *{loss_total} кг*\n"
        f"🎯 До цели ({target} кг): *{remain} кг*\n"
        f"📊 Прогресс: *{pct}%*\n"
        f"📅 Недель в работе: *~{weeks_done}*\n\n"
        f"👟 Среднее шагов/день: *{avg_steps:,}*\n".replace(",", " ") +
        comp_text +
        f"\n🤖 *Анализ динамики:*\n{a_text}\n"
        + chart_text +
        f"\n💪 {random.choice(MOTIVATIONAL_QUOTES)}"
    )

# ─────────────────────────────────────────
#  ОНБОРДИНГ
# ─────────────────────────────────────────

ONBOARDING_STEPS = [
    ("setup_weight",   "⚖️ Введи свой *текущий вес* (кг), например: `107`"),
    ("setup_target",   "🎯 Введи *желаемый вес* (кг), например: `92`"),
    ("setup_height",   "📏 Введи свой *рост* (см), например: `194`"),
    ("setup_age",      "🎂 Введи свой *возраст* (лет), например: `24`"),
    ("setup_gymdays",  "🏋️ Сколько дней в неделю готов ходить в зал?\nВведи число от 1 до 5"),
    ("setup_pref",     "💬 Что тебе больше нравится в зале?\n\n"
                       "1 — Кардио (эллипс, дорожка)\n"
                       "2 — Силовые (тренажёры, веса)\n"
                       "3 — Без разницы, пусть бот решает"),
    ("setup_deadline", "📅 За сколько *недель* хочешь достичь цели?\nНапример: `12` (3 месяца)"),
    ("setup_driver",   "🚗 Ты водитель или работаешь в основном сидя?\n\n1 — Да (водитель, офис)\n2 — Нет, есть физическая активность на работе"),
]

def start_onboarding(cid, edit=False):
    prefix = "✏️ *Обновляем профиль!*\n\n" if edit else "👤 *Настройка профиля*\n\nОтвечай на вопросы по очереди.\n\n"
    set_state(cid, "setup_weight", extra="edit" if edit else "new")
    bot.send_message(cid, prefix+ONBOARDING_STEPS[0][1], parse_mode="Markdown", reply_markup=cancel_menu())

def handle_onboarding(cid, state, text, extra):
    steps = [s[0] for s in ONBOARDING_STEPS]
    idx   = steps.index(state) if state in steps else -1
    if idx == -1: return False
    try:
        if state == "setup_weight":
            v=float(text.replace(",",".")); assert 30<v<300; save_profile(cid,current_weight=v)
        elif state == "setup_target":
            v=float(text.replace(",",".")); assert 30<v<300; save_profile(cid,target_weight=v)
        elif state == "setup_height":
            v=int(text); assert 100<v<250; save_profile(cid,height=v)
        elif state == "setup_age":
            v=int(text); assert 10<v<100; save_profile(cid,age=v)
        elif state == "setup_gymdays":
            v=int(text); assert 1<=v<=5; save_profile(cid,gym_days=v)
        elif state == "setup_pref":
            assert text in ("1","2","3")
            save_profile(cid,workout_pref={"1":"кардио","2":"силовые","3":"авто"}[text])
        elif state == "setup_deadline":
            v=int(text); assert 1<=v<=104; save_profile(cid,deadline_weeks=v)
        elif state == "setup_driver":
            assert text in ("1","2"); save_profile(cid,is_driver=1 if text=="1" else 0)
    except Exception:
        hints = {"setup_weight":"Вес числом: 107","setup_target":"Цель числом: 92",
                 "setup_height":"Рост в см: 194","setup_age":"Возраст: 24",
                 "setup_gymdays":"Число 1-5","setup_pref":"Введи 1, 2 или 3",
                 "setup_deadline":"Недели: 12","setup_driver":"Введи 1 или 2"}
        bot.send_message(cid, f"⚠️ {hints.get(state,'Некорректный ввод')}", reply_markup=cancel_menu())
        return False
    if idx+1 < len(ONBOARDING_STEPS):
        ns,np = ONBOARDING_STEPS[idx+1]
        set_state(cid, ns, extra=extra)
        bot.send_message(cid, np, parse_mode="Markdown", reply_markup=cancel_menu())
        return False
    set_state(cid, "idle")
    profile = get_profile(cid)
    plan    = calc_plan(profile)
    is_drv = int(profile.get("is_driver") or 0)
    driver_note = "\n🚗 *Водитель:* калораж снижен на ~100 ккал (сидячая работа учтена)" if is_drv else ""
    msg = (f"🎉 *Профиль настроен!*\n\n"
           f"⚖️ Вес: *{profile['current_weight']} кг* → *{profile['target_weight']} кг*\n"
           f"📉 Сбросить: *{round(profile['current_weight']-profile['target_weight'],1)} кг*\n\n"
           f"🔥 Калории: *{plan['calories']} ккал/день*\n"
           f"💪 Белок: *{plan['protein']}г/день*\n"
           f"📈 Темп: *~{plan['weekly_loss']} кг/нед*\n"
           f"🏋️ Тренировки: *{auto_workout_label(profile)}*\n"
           f"⏱️ Расчётный срок: *~{plan['weeks_needed']} нед*\n")
    msg += driver_note
    if plan['weeks_needed'] > (profile.get('deadline_weeks') or 12):
        msg += f"\n⚠️ Разница со сроком: добавь +1 день в зале.\n"
    bot.send_message(cid, msg, parse_mode="Markdown", reply_markup=main_menu(cid))
    if not get_weights(cid):
        add_weight(cid, profile["current_weight"])
    return True

# ─────────────────────────────────────────
#  МЕНЮ
# ─────────────────────────────────────────

def main_menu(uid=None):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    profile = get_profile(uid) if uid else None
    if profile and profile.get("is_sick"):
        m.add(types.KeyboardButton("💊 Режим болезни"), types.KeyboardButton("✅ Я выздоровел"))
    else:
        m.add(types.KeyboardButton("🤒 Я заболел"))
    m.add(
        types.KeyboardButton("🟢 Тренировка сегодня"),
        types.KeyboardButton("✅ Тренировка завершена"),
        types.KeyboardButton("🍽️ Рацион сегодня"),
        types.KeyboardButton("📅 Рацион на завтра"),
        types.KeyboardButton("🥩 Полуфабрикаты"),
        types.KeyboardButton("🍕 Читмил"),
        types.KeyboardButton("🔄 Заменить блюдо"),
        types.KeyboardButton("⚖️ Внести вес"),
        types.KeyboardButton("👟 Внести шаги"),
        types.KeyboardButton("💧 Внести воду"),
        types.KeyboardButton("📈 Мой прогресс"),
        types.KeyboardButton("📊 График веса"),
        types.KeyboardButton("👣 Мои шаги"),
        types.KeyboardButton("📬 Отчёт за неделю"),
        types.KeyboardButton("🕐 Расписание дня"),
        types.KeyboardButton("🍫 Сладкое"),
        types.KeyboardButton("🔥 Жиросжигающие"),
        types.KeyboardButton("💪 Спортпит"),
        types.KeyboardButton("🍓 Фрукты"),
        types.KeyboardButton("👤 Мой профиль"),
        types.KeyboardButton("⚙️ Изменить профиль"),
        types.KeyboardButton("📤 Экспорт данных"),
        types.KeyboardButton("🔔 Напоминания"),
        types.KeyboardButton("❤️ Заменить кардио"),
        types.KeyboardButton("😴 Лечь спать"),
        types.KeyboardButton("⏰ Проснулся"),
        types.KeyboardButton("💤 История сна"),
    )
    return m

def cancel_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(types.KeyboardButton("❌ Отмена"))
    return m

def fatigue_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    m.add(*[types.KeyboardButton(str(i)) for i in range(1,6)])
    return m

def foods_keyboard(flist):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for f in flist: m.add(types.KeyboardButton(f))
    m.add(types.KeyboardButton("❌ Отмена"))
    return m

# ─────────────────────────────────────────
#  НАПОМИНАНИЯ (фоновый поток)
# ─────────────────────────────────────────

REMINDER_SCHEDULE = [
    (7,  0,  "🍳 *Доброе утро!* Время завтрака!\n\n3 яйца + 60г овсянки + помидор\n\n{quote}"),
    (9,  0,  "💧 Выпей стакан воды! (1/8)"),
    (11, 0,  "💧 Выпей стакан воды! (2/8)"),
    (12, 0,  "🍗 *Время обеда!*\n\nКурица + гречка + салат"),
    (13, 30, "💧 Выпей стакан воды! (3/8)"),
    (15, 0,  "💧 Выпей стакан воды! (4/8)"),
    (16, 0,  "🍎 *Время полдника!*\n\nКуриное филе + фрукт + орехи"),
    (17, 30, "💧 Выпей стакан воды! (5/8)"),
    (18, 30, "🏋️ Скоро зал! Не забудь взять воду и форму."),
    (19, 30, "💧 Выпей стакан воды! (6/8)"),
    (20, 30, "🌙 *Время ужина!*\n\nКурица + тушёные овощи. После — только вода."),
    (22, 0,  "💧 Выпей стакан воды! (7/8)"),
    (22, 30, "😴 До сна 30 минут! Нажми «😴 Лечь спать» когда будешь готовиться ко сну."),
]

def reminder_worker():
    sent_today = set()
    while True:
        now = now_samara()
        key = (now.hour, now.minute)
        for h, mi, template in REMINDER_SCHEDULE:
            if key == (h, mi) and key not in sent_today:
                sent_today.add(key)
                users = get_all_users()
                for uid in users:
                    profile = get_profile(uid)
                    if not profile or not profile.get("reminders_enabled", 1):
                        continue
                    try:
                        quote = random.choice(MOTIVATIONAL_QUOTES)
                        msg   = template.replace("{quote}", quote)
                        # Для воды показываем сколько уже выпито
                        if "стакан воды" in msg:
                            glasses = get_water_today(uid)
                            msg += f"\n💧 Сегодня уже: *{glasses}* стак. из 8"
                        bot.send_message(uid, msg, parse_mode="Markdown")
                    except Exception:
                        pass
        # Сбрасываем в полночь
        if now.hour == 0 and now.minute == 0:
            sent_today.clear()
        # Еженедельный отчёт — воскресенье 9:00
        if now.weekday() == 6 and now.hour == 9 and now.minute == 0 and ("weekly",) not in sent_today:
            sent_today.add(("weekly",))
            users = get_all_users()
            for uid in users:
                profile = get_profile(uid)
                if not profile or not profile.get("reminders_enabled", 1):
                    continue
                try:
                    report = build_weekly_report(uid)
                    if report:
                        bot.send_message(uid, report, parse_mode="Markdown")
                except Exception:
                    pass
        time.sleep(30)

# ─────────────────────────────────────────
#  ХЭНДЛЕРЫ
# ─────────────────────────────────────────

@bot.message_handler(commands=['start','help'])
def send_welcome(message):
    cid = message.chat.id
    profile = get_profile(cid)
    if not profile:
        bot.send_message(cid,
            "👋 Привет! Я *Инженерный трекер жиросжигания PRO v7*\n\n"
            "Давай настроим твой персональный план 👇",
            parse_mode="Markdown")
        start_onboarding(cid)
    else:
        plan = calc_plan(profile)
        sick = "\n\n🤒 *Режим болезни активен*" if profile.get("is_sick") else ""
        bot.send_message(cid,
            f"👋 С возвращением!\n\n"
            f"🎯 Цель: *{profile['current_weight']} → {profile['target_weight']} кг*\n"
            f"🔥 Калории: *{plan['calories']} ккал/день*\n"
            f"📈 Темп: *~{plan['weekly_loss']} кг/нед*{sick}",
            parse_mode="Markdown", reply_markup=main_menu(cid))

@bot.message_handler(func=lambda m: True)
def router(message):
    cid  = message.chat.id
    text = message.text.strip()
    state, extra = get_state(cid)

    if text == "❌ Отмена":
        set_state(cid, "idle")
        bot.send_message(cid, "Отменено.", reply_markup=main_menu(cid))
        return

    # Онбординг
    if state in [s[0] for s in ONBOARDING_STEPS]:
        handle_onboarding(cid, state, text, extra)
        return

    # Ввод веса
    if state == "waiting_weight":
        try:
            w = float(text.replace(",",".")); assert 30<w<300
            add_weight(cid, w); save_profile(cid, current_weight=w)
            set_state(cid, "idle")
            wd = get_weights(cid); profile = get_profile(cid)
            target = profile["target_weight"] if profile else 92.0
            loss   = round(wd[0][0]-w,2); remain = round(w-target,1)
            pct    = round((wd[0][0]-w)/(wd[0][0]-target)*100,1) if wd[0][0]!=target else 100.0
            resp = (f"✅ Вес *{w} кг* сохранён! ({now_samara().strftime('%d.%m.%Y')})\n\n"
                    f"📉 Сброшено: *{loss} кг* | До цели: *{remain} кг* | Прогресс: *{pct}%*")
            if len(wd)>=2:
                a=analyze_progress(wd)
                if a:
                    resp+=f"\n\n─────────────\n🤖 {a['advice']}"
                    if a["cal_change"]!=0:
                        d="увеличен" if a["cal_change"]>0 else "снижен"
                        resp+=f"\n📋 Рацион {d} на *{abs(a['cal_change'])} ккал*."
            bot.send_message(cid, resp, parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "Введи число, например: 105.7")
        return

    # Ввод шагов
    if state == "waiting_steps":
        try:
            s=int(text.replace(" ","").replace(",","")); assert 0<s<100000
            add_steps(cid,s); set_state(cid,"idle")
            profile=get_profile(cid)
            sick_note=" (при болезни норма — 5 000)" if profile and profile.get("is_sick") else ""
            v=("🔥 Отличный день! Кардио можно пропустить." if s>=12000 else
               "✅ Хороший уровень!" if s>=8000 else
               "🟡 Добавь вечернюю прогулку." if s>=5000 else
               "🔴 Малоподвижный день. Выйди на прогулку.")
            bot.send_message(cid,f"👟 *{s:,} шагов*{sick_note}\n\n{v}".replace(",", " "),
                             parse_mode="Markdown",reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid,"Введи число шагов, например: 8500")
        return

    # Ввод воды
    if state == "waiting_water":
        try:
            g=int(text); assert 0<g<=20
            add_water(cid,g); set_state(cid,"idle")
            total=get_water_today(cid)
            ml=total*250
            bar="💧"*min(total,8)+"⬜"*max(0,8-total)
            v=("✅ Норма выполнена!" if total>=8 else
               f"Ещё {8-total} стак. до нормы")
            bot.send_message(cid,
                f"💧 *+{g} стакан(а) воды*\n\nСегодня: *{total}/8* стаканов ({ml}мл)\n{bar}\n{v}",
                parse_mode="Markdown",reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid,"Введи число стаканов (1-8)")
        return

    # Оценка усталости
    if state == "rate_fatigue":
        try:
            f=int(text); assert 1<=f<=5
            wtype=extra or "тренировка"
            save_profile(cid,fatigue=f,last_workout_date=now_samara().strftime("%Y-%m-%d %H:%M"))
            log_workout(cid,wtype,f); set_state(cid,"idle")
            if f<=2: msg=f"💪 Усталость {f}/5 — отлично! Следующая по плану."
            elif f==3: msg=f"🟡 Усталость {f}/5 — умеренная. Если завтра силовая — снизим веса."
            else:
                msg=f"🔴 Усталость {f}/5 — высокая!\nЕсли завтра силовая — *заменю на кардио*.\n+100 ккал на восстановление."
                save_profile(cid,next_workout_override="К")
            bot.send_message(cid,msg,parse_mode="Markdown",reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid,"Введи число от 1 до 5",reply_markup=fatigue_menu())
        return

    # Проверка усталости перед тренировкой
    if state == "fatigue_check_before" or text in ("😊 Хорошо","😐 Немного устал","😓 Устал сильно"):
        if text=="😊 Хорошо":
            set_state(cid,"idle")
            wt,_=get_today_workout(cid)
            bot.send_message(cid,wt,parse_mode="Markdown",reply_markup=main_menu(cid))
        elif text=="😐 Немного устал":
            save_profile(cid,fatigue=3); set_state(cid,"idle")
            wt,_=get_today_workout(cid)
            bot.send_message(cid,"🟡 Понял, снизим нагрузку.\n\n"+wt,parse_mode="Markdown",reply_markup=main_menu(cid))
        elif text=="😓 Устал сильно":
            save_profile(cid,fatigue=5,next_workout_override="К"); set_state(cid,"idle")
            wt,_=get_today_workout(cid)
            bot.send_message(cid,"🔴 Заменяю на лёгкое кардио.\n\n"+wt,parse_mode="Markdown",reply_markup=main_menu(cid))
        return

    # Замена блюда — шаг 1: выбор приёма
    if state == "subst_choose_meal":
        if text in MEAL_FOODS:
            set_state(cid,"subst_choose_from",extra=text)
            flat=[f for g in MEAL_FOODS[text].values() for f in g]
            bot.send_message(cid,f"Выбран приём: *{text}*\n\nКакой продукт заменить?",
                             parse_mode="Markdown",reply_markup=foods_keyboard(flat))
        else:
            bot.send_message(cid,"Выбери приём пищи из кнопок.")
        return

    # Замена блюда — шаг 2: выбор продукта
    if state == "subst_choose_from":
        meal=extra
        flat=[f for g in MEAL_FOODS.get(meal,{}).values() for f in g]
        if text in flat:
            grp=find_group(text)
            grams=DEFAULT_PORTIONS.get(text,100)
            kcal=round(KCAL_PER_100G.get(text,150)*grams/100)
            alts=[f for f in FOOD_GROUPS.get(grp,[]) if f!=text]
            set_state(cid,"subst_choose_to",extra=f"{meal}|{text}")
            bot.send_message(cid,
                f"Заменяем: *{text}* ({grams}г = {kcal} ккал)\nПриём: *{meal}*\n\nЧем заменить?",
                parse_mode="Markdown",reply_markup=foods_keyboard(alts))
        else:
            bot.send_message(cid,"Выбери продукт из кнопок.")
        return

    # Замена блюда — шаг 3: выбор замены
    if state == "subst_choose_to":
        parts=extra.split("|",1); meal=parts[0]; from_food=parts[1] if len(parts)>1 else ""
        all_f=[f for g in FOOD_GROUPS.values() for f in g]
        if text in all_f:
            if text==from_food:
                bot.send_message(cid,"Это тот же продукт 😄 Выбери другой."); return
            to_g,kcal=calc_equivalent(from_food,text)
            warn=SEMIFAB_WARNINGS.get(text,"")
            warn_text=f"\n\n{warn}" if warn else ""
            set_state(cid,"idle")
            bot.send_message(cid,
                f"✅ *Замена в {meal}:*\n\n"
                f"❌ {DEFAULT_PORTIONS.get(from_food,100)}г *{from_food}*\n"
                f"✅ {to_g}г *{text}*\n\n"
                f"🔁 Калорийность сохранена: *{kcal} ккал*{warn_text}",
                parse_mode="Markdown",reply_markup=main_menu(cid))
        else:
            bot.send_message(cid,"Выбери продукт из кнопок.")
        return

    # ════════════════════════════════════════
    #  КНОПКИ МЕНЮ
    # ════════════════════════════════════════

    # Болезнь
    if text=="🤒 Я заболел":
        save_profile(cid,is_sick=1,sick_since=now_samara().strftime("%Y-%m-%d"),fatigue=0)
        bot.send_message(cid,
            "🤒 *Режим болезни активирован*\n\n"
            "• Тренировки отменены\n• Дефицит калорий снят\n"
            "• Рацион переключён на лёгкий\n• Норма шагов снижена до 5 000\n"
            "• Напоминания адаптированы\n\nСкорейшего выздоровления! 💊",
            parse_mode="Markdown",reply_markup=main_menu(cid))

    elif text=="💊 Режим болезни":
        profile=get_profile(cid)
        since=profile.get("sick_since","") if profile else ""
        days=0
        if since:
            try: days=(now_samara().date()-datetime.strptime(since,"%Y-%m-%d").date()).days
            except Exception: pass
        bot.send_message(cid,
            f"💊 *Режим болезни активен*\n"
            f"{'Болеешь: *'+str(days)+' дн.*' if days else ''}\n\n"
            "• Тренировки отменены\n• Рацион: ~2000 ккал\n"
            "• Шаги: не более 5 000/день",
            parse_mode="Markdown",reply_markup=main_menu(cid))

    elif text=="✅ Я выздоровел":
        profile=get_profile(cid)
        since=profile.get("sick_since","") if profile else ""
        days=0
        if since:
            try: days=(now_samara().date()-datetime.strptime(since,"%Y-%m-%d").date()).days
            except Exception: pass
        save_profile(cid,is_sick=0,sick_since="",fatigue=2)
        bot.send_message(cid,
            f"✅ *Отлично, рад что выздоровел!*\n"
            f"{'Болел *'+str(days)+' дн.*' if days else ''}\n\n"
            "⚠️ *Первые 1-2 дня:*\n• Нагрузку снизь на 30%\n"
            "• Начни с кардио\n• Пей 3л воды\n\nУдачи! 💪",
            parse_mode="Markdown",reply_markup=main_menu(cid))

    # Тренировка
    elif text=="🟢 Тренировка сегодня":
        profile=get_profile(cid)
        if profile and profile.get("is_sick"):
            wt,_=get_today_workout(cid)
            bot.send_message(cid,wt,parse_mode="Markdown"); return
        hours=hours_since_last_workout(profile) if profile else 999
        last=get_last_workout(cid)
        if hours<20 and last:
            wt,fat,wd2=last
            set_state(cid,"fatigue_check_before")
            m2=types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=3)
            m2.add(types.KeyboardButton("😊 Хорошо"),
                   types.KeyboardButton("😐 Немного устал"),
                   types.KeyboardButton("😓 Устал сильно"))
            bot.send_message(cid,
                f"⚠️ *Короткий интервал!*\n\nПоследняя: *{wt}* ({int(hours)} ч назад)\n\n"
                "Как себя чувствуешь?",
                parse_mode="Markdown",reply_markup=m2)
            return
        wt,_=get_today_workout(cid)
        bot.send_message(cid,wt,parse_mode="Markdown")

    elif text=="✅ Тренировка завершена":
        profile=get_profile(cid)
        if profile and profile.get("is_sick"):
            bot.send_message(cid,"🤒 Ты болеешь — тренировок нет.",reply_markup=main_menu(cid)); return
        weekday=now_samara().weekday()
        gym_days=(profile.get("gym_days") or 3) if profile else 3
        schedule=get_week_schedule(profile,gym_days)
        wkey=schedule.get(weekday,"К")
        wname=WORKOUTS.get(wkey,WORKOUTS["К"])[0]
        set_state(cid,"rate_fatigue",extra=wname)
        bot.send_message(cid,
            f"🏁 *Завершено!* ({wname})\n\n"
            "Оцени усталость:\n\n"
            "1 — Свежий 💪\n2 — Хорошая усталость ✅\n"
            "3 — Умеренно 🟡\n4 — Сильно 🔴\n5 — Выжат 😵",
            parse_mode="Markdown",reply_markup=fatigue_menu())

    # Рацион
    elif text=="🍽️ Рацион сегодня":
        profile=get_profile(cid)
        if not profile:
            bot.send_message(cid,"Сначала настрой профиль.",parse_mode="Markdown"); return
        ration,cal=build_ration(cid)
        weights=get_weights(cid)
        a=analyze_progress(weights) if len(weights)>=2 else None
        label=("🤒 Режим болезни" if profile.get("is_sick") else
               "📈 Порции увеличены" if a and a["cal_change"]>0 else
               "📉 Порции снижены" if a and a["cal_change"]<0 else "✅ Стандартный рацион")
        bot.send_message(cid,
            f"🍽️ *РАЦИОН НА СЕГОДНЯ*\n{label}\n─────────────\n{ration}\n\n"
            "💡 Для замены нажми «🔄 Заменить блюдо»",
            parse_mode="Markdown")

    elif text=="📅 Рацион на завтра":
        profile=get_profile(cid)
        if not profile:
            bot.send_message(cid,"Сначала настрой профиль."); return
        plan_text=build_tomorrow_plan(cid)
        bot.send_message(cid,plan_text,parse_mode="Markdown")

    # Полуфабрикаты
    elif text=="🥩 Полуфабрикаты":
        bot.send_message(cid,
            "🥩 *ПОЛУФАБРИКАТЫ В РАЦИОНЕ*\n\n"
            "✅ *Можно использовать (одобренные):*\n\n"
            "🍗 *Готовая варёная курица из магазина*\n"
            "  Снять кожу. Белок ~25г/100г. Удобно на обед/ужин.\n\n"
            "🥫 *Консервированная курица/индейка*\n"
            "  В собственном соку, без масла. Белок ~20г/100г.\n"
            "  Идеально для полдника и быстрого обеда.\n\n"
            "🧊 *Замороженные котлеты/фрикадельки из курицы*\n"
            "  ⚠️ Состав: курица >80%, без панировки и крахмала.\n"
            "  Запекать в духовке, не жарить.\n\n"
            "🥦 *Замороженные овощные смеси*\n"
            "  ✅ Без соусов и масла в составе. Удобно на ужин.\n\n"
            "🍚 *Гречка/рис в пакетах*\n"
            "  ✅ 1 пакет ≈ 80г сухой крупы. Экономит время.\n\n"
            "⚠️ *С осторожностью (не чаще 2 раз/нед):*\n\n"
            "🌭 *Куриные сосиски*\n"
            "  Состав: мясо >80%, соль <2г/100г, без крахмала.\n\n"
            "🍗 *Куриные наггетсы*\n"
            "  Только запечённые! Не жареные. Панировка = лишние калории.\n\n"
            "🚫 *Полностью исключить:*\n"
            "• Пельмени, вареники (много теста + жирное мясо)\n"
            "• Готовые блюда с соусами (майонез, сметана)\n"
            "• Колбаса, сардельки (много жира и соли)",
            parse_mode="Markdown")

    # Читмил
    elif text=="🍕 Читмил":
        profile=get_profile(cid)
        if not profile:
            bot.send_message(cid,"Сначала настрой профиль."); return
        if profile.get("is_sick"):
            bot.send_message(cid,"🤒 При болезни читмил не рекомендуется — организм и так под нагрузкой.",
                             reply_markup=main_menu(cid)); return
        curr_week=now_samara().strftime("%Y-W%W")
        if profile.get("cheatmeal_used") and profile.get("cheatmeal_week")==curr_week:
            bot.send_message(cid,
                "⏳ *Читмил на этой неделе уже использован.*\n\n"
                "Следующий доступен на следующей неделе.\n"
                "Держись — это работает! 💪",
                parse_mode="Markdown"); return
        plan_text=build_cheatmeal_plan(cid)
        save_profile(cid,cheatmeal_used=1,cheatmeal_week=curr_week)
        bot.send_message(cid,plan_text,parse_mode="Markdown")

    # Замена блюда
    elif text=="🔄 Заменить блюдо":
        set_state(cid,"subst_choose_meal")
        m2=types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
        for meal in MEAL_FOODS: m2.add(types.KeyboardButton(meal))
        m2.add(types.KeyboardButton("❌ Отмена"))
        bot.send_message(cid,
            "🔄 *Замена продукта*\n\nВ каком приёме пищи?",
            parse_mode="Markdown",reply_markup=m2)

    # Вес
    elif text=="⚖️ Внести вес":
        set_state(cid,"waiting_weight")
        bot.send_message(cid,"⚖️ Введи текущий вес (например: *105.7*)\n\nЛучше утром натощак.",
                         parse_mode="Markdown",reply_markup=cancel_menu())

    # Шаги
    elif text=="👟 Внести шаги":
        profile=get_profile(cid)
        sick_hint="\n🤒 При болезни норма — не более 5 000." if profile and profile.get("is_sick") else ""
        set_state(cid,"waiting_steps")
        bot.send_message(cid,f"👟 Введи количество шагов (например: *8500*){sick_hint}",
                         parse_mode="Markdown",reply_markup=cancel_menu())

    # Вода
    elif text=="💧 Внести воду":
        total=get_water_today(cid)
        set_state(cid,"waiting_water")
        bot.send_message(cid,
            f"💧 Сколько стаканов (250мл) выпил?\n\nСегодня уже: *{total}/8*\n\nВведи число:",
            parse_mode="Markdown",reply_markup=cancel_menu())

    # Прогресс
    elif text=="📈 Мой прогресс":
        wd=get_weights(cid); profile=get_profile(cid)
        if not wd:
            bot.send_message(cid,"История пуста. Внеси вес кнопкой «⚖️ Внести вес»"); return
        lines=[f"• {d[:10]}: *{w} кг*" for w,d in wd]
        target=profile["target_weight"] if profile else 92.0
        loss=round(wd[0][0]-wd[-1][0],2); remain=round(wd[-1][0]-target,1)
        pct=round((wd[0][0]-wd[-1][0])/(wd[0][0]-target)*100,1) if wd[0][0]!=target else 100.0
        sick_note="\n\n🤒 *Режим болезни — похудение приостановлено.*" if profile and profile.get("is_sick") else ""
        msg=("📋 *История взвешиваний:*\n\n"+"\n".join(lines)+
             f"\n\n🔥 Сброшено: *{loss} кг* | До цели: *{remain} кг* | Прогресс: *{pct}%*{sick_note}")
        if len(wd)>=2:
            a=analyze_progress(wd)
            if a: msg+=f"\n\n─────────────\n🤖 {a['advice']}"
        bot.send_message(cid,msg,parse_mode="Markdown")

    # График
    elif text=="📊 График веса":
        chart=build_weight_chart(cid)
        if not chart:
            bot.send_message(cid,"Нужно минимум 2 взвешивания для графика."); return
        bot.send_message(cid,f"📊 *График веса (последние взвешивания):*\n\n```\n{chart}\n```",
                         parse_mode="Markdown")

    # Шаги история
    elif text=="👣 Мои шаги":
        sd=get_steps(cid)
        if not sd:
            bot.send_message(cid,"Нет данных. Нажми «👟 Внести шаги»."); return
        lines=[]; total=0; profile=get_profile(cid)
        is_sick=profile.get("is_sick") if profile else False
        for s,d in sd:
            bar="█"*(s//2000)+"░"*max(0,6-s//2000)
            emoji=("🤒" if s<=5000 else "⚠️" if s<=8000 else "💪") if is_sick else \
                  ("🔥" if s>=12000 else "✅" if s>=8000 else "🟡" if s>=5000 else "🔴")
            lines.append(f"{emoji} {d[:10]}: *{s:,}* {bar}".replace(",", " "))
            total+=s
        avg=round(total/len(sd))
        goal_days=sum(1 for s,_ in sd if s>=(5000 if is_sick else 8000))
        bot.send_message(cid,
            "👣 *Статистика шагов (2 недели):*\n\n"+"\n".join(lines)+
            f"\n\n📊 Среднее: *{avg:,}* шагов/день".replace(",", " ")+
            f"\n🎯 Дней с нормой: *{goal_days}* из {len(sd)}",
            parse_mode="Markdown")

    # Еженедельный отчёт
    elif text=="📬 Отчёт за неделю":
        report=build_weekly_report(cid)
        if not report:
            bot.send_message(cid,"Недостаточно данных. Вноси вес и шаги регулярно!"); return
        bot.send_message(cid,report,parse_mode="Markdown")

    # Расписание
    elif text=="🕐 Расписание дня":
        now2=now_samara(); hour=now2.hour; weekday=now2.weekday()
        profile=get_profile(cid)
        gym_days=(profile.get("gym_days") or 3) if profile else 3
        schedule=get_week_schedule(profile,gym_days)
        is_sick=profile.get("is_sick") if profile else False
        if is_sick:
            gym_block="🤒 *Режим болезни* — зал отменён"; dinner_time="19:00-19:30"
        elif weekday in schedule:
            wk=schedule[weekday]
            gym_block=("🏃 *18:40* — Кардио (45 мин)\n🚿 *19:45* — Душ" if wk=="К"
                       else "🏋️ *18:40* — Силовая (60 мин)\n🚿 *20:00* — Душ")
            dinner_time="20:30-21:00"
        else:
            gym_block="🛌 *День отдыха* — зал не нужен"; dinner_time="19:30-20:00"
        if 6<=hour<7: current="⏰ Время вставать!"
        elif 7<=hour<8: current="🍳 Время завтрака!"
        elif 8<=hour<12: current="💼 Рабочее утро. Обед в 12:00."
        elif 12<=hour<14: current="🍗 Время обеда!"
        elif 14<=hour<16: current="💼 Рабочий день. Полдник в 16:00."
        elif 16<=hour<17: current="🍎 Время полдника!"
        elif 17<=hour<19: current="🏃 Скоро зал!"
        elif 19<=hour<21: current="🍽️ Время тренировки/ужина!"
        elif 21<=hour<23: current="🌙 Ужин. После — только вода."
        else: current="😴 Пора спать! 23:00."
        sick_warn="\n⚠️ *Ты болеешь — отдыхай!*\n" if is_sick else ""
        bot.send_message(cid,
            f"🕐 *РАСПИСАНИЕ ДНЯ* (Самара UTC+4)\n{sick_warn}\n📍 Сейчас: {current}\n\n"
            "⏰ *06:45* — Подъём\n🍳 *07:10* — Завтрак\n💼 *07:30-12:00* — Работа\n"
            "🍗 *12:00-13:00* — Обед\n💼 *13:00-16:00* — Работа\n"
            "🍎 *16:00-16:30* — Полдник ⚠️ не позже!\n💼 *16:30-18:40* — Работа/дорога\n"
            f"{gym_block}\n🌙 *{dinner_time}* — Ужин\n💧 *До 23:00* — вода\n😴 *23:00* — Сон ✅",
            parse_mode="Markdown")

    # Сладкое
    elif text=="🍫 Сладкое":
        hour=now_samara().hour; profile=get_profile(cid)
        is_sick=profile.get("is_sick") if profile else False
        if is_sick: timing="🤒 При болезни — мёд в чай разрешён в любое время."
        elif 12<=hour<17: timing="✅ Сейчас хорошее время!"
        elif 17<=hour<20: timing="🟡 Ещё можно — последний шанс."
        else: timing="🚫 После 20:00 не стоит."
        bot.send_message(cid,
            f"🍫 *СЛАДКОЕ БЕЗ ВРЕДА*\n\n{timing}\n\n"
            "✅ *До 150-200 ккал/день:*\n• Горький шоколад 70%+ — 25г = *138 ккал* ⭐\n"
            "• Зефир — 1 шт = *75 ккал*\n• Финики — 3 шт = *82 ккал*\n• Мёд — 1 ч.л. = *23 ккал*\n\n"
            "🚫 Исключить: соки, торты, конфеты с начинкой\n\n"
            "📌 После еды · не позже 20:00 · 3-4 раза в неделю",
            parse_mode="Markdown")

    # Жиросжигающие
    elif text=="🔥 Жиросжигающие":
        profile=get_profile(cid); is_sick=profile.get("is_sick") if profile else False
        sick_note=("\n\n🤒 *При болезни:* имбирь + мёд + зелёный чай. Кофе исключить.") if is_sick else ""
        bot.send_message(cid,
            f"🔥 *ПРОДУКТЫ ДЛЯ ЖИРОСЖИГАНИЯ*\n\n"
            "⚡ *Ускоряют метаболизм:*\n• Зелёный чай — 2-3 чашки без сахара\n"
            "• Кофе без сахара — за 30 мин до тренировки\n• Острый перец — в еду\n"
            "• Имбирь — в чай\n\n"
            "💪 *Снижают кортизол:*\n• Горький шоколад 70%+ — 25г после обеда\n"
            "• Грецкие орехи — омега-3\n• Черника/голубика — 50г/день\n\n"
            f"💧 *3л воды = +30% к жиросжиганию*{sick_note}",
            parse_mode="Markdown")
        
    elif text == "🍓 Фрукты":
        # Получаем список фруктов из словаря FOOD_GROUPS
        fruit_list = FOOD_GROUPS.get("фрукты", [])
        # Добавляем к списку кнопку "Отмена" для удобства
        markup = foods_keyboard(fruit_list + ["❌ Отмена"])
        bot.send_message(cid, "🍓 *СПИСОК ФРУКТОВ*\nВыбери интересующий:", parse_mode="Markdown", reply_markup=markup)

    elif text == "💪 Спортпит":
        # Получаем список спортивного питания из словаря FOOD_GROUPS
        sportpit_list = FOOD_GROUPS.get("спортпит", [])
        # Добавляем к списку кнопку "Отмена"
        markup = foods_keyboard(sportpit_list + ["❌ Отмена"])
        bot.send_message(cid, "💪 *СПИСОК СПОРТПИТА*\nВыбери интересующий:", parse_mode="Markdown", reply_markup=markup)

        # --- НОВЫЙ КОД ДЛЯ ОБРАБОТКИ ВЫБОРА ---

    # Этот блок сработает, если ты нажмешь на кнопку с названием фрукта (например, "Яблоко")
    elif text in FOOD_GROUPS.get("фрукты", []):
        grams = DEFAULT_PORTIONS.get(text, 100)
        kcal = round(KCAL_PER_100G.get(text, 150) * grams / 100)
        bot.send_message(cid,
            f"🍎 *{text.capitalize()}*\n"
            f"📊 Порция: {grams}г\n"
            f"🔥 Калорийность: {kcal} ккал",
            parse_mode="Markdown")

    # Этот блок сработает, если ты нажмешь на кнопку с названием продукта спортпита (например, "Протеиновый батончик")
    elif text in FOOD_GROUPS.get("спортпит", []):
        grams = DEFAULT_PORTIONS.get(text, 100)
        kcal = round(KCAL_PER_100G.get(text, 150) * grams / 100)
        bot.send_message(cid,
            f"🥤 *{text}*\n"
            f"📊 Порция: {grams}г\n"
            f"🔥 Калорийность: {kcal} ккал",
            parse_mode="Markdown")
        
    # Профиль
    elif text=="👤 Мой профиль":
        profile=get_profile(cid)
        if not profile:
            bot.send_message(cid,"Профиль не настроен. Нажми *⚙️ Изменить профиль*",parse_mode="Markdown"); return
        plan=calc_plan(profile); wd=get_weights(cid)
        curr_w=wd[-1][0] if wd else profile["current_weight"]
        loss=round(profile["current_weight"]-curr_w,1)
        fatigue=int(profile.get("fatigue") or 0)
        fat_label={0:"—",1:"😊 Отлично",2:"✅ Хорошо",3:"🟡 Умеренная",
                   4:"🔴 Высокая",5:"😵 Очень высокая"}.get(fatigue,"—")
        water=get_water_today(cid)
        bot.send_message(cid,
            f"👤 *МОЙ ПРОФИЛЬ*\n\n"
            f"⚖️ Стартовый: *{profile['current_weight']} кг* | Текущий: *{curr_w} кг* (−{loss} кг)\n"
            f"🎯 Цель: *{profile['target_weight']} кг*\n"
            f"📏 Рост: *{profile['height']} см* | 🎂 Возраст: *{profile['age']} лет*\n\n"
            f"🏋️ Зал: *{profile['gym_days']} дней/нед* — {auto_workout_label(profile)}\n"
            f"📅 Срок: *{profile['deadline_weeks']} нед*\n\n"
            f"🔥 Калории: *{plan['calories']} ккал/день*\n"
            f"💪 Белок: *{plan['protein']}г/день*\n"
            f"📈 Темп: *~{plan['weekly_loss']} кг/нед*\n\n"
            f"😴 Усталость: *{fat_label}*\n"
            f"🏥 Здоровье: *{'🤒 Болезнь' if profile.get('is_sick') else '✅ Здоров'}*\n"
            f"🚗 Профиль: *{'Водитель (сидячая работа)' if profile.get('is_driver') else 'Обычная активность'}*\n"
            f"💧 Вода сегодня: *{water}/8* стаканов",
            parse_mode="Markdown")

    elif text=="⚙️ Изменить профиль":
        start_onboarding(cid,edit=True)

    # Напоминания
    elif text=="🔔 Напоминания":
        profile=get_profile(cid)
        if not profile:
            bot.send_message(cid,"Сначала настрой профиль."); return
        enabled=profile.get("reminders_enabled",1)
        m2=types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
        m2.add(types.KeyboardButton("🔔 Включить напоминания" if not enabled else "🔕 Выключить напоминания"))
        m2.add(types.KeyboardButton("❌ Отмена"))
        status="✅ Включены" if enabled else "❌ Выключены"
        bot.send_message(cid,
            f"🔔 *НАПОМИНАНИЯ*\n\nСтатус: *{status}*\n\n"
            "📋 Расписание напоминаний (Самара):\n"
            "• 07:00 — Завтрак 🍳\n• 09:00, 11:00, 13:30, 15:00, 17:30, 19:30, 22:00 — Вода 💧\n"
            "• 12:00 — Обед 🍗\n• 16:00 — Полдник 🍎\n"
            "• 18:30 — Напоминание о зале 🏋️\n• 20:30 — Ужин 🌙\n"
            "• 22:30 — Скоро сон 😴\n• Воскресенье 09:00 — Еженедельный отчёт 📬",
            parse_mode="Markdown",reply_markup=m2)

    elif text in ("🔔 Включить напоминания","🔕 Выключить напоминания"):
        profile=get_profile(cid)
        new_val=1 if text=="🔔 Включить напоминания" else 0
        save_profile(cid,reminders_enabled=new_val)
        status="✅ Включены" if new_val else "❌ Выключены"
        bot.send_message(cid,f"🔔 Напоминания: *{status}*",parse_mode="Markdown",reply_markup=main_menu(cid))

    # Экспорт
    elif text=="📤 Экспорт данных":
        wd=get_weights(cid); sd=get_steps(cid,limit=100)
        output=io.StringIO()
        w=csv.writer(output)
        w.writerow(["Тип","Значение","Дата"])
        for wv,d in wd: w.writerow(["вес",wv,d])
        for sv,d in sd: w.writerow(["шаги",sv,d])
        output.seek(0)
        data=output.getvalue().encode("utf-8-sig")
        bio=io.BytesIO(data)
        bio.name="my_data.csv"
        bot.send_document(cid,bio,caption="📊 Твои данные: вес и шаги")

    # ── Лечь спать ──
    elif text == "😴 Лечь спать":
        profile = get_profile(cid)
        now2    = now_samara()
        hour    = now2.hour
        # Предупреждение если ложится слишком поздно
        if hour >= 1 and hour < 6:
            late_warn = f"\n⚠️ Уже {hour}:00 — это очень поздно! Завтра кортизол будет высоким."
        elif hour >= 0 and hour < 23:
            late_warn = f"\n✅ {now2.strftime('%H:%M')} — хорошее время для сна."
        else:
            late_warn = ""
        sleep_time = now2.strftime("%H:%M")
        set_state(cid, "waiting_wake", extra=sleep_time)
        bot.send_message(cid,
            f"😴 *Спокойной ночи!*{late_warn}\n\n"
            f"Время отбоя: *{sleep_time}* (самарское)\n\n"
            f"Когда проснёшься — нажми *«⏰ Проснулся»* и бот:\n"
            f"• Посчитает продолжительность сна\n"
            f"• Скорректирует рацион и тренировку\n"
            f"• Покажет прогноз восстановления",
            parse_mode="Markdown", reply_markup=cancel_menu())

    # ── Проснулся ──
    elif text == "⏰ Проснулся":
        state2, sleep_time = get_state(cid)
        if state2 != "waiting_wake" or not sleep_time:
            # Не было нажатия "лечь спать" — просим ввести вручную
            set_state(cid, "manual_sleep_entry")
            bot.send_message(cid,
                "⏰ *Доброе утро!*\n\n"
                "Ты не нажал «😴 Лечь спать» вчера вечером.\n"
                "Введи время когда лёг (например: *23:00*) и я посчитаю сон:",
                parse_mode="Markdown", reply_markup=cancel_menu())
            return
        set_state(cid, "rate_sleep_quality", extra=sleep_time)
        now2      = now_samara()
        wake_time = now2.strftime("%H:%M")
        # Считаем продолжительность
        try:
            sh, sm = map(int, sleep_time.split(":"))
            wh, wm = map(int, wake_time.split(":"))
            sleep_mins = sh * 60 + sm
            wake_mins  = wh * 60 + wm
            if wake_mins < sleep_mins:
                wake_mins += 24 * 60  # переход через полночь
            duration = round((wake_mins - sleep_mins) / 60, 1)
        except Exception:
            duration = 7.0
        analysis = analyze_sleep(duration, 3)
        set_state(cid, "rate_sleep_quality", extra=f"{sleep_time}|{wake_time}|{duration}")
        bot.send_message(cid,
            f"⏰ *Доброе утро!*\n\n"
            f"😴 Лёг: *{sleep_time}* | ⏰ Встал: *{wake_time}*\n"
            f"🌙 Продолжительность: *{duration} ч*\n\n"
            f"{analysis['note']}\n\n"
            f"Оцени качество сна (1-5):\n"
            f"1 — Ужасно 😵\n2 — Плохо 😞\n3 — Нормально 😐\n"
            f"4 — Хорошо 😊\n5 — Отлично 🌟",
            parse_mode="Markdown", reply_markup=fatigue_menu())

    # ── Ручной ввод времени сна ──
    elif state == "manual_sleep_entry":
        try:
            parts = text.strip().replace(".", ":").split(":")
            assert len(parts) == 2
            h, m = int(parts[0]), int(parts[1])
            assert 0 <= h <= 23 and 0 <= m <= 59
            sleep_time = f"{h:02d}:{m:02d}"
            now2       = now_samara()
            wake_time  = now2.strftime("%H:%M")
            wh, wm     = now2.hour, now2.minute
            sleep_mins = h * 60 + m
            wake_mins  = wh * 60 + wm
            if wake_mins < sleep_mins:
                wake_mins += 24 * 60
            duration = round((wake_mins - sleep_mins) / 60, 1)
            analysis = analyze_sleep(duration, 3)
            set_state(cid, "rate_sleep_quality", extra=f"{sleep_time}|{wake_time}|{duration}")
            bot.send_message(cid,
                f"😴 Лёг: *{sleep_time}* | ⏰ Встал: *{wake_time}*\n"
                f"🌙 Продолжительность: *{duration} ч*\n\n"
                f"{analysis['note']}\n\n"
                f"Оцени качество сна (1-5):\n"
                f"1 — Ужасно 😵 · 2 — Плохо · 3 — Нормально · 4 — Хорошо · 5 — Отлично 🌟",
                parse_mode="Markdown", reply_markup=fatigue_menu())
        except Exception:
            bot.send_message(cid, "Введи время в формате ЧЧ:ММ, например: *23:00*",
                             parse_mode="Markdown")
        return

    # ── Оценка качества сна ──
    elif state == "rate_sleep_quality":
        try:
            quality = int(text); assert 1 <= quality <= 5
            parts      = extra.split("|")
            sleep_time = parts[0] if len(parts) > 0 else "23:00"
            wake_time  = parts[1] if len(parts) > 1 else "07:00"
            duration   = float(parts[2]) if len(parts) > 2 else 7.0
            analysis   = analyze_sleep(duration, quality)
            # Сохраняем сон
            log_sleep(cid, sleep_time, wake_time, duration, quality)
            # Корректируем усталость в профиле
            save_profile(cid, fatigue=analysis["fat_adj"])
            if analysis["cal_adj"] > 0:
                save_profile(cid, fatigue=analysis["fat_adj"])
            set_state(cid, "idle")
            # Формируем итог
            stars = "⭐" * quality
            msg = (
                f"✅ *Сон записан!*\n\n"
                f"🌙 *{sleep_time}* → ⏰ *{wake_time}* = *{duration} ч* {stars}\n\n"
                f"{analysis['note']}\n"
            )
            if analysis["cal_adj"] > 0:
                msg += (f"\n🍽️ *Рацион скорректирован:* +{analysis['cal_adj']} ккал сегодня "
                        f"(нажми «Рацион сегодня» — порции уже обновлены)")
            if analysis["fat_adj"] >= 4:
                msg += "\n🏋️ *Тренировка:* нажми «Тренировка сегодня» — план уже скорректирован"
            msg += f"\n\n{MOTIVATIONAL_QUOTES[quality-1]}"
            bot.send_message(cid, msg, parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "Введи число от 1 до 5", reply_markup=fatigue_menu())
        return

    # ── История сна ──
    elif text == "❤️ Заменить кардио":
        profile = get_profile(cid)
        if not profile:
            bot.send_message(cid, "Сначала настрой профиль."); return
        if profile.get("is_sick"):
            bot.send_message(cid,
                "🤒 При болезни эта замена не рекомендуется — "
                "любая нагрузка замедляет выздоровление.",
                reply_markup=main_menu(cid)); return
        # Засчитываем как кардио и логируем
        save_profile(cid,
            last_workout_date=now_samara().strftime("%Y-%m-%d %H:%M"),
            fatigue=2)
        log_workout(cid, "Интимная близость (кардио)", 2)
        wd = get_weights(cid)
        a  = analyze_progress(wd) if len(wd) >= 2 else None
        cal_note = ""
        if a and a["cal_change"] != 0:
            d = "увеличен" if a["cal_change"] > 0 else "снижен"
            cal_note = f"\n📋 Рацион {d} на {abs(a['cal_change'])} ккал по динамике веса."
        bot.send_message(cid,
            "❤️ *Кардио засчитано!*\n\n"
            "🏃 *Эквивалент нагрузки:*\n"
            "• Калории: ~200-350 ккал (как 30-40 мин эллипса)\n"
            "• Пульс: 90-130 уд/мин — зона жиросжигания ✅\n"
            "• Гормоны: окситоцин снижает кортизол — бонус для похудения 🎯\n\n"
            "💧 *Сейчас:* выпей 400-500мл воды\n"
            "🍗 *Перекус через 30 мин:* 100г куриного филе или 2 яйца\n"
            f"(белок важен для восстановления){cal_note}\n\n"
            "📊 Тренировка записана в историю.",
            parse_mode="Markdown", reply_markup=main_menu(cid))

    elif text == "💤 История сна":
        stats = build_sleep_stats(cid)
        if not stats:
            bot.send_message(cid,
                "💤 Нет данных о сне.\n\n"
                "Нажимай *«😴 Лечь спать»* перед сном и *«⏰ Проснулся»* утром — "
                "бот будет вести статистику.",
                parse_mode="Markdown")
            return
        last = get_last_sleep(cid)
        last_analysis = ""
        if last:
            a = analyze_sleep(last[2] or 7, last[3] or 3)
            last_analysis = f"\n🤖 *Последний анализ:* {a['note']}"
        bot.send_message(cid,
            f"💤 *СТАТИСТИКА СНА (7 дней)*\n\n{stats}{last_analysis}\n\n"
            f"💡 Цель: *7.5-8 часов* в 23:00 — максимальное жиросжигание.",
            parse_mode="Markdown")

    else:
        bot.send_message(cid,"Используй кнопки меню.",reply_markup=main_menu(cid))

if __name__ == '__main__':
    init_db()
    # Запуск фонового потока напоминаний
    t=threading.Thread(target=reminder_worker,daemon=True)
    t.start()
    print("Бот v7 запущен! Самара UTC+4 | Напоминания | Полуфабрикаты | Читмил | График | Экспорт")
    bot.infinity_polling()
