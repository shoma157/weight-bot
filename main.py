import telebot
from telebot import types
import sqlite3
from datetime import datetime
 
TOKEN = "8844022654:AAFZt7DXdHWoORHlGrFSi0rMyX7BUYBzUR8"
bot = telebot.TeleBot(TOKEN)
 
# ─────────────────────────────────────────
#  БАЗА КАЛОРИЙНОСТИ ПРОДУКТОВ (ккал на 100г)
# ─────────────────────────────────────────
 
KCAL_PER_100G = {
    # Белки
    "куриная грудка":    110,
    "куриное бедро":     185,
    "индейка":           115,
    "говядина":          187,
    "яйцо":              155,   # целое яйцо ~62г
    # Углеводы
    "гречка":            313,   # сухая
    "бурый рис":         337,
    "булгур":            342,
    "овсянка":           352,
    "макароны":          350,
    # Овощи
    "болгарский перец":   27,
    "морковь":            35,
    "шпинат":             23,
    "стручковая фасоль":  31,
    "брокколи":           34,
    "огурец":             15,
    "помидор":            18,
    "листовой салат":     15,
    # Жиры/снеки
    "миндаль":           576,
    "грецкий орех":      654,
    "кешью":             553,
    "тыквенные семечки": 559,
    "оливковое масло":   884,
    # Фрукты
    "яблоко":             52,
    "груша":              57,
    "ягоды":              45,
}
 
# Группы продуктов для замен (только внутри группы)
FOOD_GROUPS = {
    "белок": [
        "куриная грудка",
        "куриное бедро",
        "индейка",
        "говядина",
    ],
    "углеводы": [
        "гречка",
        "бурый рис",
        "булгур",
        "овсянка",
        "макароны",
    ],
    "овощи": [
        "болгарский перец",
        "морковь",
        "шпинат",
        "стручковая фасоль",
        "брокколи",
        "огурец",
        "помидор",
    ],
    "орехи": [
        "миндаль",
        "грецкий орех",
        "кешью",
        "тыквенные семечки",
    ],
    "фрукты": [
        "яблоко",
        "груша",
        "ягоды",
    ],
}
 
# Стандартные порции (г) в рационе
DEFAULT_PORTIONS = {
    "куриная грудка":    250,
    "куриное бедро":     250,
    "индейка":           250,
    "говядина":          200,
    "гречка":             80,
    "бурый рис":          80,
    "булгур":             80,
    "овсянка":            60,
    "макароны":          100,
    "болгарский перец":  200,
    "морковь":           200,
    "шпинат":            200,
    "стручковая фасоль": 200,
    "брокколи":          200,
    "миндаль":            20,
    "грецкий орех":       20,
    "кешью":              20,
    "тыквенные семечки":  20,
    "яблоко":            150,
    "груша":             150,
    "ягоды":             100,
}
 
def calc_equivalent_portion(from_food, to_food, from_grams=None):
    """
    Считает сколько граммов to_food содержит столько же калорий,
    сколько from_grams граммов from_food.
    """
    if from_grams is None:
        from_grams = DEFAULT_PORTIONS.get(from_food, 100)
    kcal_from = KCAL_PER_100G[from_food] * from_grams / 100
    grams_to  = round(kcal_from / KCAL_PER_100G[to_food] * 100)
    return grams_to, round(kcal_from)
 
def find_group(food_name):
    for group, items in FOOD_GROUPS.items():
        if food_name in items:
            return group
    return None
 
# ─────────────────────────────────────────
#  БАЗА ДАННЫХ
# ─────────────────────────────────────────
 
