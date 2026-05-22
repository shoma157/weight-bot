import telebot
from telebot import types
import sqlite3
from datetime import datetime, timezone, timedelta

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

MEAL_FOODS = {
    "🍳 Завтрак": {"белок": ["яйцо"], "углеводы": ["овсянка"], "овощи": ["огурец", "помидор"]},
    "🍗 Обед":    {"белок": ["куриная грудка", "куриное бедро", "индейка", "говядина"],
                   "углеводы": ["гречка", "бурый рис", "булгур", "макароны"],
                   "овощи": ["болгарский перец", "морковь", "шпинат", "огурец"]},
    "🍎 Полдник": {"белок": ["куриная грудка", "индейка"],
                   "орехи": ["миндаль", "грецкий орех", "кешью", "тыквенные семечки"],
                   "фрукты": ["яблоко", "груша", "ягоды"]},
    "🌙 Ужин":    {"белок": ["куриная грудка", "куриное бедро", "индейка", "говядина"],
                   "овощи": ["болгарский перец", "морковь", "шпинат", "стручковая фасоль", "брокколи"]},
}

DEFAULT_PORTIONS = {
    "куриная грудка": 230, "куриное бедро": 230, "индейка": 230, "говядина": 200,
    "яйцо": 186, "гречка": 65, "бурый рис": 65, "булгур": 65, "овсянка": 60, "макароны": 85,
    "болгарский перец": 200, "морковь": 200, "шпинат": 200,
    "стручковая фасоль": 200, "брокколи": 200, "огурец": 100, "помидор": 100,
    "миндаль": 20, "грецкий орех": 20, "кешью": 20, "тыквенные семечки": 20,
    "яблоко": 150, "груша": 150, "ягоды": 100,
}