def init_db():
    conn = sqlite3.connect("weight_tracker.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS weights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        weight_value REAL,
        date TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        step_count INTEGER,
        date TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_state (
        user_id INTEGER PRIMARY KEY,
        state TEXT DEFAULT 'idle',
        extra TEXT DEFAULT ''
    )''')
    conn.commit()
    conn.close()
 
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
    rows = conn.execute(
        "SELECT step_count, date FROM steps WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return list(reversed(rows))
 
def set_state(user_id, state, extra=""):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute(
        "INSERT INTO user_state (user_id, state, extra) VALUES (?,?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET state=excluded.state, extra=excluded.extra",
        (user_id, state, extra)
    )
    conn.commit(); conn.close()
 
def get_state(user_id):
    conn = sqlite3.connect("weight_tracker.db")
    row = conn.execute("SELECT state, extra FROM user_state WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return (row[0], row[1]) if row else ("idle", "")
 
# ─────────────────────────────────────────
#  АНАЛИЗ ПРОГРЕССА
# ─────────────────────────────────────────
 
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
    delta       = round(prev_w - curr_w, 2)
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
 
def get_cal_level(user_id):
    w = get_weights(user_id)
    a = analyze_progress(w) if len(w) >= 2 else None
    if not a:            return "medium"
    if a["cal_change"] > 0:  return "high"
    if a["cal_change"] < 0:  return "low"
    return "medium"
 
def build_ration(cal_level):
    # Комбо-вариант: базовый калораж снижен до ~1 950 ккал (цель 92 кг)
    # low = медленный темп → ещё −150 ккал
    # medium = норма (1 950 ккал)
    # high = слишком быстрый темп → +150 ккал
    p = {
        "low":    {"breast": 200, "carb": 50,  "snack": 100, "dinner": "только овощи без гарнира", "kcal": 1800, "prot": 165},
        "medium": {"breast": 230, "carb": 65,  "snack": 130, "dinner": "300г тушёных овощей",       "kcal": 1950, "prot": 178},
        "high":   {"breast": 260, "carb": 85,  "snack": 160, "dinner": "300г овощей + 50г гречки",  "kcal": 2100, "prot": 190},
    }[cal_level]
    return (
        f"🍳 *Завтрак:* 3 яйца + 60г овсянки на воде + помидор/огурец\n"
        f"🍗 *Обед:* {p['breast']}г куриной грудки + {p['carb']}г гречки + салат\n"
        f"🍎 *Полдник:* {p['snack']}г куриного филе + 1 фрукт + 20г орехов\n"
        f"🍗 *Ужин:* 180г запечённой курицы + {p['dinner']}\n\n"
        f"🎯 ~{p['kcal']} ккал | 💪 ~{p['prot']}г белка\n"
        f"🚶 *+1 500 шагов сверх плана* (прогулка ~15 мин после ужина)"
    ), p["kcal"]
 
# ─────────────────────────────────────────
#  МЕНЮ
# ─────────────────────────────────────────
 
def main_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(
        types.KeyboardButton("🟢 ПН (Силовой А)"),
        types.KeyboardButton("🔵 ВТ (Кардио)"),
        types.KeyboardButton("🟢 СР (Силовой Б)"),
        types.KeyboardButton("⚪ ЧТ (Отдых)"),
        types.KeyboardButton("🟢 ПТ (Силовой В)"),
        types.KeyboardButton("🟡 СБ (Прогулка)"),
        types.KeyboardButton("🔴 ВС (Контроль/Замеры)"),
        types.KeyboardButton("⚖️ Внести вес"),
        types.KeyboardButton("👟 Внести шаги"),
        types.KeyboardButton("📈 Мой Вес"),
        types.KeyboardButton("👣 Мои шаги"),
        types.KeyboardButton("🍽️ Мой рацион сегодня"),
        types.KeyboardButton("🔄 Заменить блюдо"),
        types.KeyboardButton("🕐 Моё расписание"),
        types.KeyboardButton("🍫 Сладкое"),
    )
    return m
 
def cancel_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(types.KeyboardButton("❌ Отмена"))
    return m
 
def products_keyboard(group):
    """Клавиатура с продуктами группы"""
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for item in FOOD_GROUPS[group]:
        m.add(types.KeyboardButton(item))
    m.add(types.KeyboardButton("❌ Отмена"))
    return m
 
# ─────────────────────────────────────────
#  ХЭНДЛЕРЫ
# ─────────────────────────────────────────
 
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "⚙️ *ИНЖЕНЕРНЫЙ ТРЕКЕР ЖИРОСЖИГАНИЯ PRO v5*\n\n"
        "🎯 Цель: 107 кг → 92 кг за 3 месяца\n\n"
        "📊 *Твой план (комбо-вариант):*\n"
        "• Питание: ~1 950 ккал/день\n"
        "• Дефицит: ~1 160 ккал/день\n"
        "• Темп: ~1.0-1.1 кг/нед\n"
        "• +1 500 шагов сверх нормы ежедневно\n\n"
        "🚫 Без: лактозы, капусты, кабачков, баклажанов, рыбы, бобовых\n"
        "🍫 Сладкое: до 150 ккал, не позже 20:00, 3-4 раза в неделю"
    )
    if not get_weights(message.chat.id):
        add_weight(message.chat.id, 107.0)
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())
 
@bot.message_handler(func=lambda m: True)
def router(message):
    chat_id = message.chat.id
    text    = message.text.strip()
    state, extra = get_state(chat_id)
 
    # ════════════════════════════════════════
    #  МАШИНА СОСТОЯНИЙ
    # ════════════════════════════════════════
 
    # ── Отмена из любого состояния ──
    if text == "❌ Отмена":
        set_state(chat_id, "idle")
        bot.send_message(chat_id, "Отменено.", reply_markup=main_menu())
        return
 
    # ── Ожидание ввода веса ──
    if state == "waiting_weight":
        try:
            w = float(text.replace(',', '.'))
            if not (50 < w < 200):
                bot.send_message(chat_id, "Введи корректный вес, например: 105.7")
                return
            add_weight(chat_id, w)
            set_state(chat_id, "idle")
            weights_data = get_weights(chat_id)
            start_w   = weights_data[0][0]
            loss      = round(start_w - w, 2)
            remaining = round(w - 92.0, 1)
            pct       = round((start_w - w) / (start_w - 92.0) * 100, 1) if start_w != 92.0 else 100.0
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
            bot.send_message(chat_id, resp, parse_mode="Markdown", reply_markup=main_menu())
        except ValueError:
            bot.send_message(chat_id, "Введи число, например: 105.7")
        return
 
    # ── Ожидание ввода шагов ──
    if state == "waiting_steps":
        try:
            steps = int(text.replace(' ', '').replace(',', ''))
            if not (0 < steps < 100000):
                bot.send_message(chat_id, "Введи реальное число шагов, например: 8500")
                return
            add_steps(chat_id, steps)
            set_state(chat_id, "idle")
            # Оценка дня
            if steps >= 12000:
                verdict = "🔥 Отличный день! Кардио в зале можно пропустить."
            elif steps >= 8000:
                verdict = "✅ Хороший уровень активности."
            elif steps >= 5000:
                verdict = "🟡 Средняя активность. Попробуй добавить вечернюю прогулку."
            else:
                verdict = "🔴 Малоподвижный день. Обязательно выйди на прогулку или сделай кардио."
            bot.send_message(
                chat_id,
                f"👟 *{steps:,} шагов* сохранено!\n\n{verdict}".replace(",", " "),
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
        except ValueError:
            bot.send_message(chat_id, "Введи число шагов, например: 8500")
        return
 
    # ── Замена блюда: выбор исходного продукта ──
    if state == "subst_choose_from":
        all_foods = [f for group in FOOD_GROUPS.values() for f in group]
        if text in all_foods:
            set_state(chat_id, "subst_choose_to", extra=text)
            group = find_group(text)
            from_grams = DEFAULT_PORTIONS.get(text, 100)
            kcal = round(KCAL_PER_100G[text] * from_grams / 100)
            bot.send_message(
                chat_id,
                f"Выбрано: *{text}* ({from_grams}г = {kcal} ккал)\n\n"
                f"Теперь выбери *на что заменить* (из той же группы — {group}):",
                parse_mode="Markdown",
                reply_markup=products_keyboard(group)
            )
        else:
            bot.send_message(chat_id, "Выбери продукт из списка на кнопках.")
        return
 
    # ── Замена блюда: выбор замены ──
    if state == "subst_choose_to":
        from_food = extra
        all_foods = [f for group in FOOD_GROUPS.values() for f in group]
        if text in all_foods:
            if text == from_food:
                bot.send_message(chat_id, "Это тот же продукт 😄 Выбери другой.")
                return
            from_grams = DEFAULT_PORTIONS.get(from_food, 100)
            to_grams, kcal = calc_equivalent_portion(from_food, text, from_grams)
            set_state(chat_id, "idle")
            bot.send_message(
                chat_id,
                f"✅ *Эквивалентная замена:*\n\n"
                f"❌ {from_grams}г *{from_food}*\n"
                f"✅ {to_grams}г *{text}*\n\n"
                f"🔁 Калорийность сохранена: *{kcal} ккал*\n"
                f"Замени в своём приёме пищи — рацион и дефицит не изменятся.",
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
        else:
            bot.send_message(chat_id, "Выбери продукт из списка на кнопках.")
        return
 
    # ════════════════════════════════════════
    #  КНОПКИ ГЛАВНОГО МЕНЮ
    # ════════════════════════════════════════
 
    if text == "⚖️ Внести вес":
        set_state(chat_id, "waiting_weight")
        bot.send_message(chat_id, "⚖️ Введи текущий вес (например: *105.7*)\n\nЛучше утром натощак.",
                         parse_mode="Markdown", reply_markup=cancel_menu())
 
    elif text == "👟 Внести шаги":
        set_state(chat_id, "waiting_steps")
        bot.send_message(chat_id, "👟 Введи количество шагов за сегодня (например: *8500*)",
                         parse_mode="Markdown", reply_markup=cancel_menu())
 
    elif text == "👣 Мои шаги":
        steps_data = get_steps(chat_id)
        if not steps_data:
            bot.send_message(chat_id, "Нет данных о шагах. Нажми «👟 Внести шаги».")
            return
        lines = []
        total = 0
        for s, d in steps_data:
            date_fmt = d[:10]
            bar = "█" * (s // 2000) + ("░" * max(0, 5 - s // 2000))
            emoji = "🔥" if s >= 12000 else ("✅" if s >= 8000 else ("🟡" if s >= 5000 else "🔴"))
            lines.append(f"{emoji} {date_fmt}: *{s:,}* {bar}".replace(",", " "))
            total += s
        avg = round(total / len(steps_data))
        goal_days = sum(1 for s, _ in steps_data if s >= 8000)
        msg = (
            "👣 *Статистика шагов (последние 2 недели):*\n\n" +
            "\n".join(lines) +
            f"\n\n📊 Среднее в день: *{avg:,}* шагов".replace(",", " ") +
            f"\n🎯 Дней с нормой (≥8 000): *{goal_days}* из {len(steps_data)}"
        )
        bot.send_message(chat_id, msg, parse_mode="Markdown")
 
    elif text == "📈 Мой Вес":
        weights_data = get_weights(chat_id)
        if not weights_data:
            bot.send_message(chat_id, "История пуста. Напиши /start"); return
        lines = [f"• {d[:10]}: *{w} кг*" for w, d in weights_data]
        start_w = weights_data[0][0]
        curr_w  = weights_data[-1][0]
        loss    = round(start_w - curr_w, 2)
        remaining = round(curr_w - 92.0, 1)
        pct = round((start_w - curr_w) / (start_w - 92.0) * 100, 1) if start_w != 92.0 else 100.0
        msg = (
            "📋 *История взвешиваний:*\n\n" + "\n".join(lines) +
            f"\n\n🔥 Сброшено: *{loss} кг* | До цели: *{remaining} кг* | Прогресс: *{pct}%*"
        )
        if len(weights_data) >= 2:
            a = analyze_progress(weights_data)
            if a:
                msg += f"\n\n─────────────\n🤖 {a['advice']}"
        bot.send_message(chat_id, msg, parse_mode="Markdown")
 
    elif text == "🍽️ Мой рацион сегодня":
        cal_level = get_cal_level(chat_id)
        ration_text, kcal = build_ration(cal_level)
        labels = {"low": "📉 Темп медленный — порции снижены", "medium": "✅ Стандартный рацион", "high": "📈 Темп высокий — порции увеличены"}
        bot.send_message(
            chat_id,
            f"🍽️ *РАЦИОН НА СЕГОДНЯ*\n{labels[cal_level]}\n─────────────\n{ration_text}\n\n"
            f"💡 Хочешь заменить продукт — нажми «🔄 Заменить блюдо»",
            parse_mode="Markdown"
        )
 
    elif text == "🔄 Заменить блюдо":
        set_state(chat_id, "subst_choose_from")
        # Показываем все продукты сгруппированно
        all_foods_text = ""
        for group, items in FOOD_GROUPS.items():
            group_ru = {"белок": "🍗 Белок", "углеводы": "🍚 Углеводы",
                        "овощи": "🥦 Овощи", "орехи": "🌰 Орехи", "фрукты": "🍎 Фрукты"}[group]
            all_foods_text += f"\n{group_ru}: {', '.join(items)}"
 
        # Строим единую клавиатуру со всеми продуктами
        m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for group, items in FOOD_GROUPS.items():
            for item in items:
                m.add(types.KeyboardButton(item))
        m.add(types.KeyboardButton("❌ Отмена"))
 
        bot.send_message(
            chat_id,
            "🔄 *Замена продукта с сохранением калорийности*\n\n"
            "Выбери продукт, который хочешь *заменить*:\n" + all_foods_text,
            parse_mode="Markdown",
            reply_markup=m
        )
 
    # ── Дни недели ──
    elif text == "🟢 ПН (Силовой А)":
        bot.send_message(chat_id,
            "🟢 *ПОНЕДЕЛЬНИК — Силовой А* _(Грудь + Спина + Бицепс)_\n\n"
            "1. Жим гантелей на наклонной лавке — 4×12\n"
            "2. Тяга верхнего блока широким хватом — 4×12\n"
            "3. Горизонтальная тяга в блоке — 3×12\n"
            "4. Сгибание рук с гантелями — 3×12\n"
            "5. Планка на предплечьях — 3×45 сек\n\n"
            "🍽️ Нажми «Мой рацион сегодня» для актуальных порций.", parse_mode="Markdown")
 
    elif text == "🔵 ВТ (Кардио)":
        bot.send_message(chat_id,
            "🔵 *ВТОРНИК — Кардио*\n\n"
            "📱 Если уже >12 000 шагов — в зал не идёшь!\n\n"
            "🏃 45 минут: Эллипс (пульс 120-135) ИЛИ дорожка наклон 8%, 5.5 км/ч\n\n"
            "🍽️ Нажми «Мой рацион сегодня» для актуальных порций.", parse_mode="Markdown")
 
    elif text == "🟢 СР (Силовой Б)":
        bot.send_message(chat_id,
            "🟢 *СРЕДА — Силовой Б* _(Ноги + Плечи + Трицепс)_\n\n"
            "1. Жим ногами в тренажёре — 4×12\n"
            "2. Разгибание ног в тренажёре — 3×15\n"
            "3. Жим гантелей сидя на плечи — 4×12\n"
            "4. Отжимания в гравитроне — 3×10\n"
            "5. Подъём ног в висе — 4×12\n\n"
            "🍽️ Нажми «Мой рацион сегодня» для актуальных порций.", parse_mode="Markdown")
 
    elif text == "⚪ ЧТ (Отдых)":
        bot.send_message(chat_id,
            "⚪ *ЧЕТВЕРГ — Восстановление*\n\n"
            "🛌 Зал не нужен. Если <7 000 шагов — выйди на прогулку 30 мин.\n\n"
            "🍽️ Нажми «Мой рацион сегодня» для актуальных порций.", parse_mode="Markdown")
 
    elif text == "🟢 ПТ (Силовой В)":
        bot.send_message(chat_id,
            "🟢 *ПЯТНИЦА — Силовой В* _(Спина + Кор)_\n\n"
            "1. Гиперэкстензия без веса (медленно!) — 4×15\n"
            "2. Тяга нижнего блока узким хватом — 4×12\n"
            "3. Жим гантелей лёжа — 3×12\n"
            "4. Боковая планка — 3×30 сек каждая сторона\n"
            "5. Скручивания на пресс — 3×20\n\n"
            "🍽️ Нажми «Мой рацион сегодня» для актуальных порций.", parse_mode="Markdown")
 
    elif text == "🟡 СБ (Прогулка)":
        bot.send_message(chat_id,
            "🟡 *СУББОТА — Активный отдых*\n\n"
            "🚶 Цель: 8 000-10 000 шагов. Зал не нужен.\n"
            "Не забудь внести шаги через «👟 Внести шаги»!\n\n"
            "🍽️ Нажми «Мой рацион сегодня» для актуальных порций.", parse_mode="Markdown")
 
    elif text == "🔴 ВС (Контроль/Замеры)":
        bot.send_message(chat_id,
            "🔴 *ВОСКРЕСЕНЬЕ — Аудит*\n\n"
            "⚖️ Нажми «Внести вес» — утром натощак.\n"
            "👟 Нажми «Внести шаги» — итог недели.\n\n"
            "📊 *Прогноз (комбо-вариант):*\n"
            "• Месяц 1: 107 → 101-102 кг (-5-6 кг)\n"
            "• Месяц 2: 102 → 97-98 кг (-4-5 кг)\n"
            "• Месяц 3: 97 → 92-93 кг (-4-5 кг)\n\n"
            "🛌 Тренировок нет.", parse_mode="Markdown")
 
    elif text == "🕐 Моё расписание":
        # Определяем тип дня по текущему дню недели
        weekday = datetime.now().weekday()  # 0=пн, 1=вт, 2=ср, 3=чт, 4=пт, 5=сб, 6=вс
        is_gym_day    = weekday in (0, 1, 2, 4)   # пн, вт, ср, пт
        is_rest_day   = weekday == 3               # чт
        is_walk_day   = weekday == 5               # сб
        is_audit_day  = weekday == 6               # вс
 
        if is_gym_day:
            if weekday == 1:  # вт — кардио
                gym_block = (
                    "🏃 *18:40-19:00* — Выход в зал\n"
                    "🏃 *19:00-19:45* — Кардио (эллипс / дорожка)\n"
                    "🚿 *19:45-20:15* — Душ, дорога домой"
                )
            else:
                gym_block = (
                    "🏋️ *18:40-19:00* — Выход в зал\n"
                    "🏋️ *19:00-20:00* — Силовая тренировка\n"
                    "🚿 *20:00-20:30* — Душ, дорога домой"
                )
            dinner_time = "20:30-21:00"
            dinner_note = "После тренировки — окно 1-1.5 часа, это идеально"
        elif is_rest_day:
            gym_block   = "🛌 *Сегодня зал не нужен* — день восстановления"
            dinner_time = "19:30-20:00"
            dinner_note = "Без тренировки ужинаем чуть раньше"
        elif is_walk_day:
            gym_block   = "🚶 *Прогулка* — 8 000-10 000 шагов в удобное время"
            dinner_time = "19:30-20:00"
            dinner_note = "Лёгкий субботний ужин"
        else:  # вс
            gym_block   = "🛌 *Полный отдых* — тренировок нет"
            dinner_time = "19:00-19:30"
            dinner_note = "Воскресный ужин пораньше — завтра рабочий день"
 
        now     = datetime.now()
        hour    = now.hour
        minute  = now.minute
 
        # Подсказка что сейчас делать
        if 6 <= hour < 7:
            current = "⏰ Время вставать и готовиться к завтраку!"
        elif hour == 7 and minute < 30:
            current = "🍳 Сейчас твоё время завтрака (7:10)!"
        elif 7 <= hour < 12:
            current = "💼 Рабочее утро. Следующий приём — обед в 12:00."
        elif 12 <= hour < 14:
            current = "🍗 Сейчас твоё время обеда!"
        elif 14 <= hour < 16:
            current = "💼 Рабочий день. Полдник в 16:00-16:30."
        elif 16 <= hour < 17:
            current = "🍎 Сейчас твоё время полдника!"
        elif 17 <= hour < 19:
            current = "🏃 Скоро зал / вечерняя активность."
        elif 19 <= hour < 21:
            current = "🏋️ Время тренировки или ужина!"
        elif 21 <= hour < 23:
            current = "🍗 Время ужина. После — только вода."
        elif hour >= 23 or hour < 1:
            current = "😴 Пора спать! Цель — засыпать в 23:00."
        else:
            current = "🌙 Поздно. Ложись спать, это важно для похудения!"
 
        msg = (
            "🕐 *ТВОЁ РАСПИСАНИЕ ДНЯ*\n\n"
            f"📍 *Сейчас:* {current}\n\n"
            "─────────────────\n"
            "⏰ *06:45* — Подъём\n"
            "🍳 *07:10* — Завтрак\n"
            "  └ 3 яйца + 60г овсянки + помидор/огурец\n\n"
            "💼 *07:30-12:00* — Работа\n\n"
            "🍗 *12:00-13:00* — Обед\n"
            "  └ Курица + гречка/рис + салат\n\n"
            "💼 *13:00-16:00* — Работа\n\n"
            "🍎 *16:00-16:30* — Полдник ⚠️ не позже!\n"
            "  └ Куриное филе + фрукт + орехи\n\n"
            "💼 *16:30-18:40* — Работа / дорога\n\n"
            f"{gym_block}\n\n"
            f"🍗 *{dinner_time}* — Ужин ({dinner_note})\n"
            "  └ Запечённая курица + тушёные овощи\n\n"
            "💧 *До 23:00* — только вода, никакой еды\n\n"
            "😴 *23:00* — СОН ✅\n"
            "  └ 7ч 45мин до подъёма — оптимум для жиросжигания\n\n"
            "─────────────────\n"
            "⚠️ *Почему 23:00, а не 00:45?*\n"
            "Недосып повышает кортизол → кортизол блокирует жиросжигание "
            "и разрушает мышцы. При дефиците калорий сон — это часть тренировки."
        )
        bot.send_message(chat_id, msg, parse_mode="Markdown")
 
    elif text == "🍫 Сладкое":
        now  = datetime.now()
        hour = now.hour
 
        # Подсказка по времени суток
        if 12 <= hour < 17:
            timing_tip = "✅ *Сейчас хорошее время* — после обеда или полдника самое то!"
        elif 17 <= hour < 20:
            timing_tip = "🟡 *Ещё можно* — но это последний шанс на сегодня."
        elif hour >= 20 or hour < 6:
            timing_tip = "🚫 *Сейчас не стоит* — после 20:00 сахар сильнее тормозит жиросжигание. Потерпи до завтра!"
        else:
            timing_tip = "⏰ *Утром сладкое не лучший выбор* — приберегись до обеда или полдника."
 
        msg = (
            "🍫 *СЛАДКОЕ БЕЗ ВРЕДА ДЛЯ ПОХУДЕНИЯ*\n\n"
            f"{timing_tip}\n\n"
            "─────────────────\n"
            "📋 *ТАБЛИЦА КАЛОРИЙНОСТИ*\n\n"
            "✅ *Разрешённые варианты:*\n"
            "• Горький шоколад 70%+ — 25г = *138 ккал* ⭐ лучший выбор\n"
            "• Горький шоколад 85%+ — 25г = *143 ккал* ⭐⭐ идеал\n"
            "• Зефир — 1 шт (25г) = *75 ккал*\n"
            "• Мармелад без сахара — 30г = *55 ккал*\n"
            "• Финики — 3 шт (30г) = *82 ккал*\n"
            "• Мёд — 1 ч.л. (7г) = *23 ккал*\n"
            "• Сухофрукты (курага/чернослив) — 30г = *70 ккал*\n\n"
            "⚠️ *Осторожно (изредка, маленькая порция):*\n"
            "• Молочный шоколад — 25г = *135 ккал* (сахар + жир = опасно)\n"
            "• Мороженое пломбир — 100г = *230 ккал*\n"
            "• Печенье — 2 шт (30г) = *140 ккал*\n"
            "• Вафли — 30г = *145 ккал*\n\n"
            "🚫 *Полностью исключить:*\n"
            "• Сладкие напитки/соки — 300мл = *120-150 ккал* (не насыщают)\n"
            "• Торты/пирожные — 100г = *350-450 ккал*\n"
            "• Конфеты с начинкой — 3 шт = *150-200 ккал*\n"
            "• Молочный коктейль — стакан = *250-300 ккал*\n\n"
            "─────────────────\n"
            "📌 *3 ПРАВИЛА:*\n\n"
            "1️⃣ *Только после еды* — после белка инсулин поднимается мягче, "
            "нет резкого голода через час\n\n"
            "2️⃣ *Не позже 20:00* — вечером инсулиновый ответ сильнее\n\n"
            "3️⃣ *3-4 раза в неделю, не каждый день* — ежедневная привычка "
            "разгоняет тягу и выбивает из дефицита\n\n"
            "─────────────────\n"
            "🎯 *Твой дневной бюджет на сладкое: 150-200 ккал*\n"
            "Лучший вариант: *25г горького шоколада 70%+ после обеда* — "
            "закрывает тягу, даёт магний для мышц, не мешает похудению."
        )
        bot.send_message(chat_id, msg, parse_mode="Markdown")
 
    else:
        bot.send_message(chat_id, "Используй кнопки меню.", reply_markup=main_menu())
 
if __name__ == '__main__':
    init_db()
    print("Бот v5 запущен! Цель 92 кг, комбо-вариант активирован.")
    bot.infinity_polling()