def calc_equivalent(from_food, to_food, from_grams=None):
    if from_grams is None:
        from_grams = DEFAULT_PORTIONS.get(from_food, 100)
    kcal = KCAL_PER_100G[from_food] * from_grams / 100
    return round(kcal / KCAL_PER_100G[to_food] * 100), round(kcal)

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
        is_sick INTEGER DEFAULT 0, sick_since TEXT DEFAULT "",
        fatigue INTEGER DEFAULT 0,
        last_workout_date TEXT DEFAULT "",
        next_workout_override TEXT DEFAULT "")''')
    c.execute('''CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        workout_type TEXT, fatigue_after INTEGER DEFAULT 0, date TEXT)''')
    # Миграция старых БД — добавляем колонки если их нет
    for col, dflt in [("fatigue","0"), ("last_workout_date","''"), ("next_workout_override","''")]:
        try:
            c.execute(f"ALTER TABLE user_profile ADD COLUMN {col} TEXT DEFAULT {dflt}")
        except Exception:
            pass
    conn.commit(); conn.close()

def get_profile(uid):
    conn = sqlite3.connect("weight_tracker.db")
    row = conn.execute("SELECT * FROM user_profile WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    if not row:
        return None
    keys = ["user_id","current_weight","target_weight","height","age",
            "gym_days","workout_pref","deadline_weeks","is_sick","sick_since",
            "fatigue","last_workout_date","next_workout_override"]
    return dict(zip(keys, row))

def save_profile(uid, **kw):
    conn = sqlite3.connect("weight_tracker.db")
    existing = conn.execute("SELECT user_id FROM user_profile WHERE user_id=?", (uid,)).fetchone()
    if existing:
        sets = ", ".join(f"{k}=?" for k in kw)
        conn.execute(f"UPDATE user_profile SET {sets} WHERE user_id=?", (*kw.values(), uid))
    else:
        kw["user_id"] = uid
        cols = ", ".join(kw.keys())
        vals = ", ".join("?" * len(kw))
        conn.execute(f"INSERT INTO user_profile ({cols}) VALUES ({vals})", list(kw.values()))
    conn.commit(); conn.close()

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
    return row  # (type, fatigue, date) or None

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
    bmr  = 10 * w + 6.25 * h - 5 * a + 5
    mult = {1:1.30, 2:1.35, 3:1.45, 4:1.50, 5:1.55}.get(min(gd,5), 1.45)
    tdee = round(bmr * mult)
    deficit  = min(round(tdee * 0.30), 1200)
    calories = tdee - deficit
    weekly   = round(deficit * 7 / 7700, 2)
    to_lose  = w - (profile.get("target_weight") or 92)
    weeks_needed = round(to_lose / weekly) if weekly > 0 else 999
    return {"bmr": round(bmr), "tdee": tdee, "calories": calories,
            "deficit": deficit, "protein": round(w * 1.8),
            "weekly_loss": weekly, "weeks_needed": weeks_needed}

def get_portions(calories):
    s = calories / 1950
    return {
        "breast":  round(230 * s),
        "carb":    round(65  * s),
        "snack":   round(130 * s),
        "dinner":  "300г тушёных овощей" if s >= 1 else "только овощи без гарнира",
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
    rate = round((prev_w - curr_w) / days * 7, 2)
    if rate > 2.0:
        return {"status":"fast",    "rate":rate, "cal_change":+150,
                "advice":f"⚡ Темп слишком высокий ({rate} кг/нед). *Добавь 150 ккал* к обеду."}
    elif rate >= 0.7:
        return {"status":"good",    "rate":rate, "cal_change":0,
                "advice":f"✅ Идеальный темп ({rate} кг/нед). Ничего не меняй!"}
    elif rate >= 0.1:
        return {"status":"slow",    "rate":rate, "cal_change":-150,
                "advice":f"🐢 Темп медленный ({rate} кг/нед). *Убери гарнир на ужин* (−150 ккал)."}
    elif rate >= -0.1:
        return {"status":"plateau", "rate":rate, "cal_change":-200,
                "advice":f"🪨 Плато. *Убери 200 ккал* и добавь кардио на этой неделе."}
    else:
        return {"status":"gain",    "rate":rate, "cal_change":-250,
                "advice":f"🚨 Вес растёт ({abs(rate)} кг/нед). *Убери полдник* (−250 ккал)."}

# ─────────────────────────────────────────
#  ТРЕНИРОВКИ + УСТАЛОСТЬ
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
          "• ИЛИ ходьба на дорожке: наклон 8%, скорость 5.5 км/ч\n"
          "• Не бегать при весе >100 кг"),
}

def auto_select_workout(profile):
    """Подбирает режим с учётом пожелания пользователя, дней и срочности"""
    if not profile:
        return "кардио_акцент"
    to_lose   = (profile.get("current_weight") or 107) - (profile.get("target_weight") or 92)
    gym_days  = profile.get("gym_days") or 3
    weeks     = profile.get("deadline_weeks") or 12
    user_pref = profile.get("workout_pref") or "авто"
    urgent    = (to_lose / max(weeks, 1)) > 1.5

    if user_pref == "кардио":
        return "кардио_акцент"   # пользователь хочет кардио — даём, но 1 силовая всегда
    if user_pref == "силовые":
        return "баланс" if gym_days >= 3 else "кардио_акцент"
    # авто
    if gym_days <= 3 or urgent:
        return "кардио_акцент"
    return "баланс"

def auto_workout_label(profile):
    if not profile:
        return "автоподбор"
    mode = auto_select_workout(profile)
    gd   = profile.get("gym_days") or 3
    if mode == "кардио_акцент":
        return {1:"только кардио", 2:"только кардио",
                3:"2 кардио + 1 силовая", 4:"3 кардио + 1 силовая"}.get(gd, "3 кардио + 2 силовых")
    return {1:"1 силовая", 2:"1 кардио + 1 силовая",
            3:"1 кардио + 2 силовых", 4:"2 кардио + 2 силовых"}.get(gd, "2 кардио + 3 силовых")

def get_week_schedule(profile, gym_days):
    mode = auto_select_workout(profile)
    gd   = min(gym_days, 5)
    if mode == "кардио_акцент":
        s = {1:{2:"К"}, 2:{1:"К",4:"К"}, 3:{1:"К",3:"К",5:"А"},
             4:{0:"К",2:"К",4:"К",5:"А"}, 5:{0:"К",1:"К",2:"А",3:"К",4:"К"}}
    else:
        s = {1:{2:"А"}, 2:{1:"К",3:"А"}, 3:{0:"А",2:"К",4:"Б"},
             4:{0:"А",1:"К",3:"Б",4:"К"}, 5:{0:"А",1:"К",2:"Б",3:"К",4:"В"}}
    return s.get(gd, s.get(3, {}))

def hours_since_last_workout(profile):
    """Сколько часов прошло с последней тренировки"""
    last = profile.get("last_workout_date") or ""
    if not last:
        return 999
    try:
        last_dt = datetime.strptime(last[:16], "%Y-%m-%d %H:%M").replace(tzinfo=SAMARA_TZ)
        delta   = now_samara() - last_dt
        return delta.total_seconds() / 3600
    except Exception:
        return 999

def check_fatigue_warning(uid):
    """
    Проверяет нужно ли спросить об усталости перед тренировкой.
    Возвращает (нужно_предупредить, текст_предупреждения)
    """
    profile = get_profile(uid)
    if not profile:
        return False, ""

    hours = hours_since_last_workout(profile)
    last_workout = get_last_workout(uid)

    # Менее 20 часов с последней тренировки — спрашиваем
    if hours < 20 and last_workout:
        wtype, fatigue_after, wdate = last_workout
        hours_int = int(hours)
        warn = (
            f"⚠️ *Внимание! Короткий интервал между тренировками*\n\n"
            f"Последняя тренировка: *{wtype}* ({wdate[:10]}, {hours_int} ч назад)\n"
        )
        if fatigue_after >= 4:
            warn += f"😓 После неё ты отметил усталость *{fatigue_after}/5*\n\n"
        warn += "Как себя чувствуешь сейчас?"
        return True, warn
    return False, ""

def adjust_workout_for_fatigue(workout_key, fatigue_level):
    """
    Корректирует тренировку под уровень усталости:
    1-2 = норма, 3 = облегчённая, 4-5 = кардио вместо силовой
    """
    if fatigue_level <= 2:
        return workout_key, "💪 Отлично — полная тренировка!"
    elif fatigue_level == 3:
        if workout_key in ("А", "Б", "В"):
            return workout_key, "🟡 Умеренная усталость — снизь веса на 20%, 3 подхода вместо 4."
        return workout_key, "🟡 Умеренная усталость — снизь темп кардио."
    else:  # 4-5
        if workout_key in ("А", "Б", "В"):
            return "К", "🔴 Высокая усталость — заменяем силовую на *лёгкое кардио 30 мин*. Мышцам нужен отдых!"
        return workout_key, "🔴 Высокая усталость — сократи кардио до 20 мин, пульс не выше 120."

# ─────────────────────────────────────────
#  РАЦИОН
# ─────────────────────────────────────────

def build_ration(uid):
    profile = get_profile(uid)
    if not profile:
        return "Сначала настрой профиль кнопкой *⚙️ Изменить профиль*", 0

    # Режим болезни
    if profile.get("is_sick"):
        return build_sick_ration(), 0

    plan     = calc_plan(profile)
    cal      = plan["calories"]
    weights  = get_weights(uid)
    analysis = analyze_progress(weights) if len(weights) >= 2 else None
    if analysis:
        cal += analysis["cal_change"]

    # Учитываем усталость — если высокая, добавляем +100 ккал на восстановление
    fatigue = int(profile.get("fatigue") or 0)
    if fatigue >= 4:
        cal += 100
        fatigue_note = "\n🔴 *+100 ккал на восстановление* (высокая усталость)"
    elif fatigue == 3:
        fatigue_note = "\n🟡 Умеренная усталость — ешь в срок, не пропускай приёмы"
    else:
        fatigue_note = ""

    p = get_portions(cal)
    status = ""
    if analysis:
        icons = {"fast":"📈","good":"✅","slow":"📉","plateau":"🪨","gain":"🚨"}
        status = f"{icons.get(analysis['status'],'')} {analysis['advice']}\n\n"

    ration = (
        f"{status}"
        f"🍳 *Завтрак:* 3 яйца + 60г овсянки на воде + помидор/огурец\n"
        f"🍗 *Обед:* {p['breast']}г куриной грудки + {p['carb']}г гречки + салат\n"
        f"🍎 *Полдник:* {p['snack']}г куриного филе + 1 фрукт + 20г орехов\n"
        f"🌙 *Ужин:* 180г запечённой курицы + {p['dinner']}\n\n"
        f"🎯 *~{cal} ккал* | 💪 *~{plan['protein']}г белка*"
        f"{fatigue_note}\n"
        f"🚶 +1 500 шагов сверх нормы (~15 мин прогулки)"
    )
    return ration, cal

def build_sick_ration():
    return (
        "🤒 *РАЦИОН ПРИ БОЛЕЗНИ*\n\n"
        "⚠️ Дефицит калорий отменяется — иммунитет важнее!\n\n"
        "🍳 *Завтрак:* 2 варёных яйца + 60г овсянки + мёд 1 ч.л.\n"
        "🍗 *Обед:* куриный бульон 400мл + 150г куриной грудки + 60г риса\n"
        "🍎 *Полдник:* 1 банан + 20г грецких орехов + зелёный чай\n"
        "🌙 *Ужин:* 150г куриной грудки варёной + 200г шпината тушёного\n\n"
        "💧 *Вода:* минимум 3.5л + имбирный чай\n"
        "🌡️ *Калории:* ~2 000 ккал (поддерживающие)\n\n"
        "✅ Когда выздоровеешь — нажми «Я выздоровел» и план восстановится."
    )

def get_today_workout(uid):
    profile = get_profile(uid)
    if not profile:
        return "Сначала настрой профиль кнопкой *⚙️ Изменить профиль*", None

    # Болезнь
    if profile.get("is_sick"):
        return (
            "🤒 *Ты болеешь — тренировка отменена!*\n\n"
            "Любая нагрузка при болезни замедляет выздоровление.\n"
            "Максимум: лёгкая прогулка 15-20 мин если самочувствие позволяет.\n\n"
            "✅ Нажми «Я выздоровел» когда восстановишься."
        ), None

    weekday  = now_samara().weekday()
    gym_days = profile.get("gym_days") or 3
    schedule = get_week_schedule(profile, gym_days)

    # Проверяем override (замена из-за усталости)
    override = profile.get("next_workout_override") or ""
    workout_key = override if override else schedule.get(weekday)

    if not workout_key:
        return (
            "🛌 *Сегодня день отдыха*\n\n"
            "Мышцы растут во время восстановления.\n"
            "Если менее 7 000 шагов — выйди на прогулку 30 мин.\n\n"
            "🍽️ Нажми «Рацион сегодня» для актуальных порций."
        ), None

    # Проверяем усталость и корректируем
    fatigue = int(profile.get("fatigue") or 0)
    adjusted_key, fatigue_note = adjust_workout_for_fatigue(workout_key, fatigue)

    # Если override был использован — сбрасываем его
    if override:
        save_profile(uid, next_workout_override="")

    name, exercises = WORKOUTS.get(adjusted_key, WORKOUTS["К"])
    tag  = "🔵" if adjusted_key == "К" else "🟢"
    orig = f" *(заменена с {workout_key} из-за усталости)*" if adjusted_key != workout_key else ""

    text = (
        f"{tag} *ТРЕНИРОВКА СЕГОДНЯ{orig}*\n"
        f"*{name}*\n\n"
        f"{fatigue_note}\n\n"
        f"🏋️ *Упражнения:*\n{exercises}\n\n"
        f"⏰ Рекомендуемое время: 18:40-20:00\n\n"
        f"После тренировки нажми *«✅ Тренировка завершена»* — "
        f"оценишь усталость и бот учтёт это в следующей тренировке."
    )
    return text, adjusted_key

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
]

def start_onboarding(chat_id, edit=False):
    prefix = "✏️ *Обновляем профиль!*\n\n" if edit else "👤 *Настройка профиля*\n\nОтвечай на вопросы по очереди.\n\n"
    set_state(chat_id, "setup_weight", extra="edit" if edit else "new")
    bot.send_message(chat_id, prefix + ONBOARDING_STEPS[0][1],
                     parse_mode="Markdown", reply_markup=cancel_menu())

def handle_onboarding(chat_id, state, text, extra):
    steps = [s[0] for s in ONBOARDING_STEPS]
    idx   = steps.index(state) if state in steps else -1
    if idx == -1:
        return False
    try:
        if state == "setup_weight":
            v = float(text.replace(",",".")); assert 30 < v < 300
            save_profile(chat_id, current_weight=v)
        elif state == "setup_target":
            v = float(text.replace(",",".")); assert 30 < v < 300
            save_profile(chat_id, target_weight=v)
        elif state == "setup_height":
            v = int(text); assert 100 < v < 250
            save_profile(chat_id, height=v)
        elif state == "setup_age":
            v = int(text); assert 10 < v < 100
            save_profile(chat_id, age=v)
        elif state == "setup_gymdays":
            v = int(text); assert 1 <= v <= 5
            save_profile(chat_id, gym_days=v)
        elif state == "setup_pref":
            assert text in ("1","2","3")
            save_profile(chat_id, workout_pref={"1":"кардио","2":"силовые","3":"авто"}[text])
        elif state == "setup_deadline":
            v = int(text); assert 1 <= v <= 104
            save_profile(chat_id, deadline_weeks=v)
    except Exception:
        hints = {"setup_weight":"Введи вес числом, например: 107",
                 "setup_target":"Введи желаемый вес числом, например: 92",
                 "setup_height":"Введи рост в см, например: 194",
                 "setup_age":"Введи возраст, например: 24",
                 "setup_gymdays":"Введи число от 1 до 5",
                 "setup_pref":"Введи 1, 2 или 3",
                 "setup_deadline":"Введи число недель, например: 12"}
        bot.send_message(chat_id, f"⚠️ {hints.get(state,'Некорректный ввод')}",
                         reply_markup=cancel_menu())
        return False

    if idx + 1 < len(ONBOARDING_STEPS):
        ns, np = ONBOARDING_STEPS[idx + 1]
        set_state(chat_id, ns, extra=extra)
        bot.send_message(chat_id, np, parse_mode="Markdown", reply_markup=cancel_menu())
        return False

    # Завершение онбординга
    set_state(chat_id, "idle")
    profile = get_profile(chat_id)
    plan    = calc_plan(profile)
    msg = (
        f"🎉 *Профиль настроен!*\n\n"
        f"⚖️ Текущий вес: *{profile['current_weight']} кг*\n"
        f"🎯 Цель: *{profile['target_weight']} кг*\n"
        f"📉 Сбросить: *{round(profile['current_weight']-profile['target_weight'],1)} кг*\n\n"
        f"🔥 Калории/день: *{plan['calories']} ккал*\n"
        f"💪 Белок/день: *{plan['protein']}г*\n"
        f"📉 Дефицит: *{plan['deficit']} ккал/день*\n"
        f"📈 Темп: *~{plan['weekly_loss']} кг/нед*\n\n"
        f"🏋️ Зал: *{profile['gym_days']} дней/нед*\n"
        f"💪 Тренировки: *{auto_workout_label(profile)}*\n"
        f"⏱️ Расчётный срок: *~{plan['weeks_needed']} нед*\n"
    )
    if plan['weeks_needed'] > (profile.get('deadline_weeks') or 12):
        gap = plan['weeks_needed'] - profile['deadline_weeks']
        msg += f"\n⚠️ Разница со сроком: *{gap} нед*. Добавь +1 день в зале или снизь калории.\n"
    bot.send_message(chat_id, msg, parse_mode="Markdown", reply_markup=main_menu(chat_id))
    if not get_weights(chat_id):
        add_weight(chat_id, profile["current_weight"])
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

def fatigue_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    m.add(*[types.KeyboardButton(str(i)) for i in range(1, 6)])
    return m

def foods_keyboard(foods_list):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for f in foods_list:
        m.add(types.KeyboardButton(f))
    m.add(types.KeyboardButton("❌ Отмена"))
    return m

# ─────────────────────────────────────────
#  ХЭНДЛЕРЫ
# ─────────────────────────────────────────

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    cid = message.chat.id
    profile = get_profile(cid)
    if not profile:
        bot.send_message(cid,
            "👋 Привет! Я *Инженерный трекер жиросжигания PRO v6*\n\n"
            "Давай настроим твой персональный план — это займёт 1 минуту 👇",
            parse_mode="Markdown")
        start_onboarding(cid)
    else:
        plan = calc_plan(profile)
        sick_note = "\n\n🤒 *Режим болезни активен* — тренировки отменены, рацион облегчён." if profile.get("is_sick") else ""
        bot.send_message(cid,
            f"👋 С возвращением!\n\n"
            f"🎯 Цель: *{profile['current_weight']} → {profile['target_weight']} кг*\n"
            f"🔥 Калории/день: *{plan['calories']} ккал*\n"
            f"📈 Темп: *~{plan['weekly_loss']} кг/нед*{sick_note}",
            parse_mode="Markdown", reply_markup=main_menu(cid))

@bot.message_handler(func=lambda m: True)
def router(message):
    cid  = message.chat.id
    text = message.text.strip()
    state, extra = get_state(cid)

    # ── Отмена ──
    if text == "❌ Отмена":
        set_state(cid, "idle")
        bot.send_message(cid, "Отменено.", reply_markup=main_menu(cid))
        return

    # ── Онбординг ──
    if state in [s[0] for s in ONBOARDING_STEPS]:
        handle_onboarding(cid, state, text, extra)
        return

    # ── Ожидание веса ──
    if state == "waiting_weight":
        try:
            w = float(text.replace(",","."))
            assert 30 < w < 300
            add_weight(cid, w)
            save_profile(cid, current_weight=w)
            set_state(cid, "idle")
            wd      = get_weights(cid)
            profile = get_profile(cid)
            target  = profile["target_weight"] if profile else 92.0
            loss    = round(wd[0][0] - w, 2)
            remain  = round(w - target, 1)
            pct     = round((wd[0][0]-w)/(wd[0][0]-target)*100,1) if wd[0][0] != target else 100.0
            resp = (f"✅ Вес *{w} кг* сохранён! ({now_samara().strftime('%d.%m.%Y')})\n\n"
                    f"📉 Сброшено: *{loss} кг* | До цели: *{remain} кг* | Прогресс: *{pct}%*")
            if len(wd) >= 2:
                a = analyze_progress(wd)
                if a:
                    resp += f"\n\n─────────────\n🤖 {a['advice']}"
                    if a["cal_change"] != 0:
                        d = "увеличен" if a["cal_change"] > 0 else "снижен"
                        resp += f"\n📋 Рацион автоматически {d} на *{abs(a['cal_change'])} ккал*."
            bot.send_message(cid, resp, parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "Введи число, например: 105.7")
        return

    # ── Ожидание шагов ──
    if state == "waiting_steps":
        try:
            s = int(text.replace(" ","").replace(",",""))
            assert 0 < s < 100000
            add_steps(cid, s)
            set_state(cid, "idle")
            profile = get_profile(cid)
            sick_note = " (при болезни шаги не обязательны — отдыхай)" if profile and profile.get("is_sick") else ""
            if s >= 12000:   v = "🔥 Отличный день! Кардио в зале можно пропустить."
            elif s >= 8000:  v = "✅ Хороший уровень активности."
            elif s >= 5000:  v = "🟡 Средняя активность. Добавь вечернюю прогулку."
            else:            v = "🔴 Малоподвижный день. Выйди на прогулку или сделай кардио."
            bot.send_message(cid,
                f"👟 *{s:,} шагов* сохранено!{sick_note}\n\n{v}".replace(",", " "),
                parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "Введи число шагов, например: 8500")
        return

    # ── Оценка усталости после тренировки ──
    if state == "rate_fatigue":
        try:
            f = int(text)
            assert 1 <= f <= 5
            # Сохраняем в профиль и логируем
            wtype = extra or "неизвестно"
            save_profile(cid, fatigue=f, last_workout_date=now_samara().strftime("%Y-%m-%d %H:%M"))
            log_workout(cid, wtype, f)
            set_state(cid, "idle")

            if f <= 2:
                msg = (f"💪 Отлично! Усталость {f}/5 — отличное восстановление.\n"
                       f"Следующая тренировка по плану.")
            elif f == 3:
                msg = (f"🟡 Усталость {f}/5 — умеренная.\n"
                       f"Если следующая тренировка силовая — снизим веса на 20%.")
            else:
                msg = (f"🔴 Усталость {f}/5 — высокая!\n"
                       f"Если следующая тренировка силовая — *заменю её на лёгкое кардио*.\n"
                       f"Рацион скорректирован: +100 ккал на восстановление.")
                # Сохраняем override на следующую тренировку
                save_profile(cid, next_workout_override="К")

            bot.send_message(cid, msg, parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "Введи число от 1 до 5", reply_markup=fatigue_menu())
        return

    # ── Замена блюда: выбор приёма ──
    if state == "subst_choose_meal":
        if text in MEAL_FOODS:
            set_state(cid, "subst_choose_from", extra=text)
            flat = [f for g in MEAL_FOODS[text].values() for f in g]
            bot.send_message(cid,
                f"Выбран приём: *{text}*\n\nКакой продукт заменить?",
                parse_mode="Markdown", reply_markup=foods_keyboard(flat))
        else:
            bot.send_message(cid, "Выбери приём пищи из кнопок.")
        return

    # ── Замена блюда: выбор продукта ──
    if state == "subst_choose_from":
        meal = extra
        flat = [f for g in MEAL_FOODS.get(meal, {}).values() for f in g]
        if text in flat:
            group = find_group(text)
            grams = DEFAULT_PORTIONS.get(text, 100)
            kcal  = round(KCAL_PER_100G[text] * grams / 100)
            alts  = [f for f in FOOD_GROUPS.get(group, []) if f != text]
            set_state(cid, "subst_choose_to", extra=f"{meal}|{text}")
            bot.send_message(cid,
                f"Заменяем: *{text}* ({grams}г = {kcal} ккал)\n"
                f"Приём: *{meal}* | Группа: {group}\n\nЧем заменить?",
                parse_mode="Markdown", reply_markup=foods_keyboard(alts))
        else:
            bot.send_message(cid, "Выбери продукт из кнопок.")
        return

    # ── Замена блюда: выбор замены ──
    if state == "subst_choose_to":
        parts     = extra.split("|", 1)
        meal      = parts[0]
        from_food = parts[1] if len(parts) > 1 else ""
        all_f     = [f for g in FOOD_GROUPS.values() for f in g]
        if text in all_f:
            if text == from_food:
                bot.send_message(cid, "Это тот же продукт 😄 Выбери другой.")
                return
            to_g, kcal = calc_equivalent(from_food, text)
            set_state(cid, "idle")
            bot.send_message(cid,
                f"✅ *Замена в {meal}:*\n\n"
                f"❌ {DEFAULT_PORTIONS.get(from_food,100)}г *{from_food}*\n"
                f"✅ {to_g}г *{text}*\n\n"
                f"🔁 Калорийность сохранена: *{kcal} ккал*",
                parse_mode="Markdown", reply_markup=main_menu(cid))
        else:
            bot.send_message(cid, "Выбери продукт из кнопок.")
        return

    # ════════════════════════════════════════
    #  КНОПКИ ГЛАВНОГО МЕНЮ
    # ════════════════════════════════════════

    # ── Болезнь ──
    if text == "🤒 Я заболел":
        save_profile(cid, is_sick=1, sick_since=now_samara().strftime("%Y-%m-%d"), fatigue=0)
        bot.send_message(cid,
            "🤒 *Режим болезни активирован*\n\n"
            "• Тренировки автоматически отменены\n"
            "• Дефицит калорий снят\n"
            "• Рацион переключён на лёгкую еду\n"
            "• Трекер шагов работает в щадящем режиме\n\n"
            "Скорейшего выздоровления! 💊",
            parse_mode="Markdown", reply_markup=main_menu(cid))

    elif text == "💊 Режим болезни":
        profile = get_profile(cid)
        since   = profile.get("sick_since","") if profile else ""
        days    = 0
        if since:
            try:
                days = (now_samara().date() - datetime.strptime(since, "%Y-%m-%d").date()).days
            except Exception:
                pass
        bot.send_message(cid,
            f"💊 *Режим болезни активен*\n"
            f"{'Болеешь уже: *' + str(days) + ' дн.*' if days else ''}\n\n"
            f"• Тренировки отменены\n"
            f"• Рацион: поддерживающий (~2000 ккал)\n"
            f"• Шаги: не более 5 000 в день\n\n"
            f"Нажми «Я выздоровел» когда почувствуешь себя лучше.",
            parse_mode="Markdown", reply_markup=main_menu(cid))

    elif text == "✅ Я выздоровел":
        profile = get_profile(cid)
        since   = profile.get("sick_since","") if profile else ""
        days    = 0
        if since:
            try:
                days = (now_samara().date() - datetime.strptime(since, "%Y-%m-%d").date()).days
            except Exception:
                pass
        save_profile(cid, is_sick=0, sick_since="", fatigue=2)
        bot.send_message(cid,
            f"✅ *Отлично, рад что выздоровел!*\n"
            f"{'Болел *' + str(days) + ' дн.*' if days else ''}\n\n"
            f"⚠️ *Первые 1-2 дня после болезни:*\n"
            f"• Нагрузку снизь на 30%\n"
            f"• Начни с кардио, потом силовые\n"
            f"• Пей воду — 3л\n\n"
            f"Рацион с дефицитом восстановлен. Удачи! 💪",
            parse_mode="Markdown", reply_markup=main_menu(cid))

    # ── Тренировка сегодня ──
    elif text == "🟢 Тренировка сегодня":
        profile = get_profile(cid)

        # Проверяем не болеет ли
        if profile and profile.get("is_sick"):
            bot.send_message(cid, get_today_workout(cid)[0], parse_mode="Markdown")
            return

        # Проверяем короткий интервал — предупреждение об усталости
        need_warn, warn_text = check_fatigue_warning(cid)
        if need_warn:
            set_state(cid, "fatigue_check_before", extra="")
            m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
            m.add(types.KeyboardButton("😊 Хорошо"),
                  types.KeyboardButton("😐 Немного устал"),
                  types.KeyboardButton("😓 Устал сильно"))
            bot.send_message(cid, warn_text, parse_mode="Markdown", reply_markup=m)
            return

        workout_text, _ = get_today_workout(cid)
        bot.send_message(cid, workout_text, parse_mode="Markdown")

    # ── Проверка усталости ПЕРЕД тренировкой ──
    elif state == "fatigue_check_before" or text in ("😊 Хорошо", "😐 Немного устал", "😓 Устал сильно"):
        if text == "😊 Хорошо":
            set_state(cid, "idle")
            workout_text, _ = get_today_workout(cid)
            bot.send_message(cid, workout_text, parse_mode="Markdown", reply_markup=main_menu(cid))
        elif text == "😐 Немного устал":
            save_profile(cid, fatigue=3)
            set_state(cid, "idle")
            workout_text, _ = get_today_workout(cid)
            bot.send_message(cid,
                "🟡 Понял, немного снизим нагрузку.\n\n" + workout_text,
                parse_mode="Markdown", reply_markup=main_menu(cid))
        elif text == "😓 Устал сильно":
            save_profile(cid, fatigue=5, next_workout_override="К")
            set_state(cid, "idle")
            workout_text, _ = get_today_workout(cid)
            bot.send_message(cid,
                "🔴 Понял, заменяю тренировку на лёгкое кардио.\n\n" + workout_text,
                parse_mode="Markdown", reply_markup=main_menu(cid))

    # ── Тренировка завершена — оценка усталости ──
    elif text == "✅ Тренировка завершена":
        profile = get_profile(cid)
        if profile and profile.get("is_sick"):
            bot.send_message(cid, "🤒 Ты болеешь — тренировок нет.", reply_markup=main_menu(cid))
            return
        weekday  = now_samara().weekday()
        gym_days = (profile.get("gym_days") or 3) if profile else 3
        schedule = get_week_schedule(profile, gym_days)
        wkey     = schedule.get(weekday, "К")
        wname    = WORKOUTS.get(wkey, WORKOUTS["К"])[0]
        set_state(cid, "rate_fatigue", extra=wname)
        bot.send_message(cid,
            f"🏁 *Тренировка завершена!* ({wname})\n\n"
            f"Оцени усталость после тренировки:\n\n"
            f"1 — Свежий как огурец 💪\n"
            f"2 — Хорошая усталость ✅\n"
            f"3 — Умеренно устал 🟡\n"
            f"4 — Сильно устал 🔴\n"
            f"5 — Выжат полностью 😵\n\n"
            f"Бот учтёт это при планировании следующей тренировки.",
            parse_mode="Markdown", reply_markup=fatigue_menu())

    # ── Рацион сегодня ──
    elif text == "🍽️ Рацион сегодня":
        profile = get_profile(cid)
        if not profile:
            bot.send_message(cid, "Сначала настрой профиль кнопкой *⚙️ Изменить профиль*",
                             parse_mode="Markdown"); return
        ration, cal = build_ration(cid)
        if profile.get("is_sick"):
            label = "🤒 Режим болезни"
        else:
            weights = get_weights(cid)
            a = analyze_progress(weights) if len(weights) >= 2 else None
            label = ("📈 Порции увеличены" if a and a["cal_change"] > 0 else
                     "📉 Порции снижены"   if a and a["cal_change"] < 0 else "✅ Стандартный рацион")
        bot.send_message(cid,
            f"🍽️ *РАЦИОН НА СЕГОДНЯ*\n{label}\n─────────────\n{ration}\n\n"
            f"💡 Для замены продукта нажми «🔄 Заменить блюдо»",
            parse_mode="Markdown")

    # ── Замена блюда ──
    elif text == "🔄 Заменить блюдо":
        set_state(cid, "subst_choose_meal")
        m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for meal in MEAL_FOODS:
            m.add(types.KeyboardButton(meal))
        m.add(types.KeyboardButton("❌ Отмена"))
        bot.send_message(cid,
            "🔄 *Замена продукта*\n\nВ каком приёме пищи хочешь заменить продукт?",
            parse_mode="Markdown", reply_markup=m)

    # ── Внести вес ──
    elif text == "⚖️ Внести вес":
        set_state(cid, "waiting_weight")
        bot.send_message(cid, "⚖️ Введи текущий вес (например: *105.7*)\n\nЛучше утром натощак.",
                         parse_mode="Markdown", reply_markup=cancel_menu())

    # ── Внести шаги ──
    elif text == "👟 Внести шаги":
        profile = get_profile(cid)
        sick_hint = "\n🤒 При болезни цель — не более 5 000 шагов." if profile and profile.get("is_sick") else ""
        set_state(cid, "waiting_steps")
        bot.send_message(cid, f"👟 Введи количество шагов за сегодня (например: *8500*){sick_hint}",
                         parse_mode="Markdown", reply_markup=cancel_menu())

    # ── Прогресс ──
    elif text == "📈 Мой прогресс":
        wd      = get_weights(cid)
        profile = get_profile(cid)
        if not wd:
            bot.send_message(cid, "История пуста. Внеси первый вес кнопкой «⚖️ Внести вес»"); return
        lines   = [f"• {d[:10]}: *{w} кг*" for w, d in wd]
        target  = profile["target_weight"] if profile else 92.0
        loss    = round(wd[0][0] - wd[-1][0], 2)
        remain  = round(wd[-1][0] - target, 1)
        pct     = round((wd[0][0]-wd[-1][0])/(wd[0][0]-target)*100,1) if wd[0][0] != target else 100.0
        sick_note = "\n\n🤒 *Режим болезни активен* — похудение приостановлено." if profile and profile.get("is_sick") else ""
        msg = ("📋 *История взвешиваний:*\n\n" + "\n".join(lines) +
               f"\n\n🔥 Сброшено: *{loss} кг* | До цели: *{remain} кг* | Прогресс: *{pct}%*{sick_note}")
        if len(wd) >= 2:
            a = analyze_progress(wd)
            if a:
                msg += f"\n\n─────────────\n🤖 {a['advice']}"
        bot.send_message(cid, msg, parse_mode="Markdown")

    # ── Мои шаги ──
    elif text == "👣 Мои шаги":
        sd = get_steps(cid)
        if not sd:
            bot.send_message(cid, "Нет данных. Нажми «👟 Внести шаги»."); return
        lines = []
        total = 0
        profile = get_profile(cid)
        is_sick = profile.get("is_sick") if profile else False
        for s, d in sd:
            bar   = "█" * (s // 2000) + "░" * max(0, 6 - s // 2000)
            if is_sick:
                emoji = "🤒" if s <= 5000 else ("⚠️" if s <= 8000 else "💪")
            else:
                emoji = "🔥" if s >= 12000 else ("✅" if s >= 8000 else ("🟡" if s >= 5000 else "🔴"))
            lines.append(f"{emoji} {d[:10]}: *{s:,}* {bar}".replace(",", " "))
            total += s
        avg       = round(total / len(sd))
        goal_days = sum(1 for s, _ in sd if s >= (5000 if is_sick else 8000))
        norm_text = "≥5 000 (норма болезни)" if is_sick else "≥8 000"
        bot.send_message(cid,
            "👣 *Статистика шагов (2 недели):*\n\n" + "\n".join(lines) +
            f"\n\n📊 Среднее: *{avg:,}* шагов/день".replace(",", " ") +
            f"\n🎯 Дней с нормой ({norm_text}): *{goal_days}* из {len(sd)}",
            parse_mode="Markdown")

    # ── Расписание дня ──
    elif text == "🕐 Расписание дня":
        now      = now_samara()
        hour     = now.hour
        weekday  = now.weekday()
        profile  = get_profile(cid)
        gym_days = (profile.get("gym_days") or 3) if profile else 3
        schedule = get_week_schedule(profile, gym_days)
        is_sick  = profile.get("is_sick") if profile else False

        if is_sick:
            gym_block   = "🤒 *Режим болезни* — зал отменён"
            dinner_time = "19:00-19:30"
        elif weekday in schedule:
            wk = schedule[weekday]
            gym_block   = ("🏃 *18:40* — Кардио (45 мин)\n🚿 *19:45* — Душ, домой"
                           if wk == "К" else
                           "🏋️ *18:40* — Силовая (60 мин)\n🚿 *20:00* — Душ, домой")
            dinner_time = "20:30-21:00"
        else:
            gym_block   = "🛌 *День отдыха* — зал не нужен"
            dinner_time = "19:30-20:00"

        if 6 <= hour < 7:       current = "⏰ Время вставать!"
        elif 7 <= hour < 8:     current = "🍳 Время завтрака!"
        elif 8 <= hour < 12:    current = "💼 Рабочее утро. Следующий приём — обед в 12:00."
        elif 12 <= hour < 14:   current = "🍗 Время обеда!"
        elif 14 <= hour < 16:   current = "💼 Рабочий день. Полдник в 16:00."
        elif 16 <= hour < 17:   current = "🍎 Время полдника!"
        elif 17 <= hour < 19:   current = "🏃 Скоро зал / активность."
        elif 19 <= hour < 21:   current = "🍽️ Время тренировки или ужина!"
        elif 21 <= hour < 23:   current = "🌙 Время ужина. После — только вода."
        else:                   current = "😴 Пора спать! Цель — 23:00."

        sick_warn = "\n⚠️ *Ты болеешь — отдыхай больше обычного!*\n" if is_sick else ""
        bot.send_message(cid,
            f"🕐 *РАСПИСАНИЕ ДНЯ* (Самарское время)\n{sick_warn}\n"
            f"📍 Сейчас: {current}\n\n"
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

    # ── Сладкое ──
    elif text == "🍫 Сладкое":
        hour    = now_samara().hour
        profile = get_profile(cid)
        is_sick = profile.get("is_sick") if profile else False
        if is_sick:
            timing = "🤒 При болезни — мёд в чай и горячий шоколад без сахара разрешены в любое время."
        elif 12 <= hour < 17:   timing = "✅ Сейчас хорошее время — после обеда или полдника!"
        elif 17 <= hour < 20:   timing = "🟡 Ещё можно — но это последний шанс на сегодня."
        else:                   timing = "🚫 После 20:00 не стоит — потерпи до завтра!"
        bot.send_message(cid,
            f"🍫 *СЛАДКОЕ БЕЗ ВРЕДА*\n\n{timing}\n\n"
            f"✅ *До 150-200 ккал в день:*\n"
            f"• Горький шоколад 70%+ — 25г = *138 ккал* ⭐\n"
            f"• Зефир — 1 шт (25г) = *75 ккал*\n"
            f"• Финики — 3 шт (30г) = *82 ккал*\n"
            f"• Мёд — 1 ч.л. = *23 ккал*\n\n"
            f"🚫 *Исключить:* соки, торты, конфеты с начинкой\n\n"
            f"📌 Только после еды · не позже 20:00 · 3-4 раза в неделю",
            parse_mode="Markdown")

    # ── Жиросжигающие продукты ──
    elif text == "🔥 Жиросжигающие продукты":
        profile = get_profile(cid)
        is_sick = profile.get("is_sick") if profile else False
        sick_note = ("\n\n🤒 *При болезни:* имбирь, зелёный чай и мёд — лучшие помощники. "
                     "Кофе лучше исключить — нагружает сердце.") if is_sick else ""
        bot.send_message(cid,
            f"🔥 *ПРОДУКТЫ ДЛЯ ЖИРОСЖИГАНИЯ*\n\n"
            f"⚡ *Ускоряют метаболизм:*\n"
            f"• Зелёный чай — 2-3 чашки без сахара\n"
            f"• Кофе без сахара — за 30 мин до тренировки\n"
            f"• Острый перец — добавляй в еду\n"
            f"• Имбирь — в чай, снижает инсулин\n\n"
            f"💪 *Снижают кортизол (висцеральный жир):*\n"
            f"• Тёмный шоколад 70%+ — 25г после обеда\n"
            f"• Грецкие орехи — омега-3\n"
            f"• Черника/голубика — 50г в день\n\n"
            f"💧 *3л воды в день = +30% к жиросжиганию*{sick_note}",
            parse_mode="Markdown")

    # ── Профиль ──
    elif text == "👤 Мой профиль":
        profile = get_profile(cid)
        if not profile:
            bot.send_message(cid, "Профиль не настроен. Нажми *⚙️ Изменить профиль*",
                             parse_mode="Markdown"); return
        plan    = calc_plan(profile)
        wd      = get_weights(cid)
        curr_w  = wd[-1][0] if wd else profile["current_weight"]
        loss    = round(profile["current_weight"] - curr_w, 1)
        fatigue = int(profile.get("fatigue") or 0)
        fat_label = {0:"—",1:"😊 Отлично",2:"✅ Хорошо",3:"🟡 Умеренная",
                     4:"🔴 Высокая",5:"😵 Очень высокая"}.get(fatigue, "—")
        sick_label = "🤒 Активен" if profile.get("is_sick") else "✅ Здоров"
        bot.send_message(cid,
            f"👤 *МОЙ ПРОФИЛЬ*\n\n"
            f"⚖️ Стартовый вес: *{profile['current_weight']} кг*\n"
            f"📉 Текущий вес: *{curr_w} кг* (−{loss} кг)\n"
            f"🎯 Цель: *{profile['target_weight']} кг*\n"
            f"📏 Рост: *{profile['height']} см* | 🎂 Возраст: *{profile['age']} лет*\n\n"
            f"🏋️ Зал: *{profile['gym_days']} дней/нед*\n"
            f"💪 Тренировки: *{auto_workout_label(profile)}*\n"
            f"📅 Срок: *{profile['deadline_weeks']} недель*\n\n"
            f"🔥 Калории: *{plan['calories']} ккал/день*\n"
            f"💪 Белок: *{plan['protein']}г/день*\n"
            f"📈 Темп: *~{plan['weekly_loss']} кг/нед*\n\n"
            f"😴 Усталость: *{fat_label}*\n"
            f"🏥 Здоровье: *{sick_label}*",
            parse_mode="Markdown")

    # ── Изменить профиль ──
    elif text == "⚙️ Изменить профиль":
        start_onboarding(cid, edit=True)

    else:
        bot.send_message(cid, "Используй кнопки меню.", reply_markup=main_menu(cid))

if __name__ == '__main__':
    init_db()
    print("Бот v6 запущен! Самара UTC+4 | Усталость | Болезнь | Умные тренировки")
    bot.infinity_polling()
