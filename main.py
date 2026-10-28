import telebot
from telebot import types
import sqlite3
import threading
import time
import csv
import io
import re
from datetime import datetime, timezone, timedelta
import random
from functools import lru_cache

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

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
    # Плов
    "плов с курицей": 180,
    "плов со свининой": 220,
    "плов с говядиной": 200,
    "плов с бараниной": 210,
    # Милкшейки (протеиновые/низкокалорийные)
    "протеиновый милкшейк ваниль": 95,
    "протеиновый милкшейк шоколад": 100,
    "протеиновый милкшейк клубника": 90,
    "банановый милкшейк (без сахара)": 85,
    "ягодный смузи": 65,
    "зелёный смузи": 55,
    # Супы
    "куриный суп с овощами": 45,
    "борщ без картофеля": 40,
    "томатный суп": 35,
    "суп из чечевицы": 95,
    # Рыба (несмотря на личные предпочтения — для других пользователей)
    "тунец консервированный": 96,
    "лосось запечённый": 208,
    "тилапия запечённая": 128,
    # Дополнительные белки
    "куриные яйца перепелиные": 168,
    "творожная запеканка": 140,
    "сырники из творога": 185,
    "протеиновые оладьи": 155,
    # Гарниры
    "картофельное пюре": 83,
    "запечённый картофель": 93,
    "кускус": 376,
    "полба": 338,
    # Закуски и перекусы
    "хумус": 177,
    "рисовые хлебцы": 313,
    "цельнозерновые хлебцы": 295,
    "авокадо": 160,
    "оливки": 145,
    # Напитки
    "кефир 1%": 40,
    "ряженка 2.5%": 54,
    "натуральный йогурт без сахара": 51,
    # Молочные коктейли (растительные)
    "миндальный молочный коктейль": 150,
    "кокосовый молочный коктейль": 180,
    "безлактозный молочный коктейль": 120,
    "арахисовый молочный коктейль": 160,
    "овсяный молочный коктейль": 110,
    # Новые блюда
    "куриный фарш": 143,
    "говяжий фарш": 254,
    "тефтели куриные домашние": 130,
    "тефтели говяжьи домашние": 175,
    "омлет (2 яйца)": 150,
    "запечённая говядина": 177,
    "запечённая куриная грудка": 115,
    "макароны с куриным фаршем": 145,
    "макароны с котлетой": 160,
    # ── Додо Пицца (ккал на 100г) ──
    "додо пицца пепперони": 284,
    "додо пицца сырная": 293,
    "додо пицца ветчина и сыр": 282,
    "додо пицца мясная": 260,
    "додо пицца гавайская": 216,
    "додо пицца маргарита": 235,
    "додо пицца бургер-пицца": 221,
    "додо пицца 4 сезона": 189,
    "додо пицца 4 сыра": 200,
    "додо пицца грибы и маслины": 168,
    "додо пицца ассорти": 213,
    "додо пицца дон бекон": 274,
    "додо пицца итальянская": 217,
    "додо пицца колбаски и перчик": 187,
    "додо пицца маргарита тонкое": 173,
    "додо пицца морская": 181,
    "додо пицца овощи и грибы": 174,
    "додо пицца сальса": 185,
    "додо пицца супермясная": 280,
    "додо пицца сырный цыплёнок": 196,
    "додо пицца томаты и чеснок": 151,
    "додо пицца томаты со сливками": 213,
    "додо пицца утка терияки": 240,
    "додо пицца цыплёнок барбекю": 232,
    "додо пицца чизбургер": 207,
    "додо пицца мексиканская": 200,
    "додо пицца крейзи": 232,
    "додо пицца ранч": 219,
    "додо пицца бефстроганов": 217,
    # ── Ташир Пицца (ккал на 100г, традиционное тесто) ──
    "ташир пицца маргарита": 220,
    "ташир пицца пепперони": 255,
    "ташир пицца мясной пир": 270,
    "ташир пицца четыре сыра": 265,
    "ташир пицца карбонара": 245,
    "ташир пицца гавайская": 230,
    "ташир пицца барбекю с халапеньо": 260,
    "ташир пицца ассорти": 240,
    "ташир пицца баварская": 250,
    "ташир пицца венеция": 225,
    "ташир пицца грибная с ветчиной": 228,
    "ташир пицца капричоза": 232,
    "ташир пицца европа": 255,
    "ташир пицца сливочная с курицей": 235,
    "ташир пицца сырный цыплёнок": 248,
    "ташир пицца цыплёнок с песто": 242,
    "ташир пицца чизбургер": 238,
    "ташир пицца чикен барбекю": 238,
    "ташир пицца альтоно": 243,
    "ташир пицца пять сыров": 285,
    "ташир пицца четыре сезона": 240,
    "ташир пицца том ям": 235,
    "ташир пицца с креветками": 228,
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

# ─────────────────────────────────────────
#  СИСТЕМА МЕДИЦИНСКИХ ОГРАНИЧЕНИЙ
# ─────────────────────────────────────────

HEALTH_CONDITIONS = {
    "диабет": {
        "label": "🩸 Сахарный диабет",
        "banned_foods": [
            "виноград", "арбуз", "дыня", "ананас", "манго", "банан",
            "протеиновое печенье", "протеиновый пудинг",
            "макароны с куриным фаршем", "макароны с котлетой", "макароны",
        ],
        "safe_replacements": {
            "виноград": "черника", "арбуз": "клубника", "дыня": "малина",
            "ананас": "груша", "манго": "яблоко", "банан": "вишня",
            "макароны с куриным фаршем": "гречка с куриной грудкой",
            "макароны с котлетой": "гречка с куриной грудкой",
            "макароны": "гречка",
            "протеиновое печенье": "высокобелковый творог",
            "протеиновый пудинг": "протеиновый йогурт",
        },
        "food_note": "🩸 При диабете высокий ГИ опасен скачками сахара. Заменяй высокоуглеводные фрукты и быстрые углеводы на низкогликемические варианты.",
        "banned_exercises": [],
        "workout_note": "🩸 Контролируй сахар до и после тренировки. При гипогликемии — короткий перекус перед нагрузкой.",
    },
    "аллергия_глютен": {
        "label": "🌾 Аллергия на глютен",
        "banned_foods": [
            "макароны", "макароны с куриным фаршем", "макароны с котлетой",
            "овсянка", "булгур", "куриные наггетсы запечённые",
            "куриные котлеты замороженные", "куриные фрикадельки замороженные",
            "куриные сосиски", "протеиновое печенье", "протеиновый батончик",
        ],
        "safe_replacements": {
            "макароны": "гречка", "макароны с куриным фаршем": "гречка с куриной грудкой",
            "макароны с котлетой": "рис с куриным бедром",
            "овсянка": "гречка варёная", "булгур": "бурый рис",
            "куриные наггетсы запечённые": "запечённая куриная грудка",
            "куриные котлеты замороженные": "тефтели куриные домашние",
            "куриные фрикадельки замороженные": "тефтели куриные домашние",
            "куриные сосиски": "запечённая куриная грудка",
            "протеиновое печенье": "высокобелковый творог",
            "протеиновый батончик": "орехи с фруктом",
        },
        "food_note": "🌾 Глютен содержится в пшенице (макароны, овсянка, панировка полуфабрикатов). Гречка, рис, мясо и овощи безопасны.",
        "banned_exercises": [],
        "workout_note": "",
    },
    "аллергия_лактоза": {
        "label": "🥛 Непереносимость лактозы",
        "banned_foods": [
            "высокобелковый творог", "высокобелковый творог (0%)",
            "протеин казеиновый", "протеин казеиновый (порция 30г)",
            "протеиновый йогурт", "протеиновый пудинг",
        ],
        "safe_replacements": {
            "высокобелковый творог": "консервированная курица",
            "высокобелковый творог (0%)": "консервированная курица",
            "протеин казеиновый": "протеин сывороточный",
            "протеин казеиновый (порция 30г)": "протеин сывороточный (порция 30г)",
            "протеиновый йогурт": "орехи с фруктом",
            "протеиновый пудинг": "протеиновый батончик",
        },
        "food_note": "🥛 Молочные продукты (творог, йогурт, казеин) под запретом. Сывороточный протеин-изолят обычно содержит минимум лактозы — проверь состав.",
        "banned_exercises": [],
        "workout_note": "",
    },
    "аллергия_орехи": {
        "label": "🥜 Аллергия на орехи",
        "banned_foods": ["миндаль", "грецкий орех", "кешью", "тыквенные семечки"],
        "safe_replacements": {
            "миндаль": "яблоко", "грецкий орех": "консервированная курица",
            "кешью": "протеиновый батончик", "тыквенные семечки": "яблоко",
        },
        "food_note": "🥜 Любые орехи исключены из рациона полностью. В полдниках заменяй их на белковые продукты или фрукты.",
        "banned_exercises": [],
        "workout_note": "",
    },
    "давление": {
        "label": "💔 Высокое давление / сердечные",
        "banned_foods": [
            "куриные сосиски", "куриные наггетсы запечённые",
            "консервированная курица", "консервированная индейка",
        ],
        "safe_replacements": {
            "куриные сосиски": "запечённая куриная грудка",
            "куриные наггетсы запечённые": "запечённая куриная грудка",
            "консервированная курица": "готовая варёная курица",
            "консервированная индейка": "индейка отварная",
        },
        "food_note": "💔 Ограничь соль — консервы и полуфабрикаты содержат много натрия. Готовь сам с минимумом соли, добавляй специи и травы.",
        "banned_exercises": ["Берпи", "Приседания с прыжком", "Джампинг джек"],
        "workout_note": "💔 Высокоинтенсивные интервальные упражнения (берпи, прыжки) исключены — резкие скачки пульса опасны. Кардио в спокойном темпе.",
    },
    "суставы": {
        "label": "🦴 Проблемы с суставами/связками",
        "banned_foods": [],
        "safe_replacements": {},
        "food_note": "",
        "banned_exercises": [
            "Приседания с прыжком", "Берпи", "Выпады поочерёдно", "Боковые выпады",
            "Жим ногами в тренажёре", "Разгибание ног в тренажёре", "Приседания",
        ],
        "workout_note": "🦴 Ударная нагрузка на суставы (прыжки, глубокие приседания, выпады) исключена. Замени на упражнения с малой амплитудой: ягодичный мост, планку, работу в блоках.",
    },
    "астма": {
        "label": "🫁 Астма / затруднённое дыхание",
        "banned_foods": [],
        "safe_replacements": {},
        "food_note": "🫁 При астме избегай продуктов-триггеров: сульфиты (сухофрукты, консервы, вино), арахис, орехи если на них есть реакция. Следи за гидратацией — обезвоживание сгущает слизь.",
        "banned_exercises": [
            "Берпи", "Приседания с прыжком", "Джампинг джек",
        ],
        "workout_note": "🫁 Высокоинтенсивное кардио и упражнения с прыжками могут спровоцировать бронхоспазм. Держи ингалятор рядом. Предпочти ходьбу на дорожке, эллипс в умеренном темпе — пульс не выше 120-125 уд/мин. Разминка обязательна не менее 10 мин.",
    },
}

def get_user_conditions(profile):
    if not profile: return []
    raw = profile.get("health_conditions") or ""
    return [c for c in raw.split(",") if c and c in HEALTH_CONDITIONS]

def get_banned_foods(profile):
    banned = set()
    for cond in get_user_conditions(profile):
        banned.update(HEALTH_CONDITIONS[cond]["banned_foods"])
    return banned

def get_safe_replacement(profile, food):
    for cond in get_user_conditions(profile):
        rules = HEALTH_CONDITIONS[cond]
        if food in rules["banned_foods"]:
            return rules["safe_replacements"].get(food, food)
    return food

def get_banned_exercises(profile):
    banned = set()
    for cond in get_user_conditions(profile):
        banned.update(HEALTH_CONDITIONS[cond]["banned_exercises"])
    return banned

def get_health_food_notes(profile):
    notes = []
    for cond in get_user_conditions(profile):
        note = HEALTH_CONDITIONS[cond]["food_note"]
        if note: notes.append(note)
    return notes

def get_health_workout_notes(profile):
    notes = []
    for cond in get_user_conditions(profile):
        note = HEALTH_CONDITIONS[cond]["workout_note"]
        if note: notes.append(note)
    return notes

def apply_health_filter(profile, dish_text):
    """Заменяет упоминания запрещённых продуктов в тексте блюда на безопасные"""
    banned = get_banned_foods(profile)
    if not banned: return dish_text, False
    replaced = False
    result = dish_text
    for food in banned:
        if food in result:
            replacement = get_safe_replacement(profile, food)
            result = result.replace(food, replacement)
            replaced = True
    return result, replaced

MEAL_FOODS = {
    "🍳 Завтрак": {
        "белок": ["яйцо","омлет (2 яйца)","готовая варёная курица",
                  "консервированная курица","высокобелковый творог (0%)"],
        "углеводы": ["овсянка", "гречка в пакете"],
        "овощи": ["огурец", "помидор"],
        "спортпит": ["протеин сывороточный (порция 30г)", "протеиновый йогурт"],
    },
    "🍗 Обед": {
        "белок": ["куриная грудка", "куриное бедро", "индейка", "говядина",
                  "готовая варёная курица", "консервированная курица", "консервированная индейка",
                  "куриные котлеты замороженные", "куриные фрикадельки замороженные",
                  "куриские сосиски"],
        "углеводы": ["гречка","бурый рис","булгур","макароны","гречка в пакете","рис в пакете"],
        "готовые блюда": ["макароны с куриным фаршем","макароны с котлетой",
                          "тефтели куриные домашние","тефтели говяжьи домашние",
                          "запечённая говядина","запечённая куриная грудка"],
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
        "белок": ["куриная грудка","куриное бедро","индейка","говядина",
                  "готовая варёная курица","куриные котлеты замороженные",
                  "куриные наггетсы запечённые","тефтели куриные домашние",
                  "тефтели говяжьи домашние","запечённая говядина","запечённая куриная грудка"],
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
    "плов с курицей": 300, "плов со свининой": 280, "плов с говядиной": 280, "плов с бараниной": 280,
    "протеиновый милкшейк ваниль": 300, "протеиновый милкшейк шоколад": 300,
    "протеиновый милкшейк клубника": 300, "банановый милкшейк (без сахара)": 300,
    "ягодный смузи": 350, "зелёный смузи": 350,
    "куриный суп с овощами": 400, "борщ без картофеля": 400,
    "томатный суп": 400, "суп из чечевицы": 400,
    "тунец консервированный": 185, "лосось запечённый": 180, "тилапия запечённая": 200,
    "творожная запеканка": 200, "сырники из творога": 150, "протеиновые оладьи": 150,
    "картофельное пюре": 200, "запечённый картофель": 200,
    "кускус": 65, "полба": 65, "хумус": 80,
    "рисовые хлебцы": 40, "цельнозерновые хлебцы": 40,
    "авокадо": 100, "оливки": 50,
    "кефир 1%": 250, "ряженка 2.5%": 250, "натуральный йогурт без сахара": 200,
    "миндальный молочный коктейль": 300, "кокосовый молочный коктейль": 300,
    "безлактозный молочный коктейль": 300, "арахисовый молочный коктейль": 300, "овсяный молочный коктейль": 300,
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

ALL_CARD_PRODUCTS = set(FOOD_GROUPS.get("фрукты", [])) | set(FOOD_GROUPS.get("спортпит", []))

PRODUCT_CARDS = {
    "яблоко":    {"emoji":"🍎","gi":"низкий (36)","protein":"0.3г","best_time":"Полдник, до 19:00","tip":"Пектин замедляет усвоение сахара. Лучший выбор для похудения.","warn":""},
    "банан":     {"emoji":"🍌","gi":"средний (51)","protein":"1.1г","best_time":"До/после тренировки, утром","tip":"Быстрое восстановление после нагрузки. Калий защищает мышцы от судорог.","warn":"⚠️ Не вечером — высокий ГИ поднимет инсулин перед сном."},
    "апельсин":  {"emoji":"🍊","gi":"низкий (43)","protein":"0.9г","best_time":"Утром, полдник","tip":"Витамин C ускоряет жиросжигание. Клетчатка насыщает надолго.","warn":""},
    "мандарин":  {"emoji":"🍊","gi":"низкий (40)","protein":"0.8г","best_time":"Полдник, утром","tip":"Нобилетин ускоряет метаболизм жиров.","warn":""},
    "грейпфрут": {"emoji":"🍋","gi":"низкий (25)","protein":"0.7г","best_time":"Утром натощак или за 30 мин до еды","tip":"Нарингенин снижает инсулин и активирует жиросжигание.","warn":"⚠️ Не совмещать с некоторыми лекарствами."},
    "киви":      {"emoji":"🥝","gi":"низкий (50)","protein":"1.1г","best_time":"Полдник, утром","tip":"Витамин C в 2 раза больше чем в апельсине. Лучший выбор по соотношению калории/польза.","warn":""},
    "манго":     {"emoji":"🥭","gi":"средний (51)","protein":"0.6г","best_time":"До 16:00, после тренировки","tip":"Мангиферин ускоряет метаболизм. Много витамина A.","warn":"⚠️ Не более 150г — высокое содержание сахара."},
    "персик":    {"emoji":"🍑","gi":"низкий (42)","protein":"0.9г","best_time":"Полдник","tip":"Низкокалорийный, хорошо насыщает за счёт клетчатки.","warn":""},
    "слива":     {"emoji":"🫐","gi":"низкий (40)","protein":"0.7г","best_time":"Полдник, утром","tip":"Сорбитол улучшает пищеварение. Антиоксиданты снижают воспаление.","warn":""},
    "виноград":  {"emoji":"🍇","gi":"средний (59)","protein":"0.6г","best_time":"До тренировки","tip":"Ресвератрол — мощный антиоксидант для сосудов.","warn":"⚠️ Много сахара — не более 150г. Не вечером."},
    "арбуз":     {"emoji":"🍉","gi":"высокий (72)","protein":"0.6г","best_time":"Полдник, отдельно от еды","tip":"92% воды — отличная гидратация. Очень мало калорий.","warn":"⚠️ Есть отдельно, не после другой еды."},
    "дыня":      {"emoji":"🍈","gi":"высокий (65)","protein":"0.6г","best_time":"Полдник, отдельно","tip":"Много воды и калия. Мочегонный эффект помогает при отёках.","warn":"⚠️ Есть строго отдельно."},
    "ананас":    {"emoji":"🍍","gi":"средний (59)","protein":"0.5г","best_time":"После еды, полдник","tip":"Бромелайн расщепляет белки — помогает усвоению мяса.","warn":""},
    "черника":   {"emoji":"🫐","gi":"низкий (40)","protein":"0.7г","best_time":"Утром, полдник","tip":"Лучший выбор для похудения! Антоцианы снижают воспаление и жировые отложения.","warn":""},
    "клубника":  {"emoji":"🍓","gi":"низкий (40)","protein":"0.8г","best_time":"Полдник, утром","tip":"Очень мало калорий, много витамина C. Снижает тягу к сладкому.","warn":""},
    "малина":    {"emoji":"🍓","gi":"низкий (25)","protein":"1.2г","best_time":"Полдник, утром","tip":"Кетоны малины ускоряют расщепление жира. Самый низкий ГИ среди ягод.","warn":""},
    "вишня":     {"emoji":"🍒","gi":"низкий (22)","protein":"1.0г","best_time":"Полдник, перед сном","tip":"Мелатонин улучшает сон. Снижает воспаление после тренировок.","warn":""},
    "груша":     {"emoji":"🍐","gi":"низкий (38)","protein":"0.4г","best_time":"Полдник","tip":"Пектин создаёт длительное чувство сытости.","warn":""},
    "ягоды":     {"emoji":"🫐","gi":"низкий (35)","protein":"0.8г","best_time":"Утром, полдник","tip":"Смесь ягод — максимум антиоксидантов. Снижают кортизол.","warn":""},
    "протеиновый батончик":  {"emoji":"🍫","gi":"средний","protein":"~20г/бат.","best_time":"Полдник, после тренировки","tip":"Удобная замена полдника в дороге. Закрывает белковое окно после зала.","warn":"⚠️ Белок >20г, сахар <10г. Не более 1 шт/день."},
    "протеиновое печенье":   {"emoji":"🍪","gi":"средний","protein":"~15г/порц.","best_time":"Полдник","tip":"Психологически заменяет сладкое при тяге. Держит белок в норме.","warn":"⚠️ Белок >15г, калории <200/порцию. Не более 1 шт/день."},
    "протеин сывороточный":  {"emoji":"🥤","gi":"низкий","protein":"~23г/порц.","best_time":"После тренировки (30 мин), утром","tip":"Быстрое усвоение — идеально после зала. Защищает мышцы при дефиците.","warn":"✅ На воде или миндальном молоке (без лактозы)."},
    "протеин казеиновый":    {"emoji":"🥛","gi":"низкий","protein":"~24г/порц.","best_time":"Перед сном (за 30 мин)","tip":"Медленное усвоение 6-8 часов. Питает мышцы всю ночь.","warn":"✅ Лучший выбор на ночь при похудении."},
    "протеиновый йогурт":    {"emoji":"🥣","gi":"низкий","protein":"~10-15г/150г","best_time":"Завтрак, полдник","tip":"Пробиотики улучшают усвоение белка. Удобен в дороге.","warn":"✅ Без сахара, белок >10г/100г."},
    "протеиновый пудинг":    {"emoji":"🍮","gi":"низкий","protein":"~15г/порц.","best_time":"Полдник, вечер","tip":"Заменяет десерт. Психологически важен при долгом похудении.","warn":"⚠️ Белок >15г/порцию, калории <200/порцию."},
    "высокобелковый творог": {"emoji":"🧀","gi":"низкий","protein":"~18г/100г","best_time":"Завтрак, перед сном","tip":"Казеиновый белок — медленное усвоение. Отличный бюджетный вариант.","warn":"⚠️ Уточни переносимость лактозы."},
    "протеин сывороточный (порция 30г)": {"emoji":"🥤","gi":"низкий","protein":"~23г/порц.","best_time":"После тренировки, утром","tip":"Быстрое усвоение — идеально после зала.","warn":"✅ На воде или миндальном молоке."},
    "протеин казеиновый (порция 30г)":   {"emoji":"🥛","gi":"низкий","protein":"~24г/порц.","best_time":"Перед сном","tip":"Медленное усвоение — питает мышцы всю ночь.","warn":"✅ Лучший выбор на ночь."},
    "высокобелковый творог (0%)":        {"emoji":"🧀","gi":"низкий","protein":"~18г/100г","best_time":"Завтрак, перед сном","tip":"Казеиновый белок — медленное усвоение.","warn":"⚠️ Уточни переносимость лактозы."},
}

def build_product_card(name, profile=None):
    card  = PRODUCT_CARDS.get(name)
    grams = DEFAULT_PORTIONS.get(name, 100)
    kcal  = round(KCAL_PER_100G.get(name, 150) * grams / 100)
    group = find_group(name)
    group_ru = {"белок":"🥩 Белок","углеводы":"🍚 Углеводы","овощи":"🥦 Овощи",
                "орехи":"🌰 Орехи","фрукты":"🍎 Фрукты","спортпит":"💪 Спортпит",
                "готовые блюда":"🍽️ Готовые блюда"}.get(group, "")

    health_warn = ""
    if profile and name in get_banned_foods(profile):
        replacement = get_safe_replacement(profile, name)
        active = [HEALTH_CONDITIONS[c]["label"] for c in get_user_conditions(profile)
                  if name in HEALTH_CONDITIONS[c]["banned_foods"]]
        cond_text = ", ".join(active)
        health_warn = f"\n\n🚫 *Не рекомендуется при: {cond_text}*\n✅ Безопасная замена: *{replacement}*"

    if card:
        warn_text = f"\n\n{card['warn']}" if card["warn"] else ""
        return (
            f"{card['emoji']} *{name.capitalize()}*\n{'─'*20}\n"
            f"📊 Порция: *{grams}г = {kcal} ккал*\n"
            f"🔥 Калорийность: *{KCAL_PER_100G.get(name, 150)} ккал/100г*\n"
            f"💪 Белок: *{card['protein']}*\n"
            f"📈 Гликемический индекс: *{card['gi']}*\n"
            f"⏰ Лучшее время: *{card['best_time']}*\n{'─'*20}\n"
            f"💡 {card['tip']}{warn_text}{health_warn}"
        )
    else:
        warn = SEMIFAB_WARNINGS.get(name, "")
        return (
            f"🥗 *{name.capitalize()}*\n{'─'*20}\n"
            f"📊 Порция: *{grams}г = {kcal} ккал*\n"
            f"🔥 Калорийность: *{KCAL_PER_100G.get(name, 150)} ккал/100г*\n"
            f"📌 Группа: {group_ru}"
            + (f"\n\n{warn}" if warn else "") + health_warn
        )

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
        is_driver INTEGER DEFAULT 0,
        home_workouts INTEGER DEFAULT 0,
        health_conditions TEXT DEFAULT "",
        drying_mode INTEGER DEFAULT 0,
        drying_weeks INTEGER DEFAULT 0,
        drying_start TEXT DEFAULT "")''')
    c.execute('''CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        workout_type TEXT, fatigue_after INTEGER DEFAULT 0, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sleep (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        sleep_time TEXT, wake_time TEXT,
        duration_hours REAL, quality INTEGER, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS food_diary (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        meal TEXT, product TEXT, grams REAL, kcal REAL, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS workout_weights (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        exercise TEXT, weight_kg REAL, reps INTEGER, sets INTEGER, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS wellbeing (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        mood INTEGER, energy INTEGER, stress INTEGER, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS streak (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        last_entry_date TEXT, current_streak INTEGER DEFAULT 0,
        best_streak INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS inbody (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        weight REAL, muscle_mass REAL, fat_percent REAL, fat_mass_kg REAL,
        water REAL, protein REAL, bone REAL, visceral_fat REAL, bmi REAL,
        lean_mass REAL, bmr INTEGER, tdee INTEGER, optimal_weight REAL,
        report_date TEXT, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        achievement_key TEXT, unlocked_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS waist (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        waist_cm REAL, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS supplements (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        supplement TEXT, taken_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mood_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        mood INTEGER, stress INTEGER, energy INTEGER, note TEXT, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        part TEXT, cm REAL, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS if_tracker (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        protocol TEXT, start_time TEXT, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        challenge_key TEXT, start_date TEXT, progress INTEGER DEFAULT 0,
        completed INTEGER DEFAULT 0,
        UNIQUE(user_id, challenge_key))''')
    c.execute('''CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        friend_id INTEGER,
        UNIQUE(user_id, friend_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS pressure_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        systolic INTEGER, diastolic INTEGER, pulse INTEGER, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS medications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        name TEXT, dose TEXT, times_per_day INTEGER, active INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE IF NOT EXISTS medication_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        med_id INTEGER, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        reminder_text TEXT, hour INTEGER, minute INTEGER,
        repeat_daily INTEGER DEFAULT 1, active INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE IF NOT EXISTS favorite_dishes (
        user_id INTEGER, dish TEXT,
        PRIMARY KEY (user_id, dish))''')
    c.execute('''CREATE TABLE IF NOT EXISTS meal_templates (
        user_id INTEGER, name TEXT, items_json TEXT,
        PRIMARY KEY (user_id, name))''')
    c.execute('''CREATE TABLE IF NOT EXISTS sleep_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        date TEXT, hours REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS caffeine_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        date TEXT, source TEXT, mg INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_xp (
        user_id INTEGER PRIMARY KEY, total_xp INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS weekly_challenge (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        challenge_id TEXT, start_date TEXT, completed INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS exercise_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        date TEXT, exercise TEXT, weight_kg REAL, sets INTEGER, reps INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS cardio_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        start_time TEXT, end_time TEXT, kcal INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS partner_links (
        user_id INTEGER, partner_id INTEGER,
        PRIMARY KEY (user_id, partner_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT, referrer_id INTEGER,
        new_user_id INTEGER, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS water_ml_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        date TEXT, ml INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS stress_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        date TEXT, level INTEGER, note TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS cycle_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        period_start TEXT, period_end TEXT, cycle_len INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS hrv_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        date TEXT, hrv INTEGER, resting_pulse INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS body_photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        date TEXT, file_id TEXT, note TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS one_rm_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        exercise TEXT, weight_kg REAL, reps INTEGER, one_rm REAL, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS health_import_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        source TEXT, imported_at TEXT, records INTEGER)''')
    # Миграция
    for col, dflt in [
        ("fatigue","0"), ("last_workout_date","''"), ("next_workout_override","''"),
        ("reminders_enabled","1"), ("cheatmeal_used","0"), ("cheatmeal_week","''"),
        ("is_driver","0"),
        ("home_workouts","0"),
        ("health_conditions","''"),
        ("drying_mode","0"),
        ("drying_weeks","0"),
        ("drying_start","''"),
    ]:
        try:
            c.execute(f"ALTER TABLE user_profile ADD COLUMN {col} TEXT DEFAULT {dflt}")
        except Exception:
            pass
    conn.commit(); conn.close()

_profile_cache = {}  # {uid: (profile_dict, timestamp)}
_CACHE_TTL = 300  # 5 минут

def get_profile(uid):
    import time as _time
    now_ts = _time.time()
    if uid in _profile_cache:
        cached, ts = _profile_cache[uid]
        if now_ts - ts < _CACHE_TTL:
            return cached
    conn = sqlite3.connect("weight_tracker.db")
    row = conn.execute("SELECT * FROM user_profile WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    if not row: return None
    keys = ["user_id","current_weight","target_weight","height","age",
            "gym_days","workout_pref","deadline_weeks","is_sick","sick_since",
            "fatigue","last_workout_date","next_workout_override",
            "reminders_enabled","cheatmeal_used","cheatmeal_week","is_driver","home_workouts",
            "health_conditions","drying_mode","drying_weeks","drying_start"]
    d = dict(zip(keys, row))
    # Приводим типы
    for k in ("is_sick","fatigue","reminders_enabled","cheatmeal_used","is_driver","home_workouts","drying_mode"):
        d[k] = int(d[k]) if d[k] else 0
    d["health_conditions"] = d.get("health_conditions") or ""
    _profile_cache[uid] = (d, __import__("time").time())
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
    # Сбрасываем кэш при сохранении
    if uid in _profile_cache:
        del _profile_cache[uid]

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

# ─────────────────────────────────────────
#  ОБХВАТ ТАЛИИ
# ─────────────────────────────────────────

def add_waist(uid, cm):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("INSERT INTO waist (user_id,waist_cm,date) VALUES (?,?,?)",
                 (uid, cm, now_samara().strftime("%Y-%m-%d %H:%M")))
    conn.commit(); conn.close()

def get_waist_history(uid, limit=14):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute("SELECT waist_cm,date FROM waist WHERE user_id=? ORDER BY id DESC LIMIT ?",
                        (uid, limit)).fetchall()
    conn.close()
    return list(reversed(rows))

# ─────────────────────────────────────────
#  ДОСТИЖЕНИЯ И БЕЙДЖИ
# ─────────────────────────────────────────

ACHIEVEMENTS = {
    "first_weight":     {"emoji":"⚖️",  "name":"Первый шаг",        "desc":"Внёс первый вес"},
    "lose_1kg":         {"emoji":"🔥",  "name":"Минус 1 кг",        "desc":"Сбросил первый килограмм"},
    "lose_5kg":         {"emoji":"🌟",  "name":"Минус 5 кг",        "desc":"Сбросил 5 кг — это серьёзно!"},
    "lose_10kg":        {"emoji":"💎",  "name":"Минус 10 кг",       "desc":"Сбросил 10 кг — ты молодец!"},
    "lose_half":        {"emoji":"🏆",  "name":"Полпути",           "desc":"Достиг 50% от цели"},
    "goal_reached":     {"emoji":"🎯",  "name":"ЦЕЛЬ ДОСТИГНУТА",   "desc":"Достиг своего целевого веса!"},
    "streak_7":         {"emoji":"🔥",  "name":"Неделя без пропусков","desc":"7 дней подряд вносил данные"},
    "streak_30":        {"emoji":"💪",  "name":"Месяц без пропусков","desc":"30 дней подряд вносил данные"},
    "streak_100":       {"emoji":"👑",  "name":"100 дней",          "desc":"100 дней подряд — легенда!"},
    "first_workout":    {"emoji":"🏋️", "name":"Первая тренировка", "desc":"Завершил первую тренировку"},
    "workouts_10":      {"emoji":"💪",  "name":"10 тренировок",     "desc":"Завершил 10 тренировок"},
    "workouts_50":      {"emoji":"🥇",  "name":"50 тренировок",     "desc":"Завершил 50 тренировок"},
    "steps_10k":        {"emoji":"👟",  "name":"10 000 шагов",      "desc":"Прошёл 10 000 шагов за день"},
    "steps_100k":       {"emoji":"🚶",  "name":"100 000 шагов",     "desc":"Суммарно прошёл 100 000 шагов"},
    "water_week":       {"emoji":"💧",  "name":"Неделя с водой",    "desc":"7 дней подряд выполнял норму воды"},
    "inbody_done":      {"emoji":"📋",  "name":"Первый InBody",     "desc":"Загрузил первый отчёт InBody"},
    "drying_start":     {"emoji":"🏆",  "name":"На сушке",          "desc":"Активировал режим сушки"},
    "drying_finish":    {"emoji":"🏅",  "name":"Сушка завершена",   "desc":"Успешно завершил режим сушки"},
    "sleep_week":       {"emoji":"😴",  "name":"Сон под контролем", "desc":"7 дней подряд записывал сон"},
}

def get_unlocked_achievements(uid):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute("SELECT achievement_key, unlocked_date FROM achievements WHERE user_id=? ORDER BY id",
                        (uid,)).fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

def unlock_achievement(uid, key):
    """Выдаёт достижение если ещё не получено. Возвращает True если выдано впервые."""
    if key not in ACHIEVEMENTS:
        return False
    conn = sqlite3.connect("weight_tracker.db")
    ex = conn.execute("SELECT id FROM achievements WHERE user_id=? AND achievement_key=?",
                      (uid, key)).fetchone()
    if ex:
        conn.close()
        return False
    conn.execute("INSERT INTO achievements (user_id,achievement_key,unlocked_date) VALUES (?,?,?)",
                 (uid, key, now_samara().strftime("%Y-%m-%d")))
    conn.commit(); conn.close()
    return True

def check_and_unlock(uid):
    """Проверяет все условия и выдаёт новые достижения. Возвращает список новых."""
    new_achievements = []
    profile = get_profile(uid)
    if not profile: return []

    wd = get_weights(uid)
    sd = get_steps(uid, limit=200)
    current, best = get_streak(uid)
    workouts_count = 0
    try:
        conn = sqlite3.connect("weight_tracker.db")
        workouts_count = conn.execute("SELECT COUNT(*) FROM workouts WHERE user_id=?", (uid,)).fetchone()[0]
        conn.close()
    except Exception:
        pass

    checks = [
        ("first_weight",  len(wd) >= 1),
        ("lose_1kg",      len(wd) >= 2 and (wd[0][0] - wd[-1][0]) >= 1),
        ("lose_5kg",      len(wd) >= 2 and (wd[0][0] - wd[-1][0]) >= 5),
        ("lose_10kg",     len(wd) >= 2 and (wd[0][0] - wd[-1][0]) >= 10),
        ("lose_half",     len(wd) >= 2 and profile.get("target_weight") and
                          (wd[0][0] - wd[-1][0]) >= (wd[0][0] - profile["target_weight"]) * 0.5),
        ("goal_reached",  len(wd) >= 1 and profile.get("target_weight") and
                          wd[-1][0] <= profile["target_weight"]),
        ("streak_7",      current >= 7),
        ("streak_30",     current >= 30),
        ("streak_100",    current >= 100),
        ("first_workout", workouts_count >= 1),
        ("workouts_10",   workouts_count >= 10),
        ("workouts_50",   workouts_count >= 50),
        ("steps_10k",     any(s >= 10000 for s,_ in sd)),
        ("steps_100k",    sum(s for s,_ in sd) >= 100000),
        ("inbody_done",   get_last_inbody(uid) is not None),
        ("drying_start",  int(profile.get("drying_mode") or 0) == 1),
    ]

    for key, condition in checks:
        if condition and unlock_achievement(uid, key):
            new_achievements.append(key)

    return new_achievements

def build_achievements_text(uid):
    unlocked = get_unlocked_achievements(uid)
    if not unlocked:
        return None
    lines = []
    for key, ach in ACHIEVEMENTS.items():
        if key in unlocked:
            lines.append(f"{ach['emoji']} *{ach['name']}* — {ach['desc']} ✅ ({unlocked[key]})")
        else:
            lines.append(f"🔒 *{ach['name']}* — {ach['desc']}")
    total = len(unlocked)
    return f"🏅 *МОИ ДОСТИЖЕНИЯ* ({total}/{len(ACHIEVEMENTS)})\n{'─'*24}\n\n" + "\n".join(lines)

# ─────────────────────────────────────────
#  ТАЙМЕР ОТДЫХА МЕЖДУ ПОДХОДАМИ
# ─────────────────────────────────────────

REST_TIMERS = {
    "60 сек": 60,
    "90 сек": 90,
    "120 сек": 120,
    "180 сек": 180,
}

def rest_timer_worker(uid, seconds, start_time_str):
    """Фоновый поток — ждёт N секунд и отправляет сообщение"""
    time.sleep(seconds)
    try:
        bot.send_message(uid,
            f"⏱️ *{seconds} секунд прошло — начинай следующий подход!* 💪\n\n"
            f"Начало отдыха: {start_time_str}",
            parse_mode="Markdown")
    except Exception:
        pass

def get_last_waist(uid):
    conn = sqlite3.connect("weight_tracker.db")
    row = conn.execute("SELECT waist_cm,date FROM waist WHERE user_id=? ORDER BY id DESC LIMIT 1",
                       (uid,)).fetchone()
    conn.close()
    return row

def analyze_waist(profile, waist_cm):
    """Оценка риска по обхвату талии (стандарт ВОЗ для мужчин/женщин)"""
    # Упрощённо: для мужчин риск начинается с 94см (повышенный) и 102см (высокий)
    # Для женщин — 80см и 88см. Профиль не хранит пол явно, используем мужские нормы по умолчанию
    if waist_cm < 94:
        return "✅ Низкий риск — талия в норме."
    elif waist_cm < 102:
        return "🟡 Повышенный риск — стоит обратить внимание на висцеральный жир."
    else:
        return "🔴 Высокий риск — рекомендуется проконсультироваться с врачом по поводу здоровья сердца."

def build_waist_chart(uid):
    history = get_waist_history(uid, limit=10)
    if len(history) < 2: return None
    values = [w for w,_ in history]
    dates  = [d[:10] for _,d in history]
    mn, mx = min(values), max(values)
    rng    = mx - mn if mx != mn else 1
    lines  = []
    for row in range(5, -1, -1):
        thr  = mn + rng*row/5
        line = f"{thr:5.1f} |" + "".join(" ●" if v >= thr-rng/10 else "  " for v in values)
        lines.append(line)
    lines.append("       " + "──"*len(values))
    lines.append("       " + " ".join(d[8:] for d in dates))
    return "\n".join(lines)

# ─────────────────────────────────────────
#  INBODY — ПАРСИНГ PDF ОТЧЁТОВ DDX FITNESS
# ─────────────────────────────────────────

def add_inbody_record(uid, data):
    """Сохраняет результаты замера InBody в БД"""
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute(
        "INSERT INTO inbody (user_id,weight,muscle_mass,fat_percent,fat_mass_kg,water,protein,"
        "bone,visceral_fat,bmi,lean_mass,bmr,tdee,optimal_weight,report_date,date) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (uid, data.get("weight"), data.get("muscle"), data.get("fat_percent"), data.get("fat_mass_kg"),
         data.get("water"), data.get("protein"), data.get("bone"), data.get("visceral_fat"),
         data.get("bmi"), data.get("lean_mass"), data.get("bmr"), data.get("tdee"),
         data.get("optimal_weight"), data.get("report_date"), now_samara().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit(); conn.close()

def get_inbody_history(uid, limit=10):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute(
        "SELECT weight,muscle_mass,fat_percent,fat_mass_kg,water,protein,bone,visceral_fat,"
        "bmi,lean_mass,bmr,tdee,optimal_weight,report_date,date FROM inbody "
        "WHERE user_id=? ORDER BY id DESC LIMIT ?", (uid, limit)
    ).fetchall()
    conn.close()
    return list(reversed(rows))

def get_last_inbody(uid):
    conn = sqlite3.connect("weight_tracker.db")
    row = conn.execute(
        "SELECT weight,muscle_mass,fat_percent,fat_mass_kg,water,protein,bone,visceral_fat,"
        "bmi,lean_mass,bmr,tdee,optimal_weight,report_date,date FROM inbody "
        "WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,)
    ).fetchone()
    conn.close()
    return row

def get_last_inbody_dict(uid):
    """То же самое, но в виде словаря для удобной передачи в calc_plan()"""
    row = get_last_inbody(uid)
    if not row: return None
    keys = ["weight","muscle","fat_percent","fat_mass_kg","water","protein","bone",
            "visceral_fat","bmi","lean_mass","bmr","tdee","optimal_weight","report_date","date"]
    return dict(zip(keys, row))

def get_user_plan(uid, profile=None):
    """
    Универсальная обёртка: считает план питания с учётом последнего замера InBody,
    если он есть. Использовать вместо прямого вызова calc_plan(profile) везде в боте.
    """
    if profile is None:
        profile = get_profile(uid)
    if not profile:
        return None
    inbody = get_last_inbody_dict(uid)
    return calc_plan(profile, inbody=inbody)

def parse_inbody_pdf(file_path):
    """
    Парсит PDF-отчёт InBody (формат DDX Fitness) и извлекает показатели.
    Возвращает словарь с данными или None если не удалось распознать.
    """
    if not PDF_SUPPORT:
        return None, "Парсинг PDF недоступен — на сервере не установлена библиотека pdfplumber."

    try:
        with pdfplumber.open(file_path) as pdf:
            text = pdf.pages[0].extract_text()
    except Exception as e:
        return None, f"Не удалось открыть PDF: {e}"

    if not text or "Мышцы" not in text or "Жир" not in text:
        return None, "Это не похоже на отчёт InBody — нужные поля не найдены."

    patterns = {
        "weight":         r"Вес\s*(?:Выше нормы|Ниже нормы|Норма)?\s*(\d+[.,]\d+)\s*кг",
        "muscle":         r"Мышцы\s*(?:Выше нормы|Ниже нормы|Норма)?\s*(\d+[.,]\d+)\s*кг",
        "fat_percent":    r"Жир\s*(?:Выше нормы|Ниже нормы|Норма)?\s*(\d+[.,]\d+)\s*%",
        "water":          r"Вода\s*(\d+[.,]\d+)\s*л",
        "protein":        r"Белок\s*(\d+[.,]\d+)\s*кг",
        "bone":           r"Кости\s*(\d+[.,]\d+)\s*кг",
        "visceral_fat":   r"Висцеральный жир\s*(?:Выше нормы|Ниже нормы|Норма)?\s*(\d+)",
        "bmi":            r"Индекс массы тела\s*(?:Выше нормы|Ниже нормы|Норма)?\s*(\d+[.,]\d+)",
        "lean_mass":      r"Безжировая масса\s*(\d+[.,]\d+)\s*кг",
        "bmr":            r"Обмен веществ\s*(\d+)",
        "tdee":           r"Суточная норма калорий\s*(\d+)\s*ккал",
        "optimal_weight": r"Оптимальный вес\s*(\d+[.,]\d+)\s*кг",
        "report_date":    r"Дата\s*(\d{2}\.\d{2}\.\d{2})",
    }

    result = {}
    for key, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            val = m.group(1).replace(",", ".")
            result[key] = val
        else:
            result[key] = None

    # Обязательные поля — без них отчёт нечитаем
    if not result["weight"] or not result["muscle"] or not result["fat_percent"]:
        return None, "Не удалось распознать основные показатели (вес/мышцы/жир) в отчёте."

    # Приводим типы
    for k in ("weight","muscle","fat_percent","water","protein","bone","bmi","lean_mass","optimal_weight"):
        if result.get(k):
            result[k] = float(result[k])
    for k in ("visceral_fat","bmr","tdee"):
        if result.get(k):
            result[k] = int(float(result[k]))

    # Вычисляем массу жира в кг (вес × % жира / 100)
    if result.get("weight") and result.get("fat_percent"):
        result["fat_mass_kg"] = round(result["weight"] * result["fat_percent"] / 100, 1)

    # Переименовываем для совместимости с add_inbody_record
    result["muscle"] = result.get("muscle")

    return result, None

def build_inbody_report(uid, data):
    """Формирует читаемый отчёт после успешного парсинга PDF"""
    last = get_last_inbody(uid)
    diff_block = ""
    if last:
        w_diff = round(data["weight"] - last[0], 1)
        m_diff = round(data["muscle"] - last[1], 1)
        f_diff = round(data["fat_percent"] - last[2], 1)
        diff_block = (
            f"\n📊 *Изменения с прошлого замера:*\n"
            f"⚖️ Вес: {w_diff:+.1f} кг\n"
            f"💪 Мышцы: {m_diff:+.1f} кг {'📈' if m_diff>=0 else '📉'}\n"
            f"🔥 Жир: {f_diff:+.1f} % {'📉' if f_diff<=0 else '📈'}\n"
        )

    visceral_note = ""
    if data.get("visceral_fat"):
        if data["visceral_fat"] > 10:
            visceral_note = "\n⚠️ *Висцеральный жир выше нормы* — это жир вокруг органов, повышает риск для сердца. Кардио и дефицит калорий снижают его быстрее всего."
        else:
            visceral_note = "\n✅ Висцеральный жир в норме."

    return (
        f"📋 *INBODY — РЕЗУЛЬТАТЫ ЗАМЕРА*\n{'─'*24}\n"
        f"📅 Дата отчёта: *{data.get('report_date') or '—'}*\n\n"
        f"⚖️ Вес: *{data['weight']} кг*\n"
        f"💪 Мышечная масса: *{data['muscle']} кг*\n"
        f"🔥 Жир: *{data['fat_percent']}%* (~{data.get('fat_mass_kg','—')} кг)\n"
        + (f"💧 Вода: *{data['water']} л*\n" if data.get('water') else "")
        + (f"🥩 Белок: *{data['protein']} кг*\n" if data.get('protein') else "")
        + (f"🦴 Кости: *{data['bone']} кг*\n" if data.get('bone') else "")
        + (f"🎯 Висцеральный жир: *{data['visceral_fat']}*\n" if data.get('visceral_fat') else "")
        + (f"📐 ИМТ: *{data['bmi']}*\n" if data.get('bmi') else "")
        + (f"💪 Безжировая масса: *{data['lean_mass']} кг*\n" if data.get('lean_mass') else "")
        + (f"\n🔥 Обмен веществ (BMR): *{data['bmr']} ккал*\n" if data.get('bmr') else "")
        + (f"🎯 Суточная норма: *{data['tdee']} ккал*\n" if data.get('tdee') else "")
        + (f"🏁 Оптимальный вес: *{data['optimal_weight']} кг*\n" if data.get('optimal_weight') else "")
        + diff_block + visceral_note +
        f"\n\n💡 Данные сохранены. Калораж в боте можно сверить с замером InBody — "
        f"если они сильно расходятся, обнови профиль через *«⚙️ Изменить профиль»*."
    )

def build_inbody_history_text(uid):
    history = get_inbody_history(uid, limit=10)
    if not history:
        return None
    lines = []
    for w, m, f, fm, water, prot, bone, visc, bmi, lean, bmr, tdee, opt, rdate, date in history:
        lines.append(f"• {rdate or date[:10]}: вес *{w}кг* | мышцы *{m}кг* | жир *{f}%*")
    return "\n".join(lines)

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

def calc_plan(profile, inbody=None):
    """
    inbody: последняя запись из таблицы inbody (если есть), используется чтобы:
    - подставить реальный замеренный BMR прибора вместо формулы (точнее)
    - скорректировать белок по факту мышечной массы, а не общему весу
    """
    w  = profile.get("current_weight") or 107
    h  = profile.get("height") or 194
    a  = profile.get("age") or 24
    gd = profile.get("gym_days") or 3
    is_driver = int(profile.get("is_driver") or 0)

    if inbody and inbody.get("bmr"):
        bmr = inbody["bmr"]  # реальный замер InBody точнее формулы
        bmr_source = "InBody"
    else:
        bmr = 10*w + 6.25*h - 5*a + 5
        bmr_source = "формула"

    base_mult = {1:1.30,2:1.35,3:1.45,4:1.50,5:1.55}.get(min(gd,5), 1.45)
    mult = base_mult - (0.05 if is_driver else 0)
    tdee = round(bmr * mult)
    deficit  = min(round(tdee*0.30), 1200)
    calories = tdee - deficit
    weekly   = round(deficit*7/7700, 2)
    to_lose  = w - (profile.get("target_weight") or 92)
    weeks_needed = round(to_lose/weekly) if weekly > 0 else 999

    # Белок: если есть данные о мышечной массе — считаем от неё точнее (2.2г/кг сухой массы)
    # вместо общего веса тела (который включает жир)
    if inbody and inbody.get("muscle"):
        protein = round(inbody["muscle"] * 2.2 + (w - inbody["muscle"]) * 0.5)
        protein_source = "по мышечной массе InBody"
    else:
        protein = round(w * 1.8)
        protein_source = "по общему весу"

    return {"bmr":round(bmr),"tdee":tdee,"calories":calories,
            "deficit":deficit,"protein":protein,
            "weekly_loss":weekly,"weeks_needed":weeks_needed,
            "bmr_source":bmr_source,"protein_source":protein_source}

# ─────────────────────────────────────────
#  РЕЖИМ СУШКИ
# ─────────────────────────────────────────

# Рационы для сушки — 2-3 варианта на каждую позицию с одинаковым калоражом
DRYING_BREAKFAST = [
    # (основное, варианты с тем же калоражом)
    {"main": "3 яйца варёных + 30г овсянки на воде",
     "alt1": "Омлет 3 яйца + 50г творога 0%",
     "alt2": "3 яйца + 20г гречки отварной",
     "kcal": 280},
    {"main": "4 яйца варёных (без желтка 2 шт) + огурец",
     "alt1": "Омлет из 3 яиц + шпинат",
     "alt2": "100г творога 0% + 2 яйца варёных",
     "kcal": 250},
    {"main": "3 яйца + 30г овсянки + черника 50г",
     "alt1": "100г творога 0% + 1 яйцо + зелень",
     "alt2": "Омлет 3 яйца + помидор + огурец",
     "kcal": 290},
]

DRYING_LUNCH = [
    {"main": "{breast}г куриной грудки варёной + 200г брокколи",
     "alt1": "{breast}г индейки + 200г стручковой фасоли",
     "alt2": "{breast}г куриной грудки + 200г шпината тушёного",
     "kcal_note": "без гарнира"},
    {"main": "{breast}г куриной грудки + 200г огурцов + зелень",
     "alt1": "{breast}г индейки варёной + 200г болгарского перца",
     "alt2": "{breast}г куриного бедра (без кожи) + 200г овощей",
     "kcal_note": "без гарнира"},
    {"main": "{breast}г куриной грудки запечённой + 150г брокколи",
     "alt1": "{breast}г говядины варёной + 200г стручковой фасоли",
     "alt2": "{breast}г индейки + 200г тушёного шпината",
     "kcal_note": "без гарнира"},
]

DRYING_SNACK = [
    {"main": "150г творога 0% + 1 огурец",
     "alt1": "100г куриного филе варёного + зелень",
     "alt2": "3 яйца варёных (без 1 желтка)",
     "kcal": 180},
    {"main": "150г творога 0% + зелень",
     "alt1": "120г куриной грудки + огурец",
     "alt2": "4 белка варёных + помидор",
     "kcal": 175},
    {"main": "100г куриного филе + 150г огурцов",
     "alt1": "150г творога 0% + зелёный чай",
     "alt2": "3 яйца варёных + сельдерей",
     "kcal": 185},
]

DRYING_DINNER = [
    {"main": "200г куриной грудки запечённой + 300г овощей на пару",
     "alt1": "200г индейки варёной + 300г брокколи",
     "alt2": "200г куриной грудки + 300г стручковой фасоли",
     "kcal_note": "~300 ккал"},
    {"main": "200г куриной грудки + 300г шпината тушёного",
     "alt1": "200г индейки + 300г смеси овощей на пару",
     "alt2": "180г говядины варёной + 300г брокколи",
     "kcal_note": "~310 ккал"},
    {"main": "200г куриной грудки варёной + огурцы/помидоры",
     "alt1": "200г индейки запечённой + 300г овощей",
     "alt2": "200г куриной грудки + 300г стручковой фасоли",
     "kcal_note": "~295 ккал"},
]

# Умный опрос для определения типа сушки
DRYING_SURVEY = [
    ("drying_q1", "🏆 *ОПРОС ДЛЯ РЕЖИМА СУШКИ*\n\n"
                  "Шаг 1/5 — Какой сейчас % жира?\n\n"
                  "Если не знаешь точно — оцени по фото:\n"
                  "1 — До 15% (видны кубики пресса)\n"
                  "2 — 15-20% (немного округлости)\n"
                  "3 — 20-25% (жир заметен, пресс не виден)\n"
                  "4 — Выше 25% (значительный жировой слой)"),
    ("drying_q2", "Шаг 2/5 — Сколько недель готов придерживаться строгого рациона?\n\n"
                  "1 — 4-6 недель (агрессивная сушка)\n"
                  "2 — 8-10 недель (стандартная)\n"
                  "3 — 12+ недель (мягкая, сохраняем мышцы)"),
    ("drying_q3", "Шаг 3/5 — Как переносишь низкоуглеводное питание?\n\n"
                  "1 — Хорошо, без проблем\n"
                  "2 — Бывает слабость и раздражительность\n"
                  "3 — Плохо, сильные голодные срывы"),
    ("drying_q4", "Шаг 4/5 — Цель сушки?\n\n"
                  "1 — Максимальный рельеф (соревнования/фото)\n"
                  "2 — Убрать лишний жир, сохранить мышцы\n"
                  "3 — Просто подсушиться к лету/событию"),
    ("drying_q5", "Шаг 5/5 — Сколько тренировок в неделю сможешь поддерживать на сушке?\n\n"
                  "1 — 5+ дней\n"
                  "2 — 3-4 дня\n"
                  "3 — 1-2 дня"),
]

def analyze_drying_survey(answers):
    """
    Анализирует ответы опроса и определяет:
    - тип сушки (классическая/мягкая/агрессивная)
    - рекомендуемый срок в неделях
    - дефицит калорий
    """
    fat_level   = int(answers.get("q1", 3))
    duration    = int(answers.get("q2", 2))
    tolerance   = int(answers.get("q3", 2))
    goal        = int(answers.get("q4", 2))
    training    = int(answers.get("q5", 2))

    # Определяем тип и срок
    if fat_level <= 2 and tolerance == 1 and goal == 1:
        drying_type = "агрессивная"
        weeks = 6
        deficit_pct = 40
        carbs_limit = "до 50г/день"
        desc = ("🔥 *Агрессивная сушка* — максимальный рельеф за короткий срок.\n"
                "Углеводы минимальны, белок максимальный. Требует опыта и дисциплины.")
    elif fat_level >= 4 or tolerance == 3:
        drying_type = "мягкая"
        weeks = 14
        deficit_pct = 20
        carbs_limit = "100-150г/день"
        desc = ("💚 *Мягкая сушка* — постепенное снижение жира с сохранением мышц.\n"
                "Комфортный дефицит, углеводы умеренные.")
    else:
        drying_type = "стандартная"
        weeks = 10
        deficit_pct = 30
        carbs_limit = "50-100г/день"
        desc = ("⚡ *Стандартная сушка* — оптимальный баланс скорости и комфорта.\n"
                "Умеренный дефицит, значительное снижение углеводов.")

    # Корректировка по тренировкам
    if training == 3:
        weeks = min(weeks + 2, 16)
        desc += "\n\n⚠️ При малом числе тренировок сушка идёт медленнее — увеличили срок."

    return {
        "type": drying_type,
        "weeks": weeks,
        "deficit_pct": deficit_pct,
        "carbs_limit": carbs_limit,
        "desc": desc,
    }

def calc_drying_plan(profile, inbody=None):
    """Расчёт рациона для режима сушки"""
    w  = profile.get("current_weight") or 107
    gd = profile.get("gym_days") or 3
    is_driver = int(profile.get("is_driver") or 0)

    if inbody and inbody.get("bmr"):
        bmr = inbody["bmr"]
    else:
        h = profile.get("height") or 194
        a = profile.get("age") or 24
        bmr = 10*w + 6.25*h - 5*a + 5

    base_mult = {1:1.30,2:1.35,3:1.45,4:1.50,5:1.55}.get(min(gd,5), 1.45)
    mult = base_mult - (0.05 if is_driver else 0)
    tdee = round(bmr * mult)

    drying_weeks = int(profile.get("drying_weeks") or 10)
    # Дефицит зависит от срока: чем агрессивнее — тем больше
    if drying_weeks <= 6:
        deficit_pct = 40
    elif drying_weeks <= 10:
        deficit_pct = 30
    else:
        deficit_pct = 20

    calories = max(round(tdee * (1 - deficit_pct/100)), 1200)
    # На сушке белок = 2.5г на кг сухой массы (защита мышц)
    muscle = inbody.get("muscle") if inbody else w * 0.6
    protein = round(muscle * 2.5) if muscle else round(w * 2.0)
    # Углеводы — минимум
    fat_g  = round(w * 0.8)
    carbs_g = max(round((calories - protein*4 - fat_g*9) / 4), 30)

    return {
        "calories": calories, "protein": protein,
        "fat": fat_g, "carbs": carbs_g,
        "tdee": tdee, "deficit": tdee - calories,
    }

def build_drying_ration(uid, for_tomorrow=False):
    """Строит рацион для режима сушки"""
    profile = get_profile(uid)
    if not profile: return "Сначала настрой профиль.", 0
    if profile.get("is_sick"): return build_sick_ration(), 0

    inbody = get_last_inbody_dict(uid)
    plan   = calc_drying_plan(profile, inbody)
    weekday = now_samara().weekday()
    if for_tomorrow: weekday = (weekday + 1) % 7

    idx = weekday % len(DRYING_BREAKFAST)
    b   = DRYING_BREAKFAST[idx]
    l   = DRYING_LUNCH[idx]
    s   = DRYING_SNACK[idx]
    d   = DRYING_DINNER[idx]

    breast = round(plan["protein"] * 0.35)  # ~35% белка на обед

    prefix = "📅 *РАЦИОН НА ЗАВТРА (СУШКА)*\n" if for_tomorrow else ""

    weights = get_weights(uid)
    analysis = analyze_progress(weights) if len(weights) >= 2 else None
    status = ""
    if analysis and not for_tomorrow:
        icons = {"fast":"📈","good":"✅","slow":"📉","plateau":"🪨","gain":"🚨"}
        status = f"{icons.get(analysis['status'],'')} {analysis['advice']}\n\n"

    ration = (
        f"{prefix}{'🏆 РЕЖИМ СУШКИ — РАЦИОН НА СЕГОДНЯ' if not for_tomorrow else ''}\n"
        f"{status}"
        f"{'─'*24}\n\n"
        f"🍳 *Завтрак* (~{b['kcal']} ккал):\n"
        f"  • {b['main']}\n"
        f"  • {b['alt1']}\n"
        f"  • {b['alt2']}\n\n"
        f"🍗 *Обед* ({l['kcal_note']}):\n"
        f"  • {l['main'].format(breast=breast)}\n"
        f"  • {l['alt1'].format(breast=breast)}\n"
        f"  • {l['alt2'].format(breast=breast)}\n\n"
        f"🍎 *Полдник* (~{s['kcal']} ккал):\n"
        f"  • {s['main']}\n"
        f"  • {s['alt1']}\n"
        f"  • {s['alt2']}\n\n"
        f"🌙 *Ужин* ({d['kcal_note']}):\n"
        f"  • {d['main']}\n"
        f"  • {d['alt1']}\n"
        f"  • {d['alt2']}\n\n"
        f"{'─'*24}\n"
        f"🎯 *~{plan['calories']} ккал* | 💪 Белок: *{plan['protein']}г*\n"
        f"🍚 Углеводы: *{plan['carbs']}г* | 🥑 Жиры: *{plan['fat']}г*\n\n"
        f"💧 Вода: *минимум 3.5л* — на сушке критично!\n"
        f"⚠️ Выбирай *любой из 3 вариантов* в каждом приёме — все равнозначны по калоражу."
    )
    return ration, plan["calories"]



def get_portions(calories):
    s = calories / 1950
    return {
        "breast": round(230*s), "carb": round(65*s), "snack": round(130*s),
        "dinner": "300г тушёных овощей" if s >= 1 else "только овощи без гарнира",
    }

# ─────────────────────────────────────────
#  РОТАЦИЯ БЛЮД ПО ДНЯМ НЕДЕЛИ
# ─────────────────────────────────────────

BREAKFAST_ROTATION = [
    {"name": "3 яйца + 60г овсянки на воде + помидор/огурец", "fast": "Готовая варёная курица + овсянка в пакете"},
    {"name": "Омлет с овощами (3 яйца, шпинат, помидор)", "fast": "Протеиновый йогурт + овсянка"},
    {"name": "Яйца варёные (3 шт) + овсянка + огурец", "fast": "Высокобелковый творог + ягоды"},
    {"name": "Омлет (2 яйца) + гречка в пакете + помидор", "fast": "Готовая варёная курица + гречка в пакете"},
    {"name": "Яичница (3 яйца) + овсянка на воде", "fast": "Протеин сывороточный + банан"},
    {"name": "3 яйца + овсянка + ягоды (черника/малина)", "fast": "Консервированная курица + овсянка в пакете"},
    {"name": "Омлет с овощами + 60г гречки", "fast": "Высокобелковый творог + яблоко"},
]

LUNCH_ROTATION = [
    {"name": "{breast}г куриной грудки + {carb}г гречки + салат", "fast": "Готовая курица из магазина + гречка в пакете"},
    {"name": "{breast}г куриного бедра запечённого + {carb}г бурого риса + перец", "fast": "Консервированная курица + рис в пакете"},
    {"name": "{breast}г индейки с булгуром + помидор", "fast": "Куриные котлеты замороженные + булгур"},
    {"name": "{breast}г говядины тушёной с овощами", "fast": "Куриные сосиски + гречка в пакете (не чаще раза в неделю)"},
    {"name": "Макароны с куриным фаршем ({carb}г макарон)", "fast": "Макароны с котлетой запечённой"},
    {"name": "{breast}г куриной грудки + {carb}г гречки + овощная смесь", "fast": "Тефтели куриные домашние + гречка в пакете"},
    {"name": "{breast}г куриного бедра + {carb}г бурого риса + салат", "fast": "Консервированная курица + гречка в пакете"},
]

DINNER_ROTATION = [
    {"name": "180г куриной грудки + {dinner}", "fast": "Замороженные котлеты (без панировки) + замороженные овощи"},
    {"name": "Тефтели куриные домашние (200г) + тушёная стручковая фасоль", "fast": "Куриные наггетсы запечённые + замороженная овощная смесь"},
    {"name": "180г запечённой говядины + брокколи на пару", "fast": "Готовая варёная курица + замороженные овощи"},
    {"name": "180г куриного бедра запечённого + тушёный шпинат", "fast": "Куриные фрикадельки замороженные + овощная смесь"},
    {"name": "Тефтели говяжьи домашние (200г) + овощи", "fast": "Куриные котлеты замороженные + брокколи"},
    {"name": "180г куриной грудки запечённой + {dinner}", "fast": "Готовая курица + тушёные замороженные овощи"},
    {"name": "180г индейки отварной + тушёные овощи", "fast": "Куриные наггетсы + замороженная смесь"},
]

SNACK_ROTATION = [
    {"name": "{snack}г куриного филе + 1 фрукт + 20г орехов", "fast": "Консервированная курица + яблоко"},
    {"name": "Творог высокобелковый (150г) + ягоды", "fast": "Протеиновый йогурт"},
    {"name": "Протеиновый коктейль + банан", "fast": "Протеиновый батончик"},
    {"name": "{snack}г индейки + груша + орехи", "fast": "Консервированная индейка + персик"},
    {"name": "Творог с ягодами (150г творога + 100г ягод)", "fast": "Протеиновое печенье"},
    {"name": "{snack}г куриного филе + апельсин + 20г миндаля", "fast": "Консервированная курица + мандарин"},
    {"name": "Протеиновый йогурт + клубника", "fast": "Протеиновый пудинг"},
]

def get_day_meal(rotation, weekday, **kwargs):
    item = rotation[weekday % len(rotation)]
    name = item["name"].format(**kwargs) if kwargs else item["name"]
    return name, item["fast"]

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

def predict_goal_date(wd, target_weight):
    """Предсказывает дату достижения цели на основе темпа последних взвешиваний"""
    if len(wd) < 3:
        return None
    # Берём последние 4 точки для более стабильного темпа
    recent = wd[-4:] if len(wd) >= 4 else wd
    try:
        first_w, first_d = recent[0]
        last_w, last_d = recent[-1]
        days_elapsed = (datetime.strptime(last_d[:10], "%Y-%m-%d") -
                        datetime.strptime(first_d[:10], "%Y-%m-%d")).days
        if days_elapsed < 1:
            return None
        rate_per_day = (first_w - last_w) / days_elapsed  # кг/день (положительный = похудение)
        if rate_per_day <= 0.001:
            return None  # нет прогресса
        remain = last_w - target_weight
        if remain <= 0:
            return None  # уже достигли
        days_left = round(remain / rate_per_day)
        goal_date = datetime.strptime(last_d[:10], "%Y-%m-%d") + timedelta(days=days_left)
        weeks_left = round(days_left / 7)
        return {"date": goal_date.strftime("%d.%m.%Y"), "weeks": weeks_left, "days": days_left,
                "rate_week": round(rate_per_day * 7, 2)}
    except Exception:
        return None

def check_plateau_advanced(wd):
    """Расширенный анализ плато — проверяет последние 2+ недели"""
    if len(wd) < 4:
        return None
    # Последние 3–4 взвешивания
    recent = wd[-4:]
    weights = [w for w, _ in recent]
    max_w = max(weights)
    min_w = min(weights)
    spread = round(max_w - min_w, 2)
    # Плато если разброс < 0.5 кг за последние 4 записи
    if spread < 0.5:
        tips = [
            "🔄 *Рефид-день:* увеличь калории на 300–400 ккал на 1–2 дня (углеводы).",
            "🚶 *Больше шагов:* добавь 2000–3000 шагов в день.",
            "💪 *Смени тренировку:* если привык к кардио — добавь силовую, и наоборот.",
            "⏰ *Измени время еды:* попробуй интервальное голодание 16/8.",
            "💧 *Проверь воду:* задержка жидкости маскирует потерю жира.",
        ]
        tip = random.choice(tips)
        return {"spread": spread, "weeks": len(recent), "tip": tip}
    return None

def get_exercise_progression(uid, exercise):
    """Возвращает историю прогрессии и рекомендацию по следующей тренировке"""
    history = get_exercise_history(uid, exercise, limit=5)
    if not history:
        return None
    last_weight, last_reps, last_sets, _ = history[-1]
    # Считаем средний тоннаж (вес * повт * подходы)
    tonnages = [w * r * s for w, r, s, _ in history]
    last_tonnage = tonnages[-1]
    # Рекомендация: +2.5 кг если последние 2 тренировки одинаковы или улучшились
    suggest_increase = False
    if len(history) >= 2:
        prev_weight = history[-2][0]
        if last_weight >= prev_weight and last_reps >= history[-2][1]:
            suggest_increase = True
    next_weight = round(last_weight + 2.5, 1) if suggest_increase else last_weight
    progress_pct = 0
    if len(history) >= 2 and history[0][0] > 0:
        progress_pct = round((last_weight - history[0][0]) / history[0][0] * 100, 1)
    return {
        "last_weight": last_weight, "last_reps": last_reps, "last_sets": last_sets,
        "next_weight": next_weight, "suggest_increase": suggest_increase,
        "progress_pct": progress_pct, "history": history,
    }

def build_exercise_analytics(uid):
    """Строит отчёт по прогрессии в упражнениях"""
    exercises = get_all_exercises(uid)
    if not exercises:
        return None
    lines = ["💪 *Прогресс в упражнениях:*\n"]
    for ex in exercises[:8]:  # Топ-8 упражнений
        prog = get_exercise_progression(uid, ex)
        if not prog:
            continue
        arrow = "📈 +2.5кг рекомендуется" if prog["suggest_increase"] else "🔁 удержи вес"
        pct_str = f" (+{prog['progress_pct']}% от старта)" if prog["progress_pct"] > 0 else ""
        lines.append(
            f"*{ex}*\n"
            f"  Последний: {prog['last_weight']}кг × {prog['last_reps']} × {prog['last_sets']}{pct_str}\n"
            f"  Следующий: {prog['next_weight']}кг — {arrow}"
        )
    if len(lines) <= 1:
        return None
    return "\n\n".join(lines)

# ─────────────────────────────────────────
#  ТРЕКЕР ДОБАВОК
# ─────────────────────────────────────────

SUPPLEMENTS_LIST = [
    "💊 Омега-3", "☀️ Витамин D", "🧲 Магний",
    "💊 Витамин C", "🫀 Коэнзим Q10", "🦴 Кальций",
    "🧬 Цинк", "💉 Витамин B12", "🌿 Ашваганда",
]

def log_supplement(uid, supplement):
    today = now_samara().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS supplements (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, supplement TEXT, taken_date TEXT)")
        conn.execute("INSERT INTO supplements (user_id, supplement, taken_date) VALUES (?,?,?)", (uid, supplement, today))
        conn.commit()

def get_supplements_today(uid):
    today = now_samara().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS supplements (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, supplement TEXT, taken_date TEXT)")
        rows = conn.execute("SELECT supplement FROM supplements WHERE user_id=? AND taken_date=?", (uid, today)).fetchall()
    return [r[0] for r in rows]

def get_supplements_streak(uid, supplement):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS supplements (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, supplement TEXT, taken_date TEXT)")
        rows = conn.execute("SELECT DISTINCT taken_date FROM supplements WHERE user_id=? AND supplement=? ORDER BY taken_date DESC LIMIT 30", (uid, supplement)).fetchall()
    if not rows:
        return 0
    streak = 0
    check_date = now_samara().date()
    for (d,) in rows:
        row_date = datetime.strptime(d, "%Y-%m-%d").date()
        if row_date == check_date:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    return streak

def build_supplements_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for s in SUPPLEMENTS_LIST:
        kb.add(types.KeyboardButton(s))
    kb.add(types.KeyboardButton("📊 Статистика добавок"))
    kb.add(types.KeyboardButton("🔙 Назад"))
    return kb

# ─────────────────────────────────────────
#  ТРЕКЕР НАСТРОЕНИЯ
# ─────────────────────────────────────────

MOOD_EMOJIS = {1: "😞", 2: "😕", 3: "😐", 4: "🙂", 5: "😄"}
STRESS_EMOJIS = {1: "🧘", 2: "😌", 3: "😐", 4: "😤", 5: "🤯"}

def log_mood(uid, mood, stress, energy, note=""):
    today = now_samara().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS mood_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, mood INTEGER, stress INTEGER, energy INTEGER, note TEXT, date TEXT)")
        conn.execute("DELETE FROM mood_log WHERE user_id=? AND date=?", (uid, today))
        conn.execute("INSERT INTO mood_log (user_id,mood,stress,energy,note,date) VALUES (?,?,?,?,?,?)",
                     (uid, mood, stress, energy, note, today))
        conn.commit()

def get_mood_today(uid):
    today = now_samara().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS mood_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, mood INTEGER, stress INTEGER, energy INTEGER, note TEXT, date TEXT)")
        row = conn.execute("SELECT mood,stress,energy,note FROM mood_log WHERE user_id=? AND date=?", (uid, today)).fetchone()
    return row

def get_mood_history(uid, days=7):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS mood_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, mood INTEGER, stress INTEGER, energy INTEGER, note TEXT, date TEXT)")
        rows = conn.execute("SELECT mood,stress,energy,date FROM mood_log WHERE user_id=? ORDER BY date DESC LIMIT ?", (uid, days)).fetchall()
    return rows

def mood_nutrition_advice(mood, stress, energy):
    advice = []
    if stress >= 4:
        advice.append("🍫 Стресс высокий — магний поможет: орехи, тёмный шоколад, гречка.")
    if energy <= 2:
        advice.append("⚡ Энергия низкая — добавь сложные углеводы: овсянка, банан, бурый рис.")
    if mood <= 2:
        advice.append("😊 Настроение низкое — омега-3 и триптофан: рыба, яйца, индейка.")
    if not advice:
        advice.append("✅ Всё в норме — питайся по плану!")
    return "\n".join(advice)

# ─────────────────────────────────────────
#  УМНЫЙ КБЖУ-СЧЁТЧИК
# ─────────────────────────────────────────

def get_daily_kcal_consumed(uid):
    today = now_samara().strftime("%Y-%m-%d")
    total = 0
    with sqlite3.connect(DB_PATH) as conn:
        try:
            rows = conn.execute("SELECT kcal FROM food_diary WHERE user_id=? AND date=?", (uid, today)).fetchall()
            total += sum(r[0] for r in rows if r[0])
        except Exception:
            pass
        try:
            rows2 = conn.execute("SELECT kcal FROM food_diary WHERE uid=? AND date=?", (uid, today)).fetchall()
            total += sum(r[0] for r in rows2 if r[0])
        except Exception:
            pass
    return round(total)

def get_daily_kcal_goal(uid):
    profile = get_profile(uid)
    if not profile:
        return 2000
    return profile.get("tdee") or profile.get("calories") or 2000

def build_kcal_status(uid):
    consumed = get_daily_kcal_consumed(uid)
    goal = get_daily_kcal_goal(uid)
    remain = goal - consumed
    pct = min(100, round(consumed / max(goal, 1) * 100))
    bar_len = 10
    filled = round(pct / 100 * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)
    status = "✅" if remain >= 0 else "⚠️"
    remain_str = f"+{abs(remain)} ккал перебор" if remain < 0 else f"{remain} ккал осталось"
    return (f"🍽️ *Калории сегодня:*\n"
            f"{bar} {pct}%\n"
            f"Съедено: *{consumed}* / *{goal}* ккал\n"
            f"{status} {remain_str}")

def suggest_meal_for_remaining(uid):
    remain = get_daily_kcal_goal(uid) - get_daily_kcal_consumed(uid)
    if remain < 100:
        return None
    candidates = []
    for name, data in RECIPES.items():
        kcal_str = data.get("kcal_portion", "")
        m = re.search(r"~?(\d+)", kcal_str)
        if m:
            kcal = int(m.group(1))
            if abs(kcal - remain) < remain * 0.35:
                candidates.append((name, kcal, abs(kcal - remain)))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[2])
    best = candidates[0]
    return f"📖 *{best[0]}* (~{best[1]} ккал) — подходит под твой остаток!"

# ─────────────────────────────────────────
#  АЧИВКИ И МОТИВАЦИОННЫЕ ЦИТАТЫ
# ─────────────────────────────────────────

MOTIVATIONAL_QUOTES = [
    "💪 «Каждый килограмм — это победа над собой вчерашним.»",
    "🔥 «Тело достигает то, во что верит разум.»",
    "🎯 «Прогресс, а не совершенство — вот цель.»",
    "⚡ «Дисциплина — это мост между целями и достижениями.»",
    "🏆 «Ты не похудел сегодня, но и не набрал — это тоже победа.»",
    "🌅 «Каждое утро — новый шанс стать лучше.»",
    "💡 «Маленькие ежедневные улучшения дают поразительные результаты.»",
    "🧠 «Сила воли — мышца. Чем больше тренируешь, тем сильнее.»",
    "🚀 «Вчера ты сказал 'завтра'. Сегодня — действуй.»",
    "🌊 «Не считай дни — делай так, чтобы дни считались.»",
    "🦁 «Боль временна. Гордость — навсегда.»",
    "⚖️ «1 кг в неделю — это 52 кг за год. Стабильность побеждает.»",
]

ACHIEVEMENTS_MAP = {
    "first_weight":  ("🏅 Первый шаг",      "Внёс вес первый раз"),
    "weight_5kg":    ("🥉 Минус 5 кг",       "Сбросил первые 5 кг"),
    "weight_10kg":   ("🥈 Минус 10 кг",      "Сбросил 10 кг"),
    "weight_goal":   ("🏆 Цель достигнута!", "Достиг целевого веса"),
    "streak_7":      ("🔥 Неделя подряд",    "7 дней без пропусков"),
    "streak_30":     ("💎 Месяц подряд",     "30 дней без пропусков"),
    "steps_10k":     ("👣 10 000 шагов",     "Прошёл 10 000 шагов за день"),
    "workouts_10":   ("💪 10 тренировок",    "Провёл 10 тренировок"),
    "workouts_50":   ("🦾 50 тренировок",    "Провёл 50 тренировок"),
    "supplements_7": ("💊 Неделя добавок",   "7 дней принимал добавки подряд"),
    "early_bird":    ("🌅 Ранняя пташка",    "Внёс данные до 8 утра"),
    "night_owl":     ("🦉 Ночная сова",      "Внёс данные после 23:00"),
}

def check_and_unlock_achievements(uid):
    unlocked = []
    with sqlite3.connect(DB_PATH) as conn:
        existing = {r[0] for r in conn.execute("SELECT achievement_key FROM achievements WHERE user_id=?", (uid,)).fetchall()}
        def unlock(key):
            if key not in existing:
                conn.execute("INSERT INTO achievements (user_id,achievement_key,unlocked_date) VALUES (?,?,?)",
                             (uid, key, now_samara().strftime("%Y-%m-%d")))
                unlocked.append(key)
                existing.add(key)
        wd = get_weights(uid)
        if wd:
            unlock("first_weight")
            start_w = wd[0][0]; curr_w = wd[-1][0]
            if start_w - curr_w >= 5:  unlock("weight_5kg")
            if start_w - curr_w >= 10: unlock("weight_10kg")
            profile = get_profile(uid)
            if profile and curr_w <= profile.get("target_weight", 9999):
                unlock("weight_goal")
        streak_row = conn.execute("SELECT current_streak FROM streak WHERE user_id=?", (uid,)).fetchone()
        if streak_row:
            s = streak_row[0]
            if s >= 7:  unlock("streak_7")
            if s >= 30: unlock("streak_30")
        workouts_count = conn.execute("SELECT COUNT(*) FROM workouts WHERE user_id=?", (uid,)).fetchone()[0]
        if workouts_count >= 10: unlock("workouts_10")
        if workouts_count >= 50: unlock("workouts_50")
        hour = now_samara().hour
        if hour < 8:   unlock("early_bird")
        if hour >= 23: unlock("night_owl")
        conn.commit()
    return [ACHIEVEMENTS_MAP[k] for k in unlocked if k in ACHIEVEMENTS_MAP]

def get_all_achievements(uid):
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT achievement_key, unlocked_date FROM achievements WHERE user_id=? ORDER BY id", (uid,)).fetchall()
    result = []
    for key, date in rows:
        if key in ACHIEVEMENTS_MAP:
            name, desc = ACHIEVEMENTS_MAP[key]
            result.append((name, desc, date))
    return result

# ─────────────────────────────────────────
#  ПЕРИОДИЗАЦИЯ ТРЕНИРОВОК
# ─────────────────────────────────────────

TRAINING_PHASES = [
    {"name": "📦 Адаптация (нед. 1–4)", "focus": "Базовая сила и техника",
     "reps": "3×12–15", "intensity": "60–65% от максимума", "rest": "60 сек",
     "tip": "Акцент на правильную технику. Вес не важен — форма важна."},
    {"name": "💪 Гипертрофия (нед. 5–8)", "focus": "Рост мышечной массы",
     "reps": "4×8–12", "intensity": "70–75% от максимума", "rest": "90 сек",
     "tip": "Добавляй вес на штанге каждые 2 тренировки (+2.5 кг)."},
    {"name": "🔥 Интенсивность (нед. 9–12)", "focus": "Сила и выносливость",
     "reps": "5×5–8", "intensity": "80–85% от максимума", "rest": "2–3 мин",
     "tip": "Тяжелее — не значит хуже формы. Страховка обязательна."},
    {"name": "♻️ Разгрузка (нед. 13–14)", "focus": "Восстановление",
     "reps": "3×10", "intensity": "50–60% от максимума", "rest": "45 сек",
     "tip": "Разгрузочная неделя — не слабость. Это рост после перерыва."},
]

def get_training_phase(uid):
    profile = get_profile(uid)
    if not profile:
        return TRAINING_PHASES[0]
    reg_date_str = profile.get("created_at") or profile.get("reg_date")
    if not reg_date_str:
        return TRAINING_PHASES[0]
    try:
        reg_date = datetime.strptime(reg_date_str[:10], "%Y-%m-%d")
        weeks_since = (now_samara().replace(tzinfo=None) - reg_date).days // 7
        week_in_cycle = weeks_since % 14
        if week_in_cycle < 4:    return TRAINING_PHASES[0]
        elif week_in_cycle < 8:  return TRAINING_PHASES[1]
        elif week_in_cycle < 12: return TRAINING_PHASES[2]
        else:                    return TRAINING_PHASES[3]
    except Exception:
        return TRAINING_PHASES[0]

# ─────────────────────────────────────────
#  СПИСОК ПОКУПОК
# ─────────────────────────────────────────

WEEKLY_SHOPPING_BASE = {
    "🥩 Белки": ["куриная грудка 1 кг", "яйца 10 шт", "творог 0% 500г", "греческий йогурт 400г"],
    "🌾 Углеводы": ["гречка 500г", "овсянка Геркулес 500г", "бурый рис 500г", "цельнозерновой хлеб"],
    "🥦 Овощи": ["брокколи 500г", "помидоры 500г", "огурцы 500г", "шпинат 200г", "болгарский перец 3 шт"],
    "🍎 Фрукты": ["бананы 5 шт", "яблоки 5 шт", "черника 200г"],
    "🧴 Молочное": ["молоко 1л", "кефир 1л"],
    "🫙 Прочее": ["оливковое масло", "соевый соус", "специи (куркума, паприка, орегано)"],
}

def build_shopping_list(uid):
    """Генерирует список покупок на неделю"""
    lines = ["🛒 *Список покупок на неделю:*\n"]
    for category, items in WEEKLY_SHOPPING_BASE.items():
        lines.append(f"*{category}*")
        for item in items:
            lines.append(f"  ☐ {item}")
        lines.append("")
    lines.append("💡 _Список основан на стандартном недельном рационе. Скорректируй под себя._")
    return "\n".join(lines)

# ─────────────────────────────────────────
#  ТРЕКЕР СНА
# ─────────────────────────────────────────

def log_sleep_simple(uid, hours, quality):
    today = now_samara().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM sleep WHERE user_id=? AND date=?", (uid, today))
        conn.execute("INSERT INTO sleep (user_id, sleep_time, wake_time, duration_hours, quality, date) VALUES (?,?,?,?,?,?)",
                     (uid, "", "", hours, quality, today))
        conn.commit()

def get_sleep_stats(uid, days=7):
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT duration_hours, quality, date FROM sleep WHERE user_id=? ORDER BY date DESC LIMIT ?",
                            (uid, days)).fetchall()
    return rows

def sleep_advice(hours, quality):
    tips = []
    if hours < 6:
        tips.append("😴 Меньше 6 часов — это хронический недосып. Кортизол растёт, вес стоит.")
    elif hours > 9:
        tips.append("😪 Больше 9 часов — пересып. Может снижать энергию на следующий день.")
    else:
        tips.append("✅ Продолжительность сна в норме!")
    if quality <= 2:
        tips.append("💊 Магний перед сном улучшает качество сна. Исключи экраны за час до сна.")
    elif quality >= 4:
        tips.append("🌟 Отличное качество сна — ты восстанавливаешься на 100%!")
    return "\n".join(tips)

# ─────────────────────────────────────────
#  ASCII-ГРАФИК ВЕСА
# ─────────────────────────────────────────

def build_weight_ascii_chart(uid, days=30):
    """Строит ASCII-график веса за N дней"""
    wd = get_weights(uid, limit=20)
    if len(wd) < 2:
        return None
    weights = [w for w, _ in reversed(wd)]
    dates = [d[:5] for _, d in reversed(wd)]  # DD.MM
    min_w = min(weights); max_w = max(weights)
    spread = max_w - min_w
    if spread < 0.1:
        spread = 1.0
    height = 8
    width = len(weights)
    chart = []
    for row in range(height, 0, -1):
        line = ""
        threshold = min_w + (row / height) * spread
        for w in weights:
            if w >= threshold:
                line += "█"
            else:
                line += " "
        val = min_w + (row / height) * spread
        chart.append(f"{val:5.1f} |{line}")
    chart.append("      " + "─" * width)
    # Даты (каждые 2)
    date_line = "      "
    for i, d in enumerate(dates):
        if i % 3 == 0 and i + 2 < width:
            date_line += d[:2]
        elif i % 3 != 0:
            date_line += " "
    chart.append(date_line)
    return "\n".join(chart)

# ─────────────────────────────────────────
#  ЕЖЕНЕДЕЛЬНЫЕ МИНИ-ЦЕЛИ
# ─────────────────────────────────────────

def generate_weekly_goal(uid):
    """Генерирует персональную цель на неделю"""
    profile = get_profile(uid)
    wd = get_weights(uid)
    sd = get_steps(uid, limit=7)
    goals = []
    avg_steps = round(sum(s for s,_ in sd) / max(len(sd), 1)) if sd else 0
    # Цель по шагам
    step_goal = max(8000, avg_steps + 1000)
    total_goal = step_goal * 7
    goals.append(f"👣 Пройти *{total_goal:,}* шагов за неделю ({step_goal:,}/день)".replace(",", " "))
    # Цель по весу
    if wd and profile:
        target = profile.get("target_weight", 0)
        curr = wd[-1][0]
        if curr > target:
            goals.append(f"⚖️ Сбросить *0.5–1 кг* за неделю")
    # Цель по тренировкам
    gym = profile.get("gym_days", 3) if profile else 3
    goals.append(f"💪 Провести *{gym} тренировки* без пропусков")
    # Цель по воде
    goals.append("💧 Выпивать *2–2.5л воды* каждый день")
    return goals

# ─────────────────────────────────────────
#  ДНЕВНИК ЗАМЕТОК
# ─────────────────────────────────────────

def save_note(uid, text):
    today = now_samara().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS daily_notes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, note TEXT, date TEXT)")
        conn.execute("INSERT INTO daily_notes (user_id, note, date) VALUES (?,?,?)", (uid, text, today))
        conn.commit()

def get_notes(uid, limit=7):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS daily_notes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, note TEXT, date TEXT)")
        rows = conn.execute("SELECT note, date FROM daily_notes WHERE user_id=? ORDER BY date DESC LIMIT ?", (uid, limit)).fetchall()
    return rows

# ─────────────────────────────────────────
#  ЧИТМИЛ-КАЛЬКУЛЯТОР
# ─────────────────────────────────────────

def calc_cheatmeal(extra_kcal):
    """Считает кардио для компенсации читмила"""
    activities = [
        ("🚶 Ходьба (5 км/ч)",       4.5),
        ("🚴 Велосипед (средний темп)", 7.5),
        ("🏃 Бег (8 км/ч)",           9.0),
        ("🏊 Плавание",               8.0),
        ("⛹️ Прыжки со скакалкой",    10.0),
    ]
    lines = []
    for name, kcal_per_hour in activities:
        minutes = round(extra_kcal / kcal_per_hour * 60)
        lines.append(f"{name}: *{minutes} мин*")
    return lines

# ─────────────────────────────────────────
#  КАЛЬКУЛЯТОР КБЖУ (без записи)
# ─────────────────────────────────────────

def quick_kcal_calc(product, grams):
    """Быстрый расчёт КБЖУ без записи в дневник"""
    kcal_per_100 = KCAL_PER_100G.get(product.lower())
    if not kcal_per_100:
        # Нечёткий поиск
        matches = [k for k in KCAL_PER_100G if product.lower() in k]
        if matches:
            product = matches[0]
            kcal_per_100 = KCAL_PER_100G[product]
        else:
            return None
    kcal = round(grams * kcal_per_100 / 100)
    return {"product": product, "grams": grams, "kcal": kcal, "kcal_per_100": kcal_per_100}

# ─────────────────────────────────────────
#  ШАБЛОНЫ ПИТАНИЯ
# ─────────────────────────────────────────

def save_meal_template(uid, name, items):
    """items = список (продукт, граммы)"""
    import json
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS meal_templates (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, items TEXT, created TEXT)")
        conn.execute("INSERT INTO meal_templates (user_id, name, items, created) VALUES (?,?,?,?)",
                     (uid, name, json.dumps(items, ensure_ascii=False), now_samara().strftime("%Y-%m-%d")))
        conn.commit()

def get_meal_templates(uid):
    import json
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS meal_templates (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, items TEXT, created TEXT)")
        rows = conn.execute("SELECT id, name, items FROM meal_templates WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
    result = []
    for tid, name, items_json in rows:
        try:
            items = json.loads(items_json)
        except Exception:
            items = []
        total_kcal = sum(round(KCAL_PER_100G.get(p, 0) * g / 100) for p, g in items)
        result.append({"id": tid, "name": name, "items": items, "total_kcal": total_kcal})
    return result

# ══════════════════════════════════════════════════════
#  ТРЕКЕР ОБХВАТОВ
# ══════════════════════════════════════════════════════
MEASUREMENTS_LIST = [
    ("waist", "👗 Талия"),
    ("hips", "🍑 Бёдра"),
    ("chest", "💪 Грудь"),
    ("neck", "🦒 Шея"),
    ("bicep", "💪 Бицепс"),
    ("thigh", "🦵 Бедро"),
]

def save_measurement(uid, part, cm):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute(
        "INSERT INTO measurements (user_id, part, cm, date) VALUES (?,?,?,?)",
        (uid, part, cm, now_samara().strftime("%Y-%m-%d")))
    conn.commit(); conn.close()

def get_measurements_history(uid, part, limit=10):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute(
        "SELECT cm, date FROM measurements WHERE user_id=? AND part=? ORDER BY id DESC LIMIT ?",
        (uid, part, limit)).fetchall()
    conn.close()
    return list(reversed(rows))

def get_all_measurements_latest(uid):
    conn = sqlite3.connect("weight_tracker.db")
    result = {}
    for key, label in MEASUREMENTS_LIST:
        row = conn.execute(
            "SELECT cm, date FROM measurements WHERE user_id=? AND part=? ORDER BY id DESC LIMIT 1",
            (uid, key)).fetchone()
        if row:
            result[key] = {"cm": row[0], "date": row[1], "label": label}
    conn.close()
    return result

def build_measurements_summary(uid):
    data = get_all_measurements_latest(uid)
    if not data:
        return "📏 Обхваты ещё не записаны.\n\nНажми *«➕ Добавить обхваты»* чтобы начать."
    lines = ["📏 *Текущие обхваты:*\n"]
    for key, label in MEASUREMENTS_LIST:
        if key in data:
            d = data[key]
            # динамика
            hist = get_measurements_history(uid, key, 2)
            dyn = ""
            if len(hist) >= 2:
                diff = round(hist[-1][0] - hist[-2][0], 1)
                if diff < 0:   dyn = f" (📉 {diff} см)"
                elif diff > 0: dyn = f" (📈 +{diff} см)"
                else:          dyn = " (➡️ без изм.)"
            lines.append(f"{label}: *{d['cm']} см*{dyn}")
    return "\n".join(lines)

# ══════════════════════════════════════════════════════
#  ТАЙМЕР ОТДЫХА
# ══════════════════════════════════════════════════════
_rest_timers = {}  # {cid: thread}

def start_rest_timer(bot_obj, cid, seconds):
    def _run():
        import time as _t
        remaining = seconds
        while remaining > 0:
            _t.sleep(1)
            remaining -= 1
            if cid not in _rest_timers:
                return
        if cid in _rest_timers:
            del _rest_timers[cid]
            bot_obj.send_message(cid,
                "⏰ *Время отдыха вышло! Следующий подход!* 💪",
                parse_mode="Markdown")
    t = threading.Thread(target=_run, daemon=True)
    _rest_timers[cid] = t
    t.start()

def cancel_rest_timer(cid):
    if cid in _rest_timers:
        del _rest_timers[cid]
        return True
    return False

# ══════════════════════════════════════════════════════
#  ДНЕВНИК ТРЕНИРОВОК
# ══════════════════════════════════════════════════════
def log_workout_exercise(uid, exercise, weight_kg, reps, sets):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute(
        "INSERT INTO workout_weights (user_id,exercise,weight_kg,reps,sets,date) VALUES (?,?,?,?,?,?)",
        (uid, exercise.lower().strip(), weight_kg, reps, sets, now_samara().strftime("%Y-%m-%d %H:%M")))
    conn.commit(); conn.close()

def get_workout_history(uid, limit=20):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute(
        "SELECT exercise, weight_kg, reps, sets, date FROM workout_weights "
        "WHERE user_id=? ORDER BY id DESC LIMIT ?", (uid, limit)).fetchall()
    conn.close()
    return rows

def get_last_workout_entry(uid, exercise):
    conn = sqlite3.connect("weight_tracker.db")
    row = conn.execute(
        "SELECT weight_kg, reps, sets, date FROM workout_weights "
        "WHERE user_id=? AND exercise=? ORDER BY id DESC LIMIT 1",
        (uid, exercise.lower().strip())).fetchone()
    conn.close()
    return row

def build_workout_diary(uid):
    rows = get_workout_history(uid, 30)
    if not rows:
        return "📓 Дневник тренировок пуст.\n\nЗапиши первое упражнение!"
    # Группируем по дате
    from collections import OrderedDict
    days = OrderedDict()
    for ex, w, r, s, dt in rows:
        day = dt[:10]
        days.setdefault(day, []).append((ex, w, r, s))
    lines = ["📓 *Дневник тренировок:*\n"]
    for day, exercises in list(days.items())[:7]:
        lines.append(f"📅 *{day}*")
        for ex, w, r, s in exercises:
            lines.append(f"  • {ex.capitalize()}: {w}кг × {r}повт × {s}подх")
        lines.append("")
    return "\n".join(lines)

def check_progression_advice(uid, exercise, weight_kg, reps, sets):
    """Если 3+ записи с одинаковым весом и reps>=12 — советуем увеличить"""
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute(
        "SELECT weight_kg, reps FROM workout_weights "
        "WHERE user_id=? AND exercise=? ORDER BY id DESC LIMIT 5",
        (uid, exercise.lower().strip())).fetchall()
    conn.close()
    if len(rows) >= 3:
        same_weight = all(r[0] == weight_kg for r in rows[:3])
        good_reps = all(r[1] >= 12 for r in rows[:3])
        if same_weight and good_reps:
            new_w = round(weight_kg + (2.5 if weight_kg < 50 else 5), 1)
            return f"🚀 *Прогрессия!* Ты 3 раза подряд делаешь {weight_kg}кг × {reps}+ повт.\nПопробуй *{new_w} кг* на следующей тренировке!"
    return None

# ══════════════════════════════════════════════════════
#  КОРРЕЛЯЦИИ И НЕДЕЛЬНЫЙ ОТЧЁТ
# ══════════════════════════════════════════════════════
def build_correlations_report(uid):
    conn = sqlite3.connect("weight_tracker.db")
    lines = ["🔬 *Корреляции (последние 14 дней):*\n"]
    # Сон → вес
    sleep_rows = conn.execute(
        "SELECT date, duration_hours FROM sleep WHERE user_id=? ORDER BY id DESC LIMIT 14", (uid,)).fetchall()
    weight_rows = dict(conn.execute(
        "SELECT date(date), weight_value FROM weights WHERE user_id=? ORDER BY id DESC LIMIT 14", (uid,)).fetchall())
    if len(sleep_rows) >= 5 and len(weight_rows) >= 5:
        good_sleep_days = [r[0][:10] for r in sleep_rows if r[1] >= 7]
        bad_sleep_days  = [r[0][:10] for r in sleep_rows if r[1] < 7]
        good_weights = [weight_rows[d] for d in good_sleep_days if d in weight_rows]
        bad_weights  = [weight_rows[d] for d in bad_sleep_days  if d in weight_rows]
        if good_weights and bad_weights:
            gw = round(sum(good_weights)/len(good_weights), 1)
            bw = round(sum(bad_weights)/len(bad_weights), 1)
            if gw < bw:
                lines.append(f"😴 При сне ≥7ч вес в среднем *{gw} кг*, при <7ч — *{bw} кг*\n→ Хороший сон помогает снижать вес ✅")
            else:
                lines.append(f"😴 Вес при хорошем и плохом сне примерно одинаковый (~{gw} кг)")
        lines.append("")
    # Настроение → шаги
    mood_rows = conn.execute(
        "SELECT date, mood FROM mood_log WHERE user_id=? ORDER BY id DESC LIMIT 14", (uid,)).fetchall()
    steps_dict = dict(conn.execute(
        "SELECT date(date), step_count FROM steps WHERE user_id=? ORDER BY id DESC LIMIT 14", (uid,)).fetchall())
    if len(mood_rows) >= 5:
        good_mood_days = [r[0][:10] for r in mood_rows if r[1] >= 4]
        bad_mood_days  = [r[0][:10] for r in mood_rows if r[1] <= 2]
        good_steps = [steps_dict[d] for d in good_mood_days if d in steps_dict]
        bad_steps  = [steps_dict[d] for d in bad_mood_days  if d in steps_dict]
        if good_steps and bad_steps:
            gs = round(sum(good_steps)/len(good_steps))
            bs = round(sum(bad_steps)/len(bad_steps))
            if gs > bs:
                lines.append(f"😊 В хорошем настроении шагов в среднем *{gs:,}*, в плохом — *{bs:,}*\n→ Настроение влияет на активность 💡".replace(",", " "))
            else:
                lines.append(f"🚶 Активность не зависит от настроения (оба ~{gs:,} шагов)".replace(",", " "))
        lines.append("")
    conn.close()
    if len(lines) == 1:
        return "🔬 *Корреляции*\n\nНедостаточно данных (нужно ≥5 дней записей сна, настроения и веса).\nПродолжай вести дневник!"
    return "\n".join(lines)

def build_weekly_report(uid):
    conn = sqlite3.connect("weight_tracker.db")
    today = now_samara().date()
    week_ago = today - timedelta(days=7)
    w_str = week_ago.strftime("%Y-%m-%d")
    # Вес
    weights = conn.execute(
        "SELECT weight_value FROM weights WHERE user_id=? AND date>=? ORDER BY id ASC",
        (uid, w_str)).fetchall()
    # Шаги
    steps = conn.execute(
        "SELECT step_count FROM steps WHERE user_id=? AND date>=?",
        (uid, w_str)).fetchall()
    # Вода
    water = conn.execute(
        "SELECT glasses FROM water WHERE user_id=? AND date>=?",
        (uid, w_str)).fetchall()
    # Сон
    sleep = conn.execute(
        "SELECT duration_hours FROM sleep WHERE user_id=? AND date>=?",
        (uid, w_str)).fetchall()
    conn.close()
    lines = [f"📊 *Недельный отчёт* ({week_ago.strftime('%d.%m')} – {today.strftime('%d.%m')})\n"]
    if weights:
        w_start = weights[0][0]; w_end = weights[-1][0]
        diff = round(w_end - w_start, 2)
        arrow = "📉" if diff < 0 else "📈" if diff > 0 else "➡️"
        lines.append(f"⚖️ Вес: {w_start} → {w_end} кг {arrow} ({'+' if diff>0 else ''}{diff} кг)")
    if steps:
        avg_steps = round(sum(s[0] for s in steps) / len(steps))
        lines.append(f"👟 Шаги: в среднем *{avg_steps:,}*/день ({len(steps)} дней)".replace(",", " "))
    if water:
        avg_water = round(sum(w[0] for w in water) / len(water), 1)
        lines.append(f"💧 Вода: в среднем *{avg_water}* стак./день")
    if sleep:
        avg_sleep = round(sum(s[0] for s in sleep) / len(sleep), 1)
        emoji = "✅" if avg_sleep >= 7 else "⚠️"
        lines.append(f"😴 Сон: в среднем *{avg_sleep}ч* {emoji}")
    if len(lines) == 1:
        return "📊 *Недельный отчёт*\n\nНедостаточно данных за последние 7 дней."
    lines.append(f"\n💪 Продолжай в том же духе!")
    return "\n".join(lines)

# ══════════════════════════════════════════════════════
#  ТРЕКЕР ПРИЁМА ПИЩИ (детальный)
# ══════════════════════════════════════════════════════
MEAL_SLOTS = ["🌅 Завтрак", "🥗 Обед", "🌆 Ужин", "🍎 Перекус"]

def log_meal_entry(uid, meal_slot, product, grams, kcal):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute(
        "INSERT INTO food_diary (user_id,meal,product,grams,kcal,date) VALUES (?,?,?,?,?,?)",
        (uid, meal_slot, product, grams, kcal, now_samara().strftime("%Y-%m-%d"))).fetchall()
    conn.commit(); conn.close()

def get_meals_today(uid):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute(
        "SELECT meal, product, grams, kcal FROM food_diary WHERE user_id=? AND date=?",
        (uid, now_samara().strftime("%Y-%m-%d"))).fetchall()
    conn.close()
    return rows

def build_food_diary_today(uid):
    rows = get_meals_today(uid)
    if not rows:
        return "🍽️ *Дневник питания* — сегодня пусто.\n\nНажми *«➕ Записать приём пищи»*"
    from collections import defaultdict
    slots = defaultdict(list)
    for meal, product, grams, kcal in rows:
        slots[meal].append((product, grams, kcal))
    total_kcal = sum(r[3] for r in rows)
    lines = ["🍽️ *Дневник питания — сегодня:*\n"]
    for slot in MEAL_SLOTS:
        if slot in slots:
            slot_kcal = sum(k for _, _, k in slots[slot])
            lines.append(f"*{slot}* ({slot_kcal} ккал)")
            for p, g, k in slots[slot]:
                lines.append(f"  • {p.capitalize()} — {g}г ({k} ккал)")
            lines.append("")
    lines.append(f"🔥 *Итого: {total_kcal} ккал*")
    profile = get_profile(uid)
    if profile and profile.get("target_weight"):
        goal = get_daily_kcal_goal(uid)
        remain = goal - total_kcal
        if remain > 0:
            lines.append(f"📋 Осталось до нормы: *{remain} ккал*")
        else:
            lines.append(f"⚠️ Превышение нормы на *{abs(remain)} ккал*")
    return "\n".join(lines)

# ══════════════════════════════════════════════════════
#  ИНТЕРВАЛЬНОЕ ГОЛОДАНИЕ
# ══════════════════════════════════════════════════════
IF_PROTOCOLS = {
    "16/8":  {"fast": 16, "eat": 8,  "desc": "16ч голодания, 8ч еды"},
    "18/6":  {"fast": 18, "eat": 6,  "desc": "18ч голодания, 6ч еды"},
    "20/4":  {"fast": 20, "eat": 4,  "desc": "20ч голодания, 4ч еды"},
    "5:2":   {"fast": 0,  "eat": 0,  "desc": "5 обычных дней + 2 дня до 500 ккал"},
}

def save_if_start(uid, protocol, start_time_str):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute(
        "INSERT OR REPLACE INTO if_tracker (user_id, protocol, start_time, date) VALUES (?,?,?,?)",
        (uid, protocol, start_time_str, now_samara().strftime("%Y-%m-%d")))
    conn.commit(); conn.close()

def get_if_status(uid):
    conn = sqlite3.connect("weight_tracker.db")
    row = conn.execute(
        "SELECT protocol, start_time, date FROM if_tracker WHERE user_id=? ORDER BY id DESC LIMIT 1",
        (uid,)).fetchone()
    conn.close()
    if not row: return None
    protocol, start_str, date = row
    try:
        start_dt = datetime.strptime(f"{date} {start_str}", "%Y-%m-%d %H:%M")
        start_dt = start_dt.replace(tzinfo=SAMARA_TZ)
        elapsed = (now_samara() - start_dt).total_seconds() / 3600
        fast_hours = IF_PROTOCOLS.get(protocol, {}).get("fast", 16)
        remaining = max(0, fast_hours - elapsed)
        eat_start = start_dt + timedelta(hours=fast_hours)
        return {
            "protocol": protocol,
            "elapsed": round(elapsed, 1),
            "remaining": round(remaining, 1),
            "fast_hours": fast_hours,
            "eat_start": eat_start.strftime("%H:%M"),
            "pct": min(100, round(elapsed / fast_hours * 100)) if fast_hours > 0 else 100,
        }
    except Exception:
        return None

# ══════════════════════════════════════════════════════
#  ГОТОВЫЕ ПРОГРАММЫ ТРЕНИРОВОК
# ══════════════════════════════════════════════════════
WORKOUT_PROGRAMS = {
    "🔥 Похудение": {
        "desc": "Кардио + круговые тренировки, дефицит калорий",
        "days": {
            "Пн": ["Кардио 30 мин (бег/велосипед)", "Приседания 3×15", "Выпады 3×12", "Планка 3×45 сек"],
            "Вт": ["Ходьба 8000+ шагов", "Растяжка 15 мин"],
            "Ср": ["Круговая: берпи 3×10, прыжки 3×20, скалолаз 3×20", "Пресс 4×15"],
            "Чт": ["Активный отдых: прогулка 5 км"],
            "Пт": ["Кардио 25 мин", "Становая тяга 3×10", "Жим 3×12", "Тяга 3×12"],
            "Сб": ["Длинная прогулка / велосипед 1ч"],
            "Вс": ["Отдых + растяжка"],
        }
    },
    "💪 Набор массы": {
        "desc": "Силовые тренировки, профицит калорий +300-500 ккал",
        "days": {
            "Пн": ["Жим лёжа 4×8", "Жим гантелей 3×10", "Разводка 3×12", "Трицепс кабель 3×12"],
            "Вт": ["Становая тяга 4×6", "Тяга штанги 4×8", "Тяга гантели 3×10", "Бицепс 3×12"],
            "Ср": ["Отдых / лёгкое кардио 20 мин"],
            "Чт": ["Приседания 4×8", "Жим ногами 4×10", "Выпады 3×12", "Икры 4×15"],
            "Пт": ["Жим стоя 4×8", "Тяга к подбородку 3×10", "Разводка в стороны 3×12", "Шраги 3×15"],
            "Сб": ["Подтягивания 4×max", "Отжимания 4×max", "Пресс 4×15"],
            "Вс": ["Отдых"],
        }
    },
    "🏃 Поддержание": {
        "desc": "Умеренная нагрузка, поддержание текущей формы",
        "days": {
            "Пн": ["Кардио 20 мин", "Базовые упражнения 3×10"],
            "Вт": ["Прогулка 6000+ шагов"],
            "Ср": ["Силовая: 3 упражнения × 3×10"],
            "Чт": ["Растяжка + йога 20 мин"],
            "Пт": ["Кардио 20 мин + силовая"],
            "Сб": ["Активный отдых на выбор"],
            "Вс": ["Отдых"],
        }
    },
}

def get_todays_program(program_name):
    prog = WORKOUT_PROGRAMS.get(program_name)
    if not prog: return None
    day_names = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]
    today_name = day_names[now_samara().weekday()]
    exercises = prog["days"].get(today_name, ["Отдых"])
    return {"day": today_name, "exercises": exercises, "desc": prog["desc"]}

# ══════════════════════════════════════════════════════
#  СТРИКИ
# ══════════════════════════════════════════════════════
def update_streak(uid):
    conn = sqlite3.connect("weight_tracker.db")
    today_str = now_samara().strftime("%Y-%m-%d")
    row = conn.execute(
        "SELECT last_entry_date, current_streak, best_streak FROM streak WHERE user_id=?",
        (uid,)).fetchone()
    if not row:
        conn.execute("INSERT INTO streak (user_id, last_entry_date, current_streak, best_streak) VALUES (?,?,1,1)",
                     (uid, today_str))
        conn.commit(); conn.close()
        return 1, 1
    last_date, current, best = row
    try:
        last_dt = datetime.strptime(last_date, "%Y-%m-%d").date()
        today_dt = now_samara().date()
        delta = (today_dt - last_dt).days
        if delta == 0:
            conn.close()
            return current, best
        elif delta == 1:
            current += 1
        else:
            current = 1
        best = max(best, current)
        conn.execute("UPDATE streak SET last_entry_date=?, current_streak=?, best_streak=? WHERE user_id=?",
                     (today_str, current, best, uid))
    except Exception:
        current, best = 1, 1
    conn.commit(); conn.close()
    return current, best

def get_streak(uid):
    conn = sqlite3.connect("weight_tracker.db")
    row = conn.execute(
        "SELECT current_streak, best_streak FROM streak WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return row if row else (0, 0)

# ══════════════════════════════════════════════════════
#  ЧЕЛЛЕНДЖИ
# ══════════════════════════════════════════════════════
CHALLENGES = {
    "steps_7":    {"name": "👟 10к шагов × 7 дней", "desc": "7 дней подряд по 10 000+ шагов", "days": 7},
    "water_7":    {"name": "💧 Гидрация × 7 дней",  "desc": "7 дней подряд ≥ 8 стаканов воды", "days": 7},
    "weight_14":  {"name": "⚖️ Дневник веса × 14",  "desc": "Вносить вес 14 дней подряд", "days": 14},
    "nocheat_30": {"name": "🥗 Без читмила 30 дней", "desc": "30 дней без читмил-дней", "days": 30},
    "sleep_7":    {"name": "😴 Сон ≥7ч × 7 дней",   "desc": "7 дней сна не менее 7 часов", "days": 7},
}

def start_challenge(uid, challenge_key):
    conn = sqlite3.connect("weight_tracker.db")
    today_str = now_samara().strftime("%Y-%m-%d")
    conn.execute(
        "INSERT OR REPLACE INTO challenges (user_id, challenge_key, start_date, progress, completed) VALUES (?,?,?,0,0)",
        (uid, challenge_key, today_str))
    conn.commit(); conn.close()

def get_active_challenges(uid):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute(
        "SELECT challenge_key, start_date, progress, completed FROM challenges WHERE user_id=? AND completed=0",
        (uid,)).fetchall()
    conn.close()
    result = []
    for key, start, progress, completed in rows:
        ch = CHALLENGES.get(key, {})
        result.append({
            "key": key, "name": ch.get("name","?"), "desc": ch.get("desc",""),
            "days": ch.get("days", 7), "start": start, "progress": progress
        })
    return result

def build_challenges_menu_text(uid):
    active = get_active_challenges(uid)
    lines = ["🏆 *Мои челленджи*\n"]
    if active:
        lines.append("*Активные:*")
        for ch in active:
            today = now_samara().date()
            try:
                start_d = datetime.strptime(ch["start"], "%Y-%m-%d").date()
                elapsed = (today - start_d).days
            except Exception:
                elapsed = 0
            pct = min(100, round(elapsed / ch["days"] * 100))
            bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
            lines.append(f"{ch['name']}\n[{bar}] {elapsed}/{ch['days']} дней ({pct}%)\n")
    else:
        lines.append("Нет активных челленджей.\n")
    lines.append("*Доступные челленджи:*")
    for key, ch in CHALLENGES.items():
        if not any(a["key"] == key for a in active):
            lines.append(f"• {ch['name']} — {ch['desc']}")
    return "\n".join(lines)

# ══════════════════════════════════════════════════════
#  РЕЙТИНГ ДРУЗЕЙ
# ══════════════════════════════════════════════════════
def add_friend(uid, friend_id):
    conn = sqlite3.connect("weight_tracker.db")
    try:
        conn.execute("INSERT OR IGNORE INTO friends (user_id, friend_id) VALUES (?,?)", (uid, friend_id))
        conn.commit()
        result = True
    except Exception:
        result = False
    conn.close()
    return result

def get_friends(uid):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute("SELECT friend_id FROM friends WHERE user_id=?", (uid,)).fetchall()
    conn.close()
    return [r[0] for r in rows]

def build_friends_leaderboard(uid):
    friends = get_friends(uid)
    if not friends:
        return ("👥 *Рейтинг друзей*\n\nДрузей пока нет.\n\n"
                "Чтобы добавить друга — нажми *«➕ Добавить друга»* и введи его Telegram ID.\n"
                "_Telegram ID можно узнать через бот @userinfobot_")
    all_ids = [uid] + friends
    today = now_samara().strftime("%Y-%m-%d")
    week_ago = (now_samara() - timedelta(days=7)).strftime("%Y-%m-%d")
    conn = sqlite3.connect("weight_tracker.db")
    scores = []
    for fid in all_ids:
        steps = conn.execute(
            "SELECT SUM(step_count) FROM steps WHERE user_id=? AND date>=?",
            (fid, week_ago)).fetchone()[0] or 0
        label = "Ты" if fid == uid else f"ID {fid}"
        scores.append((label, int(steps)))
    conn.close()
    scores.sort(key=lambda x: x[1], reverse=True)
    lines = ["👥 *Рейтинг друзей (шаги за 7 дней):*\n"]
    medals = ["🥇", "🥈", "🥉"]
    for i, (name, steps) in enumerate(scores):
        m = medals[i] if i < 3 else f"{i+1}."
        lines.append(f"{m} *{name}* — {steps:,} шагов".replace(",", " "))
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  УМНЫЙ ИИ-СОВЕТНИК
# ══════════════════════════════════════════════════════
def build_ai_advice(uid):
    """Анализирует все данные пользователя и даёт персональный совет на день"""
    profile = get_profile(uid)
    if not profile:
        return "🤖 *Советник*\n\nСначала пройди настройку профиля (кнопка «⚙️ Профиль»)."

    today = now_samara().strftime("%Y-%m-%d")
    yesterday = (now_samara() - timedelta(days=1)).strftime("%Y-%m-%d")
    conn = sqlite3.connect("weight_tracker.db")

    # Собираем данные
    last_sleep = conn.execute(
        "SELECT duration_hours, quality FROM sleep WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,)).fetchone()
    last_steps = conn.execute(
        "SELECT step_count FROM steps WHERE user_id=? AND date>=? ORDER BY id DESC LIMIT 1",
        (uid, yesterday)).fetchone()
    last_mood = conn.execute(
        "SELECT mood, stress, energy FROM mood_log WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,)).fetchone()
    water_today = conn.execute(
        "SELECT SUM(glasses) FROM water WHERE user_id=? AND date=?", (uid, today)).fetchone()[0] or 0
    kcal_today = conn.execute(
        "SELECT SUM(kcal) FROM food_diary WHERE user_id=? AND date=?", (uid, today)).fetchone()[0] or 0
    weights = conn.execute(
        "SELECT weight_value FROM weights WHERE user_id=? ORDER BY id DESC LIMIT 3", (uid,)).fetchall()
    conn.close()

    advice_lines = ["🤖 *Персональный совет на сегодня:*\n"]
    score = 0  # общий «балл» состояния

    # Анализ сна
    if last_sleep:
        hrs, quality = last_sleep
        if hrs >= 7 and quality >= 4:
            advice_lines.append("😴 Сон отличный — энергия на максимуме. Можно тренироваться интенсивно.")
            score += 2
        elif hrs >= 6:
            advice_lines.append("😴 Сон нормальный. Умеренная тренировка — хороший выбор.")
            score += 1
        else:
            advice_lines.append("😴 Сон плохой — организм не восстановился. Сегодня лёгкая прогулка, никакого железа.")
            score -= 1
    else:
        advice_lines.append("😴 Данных о сне нет. Веди дневник сна — это влияет на вес!")

    # Анализ шагов
    if last_steps:
        s = last_steps[0]
        if s >= 10000:
            advice_lines.append("👟 Вчера был активный день. Сегодня можно сделать силовую.")
            score += 1
        elif s >= 6000:
            advice_lines.append("👟 Активность вчера средняя. Добавь ещё 2–3 тыс. шагов сегодня.")
        else:
            advice_lines.append("👟 Вчера было мало движения. Сегодня обязательно пройди 8000+ шагов.")
            score -= 1

    # Анализ настроения
    if last_mood:
        mood, stress, energy = last_mood
        if stress >= 4:
            advice_lines.append("😤 Высокий стресс — избегай жёстких диет сегодня. Магний + медитация помогут.")
            score -= 1
        if energy <= 2:
            advice_lines.append("⚡ Низкая энергия — добавь сложных углеводов (гречка, овсянка) на завтрак.")
        elif energy >= 4:
            advice_lines.append("⚡ Энергия высокая — отличный день для интенсивной тренировки!")
            score += 1

    # Анализ воды
    if water_today < 4:
        advice_lines.append("💧 Сегодня почти не пил воду — выпей стакан прямо сейчас.")
    elif water_today >= 8:
        advice_lines.append("💧 Гидрация отличная — так держать!")

    # Анализ калорий
    goal_kcal = get_daily_kcal_goal(uid) if profile else 2000
    if kcal_today > 0:
        remain = goal_kcal - kcal_today
        if remain < -200:
            advice_lines.append(f"🍽️ Уже превышена норма на {abs(remain)} ккал — лёгкий ужин без углеводов.")
        elif remain > goal_kcal * 0.5:
            advice_lines.append(f"🍽️ Съел мало ({kcal_today} ккал) — не допускай голода, добавь белковый перекус.")

    # Тренд веса
    if len(weights) >= 2:
        diff = round(weights[0][0] - weights[-1][0], 2)
        if diff > 0.5:
            advice_lines.append(f"⚖️ Вес растёт (+{diff} кг за последние дни) — проверь калораж и соль.")
        elif diff < -0.5:
            advice_lines.append(f"⚖️ Вес снижается ({diff} кг) — всё идёт по плану! 🔥")

    # Итоговый совет
    advice_lines.append("")
    if score >= 3:
        advice_lines.append("🌟 *Итог: отличное состояние! День для рекордов.*")
    elif score >= 1:
        advice_lines.append("✅ *Итог: хорошее состояние. Стандартный план на день.*")
    elif score == 0:
        advice_lines.append("🟡 *Итог: среднее состояние. Слушай себя, не перегружайся.*")
    else:
        advice_lines.append("🔴 *Итог: организм устал. Отдых и восстановление — приоритет.*")

    return "\n".join(advice_lines)


# ══════════════════════════════════════════════════════
#  ФАСТФУД КБЖУ
# ══════════════════════════════════════════════════════
FASTFOOD_KCAL = {
    # KFC
    "kfc крылышки": 305, "kfc ножки": 215, "kfc твистер": 240,
    "kfc биг тастер": 490, "kfc шеф бургер": 510, "kfc картошка фри": 310,
    "kfc кесадилья": 270, "kfc стрипсы": 260, "kfc зингер": 380,
    # McDonald's
    "макдоналдс биг мак": 257, "макдоналдс чизбургер": 303, "макдоналдс картошка фри": 320,
    "макдоналдс маккурица": 208, "макдоналдс роял": 230, "макдоналдс нагетсы": 223,
    "макдоналдс филе-о-фиш": 260, "макдоналдс двойной чизбургер": 338,
    "макдоналдс картошка": 320, "макдоналдс яблочный пирог": 260,
    # Burger King
    "бургер кинг воппер": 253, "бургер кинг чизбургер": 290, "бургер кинг картошка": 290,
    "бургер кинг наггетсы": 215, "бургер кинг онион ринг": 380,
    "бургер кинг двойной воппер": 290, "бургер кинг кинг": 260,
    # Subway
    "сабвей курица тандури": 140, "сабвей индейка": 105, "сабвей тунец": 200,
    "сабвей ветчина": 120, "сабвей итальянский": 185, "сабвей клаб": 130,
    "сабвей митбол": 230, "сабвей хлеб": 270,
    # Шаурма
    "шаурма куриная": 180, "шаурма говядина": 210, "шаурма микс": 195,
    "донер кебаб": 220, "фалафель": 333,
    # Суши/роллы
    "ролл калифорния": 140, "ролл филадельфия": 145, "ролл темпура": 175,
    "нигири лосось": 130, "нигири тунец": 120, "мисо суп": 40,
}

# Добавляем фастфуд в общий словарь
KCAL_PER_100G.update(FASTFOOD_KCAL)

# Гликемический индекс продуктов
GI_TABLE = {
    # Высокий ГИ (>70) — ограничивать
    "белый рис": 70, "белый хлеб": 75, "картошка фри": 75, "арбуз": 72,
    "кукурузные хлопья": 85, "рисовая каша": 70, "вафли": 76, "пиво": 110,
    "финики": 100, "кока-кола": 65, "мёд": 61,
    # Средний ГИ (40–70)
    "бурый рис": 55, "овсянка": 60, "гречка": 50, "булгур": 48,
    "виноград": 46, "манго": 55, "банан": 60, "свёкла": 65,
    "картофель варёный": 65, "макароны": 55, "ананас": 66,
    # Низкий ГИ (<40) — предпочтительно
    "яблоко": 36, "апельсин": 35, "груша": 38, "клубника": 32,
    "вишня": 22, "чечевица": 29, "нут": 35, "фасоль": 40,
    "молоко": 32, "йогурт": 35, "шоколад горький": 25,
    "куриная грудка": 0, "говядина": 0, "рыба": 0, "яйцо": 0,
    "огурец": 15, "помидор": 15, "брокколи": 15, "шпинат": 10,
    "орехи": 15, "миндаль": 15, "грецкий орех": 15,
}

def get_gi_info(product):
    p = product.lower().strip()
    gi = GI_TABLE.get(p)
    if gi is None:
        # частичное совпадение
        for k, v in GI_TABLE.items():
            if k in p or p in k:
                gi = v; break
    if gi is None:
        return None
    if gi == 0:
        cat, emoji = "Нет углеводов", "✅"
    elif gi < 40:
        cat, emoji = "Низкий ГИ", "✅"
    elif gi < 70:
        cat, emoji = "Средний ГИ", "🟡"
    else:
        cat, emoji = "Высокий ГИ", "🔴"
    return {"gi": gi, "category": cat, "emoji": emoji}

def build_macros_today(uid):
    """Строит сводку макронутриентов за сегодня (упрощённо через КБЖУ)"""
    rows = get_meals_today(uid)
    if not rows:
        return "📊 *Макронутриенты сегодня*\n\nЗаписей нет. Начни вести дневник питания!"
    # Примерные соотношения БЖУ для известных продуктов
    MACROS = {
        "куриная грудка":  (23, 2, 0), "говядина": (26, 11, 0),
        "яйцо":            (13, 11, 1), "творог":   (18, 5, 3),
        "гречка":          (13, 3, 68), "бурый рис": (7, 2, 77),
        "овсянка":         (11, 6, 65), "макароны": (11, 1, 71),
        "молоко":          (3, 3, 5),   "йогурт":   (5, 3, 7),
        "куриное бедро":   (18, 15, 0), "индейка":  (22, 4, 0),
    }
    total_p = total_f = total_c = total_kcal = 0
    for meal, product, grams, kcal in rows:
        total_kcal += kcal
        if product in MACROS:
            p_ratio, f_ratio, c_ratio = MACROS[product]
            total_p += round(p_ratio * grams / 100, 1)
            total_f += round(f_ratio * grams / 100, 1)
            total_c += round(c_ratio * grams / 100, 1)
    lines = [
        "📊 *Макронутриенты сегодня:*\n",
        f"🔥 Калории: *{round(total_kcal)} ккал*",
        f"🥩 Белки: *{round(total_p)} г*",
        f"🧈 Жиры: *{round(total_f)} г*",
        f"🍞 Углеводы: *{round(total_c)} г*",
    ]
    profile = get_profile(uid)
    if profile:
        w = profile.get("current_weight", 80)
        rec_p = round(w * 2)  # 2г/кг
        lines.append(f"\n_Рекомендуется белка: ~{rec_p}г/день (2г/кг веса)_")
        if total_p > 0 and total_p < rec_p * 0.7:
            lines.append("⚠️ Белка маловато — добавь творог, яйца или грудку")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  ТРЕКЕР ДАВЛЕНИЯ И ПУЛЬСА
# ══════════════════════════════════════════════════════
def log_pressure(uid, systolic, diastolic, pulse=None):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute(
        "INSERT INTO pressure_log (user_id, systolic, diastolic, pulse, date) VALUES (?,?,?,?,?)",
        (uid, systolic, diastolic, pulse, now_samara().strftime("%Y-%m-%d %H:%M")))
    conn.commit(); conn.close()

def get_pressure_history(uid, limit=10):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute(
        "SELECT systolic, diastolic, pulse, date FROM pressure_log WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (uid, limit)).fetchall()
    conn.close()
    return rows

def analyze_pressure(systolic, diastolic):
    if systolic < 90 or diastolic < 60:
        return "🔵 Пониженное", "Выпей воды, лягь отдохнуть"
    elif systolic <= 120 and diastolic <= 80:
        return "✅ Норма", "Отличное давление!"
    elif systolic <= 139 or diastolic <= 89:
        return "🟡 Повышенное", "Ограничь соль и кофе, больше воды"
    else:
        return "🔴 Высокое", "Избегай нагрузок, обратись к врачу"

def build_pressure_history_text(uid):
    rows = get_pressure_history(uid, 7)
    if not rows:
        return "🩺 *Давление/пульс*\n\nЗаписей нет. Нажми *«➕ Записать давление»*"
    lines = ["🩺 *История давления (последние 7):*\n"]
    for sys, dia, pulse, dt in rows:
        cat, _ = analyze_pressure(sys, dia)
        pulse_str = f" | 💓 {pulse}" if pulse else ""
        lines.append(f"{dt[:16]} — *{sys}/{dia}* {cat}{pulse_str}")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  ТРЕКЕР ЛЕКАРСТВ
# ══════════════════════════════════════════════════════
def add_medication(uid, name, dose, times_per_day):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute(
        "INSERT INTO medications (user_id, name, dose, times_per_day, active) VALUES (?,?,?,?,1)",
        (uid, name.strip(), dose.strip(), times_per_day))
    conn.commit(); conn.close()

def get_medications(uid):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute(
        "SELECT id, name, dose, times_per_day FROM medications WHERE user_id=? AND active=1",
        (uid,)).fetchall()
    conn.close()
    return rows

def log_medication_taken(uid, med_id):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute(
        "INSERT INTO medication_log (user_id, med_id, date) VALUES (?,?,?)",
        (uid, med_id, now_samara().strftime("%Y-%m-%d %H:%M")))
    conn.commit(); conn.close()

def get_medications_taken_today(uid):
    conn = sqlite3.connect("weight_tracker.db")
    today = now_samara().strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT med_id, COUNT(*) FROM medication_log WHERE user_id=? AND date LIKE ? GROUP BY med_id",
        (uid, f"{today}%")).fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

def build_medications_today(uid):
    meds = get_medications(uid)
    if not meds:
        return ("💊 *Трекер лекарств*\n\nЛекарств нет.\n\n"
                "Нажми *«➕ Добавить лекарство»* чтобы добавить.")
    taken = get_medications_taken_today(uid)
    lines = ["💊 *Лекарства на сегодня:*\n"]
    for mid, name, dose, tpd in meds:
        t = taken.get(mid, 0)
        status = "✅" * t + "⬜" * max(0, tpd - t)
        lines.append(f"{status} *{name}* {dose} ({t}/{tpd} раз)")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  ЭКСПОРТ ДАННЫХ
# ══════════════════════════════════════════════════════
def export_all_data_csv(uid):
    """Экспортирует все данные пользователя в CSV-строку"""
    import io as _io
    conn = sqlite3.connect("weight_tracker.db")
    output = _io.StringIO()

    # Веса
    output.write("=== ВЕС ===\nДата,Вес (кг)\n")
    for row in conn.execute("SELECT date, weight_value FROM weights WHERE user_id=? ORDER BY id", (uid,)):
        output.write(f"{row[0]},{row[1]}\n")

    # Шаги
    output.write("\n=== ШАГИ ===\nДата,Шагов\n")
    for row in conn.execute("SELECT date, step_count FROM steps WHERE user_id=? ORDER BY id", (uid,)):
        output.write(f"{row[0]},{row[1]}\n")

    # Сон
    output.write("\n=== СОН ===\nДата,Часов,Качество\n")
    for row in conn.execute("SELECT date, duration_hours, quality FROM sleep WHERE user_id=? ORDER BY id", (uid,)):
        output.write(f"{row[0]},{row[1]},{row[2]}\n")

    # Вода
    output.write("\n=== ВОДА ===\nДата,Стаканов\n")
    for row in conn.execute("SELECT date, glasses FROM water WHERE user_id=? ORDER BY id", (uid,)):
        output.write(f"{row[0]},{row[1]}\n")

    # Настроение
    output.write("\n=== НАСТРОЕНИЕ ===\nДата,Настроение,Стресс,Энергия\n")
    for row in conn.execute("SELECT date, mood, stress, energy FROM mood_log WHERE user_id=? ORDER BY id", (uid,)):
        output.write(f"{row[0]},{row[1]},{row[2]},{row[3]}\n")

    # Давление
    output.write("\n=== ДАВЛЕНИЕ ===\nДата,Систолическое,Диастолическое,Пульс\n")
    try:
        for row in conn.execute("SELECT date, systolic, diastolic, pulse FROM pressure_log WHERE user_id=? ORDER BY id", (uid,)):
            output.write(f"{row[0]},{row[1]},{row[2]},{row[3] or ''}\n")
    except Exception:
        pass

    # Питание
    output.write("\n=== ПИТАНИЕ ===\nДата,Приём,Продукт,Граммы,Ккал\n")
    for row in conn.execute("SELECT date, meal, product, grams, kcal FROM food_diary WHERE user_id=? ORDER BY id", (uid,)):
        output.write(f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}\n")

    conn.close()
    return output.getvalue()

def export_monthly_report_text(uid):
    """Текстовый отчёт за последние 30 дней"""
    conn = sqlite3.connect("weight_tracker.db")
    month_ago = (now_samara() - timedelta(days=30)).strftime("%Y-%m-%d")
    today = now_samara().strftime("%Y-%m-%d")

    weights = conn.execute(
        "SELECT weight_value FROM weights WHERE user_id=? AND date>=? ORDER BY id",
        (uid, month_ago)).fetchall()
    steps = conn.execute(
        "SELECT step_count FROM steps WHERE user_id=? AND date>=?",
        (uid, month_ago)).fetchall()
    sleep_rows = conn.execute(
        "SELECT duration_hours FROM sleep WHERE user_id=? AND date>=?",
        (uid, month_ago)).fetchall()
    water_rows = conn.execute(
        "SELECT glasses FROM water WHERE user_id=? AND date>=?",
        (uid, month_ago)).fetchall()
    conn.close()

    lines = [f"📋 *Отчёт за 30 дней*\n({month_ago} — {today})\n"]

    if weights:
        w_start = weights[0][0]; w_end = weights[-1][0]
        diff = round(w_end - w_start, 2)
        arrow = "📉" if diff < 0 else "📈" if diff > 0 else "➡️"
        lines.append(f"⚖️ *Вес:* {w_start} → {w_end} кг {arrow} ({'+' if diff>0 else ''}{diff} кг)")
        lines.append(f"   Измерений: {len(weights)}")

    if steps:
        avg = round(sum(s[0] for s in steps) / len(steps))
        best = max(s[0] for s in steps)
        lines.append(f"\n👟 *Шаги:*\n   Среднее: *{avg:,}*/день\n   Лучший день: *{best:,}*".replace(",", " "))

    if sleep_rows:
        avg_s = round(sum(s[0] for s in sleep_rows) / len(sleep_rows), 1)
        lines.append(f"\n😴 *Сон:* среднее *{avg_s}ч*/ночь ({len(sleep_rows)} записей)")

    if water_rows:
        avg_w = round(sum(w[0] for w in water_rows) / len(water_rows), 1)
        lines.append(f"\n💧 *Вода:* среднее *{avg_w}* стак./день")

    streak_cur, streak_best = get_streak(uid)
    lines.append(f"\n🔥 *Стрик:* {streak_cur} дн. (рекорд: {streak_best} дн.)")

    lines.append("\n_Для полного экспорта данных используй «📤 Экспорт CSV»_")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  ГОЛОСОВОЙ ВВОД
# ══════════════════════════════════════════════════════
import subprocess, os

def transcribe_voice_ogg(ogg_path):
    """Конвертирует ogg→wav и пытается распознать через vosk или возвращает None"""
    try:
        wav_path = ogg_path.replace(".ogg", ".wav")
        subprocess.run(
            ["ffmpeg", "-y", "-i", ogg_path, "-ar", "16000", "-ac", "1", wav_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        try:
            import vosk, json as _json, wave as _wave
            model_path = "/opt/vosk-model-ru"
            if not os.path.exists(model_path):
                return None
            model = vosk.Model(model_path)
            wf = _wave.open(wav_path, "rb")
            rec = vosk.KaldiRecognizer(model, wf.getframerate())
            result = ""
            while True:
                data = wf.readframes(4000)
                if not data: break
                if rec.AcceptWaveform(data):
                    result += _json.loads(rec.Result()).get("text", "")
            result += _json.loads(rec.FinalResult()).get("text", "")
            wf.close()
            return result.strip() if result.strip() else None
        except ImportError:
            return None
    except Exception:
        return None

def parse_voice_command(text):
    """Парсит распознанный текст голосовой команды. Возвращает dict или None."""
    if not text:
        return None
    t = text.lower().strip()
    import re as _re
    # вес 105.7
    m = _re.search(r"(?:вес|взвесился|весит?)\s+(\d+[\.,]?\d*)", t)
    if m:
        return {"type": "weight", "value": float(m.group(1).replace(",", "."))}
    # шаги 8500
    m = _re.search(r"(?:шаги?|прошёл|прошел|ходил)\s+(\d+)", t)
    if m:
        return {"type": "steps", "value": int(m.group(1))}
    # вода 3 / выпил 3 стакана
    m = _re.search(r"(?:вода|воды|выпил|стакан[аов]*)\s+(\d+)", t)
    if m:
        return {"type": "water", "value": int(m.group(1))}
    # продукт + граммы: гречка 200 грамм
    m = _re.search(r"([а-яё ]+?)\s+(\d+)\s*(?:грамм|г\b|гр\b)?", t)
    if m:
        product = m.group(1).strip()
        grams = int(m.group(2))
        if product in KCAL_PER_100G and 10 <= grams <= 2000:
            return {"type": "food", "product": product, "grams": grams}
    return None


# ══════════════════════════════════════════════════════
#  ПОЛЬЗОВАТЕЛЬСКИЕ НАПОМИНАНИЯ
# ══════════════════════════════════════════════════════
def save_user_reminder(uid, text, hour, minute, repeat_daily=True):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute(
        "INSERT INTO user_reminders (user_id, reminder_text, hour, minute, repeat_daily, active) VALUES (?,?,?,?,?,1)",
        (uid, text, hour, minute, 1 if repeat_daily else 0))
    conn.commit(); conn.close()

def get_user_reminders(uid):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute(
        "SELECT id, reminder_text, hour, minute FROM user_reminders WHERE user_id=? AND active=1",
        (uid,)).fetchall()
    conn.close()
    return rows

def delete_user_reminder(uid, rid):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("UPDATE user_reminders SET active=0 WHERE id=? AND user_id=?", (rid, uid))
    conn.commit(); conn.close()

def build_reminders_list(uid):
    rows = get_user_reminders(uid)
    if not rows:
        return ("⏰ *Мои напоминания*\n\nНапоминаний нет.\n\n"
                "Добавь через кнопку ниже.\nПример: *«Взвеситься»* в 8:00")
    lines = ["⏰ *Мои напоминания:*\n"]
    for rid, text, hour, minute in rows:
        lines.append(f"• {hour:02d}:{minute:02d} — {text}")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  АНТИПЛАТО (детектор + план)
# ══════════════════════════════════════════════════════
def detect_plateau(uid):
    """Возвращает кол-во дней плато если оно есть, иначе 0"""
    wd = get_weights(uid)
    if len(wd) < 5:
        return 0
    recent = [w[0] for w in wd[-10:]]
    max_diff = max(recent) - min(recent)
    if max_diff < 0.5 and len(recent) >= 5:
        return len(recent)
    return 0

def build_plateau_plan():
    return (
        "🚨 *Обнаружено ПЛАТО!* Вес стоит на месте.\n\n"
        "*5 способов выйти из плато:*\n\n"
        "1️⃣ *Зигзаг калорий*\n"
        "   Пн-Ср-Пт: −200 ккал от нормы\n"
        "   Вт-Чт-Сб: +200 ккал от нормы\n"
        "   Вс: норма\n\n"
        "2️⃣ *Смени тип кардио*\n"
        "   Если бегал — пересядь на велосипед\n"
        "   Если ходил — добавь интервалы\n\n"
        "3️⃣ *Рефид-день*\n"
        "   1 день +500 ккал углеводами (не жирами)\n"
        "   Это поднимает лептин и «перезапускает» метаболизм\n\n"
        "4️⃣ *Проверь воду и соль*\n"
        "   Задержка воды маскирует потерю жира\n"
        "   Уменьши соль на 3 дня, пей больше воды\n\n"
        "5️⃣ *Сделай перерыв*\n"
        "   2–3 дня на поддерживающем калораже\n"
        "   Снижает кортизол и помогает организму перестроиться\n\n"
        "_Плато — нормальная часть пути. Это не остановка, это перегруппировка! 💪_"
    )


# ══════════════════════════════════════════════════════
#  ИНФОГРАФИКА ПРОГРЕССА
# ══════════════════════════════════════════════════════
def build_progress_infographic(uid):
    profile = get_profile(uid)
    if not profile:
        return "📊 Сначала настрой профиль."
    wd = get_weights(uid)
    if not wd:
        return "📊 Нет данных о весе."

    start_w = wd[0][0]
    curr_w  = wd[-1][0]
    target  = profile.get("target_weight") or 70.0
    total_need = round(start_w - target, 1)
    lost = round(start_w - curr_w, 1)
    remain = round(curr_w - target, 1)
    pct = max(0, min(100, round(lost / total_need * 100) if total_need > 0 else 0))

    # Прогресс-бар
    filled = pct // 5
    bar = "█" * filled + "░" * (20 - filled)

    # Дней в пути
    try:
        start_date = datetime.strptime(wd[0][1][:10], "%Y-%m-%d").date()
        days_in = (now_samara().date() - start_date).days
    except Exception:
        days_in = len(wd)

    streak_cur, streak_best = get_streak(uid)

    # Средний темп
    if len(wd) >= 2 and days_in > 0:
        rate_per_week = round(lost / (days_in / 7), 2) if days_in >= 7 else lost
    else:
        rate_per_week = 0

    lines = [
        "📊 *МОЙ ПРОГРЕСС*\n",
        f"⚖️  Старт:   *{start_w} кг*",
        f"📍  Сейчас: *{curr_w} кг*",
        f"🎯  Цель:   *{target} кг*\n",
        f"[{bar}] *{pct}%*\n",
        f"📉 Сброшено:  *{lost} кг*",
        f"📌 Осталось: *{remain} кг*",
        f"📅 Дней в пути: *{days_in}*",
        f"🔥 Стрик: *{streak_cur} дн.* (рекорд: {streak_best})",
    ]
    if rate_per_week > 0:
        lines.append(f"📈 Темп: *{rate_per_week} кг/нед*")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  ПРОГНОЗ ПО НЕДЕЛЯМ (таблица)
# ══════════════════════════════════════════════════════
def build_weekly_forecast(uid):
    profile = get_profile(uid)
    if not profile:
        return "📅 Сначала настрой профиль."
    wd = get_weights(uid)
    if len(wd) < 2:
        return "📅 Нужно минимум 2 записи веса для прогноза."

    curr_w = wd[-1][0]
    target = profile.get("target_weight") or 70.0

    # Средний темп за последние записи
    try:
        n = min(len(wd), 8)
        days_span = (datetime.strptime(wd[-1][1][:10], "%Y-%m-%d") -
                     datetime.strptime(wd[-n][1][:10], "%Y-%m-%d")).days
        lost_span = wd[-n][0] - wd[-1][0]
        if days_span > 0 and lost_span > 0:
            rate_per_week = lost_span / (days_span / 7)
        else:
            rate_per_week = 0.3
    except Exception:
        rate_per_week = 0.3

    if rate_per_week <= 0:
        return "📅 Нет устойчивого тренда снижения для прогноза."

    lines = [f"📅 *Прогноз по неделям* (темп: {round(rate_per_week, 2)} кг/нед)\n"]
    w = curr_w
    today = now_samara().date()
    for week in range(1, 13):
        w = round(w - rate_per_week, 1)
        date = today + timedelta(weeks=week)
        marker = " ← 🎯 ЦЕЛЬ!" if w <= target and (w + rate_per_week) > target else ""
        lines.append(f"Нед. {week:2d} ({date.strftime('%d.%m')}) → *{max(w, target):.1f} кг*{marker}")
        if w <= target:
            break

    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  МЕНЮ НА НЕДЕЛЮ
# ══════════════════════════════════════════════════════
WEEK_MENU_TEMPLATE = {
    "Пн": {
        "🌅 Завтрак": ("овсянка", 80, "яйцо", 2, "яблоко", 150),
        "🥗 Обед":    ("куриная грудка", 200, "бурый рис", 100, "огурец", 150),
        "🌆 Ужин":    ("говядина", 150, "гречка", 80, "помидор", 150),
    },
    "Вт": {
        "🌅 Завтрак": ("творог", 200, "банан", 120, None, 0),
        "🥗 Обед":    ("индейка", 200, "макароны", 100, "брокколи", 150),
        "🌆 Ужин":    ("куриное бедро", 150, "булгур", 80, "огурец", 150),
    },
    "Ср": {
        "🌅 Завтрак": ("гречка", 80, "яйцо", 2, "помидор", 150),
        "🥗 Обед":    ("куриная грудка", 200, "овощной суп", 300, None, 0),
        "🌆 Ужин":    ("рыба", 200, "бурый рис", 80, "стручковая фасоль", 150),
    },
    "Чт": {
        "🌅 Завтрак": ("овсянка", 80, "яблоко", 150, None, 0),
        "🥗 Обед":    ("говядина", 180, "гречка", 100, "брокколи", 150),
        "🌆 Ужин":    ("куриная грудка", 180, "булгур", 80, "шпинат", 100),
    },
    "Пт": {
        "🌅 Завтрак": ("творог", 200, "груша", 130, None, 0),
        "🥗 Обед":    ("индейка", 200, "бурый рис", 100, "огурец", 150),
        "🌆 Ужин":    ("рыба", 200, "гречка", 80, "помидор", 150),
    },
    "Сб": {
        "🌅 Завтрак": ("яйцо", 3, "овсянка", 60, "банан", 120),
        "🥗 Обед":    ("куриная грудка", 250, "макароны", 120, "стручковая фасоль", 150),
        "🌆 Ужин":    ("говядина", 200, "булгур", 100, "огурец", 150),
    },
    "Вс": {
        "🌅 Завтрак": ("гречка", 100, "яйцо", 2, "яблоко", 150),
        "🥗 Обед":    ("куриное бедро", 200, "бурый рис", 120, "помидор", 150),
        "🌆 Ужин":    ("индейка", 180, "овощной суп", 250, None, 0),
    },
}

def build_week_menu(uid):
    profile = get_profile(uid)
    goal_kcal = get_daily_kcal_goal(uid) if profile else 2000
    lines = [f"📅 *МЕНЮ НА НЕДЕЛЮ* (~{goal_kcal} ккал/день)\n"]
    for day, meals in WEEK_MENU_TEMPLATE.items():
        day_kcal = 0
        lines.append(f"*{day}*")
        for slot, items in meals.items():
            slot_kcal = 0
            foods = []
            for i in range(0, len(items), 2):
                prod = items[i]; grams = items[i+1]
                if prod:
                    k = round(KCAL_PER_100G.get(prod, 0) * grams / 100)
                    slot_kcal += k
                    foods.append(f"{prod} {grams}г")
            day_kcal += slot_kcal
            lines.append(f"  {slot}: {', '.join(foods)} — {slot_kcal} ккал")
        lines.append(f"  *Итого: {day_kcal} ккал*\n")
    return "\n".join(lines)

def build_shopping_list_from_menu():
    """Список покупок на неделю из меню"""
    from collections import defaultdict
    totals = defaultdict(float)
    for day, meals in WEEK_MENU_TEMPLATE.items():
        for slot, items in meals.items():
            for i in range(0, len(items), 2):
                prod = items[i]; grams = items[i+1]
                if prod:
                    totals[prod] += grams
    lines = ["🛒 *Список покупок на неделю:*\n"]
    categories = {
        "🥩 Мясо/рыба": ["куриная грудка","куриное бедро","говядина","индейка","рыба"],
        "🥚 Молочное/яйца": ["яйцо","творог","молоко","йогурт"],
        "🌾 Крупы": ["гречка","бурый рис","булгур","овсянка","макароны"],
        "🥦 Овощи": ["брокколи","огурец","помидор","шпинат","стручковая фасоль","морковь"],
        "🍎 Фрукты": ["яблоко","банан","груша","апельсин"],
        "🍲 Прочее": ["овощной суп"],
    }
    categorized = set()
    for cat, products in categories.items():
        cat_items = []
        for p in products:
            if p in totals:
                cat_items.append(f"  • {p.capitalize()} — {round(totals[p])} г")
                categorized.add(p)
        if cat_items:
            lines.append(cat)
            lines.extend(cat_items)
            lines.append("")
    other = [(p, g) for p, g in totals.items() if p not in categorized]
    if other:
        lines.append("📦 Остальное")
        for p, g in other:
            lines.append(f"  • {p.capitalize()} — {round(g)} г")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  ИЗБРАННЫЕ БЛЮДА
# ══════════════════════════════════════════════════════
def add_favorite_dish(uid, dish):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("INSERT OR IGNORE INTO favorite_dishes (user_id, dish) VALUES (?,?)", (uid, dish))
    conn.commit(); conn.close()

def remove_favorite_dish(uid, dish):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("DELETE FROM favorite_dishes WHERE user_id=? AND dish=?", (uid, dish))
    conn.commit(); conn.close()

def get_favorite_dishes(uid):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute("SELECT dish FROM favorite_dishes WHERE user_id=?", (uid,)).fetchall()
    conn.close()
    return [r[0] for r in rows]

def build_favorites_menu(uid):
    favs = get_favorite_dishes(uid)
    if not favs:
        return "⭐ *Избранные блюда*\n\nПусто. Нажми ⭐ рядом с блюдом чтобы добавить."
    lines = ["⭐ *Мои избранные блюда:*\n"]
    for dish in favs:
        kcal = KCAL_PER_100G.get(dish, 0)
        portion = DEFAULT_PORTIONS.get(dish, 100)
        lines.append(f"• {dish.capitalize()} — {portion}г / {round(kcal*portion/100)} ккал")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  СУПЕР-СЕТЫ
# ══════════════════════════════════════════════════════
SUPERSETS = {
    "💪 Грудь + трицепс": [
        ("Жим лёжа", 4, 10, "https://youtu.be/rT7DgCr-3pg"),
        ("Разводка гантелей", 3, 12, "https://youtu.be/eozdVDA78K0"),
        ("Отжимания узким хватом", 3, 15, None),
        ("Французский жим", 3, 12, "https://youtu.be/d_KZxkY_0cM"),
    ],
    "🏋️ Спина + бицепс": [
        ("Тяга штанги в наклоне", 4, 10, "https://youtu.be/G8l_8chR5BE"),
        ("Подтягивания", 4, "макс", None),
        ("Тяга гантели одной рукой", 3, 12, "https://youtu.be/pYcpY20QaE8"),
        ("Сгибание на бицепс", 3, 12, "https://youtu.be/ykJmrZ5v0Oo"),
    ],
    "🦵 Ноги": [
        ("Приседания со штангой", 4, 10, "https://youtu.be/ultWZbUMPL8"),
        ("Жим ногами", 4, 12, "https://youtu.be/IZxyjW7MPJQ"),
        ("Румынская тяга", 3, 12, "https://youtu.be/jEy_czb3RKA"),
        ("Выпады с гантелями", 3, 12, None),
        ("Подъёмы на икры", 4, 20, None),
    ],
    "🔥 Всё тело (круговая)": [
        ("Берпи", 3, 10, None),
        ("Приседания", 3, 15, None),
        ("Отжимания", 3, 15, None),
        ("Скалолаз", 3, 20, None),
        ("Планка", 3, "45 сек", None),
    ],
}

WARMUP_BY_MUSCLE = {
    "💪 Грудь + трицепс": [
        "Вращение плечами назад 20 раз",
        "Разведение рук в стороны 15 раз",
        "Отжимания от стены 15 раз",
        "Растяжка груди у стены 30 сек × 2",
    ],
    "🏋️ Спина + бицепс": [
        "Круговые движения руками 20 раз",
        "Наклоны вперёд без веса 10 раз",
        "Тяга резинки 15 раз",
        "Вис на перекладине 20 сек",
    ],
    "🦵 Ноги": [
        "Ходьба на месте с высоким подъёмом колен 30 сек",
        "Приседания без веса 15 раз",
        "Выпады без веса 10 раз каждая нога",
        "Боковые выпады 10 раз каждая нога",
        "Вращение коленей 10 раз",
    ],
    "🔥 Всё тело (круговая)": [
        "Прыжки на месте 30 сек",
        "Бег на месте 30 сек",
        "Приседания без веса 10 раз",
        "Отжимания облегчённые 10 раз",
    ],
}

def build_superset_text(name):
    exercises = SUPERSETS.get(name)
    if not exercises:
        return "Не найдено."
    warmup = WARMUP_BY_MUSCLE.get(name, [])
    lines = [f"*{name}*\n"]
    if warmup:
        lines.append("🔥 *Разминка (5 мин):*")
        for w in warmup:
            lines.append(f"  • {w}")
        lines.append("")
    lines.append("💪 *Упражнения:*")
    for i, (ex, sets, reps, url) in enumerate(exercises, 1):
        link = f" [▶️]({url})" if url else ""
        lines.append(f"  {i}. {ex} — {sets}×{reps}{link}")
    lines.append("\n⏱️ Отдых между суперсетами: 90–120 сек")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  ВИРТУАЛЬНЫЙ ТРЕНЕР + ЦИТАТА ДНЯ
# ══════════════════════════════════════════════════════
MORNING_QUOTES = [
    "☀️ Каждое утро — новый шанс стать лучше вчерашнего себя.",
    "💪 Дисциплина — это выбор между тем, чего ты хочешь сейчас, и тем, чего ты хочешь больше всего.",
    "🔥 Боль от тренировки проходит. Гордость остаётся навсегда.",
    "🏆 Ты не должен быть великим чтобы начать, но ты должен начать чтобы стать великим.",
    "⚡ Тело достигает того, во что верит разум.",
    "🎯 Прогресс, а не совершенство. Каждый шаг вперёд имеет значение.",
    "🌟 Сложнее всего начать. Всё остальное — просто продолжение.",
    "💎 Трудности делают тебя сильнее. Принимай их как топливо.",
    "🚀 Сегодня ты сделаешь то, что другие не хотят, чтобы завтра иметь то, чего другие не могут.",
    "🧠 Разум сдаётся раньше тела. Держись ещё чуть-чуть.",
    "🌅 Новый день — чистый лист. Напиши что-то достойное.",
    "💫 Маленькие ежедневные улучшения приводят к потрясающим результатам.",
    "🏃 Единственная плохая тренировка — та, которой не было.",
    "⚖️ Весы показывают вес, но не показывают твою силу воли.",
]

def get_quote_of_day():
    day_num = now_samara().timetuple().tm_yday
    return MORNING_QUOTES[day_num % len(MORNING_QUOTES)]

def build_trainer_message(uid):
    """Виртуальный тренер — анализирует активность и реагирует"""
    conn = sqlite3.connect("weight_tracker.db")
    today = now_samara().date()
    # Последняя запись веса
    last_weight = conn.execute(
        "SELECT date FROM weights WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,)).fetchone()
    # Последние шаги
    last_steps_row = conn.execute(
        "SELECT step_count, date FROM steps WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,)).fetchone()
    conn.close()

    messages = []

    if last_weight:
        try:
            lw_date = datetime.strptime(last_weight[0][:10], "%Y-%m-%d").date()
            days_ago = (today - lw_date).days
            if days_ago >= 3:
                messages.append(f"😤 Эй! Ты не взвешивался уже *{days_ago} дня(-ей)*!\nВзвесься сегодня утром — без данных нельзя анализировать прогресс.")
            elif days_ago == 0:
                messages.append("✅ Молодец, сегодня уже взвесился!")
        except Exception:
            pass

    if last_steps_row:
        try:
            steps, sdate = last_steps_row
            sd = datetime.strptime(sdate[:10], "%Y-%m-%d").date()
            days_ago = (today - sd).days
            if days_ago >= 2:
                messages.append(f"🦥 Шаги не вносились *{days_ago} дня(-ей)*. Даже прогулка на 20 минут — это уже 2000 шагов!")
            elif steps < 5000:
                messages.append(f"🔴 Вчера было только *{steps:,} шагов*. Сегодня постарайся дойти до 8000+!".replace(",", " "))
            elif steps >= 12000:
                messages.append(f"🔥 *{steps:,} шагов* вчера — это огонь! Так держать!".replace(",", " "))
        except Exception:
            pass

    streak_cur, streak_best = get_streak(uid)
    if streak_cur >= 7:
        messages.append(f"🏆 *{streak_cur} дней подряд* с активностью! Рекорд под угрозой — не останавливайся!")
    elif streak_cur == 0:
        messages.append("💤 Стрик сброшен. Начни заново — первый шаг сделай сегодня!")

    if not messages:
        messages.append("👍 Всё идёт по плану. Продолжай в том же духе!")

    messages.append(f"\n_{get_quote_of_day()}_")
    return "🤖 *Твой тренер:*\n\n" + "\n\n".join(messages)


# ══════════════════════════════════════════════════════
#  ТЕПЛОВАЯ КАРТА АКТИВНОСТИ
# ══════════════════════════════════════════════════════
def build_activity_heatmap(uid):
    """Текстовая тепловая карта активности за последние 5 недель (как GitHub)"""
    conn = sqlite3.connect("weight_tracker.db")
    today = now_samara().date()
    # Собираем данные за 35 дней
    days_data = {}
    for i in range(34, -1, -1):
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        days_data[d] = 0
    # Шаги
    rows = conn.execute(
        "SELECT date, step_count FROM steps WHERE user_id=? AND date >= ?",
        (uid, (today - timedelta(days=34)).strftime("%Y-%m-%d"))).fetchall()
    for d, s in rows:
        k = d[:10]
        if k in days_data:
            if s >= 10000: days_data[k] = max(days_data[k], 3)
            elif s >= 7000: days_data[k] = max(days_data[k], 2)
            elif s >= 3000: days_data[k] = max(days_data[k], 1)
    # Вес (взвесился = активность)
    rows2 = conn.execute(
        "SELECT date FROM weights WHERE user_id=? AND date >= ?",
        (uid, (today - timedelta(days=34)).strftime("%Y-%m-%d"))).fetchall()
    for (d,) in rows2:
        k = d[:10]
        if k in days_data:
            days_data[k] = max(days_data[k], 1)
    conn.close()

    BLOCKS = {0: "⬛", 1: "🟦", 2: "🟨", 3: "🟩"}
    DAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    # Строим сетку: строки = дни недели, колонки = недели
    dates_list = sorted(days_data.keys())
    # Выравниваем на понедельник
    first_date = datetime.strptime(dates_list[0], "%Y-%m-%d").date()
    offset = first_date.weekday()  # 0=Пн

    grid = [["⬛"] * 5 for _ in range(7)]
    for i, d in enumerate(dates_list):
        col = (i + offset) // 7
        row = (i + offset) % 7
        if col < 5:
            grid[row][col] = BLOCKS[days_data[d]]

    lines = ["📅 *Активность за 5 недель:*\n"]
    for r, day_name in enumerate(DAYS_RU):
        lines.append(f"`{day_name}` " + "".join(grid[r]))
    lines.append("\n⬛ нет данных  🟦 мало  🟨 хорошо  🟩 отлично")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  СРАВНЕНИЕ МЕСЯЦЕВ
# ══════════════════════════════════════════════════════
def build_month_comparison(uid):
    """Сравнивает текущий и прошлый месяц"""
    today = now_samara().date()
    cur_month_start = today.replace(day=1)
    if cur_month_start.month == 1:
        prev_month_start = cur_month_start.replace(year=cur_month_start.year-1, month=12)
    else:
        prev_month_start = cur_month_start.replace(month=cur_month_start.month-1)
    prev_month_end = cur_month_start - timedelta(days=1)

    conn = sqlite3.connect("weight_tracker.db")

    def get_avg(table, col, start, end):
        r = conn.execute(
            f"SELECT AVG({col}) FROM {table} WHERE user_id=? AND date>=? AND date<=?",
            (uid, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))).fetchone()
        return round(r[0], 1) if r and r[0] else 0

    def get_sum(table, col, start, end):
        r = conn.execute(
            f"SELECT SUM({col}) FROM {table} WHERE user_id=? AND date>=? AND date<=?",
            (uid, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))).fetchone()
        return int(r[0]) if r and r[0] else 0

    def get_count(table, start, end):
        r = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE user_id=? AND date>=? AND date<=?",
            (uid, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))).fetchone()
        return r[0] if r else 0

    # Текущий месяц (с начала по сегодня)
    c_steps_avg = get_avg("steps", "step_count", cur_month_start, today)
    c_kcal_avg  = get_avg("food_diary", "calories", cur_month_start, today)
    c_water_avg = get_avg("water_log", "cups", cur_month_start, today)
    c_weight_entries = get_count("weights", cur_month_start, today)

    # Прошлый месяц
    p_steps_avg = get_avg("steps", "step_count", prev_month_start, prev_month_end)
    p_kcal_avg  = get_avg("food_diary", "calories", prev_month_start, prev_month_end)
    p_water_avg = get_avg("water_log", "cups", prev_month_start, prev_month_end)
    p_weight_entries = get_count("weights", prev_month_start, prev_month_end)

    # Вес первый/последний
    cw_first = conn.execute(
        "SELECT weight FROM weights WHERE user_id=? AND date>=? ORDER BY date ASC LIMIT 1",
        (uid, cur_month_start.strftime("%Y-%m-%d"))).fetchone()
    cw_last = conn.execute(
        "SELECT weight FROM weights WHERE user_id=? AND date<=? ORDER BY date DESC LIMIT 1",
        (uid, today.strftime("%Y-%m-%d"))).fetchone()
    pw_first = conn.execute(
        "SELECT weight FROM weights WHERE user_id=? AND date>=? ORDER BY date ASC LIMIT 1",
        (uid, prev_month_start.strftime("%Y-%m-%d"))).fetchone()
    pw_last = conn.execute(
        "SELECT weight FROM weights WHERE user_id=? AND date<=? ORDER BY date DESC LIMIT 1",
        (uid, prev_month_end.strftime("%Y-%m-%d"))).fetchone()
    conn.close()

    def arrow(cur, prev):
        if not prev: return ""
        if cur > prev: return " 📈"
        if cur < prev: return " 📉"
        return " ➡️"

    def weight_delta(first, last):
        if not first or not last: return "нет данных"
        d = round(last[0] - first[0], 1)
        return f"{'+' if d>0 else ''}{d} кг"

    cur_name  = cur_month_start.strftime("%B %Y")
    prev_name = prev_month_start.strftime("%B %Y")

    MONTHS_RU = {"January":"Январь","February":"Февраль","March":"Март","April":"Апрель",
                 "May":"Май","June":"Июнь","July":"Июль","August":"Август",
                 "September":"Сентябрь","October":"Октябрь","November":"Ноябрь","December":"Декабрь"}
    for en, ru in MONTHS_RU.items():
        cur_name = cur_name.replace(en, ru)
        prev_name = prev_name.replace(en, ru)

    lines = [
        "📊 *СРАВНЕНИЕ МЕСЯЦЕВ*\n",
        f"{'Показатель':<18} {'Прошлый':>10} {'Текущий':>10}",
        "─" * 42,
        f"{'🦶 Шаги (ср.)':<18} {p_steps_avg:>10} {c_steps_avg:>10}{arrow(c_steps_avg, p_steps_avg)}",
        f"{'🔥 Ккал (ср.)':<18} {p_kcal_avg:>10} {c_kcal_avg:>10}{arrow(c_kcal_avg, p_kcal_avg)}",
        f"{'💧 Вода (ср.)':<18} {p_water_avg:>10} {c_water_avg:>10}{arrow(c_water_avg, p_water_avg)}",
        f"{'⚖️ Взвешиваний':<18} {p_weight_entries:>10} {c_weight_entries:>10}",
        f"{'📉 Изм. веса':<18} {weight_delta(pw_first,pw_last):>10} {weight_delta(cw_first,cw_last):>10}",
        "",
        f"_{prev_name}_ vs _{cur_name}_"
    ]
    return "```\n" + "\n".join(lines) + "\n```"


# ══════════════════════════════════════════════════════
#  % ВЫПОЛНЕНИЯ ДНЕВНЫХ ЦЕЛЕЙ
# ══════════════════════════════════════════════════════
def build_daily_goals_pct(uid):
    """Показывает % выполнения целей за последние 7 дней"""
    profile = get_profile(uid)
    goal_steps = 10000
    goal_kcal  = get_daily_kcal_goal(uid) if profile else 2000
    goal_water = 8

    today = now_samara().date()
    conn = sqlite3.connect("weight_tracker.db")

    lines = ["🎯 *ВЫПОЛНЕНИЕ ЦЕЛЕЙ (7 дней)*\n"]
    lines.append(f"Цели: {goal_steps:,} шагов | {goal_kcal} ккал | {goal_water} стак. воды\n".replace(",", " "))

    total_score = 0
    days_counted = 0
    for i in range(6, -1, -1):
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        d_short = (today - timedelta(days=i)).strftime("%d.%m")
        steps_r = conn.execute(
            "SELECT step_count FROM steps WHERE user_id=? AND date=?", (uid, d)).fetchone()
        kcal_r = conn.execute(
            "SELECT SUM(calories) FROM food_diary WHERE user_id=? AND date=?", (uid, d)).fetchone()
        water_r = conn.execute(
            "SELECT SUM(cups) FROM water_log WHERE user_id=? AND date=?", (uid, d)).fetchone()

        steps = steps_r[0] if steps_r else 0
        kcal  = kcal_r[0]  if kcal_r and kcal_r[0] else 0
        water = water_r[0] if water_r and water_r[0] else 0

        s_pct = min(100, round(steps / goal_steps * 100)) if goal_steps else 0
        k_pct = min(100, round(kcal  / goal_kcal  * 100)) if goal_kcal  else 0
        w_pct = min(100, round(water / goal_water * 100)) if goal_water else 0
        day_score = round((s_pct + k_pct + w_pct) / 3)

        bar_len = day_score // 10
        bar = "█" * bar_len + "░" * (10 - bar_len)
        emoji = "🟩" if day_score >= 80 else ("🟨" if day_score >= 50 else "🟥")

        lines.append(f"{emoji} *{d_short}* [{bar}] *{day_score}%*")
        lines.append(f"   🦶{s_pct}%  🔥{k_pct}%  💧{w_pct}%")

        if steps or kcal or water:
            total_score += day_score
            days_counted += 1

    if days_counted:
        avg = round(total_score / days_counted)
        lines.append(f"\n📊 Средний балл за неделю: *{avg}%*")

    conn.close()
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  ТРЕКЕР СНА
# ══════════════════════════════════════════════════════
def log_sleep(uid, hours):
    conn = sqlite3.connect("weight_tracker.db")
    today = now_samara().date().strftime("%Y-%m-%d")
    conn.execute(
        "INSERT OR REPLACE INTO sleep_log (user_id, date, hours) VALUES (?,?,?)",
        (uid, today, hours))
    conn.commit(); conn.close()

def get_sleep_history(uid, days=7):
    conn = sqlite3.connect("weight_tracker.db")
    today = now_samara().date()
    since = (today - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT date, hours FROM sleep_log WHERE user_id=? AND date>=? ORDER BY date DESC",
        (uid, since)).fetchall()
    conn.close()
    return rows

def build_sleep_report(uid):
    rows = get_sleep_history(uid, 14)
    if not rows:
        return ("😴 *Трекер сна*\n\nДанных нет.\n\n"
                "Введи кол-во часов сна через кнопку ниже.")
    lines = ["😴 *ТРЕКЕР СНА (14 дней)*\n"]
    total = 0
    for d, h in rows:
        emoji = "🟩" if h >= 7 else ("🟨" if h >= 6 else "🟥")
        bar = "█" * int(h) + ("▌" if h % 1 >= 0.5 else "")
        lines.append(f"{emoji} {d[5:]} — *{h}ч* {bar}")
        total += h
    avg = round(total / len(rows), 1)
    lines.append(f"\n💤 Среднее: *{avg} ч/ночь*")
    if avg < 6:
        lines.append("⚠️ Сон меньше нормы! Недосып замедляет похудение.")
    elif avg >= 7:
        lines.append("✅ Отличный режим сна!")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  ИМТ С ДИНАМИКОЙ
# ══════════════════════════════════════════════════════
def build_bmi_report(uid):
    profile = get_profile(uid)
    if not profile or not profile.get("height"):
        return "📐 Укажи рост в настройках профиля."
    h = float(profile["height"]) / 100
    wd = get_weights(uid)
    if not wd:
        return "📐 Нет данных о весе."
    lines = ["📐 *ИМТ — ДИНАМИКА*\n"]
    for w, d, *_ in wd[-5:]:
        bmi = round(w / (h * h), 1)
        if bmi < 18.5:   cat = "Дефицит"
        elif bmi < 25:   cat = "Норма ✅"
        elif bmi < 30:   cat = "Избыток"
        else:            cat = "Ожирение"
        lines.append(f"• {d[:10]} — {w} кг → ИМТ *{bmi}* ({cat})")
    curr_bmi = round(wd[-1][0] / (h * h), 1)
    normal_w_min = round(18.5 * h * h, 1)
    normal_w_max = round(24.9 * h * h, 1)
    lines.append(f"\n🎯 Норма веса для твоего роста: *{normal_w_min}–{normal_w_max} кг*")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  СЧЁТЧИК КОФЕИНА
# ══════════════════════════════════════════════════════
CAFFEINE_DB = {
    "кофе": 80, "эспрессо": 60, "американо": 70, "капучино": 60,
    "латте": 60, "чай чёрный": 40, "чай зелёный": 25,
    "энергетик": 80, "кока-кола": 35, "pepsi": 35,
    "предтреник": 150, "матча": 35,
}

def log_caffeine(uid, source, mg):
    conn = sqlite3.connect("weight_tracker.db")
    today = now_samara().date().strftime("%Y-%m-%d")
    conn.execute(
        "INSERT INTO caffeine_log (user_id, date, source, mg) VALUES (?,?,?,?)",
        (uid, today, source, mg))
    conn.commit(); conn.close()

def get_caffeine_today(uid):
    conn = sqlite3.connect("weight_tracker.db")
    today = now_samara().date().strftime("%Y-%m-%d")
    r = conn.execute(
        "SELECT SUM(mg), GROUP_CONCAT(source, ', ') FROM caffeine_log WHERE user_id=? AND date=?",
        (uid, today)).fetchone()
    conn.close()
    return (r[0] or 0, r[1] or "")

def build_caffeine_today(uid):
    total, sources = get_caffeine_today(uid)
    limit = 400
    pct = min(100, round(total / limit * 100))
    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
    status = "✅ В норме" if total <= limit else "⚠️ Превышена норма!"
    return (
        f"☕ *Кофеин сегодня*\n\n"
        f"[{bar}] *{total} / {limit} мг* — {status}\n\n"
        f"Источники: {sources or 'нет'}\n\n"
        f"_Норма: до 400 мг/день (ВОЗ)_"
    )


# ══════════════════════════════════════════════════════
#  ГЕЙМИФИКАЦИЯ: XP И УРОВНИ
# ══════════════════════════════════════════════════════
XP_REWARDS = {
    "weight_logged":   10,
    "steps_goal":      20,
    "water_goal":      10,
    "kcal_goal":       15,
    "sleep_logged":    5,
    "streak_bonus":    5,   # × дни стрика
    "challenge_done":  50,
}

LEVELS = [
    (0,    "🥚 Новичок"),
    (100,  "🌱 Старательный"),
    (300,  "💪 Активный"),
    (600,  "🔥 Спортсмен"),
    (1000, "⚡ Атлет"),
    (1500, "🏆 Чемпион"),
    (2500, "💎 Легенда"),
    (5000, "🌟 Мастер"),
]

def add_xp(uid, reason, amount=None):
    pts = amount if amount is not None else XP_REWARDS.get(reason, 5)
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute(
        "INSERT OR IGNORE INTO user_xp (user_id, total_xp) VALUES (?,0)", (uid,))
    conn.execute(
        "UPDATE user_xp SET total_xp = total_xp + ? WHERE user_id=?", (pts, uid))
    conn.commit()
    total = conn.execute(
        "SELECT total_xp FROM user_xp WHERE user_id=?", (uid,)).fetchone()[0]
    conn.close()
    return total

def get_xp(uid):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("INSERT OR IGNORE INTO user_xp (user_id, total_xp) VALUES (?,0)", (uid,))
    conn.commit()
    r = conn.execute("SELECT total_xp FROM user_xp WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return r[0] if r else 0

def get_level(xp):
    level_name = LEVELS[0][1]
    for min_xp, name in LEVELS:
        if xp >= min_xp:
            level_name = name
    return level_name

def get_next_level(xp):
    for i, (min_xp, name) in enumerate(LEVELS):
        if xp < min_xp:
            return min_xp, name
    return None, None

def build_xp_card(uid):
    xp = get_xp(uid)
    level = get_level(xp)
    next_xp, next_name = get_next_level(xp)
    lines = [f"⚡ *МОЙ УРОВЕНЬ*\n", f"Уровень: *{level}*", f"XP: *{xp}*"]
    if next_xp:
        need = next_xp - xp
        pct = max(0, min(100, round((xp - (next_xp - 500)) / 500 * 100))) if next_xp > 500 else round(xp/next_xp*100)
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        lines.append(f"[{bar}] до {next_name}: ещё *{need} XP*")
    else:
        lines.append("🌟 *Максимальный уровень!*")
    lines.append(f"\n*Как зарабатывать XP:*")
    lines.append("• Записать вес — +10 XP")
    lines.append("• 10 000 шагов — +20 XP")
    lines.append("• Норма воды — +10 XP")
    lines.append("• Норма калорий — +15 XP")
    lines.append("• Трекер сна — +5 XP")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  ЕЖЕНЕДЕЛЬНЫЕ ЧЕЛЛЕНДЖИ
# ══════════════════════════════════════════════════════
WEEKLY_CHALLENGES = [
    {"id": "steps_plus", "name": "🦶 Шаговый вызов",
     "desc": "Пройди +1000 шагов сверх своей нормы каждый день недели",
     "xp": 100},
    {"id": "water_week", "name": "💧 Водная неделя",
     "desc": "Выпивай 8+ стаканов каждый день этой недели",
     "xp": 80},
    {"id": "no_sugar",  "name": "🚫 Без сахара",
     "desc": "Не вноси сладкое в дневник питания 5 дней подряд",
     "xp": 120},
    {"id": "weigh_daily", "name": "⚖️ Ежедневное взвешивание",
     "desc": "Взвешивайся каждое утро 7 дней подряд",
     "xp": 70},
    {"id": "sleep_7",   "name": "😴 Сонная неделя",
     "desc": "Спи 7+ часов каждую ночь в течение недели",
     "xp": 90},
]

def get_current_challenge(uid):
    conn = sqlite3.connect("weight_tracker.db")
    r = conn.execute(
        "SELECT challenge_id, start_date, completed FROM weekly_challenge "
        "WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,)).fetchone()
    conn.close()
    return r

def start_challenge(uid, challenge_id):
    today = now_samara().date().strftime("%Y-%m-%d")
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute(
        "INSERT INTO weekly_challenge (user_id, challenge_id, start_date, completed) VALUES (?,?,?,0)",
        (uid, challenge_id, today))
    conn.commit(); conn.close()

def build_challenges_menu(uid):
    current = get_current_challenge(uid)
    lines = ["🏆 *ЕЖЕНЕДЕЛЬНЫЕ ЧЕЛЛЕНДЖИ*\n"]
    if current and not current[2]:
        ch_id = current[0]
        ch = next((c for c in WEEKLY_CHALLENGES if c["id"] == ch_id), None)
        if ch:
            lines.append(f"🎯 *Текущий челлендж:*\n{ch['name']}\n_{ch['desc']}_\n+{ch['xp']} XP\n")
    lines.append("*Выбери следующий:*")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  ДНЕВНИК ТРЕНИРОВОК
# ══════════════════════════════════════════════════════
def log_exercise(uid, exercise, weight_kg, sets, reps):
    conn = sqlite3.connect("weight_tracker.db")
    today = now_samara().date().strftime("%Y-%m-%d")
    conn.execute(
        "INSERT INTO exercise_log (user_id, date, exercise, weight_kg, sets, reps) "
        "VALUES (?,?,?,?,?,?)",
        (uid, today, exercise, weight_kg, sets, reps))
    conn.commit(); conn.close()

def get_exercise_history(uid, exercise, limit=5):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute(
        "SELECT date, weight_kg, sets, reps FROM exercise_log "
        "WHERE user_id=? AND exercise=? ORDER BY date DESC LIMIT ?",
        (uid, exercise, limit)).fetchall()
    conn.close()
    return rows

def build_exercise_log_today(uid):
    conn = sqlite3.connect("weight_tracker.db")
    today = now_samara().date().strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT exercise, weight_kg, sets, reps FROM exercise_log "
        "WHERE user_id=? AND date=? ORDER BY id",
        (uid, today)).fetchall()
    conn.close()
    if not rows:
        return "🏋️ *Дневник тренировки*\n\nСегодня ничего не записано."
    lines = [f"🏋️ *Тренировка {today}*\n"]
    for ex, w, s, r in rows:
        volume = round(w * s * r, 1) if w else 0
        lines.append(f"• *{ex}* — {w}кг × {s}×{r} = {volume} кг объём")
    return "\n".join(lines)

def build_exercise_progression(uid, exercise):
    rows = get_exercise_history(uid, exercise, 8)
    if not rows:
        return f"📈 Нет данных по *{exercise}*"
    lines = [f"📈 *Прогрессия: {exercise}*\n"]
    for d, w, s, r in reversed(rows):
        vol = round(w * s * r, 1) if w else 0
        lines.append(f"• {d[5:]} — {w}кг × {s}×{r} (объём: {vol})")
    # Тренд
    weights = [r[1] for r in rows if r[1]]
    if len(weights) >= 2:
        delta = round(weights[0] - weights[-1], 1)
        if delta < 0:
            lines.append(f"\n📉 Рабочий вес вырос на *{abs(delta)} кг* за период!")
        elif delta > 0:
            lines.append(f"\n📈 Рабочий вес снизился на *{delta} кг*")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  ПЕРСОНАЛЬНЫЙ ПЛАН ПИТАНИЯ
# ══════════════════════════════════════════════════════
def build_nutrition_plan(uid):
    profile = get_profile(uid)
    if not profile:
        return "📋 Сначала настрой профиль (/start)"
    goal_kcal = get_daily_kcal_goal(uid)
    # КБЖУ разбивка
    if profile.get("drying_mode"):
        protein_pct, fat_pct, carb_pct = 0.40, 0.30, 0.30
        goal_label = "🔥 Сушка"
    else:
        protein_pct, fat_pct, carb_pct = 0.30, 0.25, 0.45
        goal_label = "📉 Похудение"
    protein_g = round(goal_kcal * protein_pct / 4)
    fat_g     = round(goal_kcal * fat_pct     / 9)
    carb_g    = round(goal_kcal * carb_pct    / 4)

    lines = [
        f"📋 *ПЕРСОНАЛЬНЫЙ ПЛАН ПИТАНИЯ*\n",
        f"Цель: {goal_label}",
        f"Калории: *{goal_kcal} ккал/день*\n",
        f"🥩 Белки:  *{protein_g} г* ({round(protein_pct*100)}%) — {round(protein_g/4*4)} ккал",
        f"🥑 Жиры:   *{fat_g} г* ({round(fat_pct*100)}%) — {round(fat_g*9)} ккал",
        f"🌾 Углеводы: *{carb_g} г* ({round(carb_pct*100)}%) — {round(carb_g*4)} ккал\n",
        "*Распределение по приёмам пищи:*",
        f"🌅 Завтрак (25%): {round(goal_kcal*0.25)} ккал",
        f"🥗 Обед    (35%): {round(goal_kcal*0.35)} ккал",
        f"🍎 Перекус (10%): {round(goal_kcal*0.10)} ккал",
        f"🌆 Ужин    (30%): {round(goal_kcal*0.30)} ккал\n",
        "*Рекомендации:*",
        f"• Пей *{round(float(profile.get('current_weight') or 75) * 0.033, 1)} л* воды в день",
        f"• Белка минимум *{round(float(profile.get('current_weight') or 75) * 1.8)} г/день*",
        "• Последний приём пищи за 2–3 ч до сна",
        "• Углеводы — в первой половине дня",
    ]
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  РЕФЕРАЛЬНАЯ СИСТЕМА
# ══════════════════════════════════════════════════════
def get_referral_code(uid):
    return f"FIT{uid}"

def get_referral_count(uid):
    conn = sqlite3.connect("weight_tracker.db")
    r = conn.execute(
        "SELECT COUNT(*) FROM referrals WHERE referrer_id=?", (uid,)).fetchone()
    conn.close()
    return r[0] if r else 0

def register_referral(new_uid, ref_code):
    try:
        referrer_id = int(ref_code.replace("FIT", ""))
        if referrer_id == new_uid:
            return False
        conn = sqlite3.connect("weight_tracker.db")
        existing = conn.execute(
            "SELECT id FROM referrals WHERE new_user_id=?", (new_uid,)).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO referrals (referrer_id, new_user_id, date) VALUES (?,?,?)",
                (referrer_id, new_uid, now_samara().date().strftime("%Y-%m-%d")))
            conn.commit()
            # Бонус XP
            add_xp(referrer_id, "referral", 100)
        conn.close()
        return True
    except Exception:
        return False

def build_referral_info(uid):
    code = get_referral_code(uid)
    count = get_referral_count(uid)
    bot_name = "your_fitness_bot"  # будет заменён
    link = f"https://t.me/{bot_name}?start={code}"
    return (
        f"👥 *РЕФЕРАЛЬНАЯ ПРОГРАММА*\n\n"
        f"Приглашай друзей и получай *+100 XP* за каждого!\n\n"
        f"🔗 Твоя ссылка:\n`{link}`\n\n"
        f"👤 Приглашено друзей: *{count}*\n"
        f"⚡ Заработано XP: *{count * 100}*\n\n"
        f"_Поделись ссылкой — друг получит бота, ты — XP!_"
    )


# ══════════════════════════════════════════════════════
#  ЭКСПОРТ ДАННЫХ В JSON (бэкап)
# ══════════════════════════════════════════════════════
def export_full_json(uid):
    import json as _json
    conn = sqlite3.connect("weight_tracker.db")
    data = {}
    tables = [
        ("weights", "SELECT date, weight FROM weights WHERE user_id=? ORDER BY date"),
        ("steps",   "SELECT date, step_count FROM steps WHERE user_id=? ORDER BY date"),
        ("food_diary", "SELECT date, food_name, calories FROM food_diary WHERE user_id=? ORDER BY date"),
        ("water_log",  "SELECT date, cups FROM water_log WHERE user_id=? ORDER BY date"),
        ("sleep_log",  "SELECT date, hours FROM sleep_log WHERE user_id=? ORDER BY date"),
        ("pressure_log", "SELECT date, systolic, diastolic, pulse FROM pressure_log WHERE user_id=? ORDER BY date"),
    ]
    for table, query in tables:
        try:
            rows = conn.execute(query, (uid,)).fetchall()
            data[table] = [list(r) for r in rows]
        except Exception:
            data[table] = []
    profile = get_profile(uid)
    if profile:
        data["profile"] = {k: str(v) for k, v in profile.items() if k != "user_id"}
    data["exported_at"] = now_samara().strftime("%Y-%m-%d %H:%M")
    conn.close()
    return _json.dumps(data, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════
#  АНАЛИЗ ФОТО ЕДЫ / ЧЕКА ЧЕРЕЗ ANTHROPIC VISION
# ══════════════════════════════════════════════════════
def analyze_food_photo(image_bytes, mime_type="image/jpeg"):
    """Отправляет фото еды в Anthropic Vision API, получает оценку КБЖУ"""
    try:
        import anthropic, base64
        client = anthropic.Anthropic()
        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64",
                                                  "media_type": mime_type,
                                                  "data": b64}},
                    {"type": "text", "text": (
                        "Ты нутрициолог. Посмотри на фото еды и оцени примерное содержание "
                        "КБЖУ (калории, белки, жиры, углеводы) для этой порции.\n\n"
                        "Ответь строго в формате:\n"
                        "🍽️ Блюдо: [название]\n"
                        "📏 Порция: ~[вес] г\n"
                        "🔥 Калории: ~[ккал] ккал\n"
                        "🥩 Белки: ~[г] г\n"
                        "🥑 Жиры: ~[г] г\n"
                        "🌾 Углеводы: ~[г] г\n\n"
                        "Затем 1-2 строки: что здесь полезного и что стоит учесть. "
                        "Отвечай по-русски, коротко."
                    )}
                ]
            }]
        )
        return msg.content[0].text
    except ImportError:
        return None
    except Exception as e:
        return None

def analyze_receipt_photo(image_bytes, mime_type="image/jpeg"):
    """Разбирает фото чека из магазина → список продуктов с калориями"""
    try:
        import anthropic, base64
        client = anthropic.Anthropic()
        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=800,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64",
                                                  "media_type": mime_type,
                                                  "data": b64}},
                    {"type": "text", "text": (
                        "Это фото кассового чека из магазина. "
                        "Найди все продукты питания (игнорируй бытовую химию, непродукты). "
                        "Для каждого съедобного продукта укажи примерную калорийность на 100г.\n\n"
                        "Формат ответа:\n"
                        "🛒 Продукты из чека:\n"
                        "• [название] — ~[ккал]/100г\n"
                        "• ...\n\n"
                        "Если не видно чека — скажи об этом. Отвечай по-русски."
                    )}
                ]
            }]
        )
        return msg.content[0].text
    except Exception:
        return None


# ══════════════════════════════════════════════════════
#  ШАБЛОНЫ ПРИЁМОВ ПИЩИ
# ══════════════════════════════════════════════════════
def save_meal_template(uid, name, items):
    """items = [(food_name, calories), ...]"""
    import json as _json
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute(
        "INSERT OR REPLACE INTO meal_templates (user_id, name, items_json) VALUES (?,?,?)",
        (uid, name, _json.dumps(items, ensure_ascii=False)))
    conn.commit(); conn.close()

def get_meal_templates(uid):
    import json as _json
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute(
        "SELECT name, items_json FROM meal_templates WHERE user_id=? ORDER BY name",
        (uid,)).fetchall()
    conn.close()
    result = []
    for name, items_json in rows:
        try:
            items = _json.loads(items_json)
        except Exception:
            items = []
        result.append((name, items))
    return result

def delete_meal_template(uid, name):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("DELETE FROM meal_templates WHERE user_id=? AND name=?", (uid, name))
    conn.commit(); conn.close()

def apply_meal_template(uid, name):
    """Вносит все позиции шаблона в дневник питания сегодня"""
    templates = get_meal_templates(uid)
    for tname, items in templates:
        if tname == name:
            today = now_samara().date().strftime("%Y-%m-%d")
            conn = sqlite3.connect("weight_tracker.db")
            for food_name, calories in items:
                conn.execute(
                    "INSERT INTO food_diary (user_id, date, food_name, calories) VALUES (?,?,?,?)",
                    (uid, today, food_name, calories))
            conn.commit(); conn.close()
            total = sum(c for _, c in items)
            return total
    return 0

def build_templates_menu(uid):
    templates = get_meal_templates(uid)
    if not templates:
        return ("📋 *Шаблоны приёмов пищи*\n\nПусто.\n\n"
                "💡 Как создать шаблон:\n"
                "1. Открой 📓 Дневник питания\n"
                "2. Внеси приём пищи\n"
                "3. Нажми *«💾 Сохранить как шаблон»*")
    lines = ["📋 *Мои шаблоны:*\n"]
    for name, items in templates:
        total = sum(c for _, c in items)
        foods = ", ".join(f[0] for f in items[:3])
        if len(items) > 3:
            foods += f" +{len(items)-3}"
        lines.append(f"• *{name}* — {total} ккал\n  _{foods}_")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  СВОДКА ЗА СЕГОДНЯ (/summary)
# ══════════════════════════════════════════════════════
def build_today_summary(uid):
    today = now_samara().date().strftime("%Y-%m-%d")
    conn = sqlite3.connect("weight_tracker.db")

    # Вес
    w_row = conn.execute(
        "SELECT weight FROM weights WHERE user_id=? AND date LIKE ? ORDER BY id DESC LIMIT 1",
        (uid, today+"%")).fetchone()
    # Шаги
    s_row = conn.execute(
        "SELECT step_count FROM steps WHERE user_id=? AND date=?", (uid, today)).fetchone()
    # Ккал
    k_row = conn.execute(
        "SELECT SUM(calories), COUNT(*) FROM food_diary WHERE user_id=? AND date=?",
        (uid, today)).fetchone()
    # Вода
    wt_row = conn.execute(
        "SELECT SUM(cups) FROM water_log WHERE user_id=? AND date=?", (uid, today)).fetchone()
    # Сон
    sl_row = conn.execute(
        "SELECT hours FROM sleep_log WHERE user_id=? AND date=?", (uid, today)).fetchone()
    # Кофеин
    cf_row = conn.execute(
        "SELECT SUM(mg) FROM caffeine_log WHERE user_id=? AND date=?", (uid, today)).fetchone()
    conn.close()

    profile = get_profile(uid)
    goal_kcal  = get_daily_kcal_goal(uid) if profile else 2000
    goal_steps = 10000
    goal_water = 8

    weight  = w_row[0] if w_row else None
    steps   = s_row[0] if s_row else 0
    kcal    = int(k_row[0]) if k_row and k_row[0] else 0
    meals   = k_row[1] if k_row else 0
    water   = wt_row[0] if wt_row and wt_row[0] else 0
    sleep_h = sl_row[0] if sl_row else None
    caffeine= int(cf_row[0]) if cf_row and cf_row[0] else 0

    def pct_bar(val, goal, width=8):
        p = min(100, round(val / goal * 100)) if goal else 0
        filled = round(p / 100 * width)
        return "█"*filled + "░"*(width-filled), p

    s_bar, s_pct = pct_bar(steps, goal_steps)
    k_bar, k_pct = pct_bar(kcal,  goal_kcal)
    w_bar, w_pct = pct_bar(water, goal_water)

    now_h = now_samara().strftime("%H:%M")
    lines = [f"📋 *СВОДКА ЗА СЕГОДНЯ* ({now_h})\n"]

    if weight:
        lines.append(f"⚖️ Вес: *{weight} кг*")
    else:
        lines.append("⚖️ Вес: *не взвешивался*")

    lines.append(f"🦶 Шаги:  [{s_bar}] *{steps:,}/{goal_steps:,}* ({s_pct}%)".replace(",", " "))
    lines.append(f"🔥 Ккал:  [{k_bar}] *{kcal}/{goal_kcal}* ({k_pct}%) — {meals} приёмов")
    lines.append(f"💧 Вода:  [{w_bar}] *{int(water)}/{goal_water}* ст. ({w_pct}%)")

    if sleep_h:
        sleep_emoji = "✅" if sleep_h >= 7 else ("⚠️" if sleep_h >= 6 else "🔴")
        lines.append(f"😴 Сон:   *{sleep_h} ч* {sleep_emoji}")

    if caffeine:
        cf_emoji = "✅" if caffeine <= 400 else "⚠️"
        lines.append(f"☕ Кофеин: *{caffeine} мг* {cf_emoji}")

    # Итоговый балл
    score = round((s_pct + k_pct + w_pct) / 3)
    score_emoji = "🟩" if score >= 80 else ("🟨" if score >= 50 else "🟥")
    lines.append(f"\n{score_emoji} Балл дня: *{score}%*")

    # Мотивация
    if score >= 90:
        lines.append("🏆 Отличный день! Так держать!")
    elif score >= 70:
        lines.append("💪 Хороший день. Ещё чуть-чуть!")
    elif score >= 40:
        lines.append("🔄 День ещё не закончен — догони норму!")
    else:
        lines.append("💡 Начни с малого: выпей стакан воды прямо сейчас.")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  БАЛАНС КАЛОРИЙ: потрачено vs съедено
# ══════════════════════════════════════════════════════
def estimate_calories_burned(steps, workout_done=False, weight_kg=80):
    """Примерный расход калорий по шагам + базовый метаболизм"""
    bmr_per_hour = weight_kg * 1.0  # ~1 ккал/кг/час в покое
    bmr_day = round(bmr_per_hour * 24)
    steps_kcal = round(steps * 0.04)   # ~0.04 ккал/шаг
    workout_kcal = 300 if workout_done else 0
    return bmr_day + steps_kcal + workout_kcal

def build_calorie_balance(uid):
    today = now_samara().date().strftime("%Y-%m-%d")
    conn = sqlite3.connect("weight_tracker.db")
    kcal_eaten = conn.execute(
        "SELECT SUM(calories) FROM food_diary WHERE user_id=? AND date=?",
        (uid, today)).fetchone()
    steps_row = conn.execute(
        "SELECT step_count FROM steps WHERE user_id=? AND date=?",
        (uid, today)).fetchone()
    conn.close()

    profile = get_profile(uid)
    weight  = float(profile.get("current_weight") or 80) if profile else 80
    eaten   = int(kcal_eaten[0]) if kcal_eaten and kcal_eaten[0] else 0
    steps   = steps_row[0] if steps_row else 0
    burned  = estimate_calories_burned(steps, weight_kg=weight)
    balance = eaten - burned

    bar_val = min(abs(balance), 1000)
    bar_len = round(bar_val / 1000 * 10)
    if balance < 0:
        bar = "🟩" * bar_len + "░" * (10 - bar_len)
        status = f"дефицит *{abs(balance)} ккал* 📉"
    elif balance == 0:
        bar = "🟨" * 10
        status = "баланс ±0 ➡️"
    else:
        bar = "🟥" * bar_len + "░" * (10 - bar_len)
        status = f"профицит *{balance} ккал* 📈"

    return (
        f"⚖️ *КАЛОРИЙНЫЙ БАЛАНС СЕГОДНЯ*\n\n"
        f"🔥 Съедено:   *{eaten} ккал*\n"
        f"🏃 Потрачено: *{burned} ккал*\n"
        f"   (базал. {round(weight*24)} + шаги {round(steps*0.04)})\n\n"
        f"[{bar}]\n{status}\n\n"
        f"{'✅ Ты в дефиците — жир горит!' if balance < -100 else ''}"
        f"{'⚠️ Небольшой профицит — следи за ккал' if 0 < balance < 300 else ''}"
        f"{'🔴 Большой профицит — пересмотри питание' if balance >= 300 else ''}"
    )


# ══════════════════════════════════════════════════════
#  КАЛЬКУЛЯТОР ВОССТАНОВЛЕНИЯ МЫШЦ
# ══════════════════════════════════════════════════════
MUSCLE_RECOVERY_HOURS = {
    "Грудь":      48,
    "Спина":      48,
    "Ноги":       72,
    "Плечи":      48,
    "Бицепс":     36,
    "Трицепс":    36,
    "Пресс":      24,
    "Ягодицы":    72,
}

WORKOUT_MUSCLES = {
    "А":  ["Грудь", "Спина", "Бицепс"],
    "Б":  ["Ноги", "Плечи", "Трицепс"],
    "В":  ["Спина", "Пресс"],
    "ДА": ["Грудь", "Трицепс", "Пресс"],
    "ДБ": ["Ноги", "Ягодицы", "Спина"],
    "ДВ": ["Грудь", "Ноги", "Пресс", "Плечи"],
    "К":  [],
    "ДК": [],
}

def build_muscle_recovery(uid):
    """Показывает готовность мышц к тренировке"""
    conn = sqlite3.connect("weight_tracker.db")
    # Последние 5 тренировок
    rows = conn.execute(
        "SELECT date, exercise FROM exercise_log WHERE user_id=? "
        "ORDER BY date DESC LIMIT 20", (uid,)).fetchall()
    conn.close()

    # Собираем последнюю дату нагрузки на каждую мышцу
    profile = get_profile(uid)
    last_trained = {}
    # Из журнала тренировок
    weekday = now_samara().weekday()
    gym_days = int(profile.get("gym_days") or 3) if profile else 3
    schedule = get_week_schedule(profile, gym_days) if profile else {}
    for i in range(1, 8):
        day = (weekday - i) % 7
        wkey = schedule.get(day)
        if wkey and wkey in WORKOUT_MUSCLES:
            for muscle in WORKOUT_MUSCLES[wkey]:
                if muscle not in last_trained:
                    last_trained[muscle] = i * 24  # часов назад примерно

    now_dt = now_samara()
    lines = ["💪 *ВОССТАНОВЛЕНИЕ МЫШЦ*\n"]
    for muscle, recovery_h in MUSCLE_RECOVERY_HOURS.items():
        trained_h = last_trained.get(muscle, 999)
        rest_h = recovery_h - trained_h
        if rest_h <= 0:
            status = "✅ Готова"
            bar = "█████"
        else:
            pct = max(0, min(100, round((1 - rest_h/recovery_h) * 100)))
            filled = pct // 20
            bar = "█"*filled + "░"*(5-filled)
            if rest_h < 12:
                status = f"⚠️ ещё ~{int(rest_h)}ч"
            else:
                status = f"🔴 ещё ~{int(rest_h//24)}д {int(rest_h%24)}ч"
        lines.append(f"{muscle:<10} [{bar}] {status}")

    lines.append("\n_Данные приблизительные, основаны на расписании_")
    return "```\n" + "\n".join(lines) + "\n```"


# ══════════════════════════════════════════════════════
#  ТАЙМЕР КАРДИО
# ══════════════════════════════════════════════════════
def start_cardio_timer(uid):
    conn = sqlite3.connect("weight_tracker.db")
    now_str = now_samara().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT OR REPLACE INTO cardio_sessions (user_id, start_time, end_time, kcal) "
        "VALUES (?,?,NULL,NULL)", (uid, now_str))
    conn.commit(); conn.close()

def stop_cardio_timer(uid):
    conn = sqlite3.connect("weight_tracker.db")
    row = conn.execute(
        "SELECT id, start_time FROM cardio_sessions WHERE user_id=? AND end_time IS NULL "
        "ORDER BY id DESC LIMIT 1", (uid,)).fetchone()
    if not row:
        conn.close()
        return None
    session_id, start_str = row
    end_dt = now_samara()
    start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
    minutes = round((end_dt - start_dt).total_seconds() / 60)
    profile = get_profile(uid)
    weight = float(profile.get("current_weight") or 80) if profile else 80
    kcal = round(minutes * weight * 0.1)  # ~0.1 ккал/кг/мин для умеренного кардио
    conn.execute(
        "UPDATE cardio_sessions SET end_time=?, kcal=? WHERE id=?",
        (end_dt.strftime("%Y-%m-%d %H:%M:%S"), kcal, session_id))
    # Записываем в дневник
    today = end_dt.date().strftime("%Y-%m-%d")
    conn.execute(
        "INSERT INTO food_diary (user_id, date, food_name, calories) VALUES (?,?,?,?)",
        (uid, today, f"Кардио {minutes} мин", -kcal))
    conn.commit(); conn.close()
    return minutes, kcal


# ══════════════════════════════════════════════════════
#  КАРТОЧКА ПРОГРЕССА ДЛЯ STORIES
# ══════════════════════════════════════════════════════
def build_stories_card(uid):
    profile = get_profile(uid)
    wd = get_weights(uid)
    if not wd or not profile:
        return "📸 Нет данных для карточки."

    start_w  = wd[0][0]
    curr_w   = wd[-1][0]
    target_w = profile.get("target_weight") or 70.0
    lost     = round(start_w - curr_w, 1)
    remain   = round(curr_w - target_w, 1)
    total    = round(start_w - target_w, 1)
    pct      = max(0, min(100, round(lost / total * 100))) if total > 0 else 0

    try:
        start_date = datetime.strptime(wd[0][1][:10], "%Y-%m-%d").date()
        days = (now_samara().date() - start_date).days
    except Exception:
        days = len(wd)

    streak_cur, _ = get_streak(uid)
    xp = get_xp(uid)
    level = get_level(xp)

    bar_filled = pct // 5
    bar = "▓" * bar_filled + "░" * (20 - bar_filled)

    card = [
        "╔══════════════════════════╗",
        "║   💪 МОЙ ФИТНЕС-ПРОГРЕСС  ║",
        "╠══════════════════════════╣",
        f"║  📅 В пути: {days} дн.".ljust(27) + "║",
        f"║  ⚖️  {start_w} → {curr_w} кг".ljust(27) + "║",
        f"║  📉 Минус: {lost} кг".ljust(27) + "║",
        f"║  🎯 До цели: {remain} кг".ljust(27) + "║",
        "║                          ║",
        f"║ [{bar}]║",
        f"║  Прогресс: {pct}%".ljust(27) + "║",
        "║                          ║",
        f"║  🔥 Стрик: {streak_cur} дн.".ljust(27) + "║",
        f"║  {level}".ljust(27) + "║",
        "╚══════════════════════════╝",
    ]
    return "```\n" + "\n".join(card) + "\n```"


# ══════════════════════════════════════════════════════
#  ПАРНЫЙ РЕЖИМ
# ══════════════════════════════════════════════════════
def link_partner(uid, partner_code):
    """Связывает двух пользователей как партнёров"""
    try:
        partner_id = int(partner_code.replace("PAIR", ""))
        if partner_id == uid:
            return False, "Нельзя добавить себя"
        conn = sqlite3.connect("weight_tracker.db")
        # Проверяем что partner_id существует
        exists = conn.execute(
            "SELECT user_id FROM user_profile WHERE user_id=?", (partner_id,)).fetchone()
        if not exists:
            conn.close()
            return False, "Пользователь не найден. Убедись что код верный."
        conn.execute(
            "INSERT OR REPLACE INTO partner_links (user_id, partner_id) VALUES (?,?)",
            (uid, partner_id))
        conn.execute(
            "INSERT OR REPLACE INTO partner_links (user_id, partner_id) VALUES (?,?)",
            (partner_id, uid))
        conn.commit(); conn.close()
        return True, partner_id
    except Exception:
        return False, "Неверный код партнёра"

def get_partner(uid):
    conn = sqlite3.connect("weight_tracker.db")
    r = conn.execute(
        "SELECT partner_id FROM partner_links WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return r[0] if r else None

def build_partner_comparison(uid):
    partner_id = get_partner(uid)
    if not partner_id:
        my_code = f"PAIR{uid}"
        return (
            "👫 *ПАРНЫЙ РЕЖИМ*\n\n"
            "Партнёр не подключён.\n\n"
            f"🔗 Твой код: `{my_code}`\n\n"
            "Отправь этот код партнёру. "
            "Он должен нажать кнопку *«👫 Подключить партнёра»* и ввести твой код."
        )

    my_wd = get_weights(uid)
    pr_wd = get_weights(partner_id)
    my_streak, _ = get_streak(uid)
    pr_streak, _ = get_streak(partner_id)
    my_xp = get_xp(uid)
    pr_xp = get_xp(partner_id)

    my_lost  = round(my_wd[0][0] - my_wd[-1][0], 1) if len(my_wd) >= 2 else 0
    pr_lost  = round(pr_wd[0][0] - pr_wd[-1][0], 1) if len(pr_wd) >= 2 else 0

    def medal(a, b):
        if a > b: return "🥇", "🥈"
        if a < b: return "🥈", "🥇"
        return "🤝", "🤝"

    m_l, p_l = medal(my_lost, pr_lost)
    m_s, p_s = medal(my_streak, pr_streak)
    m_x, p_x = medal(my_xp, pr_xp)

    return (
        f"👫 *СОРЕВНОВАНИЕ С ПАРТНЁРОМ*\n\n"
        f"{'Показатель':<14} {'Ты':>7} {'Партнёр':>9}\n"
        f"{'─'*32}\n"
        f"📉 Сброшено    {m_l} {my_lost}кг  {p_l} {pr_lost}кг\n"
        f"🔥 Стрик       {m_s} {my_streak}дн   {p_s} {pr_streak}дн\n"
        f"⚡ XP           {m_x} {my_xp}    {p_x} {pr_xp}\n\n"
        f"_Удачи вам обоим! Вместе проще! 💪_"
    )


# ─────────────────────────────────────────
#  ВОДА В МЛ
# ─────────────────────────────────────────

def add_water_ml(uid, ml):
    today = now_samara().strftime("%Y-%m-%d")
    conn = sqlite3.connect("weight_tracker.db")
    ex = conn.execute("SELECT id, ml FROM water_ml_log WHERE user_id=? AND date=?", (uid, today)).fetchone()
    if ex:
        conn.execute("UPDATE water_ml_log SET ml=? WHERE id=?", (ex[1]+ml, ex[0]))
    else:
        conn.execute("INSERT INTO water_ml_log (user_id,date,ml) VALUES (?,?,?)", (uid, today, ml))
    conn.commit(); conn.close()

def get_water_ml_today(uid):
    today = now_samara().strftime("%Y-%m-%d")
    conn = sqlite3.connect("weight_tracker.db")
    row = conn.execute("SELECT ml FROM water_ml_log WHERE user_id=? AND date=?", (uid, today)).fetchone()
    conn.close()
    return row[0] if row else 0

def build_water_ml_status(uid):
    ml = get_water_ml_today(uid)
    goal_ml = 2500
    pct = min(100, round(ml / goal_ml * 100))
    filled = round(pct / 10)
    bar = "💧" * filled + "⬜" * (10 - filled)
    return (f"💧 *Вода сегодня*\n\n"
            f"{bar}\n"
            f"*{ml} мл* из {goal_ml} мл ({pct}%)\n\n"
            f"{'✅ Норма выполнена!' if ml >= goal_ml else f'Осталось: {goal_ml-ml} мл'}")

# ─────────────────────────────────────────
#  ШТРИХКОД → Open Food Facts
# ─────────────────────────────────────────

def lookup_barcode(barcode: str):
    """Запрос к Open Food Facts по штрихкоду. Возвращает dict или None."""
    try:
        import urllib.request, json as _json
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        req = urllib.request.Request(url, headers={"User-Agent": "FitnessBot/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = _json.loads(r.read().decode())
        if data.get("status") != 1:
            return None
        prod = data["product"]
        n = prod.get("nutriments", {})
        return {
            "name":     prod.get("product_name", "Продукт"),
            "brand":    prod.get("brands", ""),
            "kcal":     round(n.get("energy-kcal_100g") or n.get("energy_100g", 0) / 4.184 or 0),
            "protein":  round(n.get("proteins_100g", 0), 1),
            "fat":      round(n.get("fat_100g", 0), 1),
            "carbs":    round(n.get("carbohydrates_100g", 0), 1),
        }
    except Exception:
        return None

def build_barcode_result(info, grams=100):
    """Форматирует результат штрихкода"""
    factor = grams / 100
    name = info['name'] + (f" ({info['brand']})" if info['brand'] else "")
    return (f"📦 *{name}*\n\n"
            f"На {grams}г:\n"
            f"🔥 Калории: *{round(info['kcal']*factor)} ккал*\n"
            f"💪 Белки: *{round(info['protein']*factor,1)}г*\n"
            f"🥑 Жиры: *{round(info['fat']*factor,1)}г*\n"
            f"🌾 Углеводы: *{round(info['carbs']*factor,1)}г*")

# ─────────────────────────────────────────
#  ДНЕВНИК СТРЕССА
# ─────────────────────────────────────────

def log_stress(uid, level, note=""):
    today = now_samara().strftime("%Y-%m-%d")
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("INSERT INTO stress_log (user_id,date,level,note) VALUES (?,?,?,?)",
                 (uid, today, level, note))
    conn.commit(); conn.close()

def get_stress_history(uid, days=14):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute(
        "SELECT date, level, note FROM stress_log WHERE user_id=? ORDER BY date DESC LIMIT ?",
        (uid, days)).fetchall()
    conn.close()
    return rows

def build_stress_report(uid):
    rows = get_stress_history(uid, 14)
    if not rows:
        return "📊 Записей стресса пока нет.\n\nОтмечай уровень стресса ежедневно для анализа."
    avg = round(sum(r[1] for r in rows) / len(rows), 1)
    emoji_map = {1:"😌",2:"🙂",3:"😐",4:"😟",5:"😰",6:"😣",7:"😤",8:"😡",9:"🤯",10:"💀"}
    lines = [f"🧠 *Дневник стресса (14 дней)*\n", f"Средний уровень: *{avg}/10*\n"]
    for date, lvl, note in rows[:7]:
        em = emoji_map.get(lvl, "😐")
        d = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m")
        lines.append(f"{d}: {em} *{lvl}/10*" + (f" — {note}" if note else ""))
    return "\n".join(lines)

# ─────────────────────────────────────────
#  МЕНСТРУАЛЬНЫЙ ЦИКЛ
# ─────────────────────────────────────────

CYCLE_PHASES = {
    "менструация":    (1, 5,  "🩸 Фаза: *Менструация* (1-5 день)\n\n💡 Рекомендации:\n• Лёгкие тренировки — йога, ходьба\n• Больше железа: красное мясо, шпинат\n• Снизь интенсивность на 20-30%"),
    "фолликулярная":  (6, 13, "🌱 Фаза: *Фолликулярная* (6-13 день)\n\n💡 Рекомендации:\n• Отличное время для силовых!\n• Энергия растёт — увеличь нагрузку\n• Углеводы помогут восстановлению"),
    "овуляция":       (14,16, "🌸 Фаза: *Овуляция* (14-16 день)\n\n💡 Рекомендации:\n• Пик силы и выносливости\n• Подходит для рекордов и HIIT\n• Больше белка для мышц"),
    "лютеиновая":     (17,28, "🍂 Фаза: *Лютеиновая* (17-28 день)\n\n💡 Рекомендации:\n• Умеренные тренировки\n• Тяга к сладкому — нормально\n• Больше магния: орехи, тёмный шоколад"),
}

def get_cycle_phase(uid):
    conn = sqlite3.connect("weight_tracker.db")
    row = conn.execute(
        "SELECT period_start FROM cycle_log WHERE user_id=? ORDER BY id DESC LIMIT 1",
        (uid,)).fetchone()
    conn.close()
    if not row:
        return None
    try:
        start = datetime.strptime(row[0], "%Y-%m-%d")
        day = (now_samara().replace(tzinfo=None) - start).days + 1
        for phase, (d1, d2, text) in CYCLE_PHASES.items():
            if d1 <= day <= d2:
                return day, phase, text
        return day, "лютеиновая", CYCLE_PHASES["лютеиновая"][2]
    except Exception:
        return None

def log_cycle_start(uid):
    today = now_samara().strftime("%Y-%m-%d")
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("INSERT INTO cycle_log (user_id, period_start) VALUES (?,?)", (uid, today))
    conn.commit(); conn.close()

# ─────────────────────────────────────────
#  HRV / ПУЛЬС ПОКОЯ
# ─────────────────────────────────────────

def log_hrv(uid, hrv=None, pulse=None):
    today = now_samara().strftime("%Y-%m-%d")
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("INSERT INTO hrv_log (user_id,date,hrv,resting_pulse) VALUES (?,?,?,?)",
                 (uid, today, hrv or 0, pulse or 0))
    conn.commit(); conn.close()

def build_hrv_report(uid):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute(
        "SELECT date, hrv, resting_pulse FROM hrv_log WHERE user_id=? ORDER BY date DESC LIMIT 14",
        (uid,)).fetchall()
    conn.close()
    if not rows:
        return "💓 Данных HRV/пульса пока нет.\n\nВведи данные через кнопку *HRV / Пульс покоя*."
    lines = ["💓 *HRV и пульс покоя (14 дней)*\n"]
    for date, hrv, pulse in rows[:7]:
        d = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m")
        parts = []
        if hrv: parts.append(f"HRV: *{hrv}*")
        if pulse: parts.append(f"Пульс: *{pulse} уд/мин*")
        lines.append(f"{d}: {', '.join(parts)}")
    avg_pulse = round(sum(r[2] for r in rows if r[2]) / max(1, sum(1 for r in rows if r[2])))
    if avg_pulse:
        status = "🟢 Отлично" if avg_pulse < 60 else ("🟡 Норма" if avg_pulse < 75 else "🔴 Повышен")
        lines.append(f"\nСредний пульс покоя: *{avg_pulse} уд/мин* {status}")
    return "\n".join(lines)

# ─────────────────────────────────────────
#  ФОТО-ПРОГРЕСС
# ─────────────────────────────────────────

def save_body_photo(uid, file_id, note=""):
    today = now_samara().strftime("%Y-%m-%d")
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("INSERT INTO body_photos (user_id,date,file_id,note) VALUES (?,?,?,?)",
                 (uid, today, file_id, note))
    conn.commit(); conn.close()

def get_body_photos(uid, limit=10):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute(
        "SELECT date, file_id, note FROM body_photos WHERE user_id=? ORDER BY date DESC LIMIT ?",
        (uid, limit)).fetchall()
    conn.close()
    return rows

def build_body_photos_menu(uid):
    photos = get_body_photos(uid, 5)
    if not photos:
        return "📷 *Фото-прогресс*\n\nФотографий пока нет.\n\nОтправь фото с подписью *#прогресс* чтобы сохранить."
    lines = ["📷 *Фото-прогресс*\n\nПоследние фото:\n"]
    for date, fid, note in photos:
        d = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
        lines.append(f"📅 {d}" + (f" — {note}" if note else ""))
    lines.append("\n💡 Отправь фото с подписью *#прогресс* для новой записи")
    return "\n".join(lines)

# ─────────────────────────────────────────
#  1RM — МАКСИМАЛЬНЫЙ ВЕС
# ─────────────────────────────────────────

def calculate_1rm(weight_kg, reps):
    """Формула Эпли: 1RM = вес × (1 + повторения/30)"""
    if reps == 1:
        return weight_kg
    return round(weight_kg * (1 + reps / 30), 1)

def log_1rm(uid, exercise, weight_kg, reps):
    one_rm = calculate_1rm(weight_kg, reps)
    today = now_samara().strftime("%Y-%m-%d")
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("INSERT INTO one_rm_log (user_id,exercise,weight_kg,reps,one_rm,date) VALUES (?,?,?,?,?,?)",
                 (uid, exercise.lower(), weight_kg, reps, one_rm, today))
    conn.commit(); conn.close()
    return one_rm

def get_1rm_history(uid, exercise):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute(
        "SELECT date, weight_kg, reps, one_rm FROM one_rm_log WHERE user_id=? AND exercise=? ORDER BY date DESC LIMIT 10",
        (uid, exercise.lower())).fetchall()
    conn.close()
    return rows

def build_1rm_report(uid):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute(
        "SELECT exercise, MAX(one_rm), MAX(date) FROM one_rm_log WHERE user_id=? GROUP BY exercise ORDER BY MAX(date) DESC LIMIT 10",
        (uid,)).fetchall()
    conn.close()
    if not rows:
        return ("🏋️ *Рекорды (1RM)*\n\nЗаписей пока нет.\n\n"
                "Введи: /1rm *жим лёжа* 100 5\n(упражнение, вес кг, повторений)")
    lines = ["🏋️ *Мои рекорды (1RM)*\n"]
    for ex, orm, date in rows:
        d = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
        lines.append(f"• {ex.capitalize()}: *{orm} кг* ({d})")
    return "\n".join(lines)

# ═══════════════════════════════════════════════════════════
#  TASK #59 — ТРЕНИРОВКИ: ЖУРНАЛ, СТРИК, РАЗМИНКА, ПУЛЬС-ЗОНЫ, СУПЕРСЕТЫ
# ═══════════════════════════════════════════════════════════

def log_exercise_set(uid, exercise, weight_kg, reps, sets=1):
    conn = sqlite3.connect("weight_tracker.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS exercise_journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        date TEXT, exercise TEXT, weight_kg REAL, reps INTEGER, sets INTEGER)''')
    today = date.today().isoformat()
    c.execute("INSERT INTO exercise_journal (user_id, date, exercise, weight_kg, reps, sets) VALUES (?,?,?,?,?,?)",
              (uid, today, exercise.lower(), weight_kg, reps, sets))
    conn.commit(); conn.close()

def get_exercise_history(uid, exercise, limit=10):
    conn = sqlite3.connect("weight_tracker.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS exercise_journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        date TEXT, exercise TEXT, weight_kg REAL, reps INTEGER, sets INTEGER)''')
    c.execute('''SELECT date, weight_kg, reps, sets FROM exercise_journal
                 WHERE user_id=? AND exercise=? ORDER BY date DESC, id DESC LIMIT ?''',
              (uid, exercise.lower(), limit))
    rows = c.fetchall(); conn.close()
    return rows

def build_exercise_history(uid, exercise):
    rows = get_exercise_history(uid, exercise)
    if not rows:
        return f"Нет записей для упражнения *{exercise}*."
    lines = [f"📒 *{exercise.capitalize()} — история*\n"]
    prev_max = 0
    for d, w, r, s in rows:
        vol = w * r * s
        arrow = " 📈" if w > prev_max and prev_max > 0 else ""
        lines.append(f"{d[5:]} — {s}×{r} @ {w}кг (объём {vol:.0f}кг){arrow}")
        prev_max = max(prev_max, w)
    return "\n".join(lines)

def get_activity_streak(uid):
    conn = sqlite3.connect("weight_tracker.db")
    c = conn.cursor()
    c.execute("SELECT DISTINCT date FROM workout_log WHERE user_id=? ORDER BY date DESC", (uid,))
    rows = c.fetchall(); conn.close()
    if not rows:
        return 0, 0
    dates = [date.fromisoformat(r[0]) for r in rows]
    streak = 1
    for i in range(1, len(dates)):
        if (dates[i-1] - dates[i]).days == 1:
            streak += 1
        else:
            break
    return streak, len(dates)

def build_activity_streak(uid):
    streak, total = get_activity_streak(uid)
    if streak == 0:
        return "🔥 *Стрик активности*\n\nЕщё нет тренировок. Начни первую! 💪"
    fire = "🔥" * min(streak, 10)
    msg = f"🔥 *Стрик активности*\n\n{fire}\n\n*{streak}* дней подряд!\nВсего тренировочных дней: *{total}*\n\n"
    if streak >= 30:   msg += "🏆 Легенда! 30+ дней без пропусков!"
    elif streak >= 14: msg += "⭐ Отлично! Уже 2 недели без остановки!"
    elif streak >= 7:  msg += "💪 Неделя позади — так держать!"
    elif streak >= 3:  msg += "✅ Хорошее начало — продолжай!"
    else:              msg += "🌱 Начало положено!"
    return msg

WARMUP_BY_MUSCLE = {
    "грудь":   ["Отжимания широкие — 2×15", "Разводка руками стоя — 30 сек", "Растяжка груди у стены — 20 сек", "Отжимания от стены — 1×20"],
    "спина":   ["Кошка-корова — 10 раз", "Разведение лопаток стоя — 15 раз", "Вращение торсом — 15 раз", "Тяга резинки — 2×15"],
    "ноги":    ["Приседания без веса — 2×20", "Выпады на месте — 1×10 каждая", "Вращение колен — 10 раз", "Растяжка квадрицепса — 20 сек", "Прыжки — 30 сек"],
    "плечи":   ["Вращение плечами вперёд/назад — 15 раз", "Разведение с резинкой — 2×15", "Круги руками — 30 сек", "Растяжка дельты — 20 сек"],
    "руки":    ["Сжатие кулаков — 30 сек", "Вращение запястьями — 15 раз", "Растяжка бицепса — 20 сек", "Отжимания узкие — 1×15"],
    "пресс":   ["Скручивания без веса — 20 раз", "Планка — 30 сек", "Велосипед — 20 раз", "Поднятие колен стоя — 15 раз"],
    "кардио":  ["Ходьба на месте — 2 мин", "Джумпинг Джек — 30 сек", "Бег с высоким подъёмом колен — 30 сек", "Динамичные выпады — 10 раз"],
}

def build_warmup(muscle_group):
    muscle = muscle_group.lower().strip()
    for key in WARMUP_BY_MUSCLE:
        if key in muscle or muscle in key:
            lines = [f"🤸 *Разминка — {key.capitalize()}*\n"]
            for i, ex in enumerate(WARMUP_BY_MUSCLE[key], 1):
                lines.append(f"{i}. {ex}")
            lines.append("\n⏱️ Общее время: 5–7 минут\n💡 После разминки — сразу к рабочим весам!")
            return "\n".join(lines)
    return f"Группа не найдена. Доступные: {', '.join(WARMUP_BY_MUSCLE)}"

def build_warmup_menu():
    kb = types.InlineKeyboardMarkup(row_width=3)
    btns = [types.InlineKeyboardButton(k.capitalize(), callback_data=f"warmup:{k}") for k in WARMUP_BY_MUSCLE]
    for i in range(0, len(btns), 3):
        kb.add(*btns[i:i+3])
    return "🤸 *Разминка* — выбери группу мышц:", kb

def calculate_hr_zones(age, resting_hr=60):
    max_hr = 220 - age
    hrr = max_hr - resting_hr
    zones = {
        "1 — Восстановление":  (int(resting_hr + 0.50 * hrr), int(resting_hr + 0.60 * hrr)),
        "2 — Жиросжигание":    (int(resting_hr + 0.60 * hrr), int(resting_hr + 0.70 * hrr)),
        "3 — Аэробная":        (int(resting_hr + 0.70 * hrr), int(resting_hr + 0.80 * hrr)),
        "4 — Анаэробная":      (int(resting_hr + 0.80 * hrr), int(resting_hr + 0.90 * hrr)),
        "5 — Максимальная":    (int(resting_hr + 0.90 * hrr), max_hr),
    }
    return max_hr, zones

def build_hr_zones(uid):
    p = get_profile(uid)
    if not p or not p.get("age"):
        return "⚠️ Укажи возраст в профиле для расчёта пульсовых зон.", None
    age = p["age"]
    resting = p.get("resting_hr", 60)
    max_hr, zones = calculate_hr_zones(age, resting)
    lines = [f"❤️ *Пульсовые зоны* (возраст {age}, пульс покоя {resting})\n",
             f"Макс. пульс: *{max_hr} уд/мин*\n"]
    emojis = ["🔵", "🟢", "🟡", "🟠", "🔴"]
    for i, (name, (lo, hi)) in enumerate(zones.items()):
        lines.append(f"{emojis[i]} *{name}*: {lo}–{hi} уд/мин")
    lines.append("\n💡 Жиросжигание: зона 2–3 | Выносливость: зона 3–4")
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⚙️ Изменить пульс покоя", callback_data="set_resting_hr"))
    return "\n".join(lines), kb

def log_cardio_session(uid, minutes, zone, avg_hr=0):
    conn = sqlite3.connect("weight_tracker.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cardio_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        date TEXT, minutes INTEGER, zone INTEGER, avg_hr INTEGER)''')
    today = date.today().isoformat()
    c.execute("INSERT INTO cardio_log (user_id, date, minutes, zone, avg_hr) VALUES (?,?,?,?,?)",
              (uid, today, minutes, zone, avg_hr))
    conn.commit(); conn.close()

SUPERSET_TEMPLATES = {
    "грудь+спина":          [("Жим штанги лёжа", "Тяга штанги в наклоне"), ("Разводка гантелей", "Тяга гантели одной рукой"), ("Отжимания", "Подтягивания")],
    "бицепс+трицепс":       [("Подъём штанги на бицепс", "Жим узким хватом"), ("Концентрированный сгиб", "Французский жим"), ("Молотковые сгибания", "Отжимания на брусьях")],
    "пресс+спина":          [("Скручивания", "Гиперэкстензия"), ("Планка", "Обратная гиперэкстензия"), ("Велосипед", "Тяга нижнего блока")],
    "плечи+трапеция":       [("Жим гантелей сидя", "Шраги со штангой"), ("Разведение в стороны", "Тяга к подбородку"), ("Фронтальный подъём", "Шраги с гантелями")],
    "квадрицепс+бицепс бедра": [("Приседания", "Становая тяга"), ("Жим ногами", "Сгибания ног лёжа"), ("Выпады", "Румынская тяга")],
}

def build_superset_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    for name in SUPERSET_TEMPLATES:
        kb.add(types.InlineKeyboardButton(f"⚡ {name.capitalize()}", callback_data=f"superset:{name}"))
    return "⚡ *Суперсеты* — выбери группу мышц:", kb

def build_superset_plan(template_name):
    pairs = SUPERSET_TEMPLATES.get(template_name)
    if not pairs:
        return "Шаблон не найден."
    lines = [f"⚡ *Суперсет — {template_name.capitalize()}*\n", "3–4 раунда, отдых 90 сек:\n"]
    for i, (a, b) in enumerate(pairs, 1):
        lines.append(f"*Суперсет {i}:*")
        lines.append(f"  A. {a} — 3×10–12")
        lines.append(f"  B. {b} — 3×10–12\n")
    lines.append("⏱️ Отдых A→B: 0 сек | Между суперсетами: 90–120 сек")
    return "\n".join(lines)


# ─────────────────────────────────────────
#  8-НЕДЕЛЬНАЯ ПРОГРАММА ТРЕНИРОВОК
# ─────────────────────────────────────────

def build_8week_program(uid):
    profile = get_profile(uid)
    if not profile:
        return "⚠️ Сначала настрой профиль."
    pref = profile.get("workout_pref", "авто")
    home = int(profile.get("home_workouts", 0))
    lines = ["📅 *8-недельная программа прогрессии*\n"]
    if home == 2:
        lines.append("🏠 Режим: только домашние тренировки\n")
        phases = [
            ("Нед 1-2", "Адаптация", "3×12, лёгкий вес / своё тело"),
            ("Нед 3-4", "Нагрузка",  "4×10, увеличь вес/сложность на 10%"),
            ("Нед 5-6", "Интенсив",  "4×8, добавь HIIT 2 раза в неделю"),
            ("Нед 7",   "Перегрузка","5×6, максимальная интенсивность"),
            ("Нед 8",   "Разгрузка", "3×12, лёгкий вес — восстановление"),
        ]
    else:
        lines.append("🏋️ Режим: зал\n")
        phases = [
            ("Нед 1-2", "Адаптация", "3×12, 60% от 1RM — техника"),
            ("Нед 3-4", "Нагрузка",  "4×10, 70% от 1RM — объём"),
            ("Нед 5-6", "Интенсив",  "4×8, 75-80% от 1RM — сила"),
            ("Нед 7",   "Перегрузка","5×5, 85% от 1RM — максимум"),
            ("Нед 8",   "Разгрузка", "3×12, 60% — восстановление"),
        ]
    for period, name, desc in phases:
        lines.append(f"*{period}* — {name}\n  ↳ {desc}\n")
    lines.append("💡 Принцип: каждые 2 недели повышай нагрузку на 5-10%.\n"
                 "Записывай веса в дневнике упражнений для отслеживания прогрессии.")
    return "\n".join(lines)

# ─────────────────────────────────────────
#  ИИ-АНАЛИЗ НЕДЕЛИ
# ─────────────────────────────────────────

def build_ai_week_analysis(uid):
    """Собирает данные недели и формирует персональный анализ через Anthropic API"""
    import os
    profile = get_profile(uid)
    if not profile:
        return "⚠️ Сначала настрой профиль."
    # Собираем данные
    wd = get_weights(uid)
    sd = get_steps(uid, limit=7)
    today = now_samara().strftime("%Y-%m-%d")
    week_ago = (now_samara() - timedelta(days=7)).strftime("%Y-%m-%d")
    conn = sqlite3.connect("weight_tracker.db")
    kcal_rows = conn.execute(
        "SELECT SUM(kcal) FROM food_diary WHERE uid=? AND date>=?", (uid, week_ago)).fetchone()
    workout_rows = conn.execute(
        "SELECT COUNT(*) FROM workouts WHERE user_id=? AND date>=?", (uid, week_ago)).fetchone()
    sleep_rows = conn.execute(
        "SELECT AVG(duration_h) FROM sleep_log WHERE user_id=? AND date>=?", (uid, week_ago)).fetchone()
    conn.close()
    avg_kcal = round((kcal_rows[0] or 0) / 7)
    workouts_count = workout_rows[0] or 0
    avg_sleep = round(sleep_rows[0] or 0, 1)
    weight_change = 0
    if len(wd) >= 2:
        weight_change = round(wd[-1][1] - wd[-2][1], 1)
    avg_steps = round(sum(r[1] for r in sd) / max(1, len(sd)))
    summary = (f"Данные за неделю: вес изменился на {weight_change} кг, "
               f"среднее потребление {avg_kcal} ккал/день, "
               f"тренировок {workouts_count}, "
               f"средний сон {avg_sleep}ч, "
               f"средние шаги {avg_steps}. "
               f"Цель: {profile.get('target_weight','не указана')} кг.")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return (f"📊 *Анализ недели (без ИИ)*\n\n"
                f"⚖️ Изменение веса: *{weight_change:+.1f} кг*\n"
                f"🔥 Среднее ккал/день: *{avg_kcal}*\n"
                f"🏋️ Тренировок: *{workouts_count}*\n"
                f"😴 Средний сон: *{avg_sleep}ч*\n"
                f"👣 Средние шаги: *{avg_steps}*\n\n"
                f"💡 Добавь ANTHROPIC_API_KEY для ИИ-анализа")
    try:
        import anthropic as _anthropic
        client = _anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=400,
            messages=[{"role": "user", "content":
                f"Ты персональный фитнес-тренер. Дай краткий анализ недели и 3 конкретных совета. "
                f"{summary} Отвечай на русском, кратко, с эмодзи, без воды."}]
        )
        ai_text = resp.content[0].text
        return f"🤖 *ИИ-анализ недели*\n\n{ai_text}"
    except Exception as e:
        return f"⚠️ ИИ временно недоступен.\n\n📊 Данные недели:\n{summary}"

# ─────────────────────────────────────────
#  ПРОГНОЗ «ЧТО БУДЕТ ЕСЛИ»
# ─────────────────────────────────────────

def build_scenario_forecast(uid, scenario: str):
    profile = get_profile(uid)
    wd = get_weights(uid)
    if not profile or not wd:
        return "⚠️ Недостаточно данных для прогноза."
    current_w = wd[-1][1]
    target_w  = profile.get("target_weight", current_w - 10)
    plan = get_user_plan(uid, profile)
    weekly_loss = plan.get("weekly_loss", 0.3)
    lines = [f"🔮 *Прогноз: «{scenario}»*\n"]
    if "пропущу" in scenario.lower() or "пропуск" in scenario.lower():
        missed = 3
        extra_weeks = round(missed * 0.2, 1)
        new_date_days = int((current_w - target_w) / max(0.01, weekly_loss) * 7) + int(extra_weeks * 7)
        lines.append(f"❌ При пропуске {missed} тренировок:\n"
                     f"• Потеря темпа: +{extra_weeks} нед к сроку\n"
                     f"• Риск потери мышц: минимальный (до 5 дней)\n"
                     f"• Срок цели сдвигается на ~{int(extra_weeks*7)} дней\n\n"
                     f"💡 Замени тренировку прогулкой — это лучше, чем ничего.")
    elif "лишн" in scenario.lower() or "500 ккал" in scenario.lower() or "переел" in scenario.lower():
        extra_kcal = 500
        extra_fat_g = round(extra_kcal / 7.7, 1)
        lines.append(f"🍕 При лишних {extra_kcal} ккал в день (7 дней):\n"
                     f"• Лишних калорий: +{extra_kcal*7} ккал\n"
                     f"• Возможный набор: ~{extra_fat_g*7/1000:.2f} кг жира\n"
                     f"• Отработка: +1 тренировка или -500 ккал/день\n\n"
                     f"💡 Один плохой день не испортит прогресс — важна неделя в целом.")
    elif "буду" in scenario.lower() or "каждый день" in scenario.lower():
        bonus_weeks = round(weekly_loss * 1.3, 2)
        days_saved = int((current_w - target_w) / max(0.01, bonus_weeks) * 7)
        lines.append(f"✅ При ежедневной активности (+10% нагрузки):\n"
                     f"• Темп потери: ~{bonus_weeks} кг/нед\n"
                     f"• До цели: ~{days_saved} дней\n"
                     f"• Экономия времени: ~{int((current_w-target_w)/max(0.01,weekly_loss)*7)-days_saved} дней\n\n"
                     f"💡 Постоянство важнее интенсивности!")
    else:
        lines.append(f"Текущий темп: *{weekly_loss} кг/нед*\n"
                     f"До цели: *{round((current_w-target_w)/max(0.01,weekly_loss))} нед*\n\n"
                     f"Попробуй сценарии:\n• /прогноз пропущу 3 тренировки\n"
                     f"• /прогноз съем лишние 500 ккал\n• /прогноз буду тренироваться каждый день")
    return "\n".join(lines)

# ─────────────────────────────────────────
#  ИМПОРТ Apple Health / Google Fit (CSV)
# ─────────────────────────────────────────

def import_health_csv(uid, file_bytes: bytes, source: str = "apple"):
    """Парсит CSV из Apple Health или Google Fit и импортирует шаги/вес"""
    import csv as _csv, io as _io
    try:
        text = file_bytes.decode("utf-8", errors="ignore")
        reader = _csv.DictReader(_io.StringIO(text))
        imported = 0
        for row in reader:
            # Apple Health export
            keys = {k.lower().strip(): v for k, v in row.items()}
            date_val = keys.get("date") or keys.get("startdate") or keys.get("creation_date", "")
            date_str = date_val[:10] if date_val else ""
            if not date_str:
                continue
            # Шаги
            steps_val = keys.get("steps") or keys.get("step count") or keys.get("value", "")
            type_val = keys.get("type", "").lower()
            if steps_val and ("step" in type_val or "шаги" in type_val or source == "google_steps"):
                try:
                    steps = int(float(steps_val))
                    conn = sqlite3.connect("weight_tracker.db")
                    ex = conn.execute("SELECT id FROM steps WHERE user_id=? AND date=?", (uid, date_str)).fetchone()
                    if not ex:
                        conn.execute("INSERT INTO steps (user_id,steps,date) VALUES (?,?,?)", (uid, steps, date_str))
                        conn.commit(); imported += 1
                    conn.close()
                except Exception:
                    pass
            # Вес
            weight_val = keys.get("weight") or keys.get("body mass") or ""
            if weight_val and ("weight" in type_val or "mass" in type_val or source == "google_weight"):
                try:
                    w = float(weight_val)
                    if 30 < w < 300:
                        conn = sqlite3.connect("weight_tracker.db")
                        ex = conn.execute("SELECT id FROM weights WHERE user_id=? AND date=?", (uid, date_str)).fetchone()
                        if not ex:
                            conn.execute("INSERT INTO weights (user_id,weight,date) VALUES (?,?,?)", (uid, w, date_str))
                            conn.commit(); imported += 1
                        conn.close()
                except Exception:
                    pass
        # Запишем лог
        conn = sqlite3.connect("weight_tracker.db")
        conn.execute("INSERT INTO health_import_log (user_id,source,imported_at,records) VALUES (?,?,?,?)",
                     (uid, source, now_samara().strftime("%Y-%m-%d %H:%M"), imported))
        conn.commit(); conn.close()
        return imported
    except Exception as e:
        return 0

# ─────────────────────────────────────────
#  МИНИ-ИГРА: угадай калорийность
# ─────────────────────────────────────────

KCAL_QUIZ_ITEMS = [
    ("🍌 Банан (1 шт, 120г)", 107, [80, 107, 150, 200]),
    ("🍕 Пицца Маргарита (1 кусок 100г)", 266, [180, 220, 266, 320]),
    ("🥚 Яйцо варёное (1 шт)", 78, [55, 78, 100, 130]),
    ("🍚 Варёный рис (200г)", 260, [180, 220, 260, 340]),
    ("🥑 Авокадо (100г)", 160, [100, 130, 160, 210]),
    ("🍫 Шоколад молочный (30г)", 158, [100, 130, 158, 190]),
    ("🥗 Греческий салат (200г)", 120, [80, 120, 160, 200]),
    ("🍗 Куриная грудка варёная (150г)", 165, [120, 165, 200, 240]),
    ("🥤 Кока-кола (330мл банка)", 139, [80, 110, 139, 180]),
    ("🥜 Миндаль (30г)", 173, [120, 150, 173, 210]),
    ("🍳 Яичница из 2 яиц на масле", 210, [150, 180, 210, 260]),
    ("🥛 Молоко 3.2% (200мл)", 124, [80, 100, 124, 160]),
]

def get_kcal_quiz_question():
    item = random.choice(KCAL_QUIZ_ITEMS)
    name, correct, options = item
    opts = list(options)
    random.shuffle(opts)
    return name, correct, opts

def build_kcal_quiz_message(uid=None):
    name, correct, opts = get_kcal_quiz_question()
    kb = types.InlineKeyboardMarkup()
    for opt in opts:
        mark = "✅" if opt == correct else ""
        kb.add(types.InlineKeyboardButton(
            f"{opt} ккал {mark}",
            callback_data=f"quiz_ans:{opt}:{correct}"
        ))
    return f"🎮 *Угадай калорийность!*\n\n{name}\n\nСколько калорий?", kb

# ─────────────────────────────────────────
#  ПОМОЩЬ / НАВИГАЦИЯ
# ─────────────────────────────────────────

HELP_TEXT = """❓ *ПОМОЩЬ И НАВИГАЦИЯ*

Бот разделён на 6 разделов. Нажми нужный в главном меню:

🍽️ *Питание* — рацион, дневник, калории, рецепты, штрихкод, покупки, избранное, шаблоны
🏋️ *Тренировки* — план тренировок, программа 8 нед, разминка, таймеры, рекорды 1RM
📊 *Моё тело* — вес, шаги, вода, обхваты, InBody, фото-прогресс, ачивки, партнёр
📈 *Аналитика* — инфографика, прогнозы, ИИ-анализ, отчёты, XP, челленджи, экспорт
😴 *Здоровье* — сон, стресс, цикл, HRV, давление, ограничения, импорт Health
⚙️ *Настройки* — профиль, домашние тренировки, напоминания, партнёр

━━━━━━━━━━━━━━━━━━━
⚡ *БЫСТРЫЕ КОМАНДЫ*

`/w 105.7` — записать вес (кг)
`/s 8500` — записать шаги
`/water 3` — записать воду (стаканы)
`/hrv 65 55` — HRV и пульс покоя
`/1rm жим лёжа 100 5` — записать 1RM
`/summary` — сводка за день
`/receipt` — анализ чека (фото)
`/partner` — парный режим

━━━━━━━━━━━━━━━━━━━
📸 *УМНЫЙ ВВОД*

• *гречка 200* — быстрый расчёт калорий
• Отправь *фото еды* — ИИ распознает и посчитает ккал
• Отправь *фото чека* — бот разберёт покупки
• Отправь *фото с #прогресс* — сохранится в архив
• Отправь *голосовое* — бот поймёт команду
• Отправь *CSV-файл* — импорт из Apple Health / Google Fit

━━━━━━━━━━━━━━━━━━━
💡 *СОВЕТЫ*

• Вноси вес *каждое утро натощак* для точного графика
• Используй *штрихкод* для точного КБЖУ упакованных продуктов
• *Серия дней* — главная мотивация: не прерывай её!
• Подключи *партнёра* — вдвоём придерживаться цели легче
• *ИИ-анализ недели* — раз в неделю для персональных советов"""

def build_help_message():
    return HELP_TEXT

# ─────────────────────────────────────────
#  УМНЫЙ ДНЕВНИК НАСТРОЕНИЯ (расширенный)
# ─────────────────────────────────────────

MOOD_EMOJIS = {1:"😫",2:"😔",3:"😕",4:"😐",5:"🙂",6:"😊",7:"😀",8:"😄",9:"🤩",10:"🥳"}

def log_mood_full(uid, mood, energy, note=""):
    """Расширенная версия: настроение + энергия + заметка"""
    today = now_samara().strftime("%Y-%m-%d")
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("CREATE TABLE IF NOT EXISTS mood_full (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, mood INTEGER, energy INTEGER, note TEXT)")
    ex = conn.execute("SELECT id FROM mood_full WHERE user_id=? AND date=?", (uid, today)).fetchone()
    if ex:
        conn.execute("UPDATE mood_full SET mood=?, energy=?, note=? WHERE id=?", (mood, energy, note, ex[0]))
    else:
        conn.execute("INSERT INTO mood_full (user_id,date,mood,energy,note) VALUES (?,?,?,?,?)", (uid, today, mood, energy, note))
    conn.commit(); conn.close()

def build_mood_week(uid):
    conn = sqlite3.connect("weight_tracker.db")
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS mood_full (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, mood INTEGER, energy INTEGER, note TEXT)")
        rows = conn.execute(
            "SELECT date, mood, energy, note FROM mood_full WHERE user_id=? ORDER BY date DESC LIMIT 7", (uid,)).fetchall()
    except Exception:
        rows = []
    conn.close()
    if not rows:
        return "😊 *Дневник настроения*\n\nЗаписей пока нет.\n\nОцени настроение кнопкой *«😊 Самочувствие»*."
    lines = ["😊 *Дневник настроения (7 дней)*\n"]
    avg_m = round(sum(r[1] for r in rows)/len(rows),1)
    avg_e = round(sum(r[2] for r in rows if r[2])/max(1,sum(1 for r in rows if r[2])),1)
    for date, mood, energy, note in rows:
        d = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m")
        em = MOOD_EMOJIS.get(mood, "😐")
        en = f"⚡{energy}" if energy else ""
        lines.append(f"{d}: {em} *{mood}* {en}" + (f" — _{note}_" if note else ""))
    lines.append(f"\nСредние: настроение *{avg_m}*, энергия *{avg_e}*")
    return "\n".join(lines)

# ═══════════════════════════════════════════════════════════
#  TASK #60 — ТЕЛО: % ЖИРА, ASCII ОБХВАТЫ, ДЕРЕВО ДОСТИЖЕНИЙ, БИОРИТМЫ
# ═══════════════════════════════════════════════════════════

import math as _math

def calculate_body_fat_navy(uid):
    p = get_profile(uid)
    if not p:
        return None, "Профиль не найден"
    conn = sqlite3.connect("weight_tracker.db")
    c = conn.cursor()
    c.execute("SELECT measurement, value FROM body_measurements WHERE user_id=? ORDER BY date DESC LIMIT 20", (uid,))
    rows = c.fetchall(); conn.close()
    measures = {r[0]: r[1] for r in rows}
    gender = p.get("gender", "male")
    height = p.get("height")
    if not height:
        return None, "Укажи рост в профиле"
    waist = measures.get("waist")
    neck  = measures.get("neck")
    hip   = measures.get("hip")
    if not waist or not neck:
        return None, "Добавь обхваты: талия и шея (для женщин ещё бёдра)"
    try:
        if gender == "female":
            if not hip:
                return None, "Для женщин нужен обхват бёдер"
            bf = 163.205 * _math.log10(waist + hip - neck) - 97.684 * _math.log10(height) - 78.387
        else:
            bf = 86.010 * _math.log10(waist - neck) - 70.041 * _math.log10(height) + 36.76
        bf = max(3.0, min(60.0, round(bf, 1)))
    except Exception:
        return None, "Ошибка расчёта (проверь значения обхватов)"
    if gender == "female":
        cat = "Спортсменка" if bf < 14 else "Фитнес" if bf < 21 else "Норма" if bf < 25 else "Выше нормы" if bf < 32 else "Ожирение"
    else:
        cat = "Существенный дефицит" if bf < 6 else "Спортсмен" if bf < 14 else "Фитнес" if bf < 18 else "Норма" if bf < 25 else "Ожирение"
    wd = get_weights(uid)
    weight = wd[-1][1] if wd else None
    fat_kg  = round(weight * bf / 100, 1) if weight else None
    lean_kg = round(weight - fat_kg, 1) if weight and fat_kg else None
    lines = [f"📐 *% Жира (формула ВМС США)*\n", f"Жир: *{bf}%* — {cat}"]
    if fat_kg:  lines.append(f"Жировая масса: *{fat_kg} кг*")
    if lean_kg: lines.append(f"Сухая масса: *{lean_kg} кг*")
    lines.append("\n*Ориентиры муж:* 6–13% спортсмен | 14–17% фитнес | 18–24% норма")
    lines.append("*Ориентиры жен:* 14–20% спортсменка | 21–24% фитнес | 25–31% норма")
    return bf, "\n".join(lines)

def build_measurements_compare(uid):
    conn = sqlite3.connect("weight_tracker.db")
    c = conn.cursor()
    c.execute("SELECT measurement, value, date FROM body_measurements WHERE user_id=? ORDER BY date ASC", (uid,))
    rows = c.fetchall(); conn.close()
    if not rows:
        return "Нет данных обхватов. Добавь через 📏 Обхваты тела."
    first = {}; last = {}
    for measure, val, d in rows:
        if measure not in first: first[measure] = val
        last[measure] = val
    labels = {"waist": "Талия", "chest": "Грудь", "hip": "Бёдра", "bicep": "Бицепс", "thigh": "Бедро", "neck": "Шея"}
    lines = ["📏 *Прогресс обхватов — было → стало*\n"]
    for key, label in labels.items():
        if key in first and key in last:
            f = first[key]; l = last[key]; diff = l - f
            arrow = "⬇️" if diff < 0 else "⬆️" if diff > 0 else "➡️"
            sign  = "−" if diff < 0 else "+"
            lines.append(f"{label}: {f}см → *{l}см* {arrow} {sign}{abs(diff):.1f}см")
    return "\n".join(lines)

ACHIEVEMENT_TREE = [
    {"level": 1,  "xp": 0,     "title": "🌱 Новичок",   "desc": "Только начал путь"},
    {"level": 2,  "xp": 100,   "title": "💪 Боец",      "desc": "Первые шаги сделаны"},
    {"level": 3,  "xp": 250,   "title": "🏃 Бегун",     "desc": "Войди в ритм"},
    {"level": 4,  "xp": 500,   "title": "⚡ Атлет",     "desc": "Стабильные тренировки"},
    {"level": 5,  "xp": 1000,  "title": "🔥 Огонь",     "desc": "Неделя без пропусков"},
    {"level": 6,  "xp": 2000,  "title": "🏋️ Лифтер",    "desc": "Серьёзные веса"},
    {"level": 7,  "xp": 3500,  "title": "🌟 Звезда",    "desc": "Месяц стабильности"},
    {"level": 8,  "xp": 5000,  "title": "💎 Кристалл",  "desc": "Изменения очевидны"},
    {"level": 9,  "xp": 7500,  "title": "🚀 Ракета",    "desc": "Ты вдохновляешь"},
    {"level": 10, "xp": 10000, "title": "🏆 Легенда",   "desc": "Элита — топ 1%"},
]

def build_achievement_tree(uid):
    conn = sqlite3.connect("weight_tracker.db")
    c = conn.cursor()
    c.execute("SELECT xp FROM user_xp WHERE user_id=?", (uid,))
    row = c.fetchone(); conn.close()
    total_xp = row[0] if row else 0
    current_level = max((a["level"] for a in ACHIEVEMENT_TREE if total_xp >= a["xp"]), default=1)
    lines = [f"🌳 *Дерево достижений*\n", f"Всего XP: *{total_xp}*\n"]
    for ach in ACHIEVEMENT_TREE:
        if total_xp >= ach["xp"]:
            marker = "⭐" if ach["level"] == current_level else "✅"
            lines.append(f"{marker} *Ур.{ach['level']}* {ach['title']} — {ach['desc']}")
        else:
            needed = ach["xp"] - total_xp
            lines.append(f"🔒 *Ур.{ach['level']}* {ach['title']} — нужно ещё {needed} XP")
    return "\n".join(lines)

def build_biorhythms(uid):
    p = get_profile(uid)
    if not p or not p.get("birthdate"):
        return "⚠️ Укажи дату рождения в профиле для расчёта биоритмов."
    try:
        bd = date.fromisoformat(p["birthdate"])
    except Exception:
        return "⚠️ Неверный формат даты рождения."
    days_lived = (date.today() - bd).days
    phys  = _math.sin(2 * _math.pi * days_lived / 23)
    emot  = _math.sin(2 * _math.pi * days_lived / 28)
    intel = _math.sin(2 * _math.pi * days_lived / 33)
    def bar(val):
        pct = int((val + 1) / 2 * 10)
        return "█" * pct + "░" * (10 - pct) + f" {val:+.2f}"
    def level(val):
        if val > 0.5: return "высокий ↑"
        if val > 0:   return "выше среднего"
        if val > -0.5: return "ниже среднего"
        return "низкий ↓"
    today_str = date.today().strftime("%d.%m.%Y")
    lines = [f"🔮 *Биоритмы на {today_str}*\n",
             f"💪 Физический:       `{bar(phys)}`  — {level(phys)}",
             f"❤️ Эмоциональный:   `{bar(emot)}`  — {level(emot)}",
             f"🧠 Интеллектуальный: `{bar(intel)}` — {level(intel)}",
             "\n💡 Биоритмы — ориентировочный инструмент самопознания."]
    return "\n".join(lines)

# ─────────────────────────────────────────
#  ЛИЧНЫЙ РЕКОРД ВЕСА / ШАГОВ
# ─────────────────────────────────────────

def build_personal_records(uid):
    wd = get_weights(uid)
    sd = get_steps(uid, limit=365)
    lines = ["🏆 *Личные рекорды*\n"]
    if wd:
        min_w = min(wd, key=lambda x: x[1])
        max_w = max(wd, key=lambda x: x[1])
        start_w = wd[0][1]
        cur_w   = wd[-1][1]
        lost    = round(start_w - cur_w, 1)
        lines.append(f"⚖️ Стартовый вес: *{start_w} кг*")
        lines.append(f"⚖️ Минимальный вес: *{min_w[1]} кг* ({min_w[0][:10]})")
        lines.append(f"📉 Всего сброшено: *{lost} кг* 🎉\n")
    if sd:
        best_day = max(sd, key=lambda x: x[1])
        avg_steps = round(sum(r[1] for r in sd)/len(sd))
        lines.append(f"👣 Рекорд шагов: *{best_day[1]:,}* ({best_day[0][:10]})".replace(",","_"))
        lines.append(f"👣 Среднее шагов/день: *{avg_steps:,}*".replace(",","_"))
    conn = sqlite3.connect("weight_tracker.db")
    streak_row = conn.execute("SELECT MAX(streak) FROM user_profile WHERE user_id=?", (uid,)).fetchone()
    cur_streak = conn.execute("SELECT streak FROM user_profile WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    if cur_streak and cur_streak[0]:
        lines.append(f"\n🔥 Текущая серия: *{cur_streak[0]} дней*")
    return "\n".join(lines)

# ─────────────────────────────────────────
#  БЫСТРЫЕ ЗАМЕТКИ / TODO
# ─────────────────────────────────────────

def add_quick_note(uid, text):
    today = now_samara().strftime("%Y-%m-%d %H:%M")
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("CREATE TABLE IF NOT EXISTS quick_notes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, note TEXT, created TEXT, done INTEGER DEFAULT 0)")
    conn.execute("INSERT INTO quick_notes (user_id,note,created) VALUES (?,?,?)", (uid, text, today))
    conn.commit(); conn.close()

def get_quick_notes(uid):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("CREATE TABLE IF NOT EXISTS quick_notes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, note TEXT, created TEXT, done INTEGER DEFAULT 0)")
    rows = conn.execute(
        "SELECT id, note, done, created FROM quick_notes WHERE user_id=? ORDER BY id DESC LIMIT 15", (uid,)).fetchall()
    conn.close()
    return rows

def build_notes_menu(uid):
    rows = get_quick_notes(uid)
    if not rows:
        return "📝 *Заметки*\n\nЗаметок пока нет.\n\nНапиши боту `/note текст` чтобы добавить заметку."
    lines = ["📝 *Мои заметки*\n"]
    kb = types.InlineKeyboardMarkup(row_width=2)
    for nid, note, done, created in rows:
        status = "✅" if done else "⬜"
        lines.append(f"{status} {note}")
        if not done:
            kb.add(types.InlineKeyboardButton(f"✅ {note[:25]}", callback_data=f"note_done:{nid}"))
    kb.add(types.InlineKeyboardButton("🗑️ Очистить выполненные", callback_data="notes_clear"))
    return "\n".join(lines), kb

# ─────────────────────────────────────────
#  КАЛЬКУЛЯТОР НОРМЫ ВОДЫ
# ─────────────────────────────────────────

def build_water_norm(uid):
    profile = get_profile(uid)
    if not profile:
        return "⚠️ Сначала настрой профиль."
    weight = profile.get("current_weight", 80)
    is_driver = int(profile.get("is_driver", 0))
    # Базовая норма: 35 мл на кг
    base_ml = round(weight * 35)
    # +500 мл если активные тренировки
    gym_days = int(profile.get("gym_days") or 0)
    if gym_days >= 3:
        base_ml += 500
    # -100 мл если сидячая работа
    if is_driver:
        base_ml -= 100
    glasses = round(base_ml / 250)
    ml_today = get_water_ml_today(uid)
    water_cups = get_water_today(uid)
    total_ml = ml_today + water_cups * 250
    pct = min(100, round(total_ml / base_ml * 100))
    bar = "💧" * round(pct/10) + "⬜" * (10 - round(pct/10))
    return (f"💧 *Норма воды*\n\n"
            f"Твоя норма: *{base_ml} мл* (~{glasses} стаканов)\n"
            f"Выпито сегодня: *{total_ml} мл*\n\n"
            f"{bar} {pct}%\n\n"
            f"{'✅ Норма выполнена!' if total_ml >= base_ml else f'Осталось: {base_ml - total_ml} мл'}\n\n"
            f"_Расчёт: {weight}кг × 35мл{'+ тренировки' if gym_days>=3 else ''}_")

# ─────────────────────────────────────────
#  СЧЁТЧИК ПРИВЫЧЕК
# ─────────────────────────────────────────

DEFAULT_HABITS = [
    ("💧 Вода 2л+",   "water"),
    ("🏃 Зарядка",    "morning_exercise"),
    ("🥗 Овощи",      "vegetables"),
    ("📵 Без сладкого","no_sugar"),
    ("😴 Сон 8ч",     "sleep8"),
    ("🚶 10к шагов",  "steps10k"),
]

def get_habits_today(uid):
    today = now_samara().strftime("%Y-%m-%d")
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("CREATE TABLE IF NOT EXISTS habit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, habit_key TEXT)")
    done = {r[0] for r in conn.execute("SELECT habit_key FROM habit_log WHERE user_id=? AND date=?", (uid, today)).fetchall()}
    conn.close()
    return done

def toggle_habit(uid, habit_key):
    today = now_samara().strftime("%Y-%m-%d")
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("CREATE TABLE IF NOT EXISTS habit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, habit_key TEXT)")
    ex = conn.execute("SELECT id FROM habit_log WHERE user_id=? AND date=? AND habit_key=?", (uid, today, habit_key)).fetchone()
    if ex:
        conn.execute("DELETE FROM habit_log WHERE id=?", (ex[0],))
        done = False
    else:
        conn.execute("INSERT INTO habit_log (user_id,date,habit_key) VALUES (?,?,?)", (uid, today, habit_key))
        done = True
    conn.commit(); conn.close()
    return done

def build_habits_keyboard(uid):
    done = get_habits_today(uid)
    count = len(done)
    kb = types.InlineKeyboardMarkup(row_width=2)
    for name, key in DEFAULT_HABITS:
        status = "✅" if key in done else "⬜"
        kb.add(types.InlineKeyboardButton(f"{status} {name}", callback_data=f"habit:{key}"))
    kb.add(types.InlineKeyboardButton(f"📊 Выполнено: {count}/{len(DEFAULT_HABITS)}", callback_data="habits_stats"))
    return kb

def build_habits_stats(uid):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("CREATE TABLE IF NOT EXISTS habit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, habit_key TEXT)")
    rows = conn.execute(
        "SELECT habit_key, COUNT(*) FROM habit_log WHERE user_id=? AND date >= date('now','-30 days') GROUP BY habit_key",
        (uid,)).fetchall()
    conn.close()
    if not rows:
        return "📊 *Статистика привычек*\n\nПока нет данных за 30 дней."
    lines = ["📊 *Привычки за 30 дней*\n"]
    habit_names = {k: n for n, k in DEFAULT_HABITS}
    for key, count in sorted(rows, key=lambda x: -x[1]):
        name = habit_names.get(key, key)
        pct = round(count/30*100)
        bar = "🟩" * round(pct/10) + "⬜" * (10 - round(pct/10))
        lines.append(f"{name}: {bar} {pct}%")
    return "\n".join(lines)

# ─────────────────────────────────────────
#  КАЛЬКУЛЯТОР БЕЛКА ПО ВЕСУ
# ─────────────────────────────────────────

def build_protein_calc(uid):
    profile = get_profile(uid)
    if not profile:
        return "⚠️ Сначала настрой профиль."
    weight = profile.get("current_weight", 80)
    gym_days = int(profile.get("gym_days") or 0)
    drying = int(profile.get("drying_mode", 0))
    # Коэффициент: 1.6–2.2 г/кг в зависимости от активности
    if drying:
        coef = 2.2
        label = "сушка — максимум белка"
    elif gym_days >= 4:
        coef = 2.0
        label = "высокая активность"
    elif gym_days >= 2:
        coef = 1.8
        label = "средняя активность"
    else:
        coef = 1.6
        label = "низкая активность"
    protein_g = round(weight * coef)
    # Источники белка на день
    sources = [
        ("Куриная грудка", 100, 23),
        ("Яйца", 1, 6),
        ("Творог 0%", 100, 18),
        ("Протеин (порция 30г)", 1, 24),
        ("Рыба (лосось)", 100, 20),
    ]
    lines = [
        f"💪 *Норма белка*\n",
        f"Твой вес: *{weight} кг* ({label})",
        f"Коэффициент: *{coef} г/кг*",
        f"Норма в день: *{protein_g}г белка*\n",
        f"Примерный набор:\n"
    ]
    remaining = protein_g
    for src, unit, per_unit in sources:
        qty = round(remaining / per_unit)
        if unit == 100:
            lines.append(f"• {src}: ~{qty*100}г")
        else:
            lines.append(f"• {src}: ~{qty} шт/порций")
        remaining -= qty * per_unit
        if remaining <= 0:
            break
    return "\n".join(lines)

# ═══════════════════════════════════════════════════════════
#  TASK #58 — ПИТАНИЕ: ГОЛОДАНИЕ, ГИ, СРАВНЕНИЕ ДНЕЙ, ИЗБРАННЫЕ, АЛКОГОЛЬ
# ═══════════════════════════════════════════════════════════

# ── Интервальное голодание ──────────────────────────────────
IF_PRESETS = {
    "16:8":  {"fast": 16, "eat": 8,  "label": "16:8 — популярный"},
    "18:6":  {"fast": 18, "eat": 6,  "label": "18:6 — интенсивный"},
    "20:4":  {"fast": 20, "eat": 4,  "label": "20:4 — продвинутый"},
    "14:10": {"fast": 14, "eat": 10, "label": "14:10 — мягкий"},
    "5:2":   {"fast": 0,  "eat": 0,  "label": "5:2 — два дня 500 ккал"},
}

def start_fasting(uid, protocol="16:8"):
    conn = sqlite3.connect("weight_tracker.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS fasting_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        start_ts TEXT, end_ts TEXT, protocol TEXT, completed INTEGER DEFAULT 0)''')
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE fasting_log SET end_ts=?, completed=0 WHERE user_id=? AND end_ts IS NULL",
              (now, uid))
    c.execute("INSERT INTO fasting_log (user_id, start_ts, protocol) VALUES (?,?,?)",
              (uid, now, protocol))
    conn.commit(); conn.close()

def stop_fasting(uid):
    conn = sqlite3.connect("weight_tracker.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS fasting_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        start_ts TEXT, end_ts TEXT, protocol TEXT, completed INTEGER DEFAULT 0)''')
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE fasting_log SET end_ts=?, completed=1 WHERE user_id=? AND end_ts IS NULL",
              (now, uid))
    conn.commit(); conn.close()

def get_fasting_status(uid):
    conn = sqlite3.connect("weight_tracker.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS fasting_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        start_ts TEXT, end_ts TEXT, protocol TEXT, completed INTEGER DEFAULT 0)''')
    c.execute("SELECT start_ts, protocol FROM fasting_log WHERE user_id=? AND end_ts IS NULL ORDER BY id DESC LIMIT 1",
              (uid,))
    row = c.fetchone()
    conn.close()
    return row  # (start_ts, protocol) or None

def build_fasting_status(uid):
    status = get_fasting_status(uid)
    if not status:
        lines = ["⏳ *Интервальное голодание*\n",
                 "Голодание сейчас не активно.\n",
                 "Выбери протокол:"]
        kb = types.InlineKeyboardMarkup(row_width=2)
        btns = [types.InlineKeyboardButton(v["label"], callback_data=f"if_start:{k}")
                for k, v in IF_PRESETS.items()]
        for i in range(0, len(btns), 2):
            kb.add(*btns[i:i+2])
        return "\n".join(lines), kb
    start_ts, protocol = status
    start_dt = datetime.strptime(start_ts, "%Y-%m-%d %H:%M:%S")
    elapsed = datetime.now() - start_dt
    elapsed_h = elapsed.total_seconds() / 3600
    preset = IF_PRESETS.get(protocol, {"fast": 16, "eat": 8})
    fast_h = preset["fast"]
    remaining_h = max(0, fast_h - elapsed_h)
    pct = min(100, int(elapsed_h / fast_h * 100)) if fast_h > 0 else 100
    bar_len = 20
    filled = int(bar_len * pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)
    end_dt = start_dt + timedelta(hours=fast_h)
    lines = [f"⏳ *Интервальное голодание — {protocol}*\n",
             f"Начало: {start_dt.strftime('%H:%M')}",
             f"Конец окна голодания: {end_dt.strftime('%H:%M')}",
             f"\n`[{bar}]` {pct}%",
             f"Прошло: {int(elapsed_h)}ч {int((elapsed_h % 1)*60)}мин"]
    if remaining_h > 0:
        lines.append(f"Осталось: {int(remaining_h)}ч {int((remaining_h % 1)*60)}мин")
    else:
        lines.append("✅ Окно голодания завершено! Можно есть.")
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Завершить голодание", callback_data="if_stop"))
    kb.add(types.InlineKeyboardButton("📊 История", callback_data="if_history"))
    return "\n".join(lines), kb

def build_fasting_history(uid):
    conn = sqlite3.connect("weight_tracker.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS fasting_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        start_ts TEXT, end_ts TEXT, protocol TEXT, completed INTEGER DEFAULT 0)''')
    c.execute("SELECT start_ts, end_ts, protocol, completed FROM fasting_log WHERE user_id=? AND end_ts IS NOT NULL ORDER BY id DESC LIMIT 10",
              (uid,))
    rows = c.fetchall(); conn.close()
    if not rows:
        return "История голодания пуста."
    lines = ["📊 *История голодания (последние 10)*\n"]
    for start_ts, end_ts, protocol, completed in rows:
        try:
            s = datetime.strptime(start_ts, "%Y-%m-%d %H:%M:%S")
            e = datetime.strptime(end_ts,   "%Y-%m-%d %H:%M:%S")
            dur_h = (e - s).total_seconds() / 3600
            mark = "✅" if completed else "⛔"
            lines.append(f"{mark} {s.strftime('%d.%m')} — {protocol}, {dur_h:.1f}ч")
        except Exception:
            pass
    return "\n".join(lines)

# ── Гликемический индекс продуктов ─────────────────────────
GI_DATA = {
    "гречка": 50, "овсянка": 55, "рис белый": 72, "рис бурый": 50,
    "картофель": 80, "батат": 61, "хлеб белый": 75, "хлеб цельнозерновой": 50,
    "макароны": 50, "яблоко": 36, "банан": 51, "апельсин": 43,
    "арбуз": 72, "виноград": 59, "морковь": 35, "свекла": 64,
    "кукурузные хлопья": 81, "мёд": 61, "сахар": 65,
    "шоколад молочный": 49, "мороженое": 60, "йогурт": 36,
    "молоко": 31, "творог": 30, "яйцо": 0, "курица": 0,
    "говядина": 0, "рыба": 0, "авокадо": 10, "орехи": 15,
    "чечевица": 29, "фасоль": 34, "нут": 28,
}

def get_gi(product_name):
    name = product_name.lower().strip()
    if name in GI_DATA:
        return GI_DATA[name]
    for key in GI_DATA:
        if key in name or name in key:
            return GI_DATA[key]
    return None

def gi_label(gi):
    if gi == 0:   return "🟢 ГИ=0 (белок/жир)"
    if gi <= 40:  return f"🟢 ГИ={gi} — низкий"
    if gi <= 70:  return f"🟡 ГИ={gi} — средний"
    return f"🔴 ГИ={gi} — высокий"

# ── Сравнение КБЖУ: вчера vs сегодня ───────────────────────
def build_compare_days_kcal(uid):
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    conn = sqlite3.connect("weight_tracker.db")
    c = conn.cursor()
    def day_totals(d):
        c.execute("SELECT SUM(kcal), SUM(protein), SUM(fat), SUM(carbs) FROM food_log WHERE user_id=? AND date=?",
                  (uid, d))
        row = c.fetchone()
        return [r or 0 for r in row]
    t = day_totals(today); y = day_totals(yesterday)
    conn.close()
    def diff(a, b):
        d = a - b
        return f"+{d:.0f}" if d > 0 else f"{d:.0f}"
    lines = ["📊 *Сравнение дней — КБЖУ*\n",
             f"{'Показатель':<12} {'Вчера':>8} {'Сегодня':>8} {'Δ':>6}",
             "─" * 38,
             f"{'Калории':<12} {y[0]:>8.0f} {t[0]:>8.0f} {diff(t[0],y[0]):>6}",
             f"{'Белки':<12} {y[1]:>8.0f} {t[1]:>8.0f} {diff(t[1],y[1]):>6}",
             f"{'Жиры':<12} {y[2]:>8.0f} {t[2]:>8.0f} {diff(t[2],y[2]):>6}",
             f"{'Углеводы':<12} {y[3]:>8.0f} {t[3]:>8.0f} {diff(t[3],y[3]):>6}"]
    return "```\n" + "\n".join(lines) + "\n```"

# ── Избранные блюда (быстрый повтор) ───────────────────────
def get_favorite_foods(uid, limit=10):
    conn = sqlite3.connect("weight_tracker.db")
    c = conn.cursor()
    c.execute('''SELECT name, kcal, protein, fat, carbs, COUNT(*) as cnt
                 FROM food_log WHERE user_id=?
                 GROUP BY name ORDER BY cnt DESC LIMIT ?''', (uid, limit))
    rows = c.fetchall(); conn.close()
    return rows  # (name, kcal, protein, fat, carbs, cnt)

def build_favorites_menu(uid):
    rows = get_favorite_foods(uid)
    if not rows:
        return "Избранные блюда появятся после нескольких записей в дневник питания.", None
    lines = ["⭐ *Избранные блюда*\n", "Нажми чтобы быстро добавить:\n"]
    kb = types.InlineKeyboardMarkup(row_width=1)
    for name, kcal, protein, fat, carbs, cnt in rows:
        short = name[:20] + "…" if len(name) > 20 else name
        lines.append(f"• {short} — {kcal:.0f} ккал (×{cnt})")
        kb.add(types.InlineKeyboardButton(
            f"➕ {short} ({kcal:.0f} ккал)",
            callback_data=f"fav_add:{name[:40]}:{kcal:.0f}:{protein:.0f}:{fat:.0f}:{carbs:.0f}"))
    return "\n".join(lines), kb

# ── Алкоголь-трекер ────────────────────────────────────────
ALCOHOL_UNITS = {
    "пиво 0.5":     {"units": 2.3, "kcal": 215, "label": "🍺 Пиво 0.5л"},
    "вино 150мл":   {"units": 2.0, "kcal": 120, "label": "🍷 Вино 150мл"},
    "водка 50мл":   {"units": 2.0, "kcal": 115, "label": "🥃 Водка 50мл"},
    "виски 50мл":   {"units": 2.0, "kcal": 115, "label": "🥃 Виски 50мл"},
    "коктейль":     {"units": 1.5, "kcal": 180, "label": "🍹 Коктейль"},
    "шампанское":   {"units": 1.5, "kcal": 105, "label": "🍾 Шампанское 150мл"},
}

def log_alcohol(uid, drink_key, qty=1):
    conn = sqlite3.connect("weight_tracker.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS alcohol_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        date TEXT, drink TEXT, units REAL, kcal INTEGER)''')
    today = date.today().isoformat()
    info = ALCOHOL_UNITS.get(drink_key, {"units": 1.0, "kcal": 100})
    c.execute("INSERT INTO alcohol_log (user_id, date, drink, units, kcal) VALUES (?,?,?,?,?)",
              (uid, today, drink_key, info["units"] * qty, int(info["kcal"] * qty)))
    conn.commit(); conn.close()

def get_alcohol_today(uid):
    conn = sqlite3.connect("weight_tracker.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS alcohol_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        date TEXT, drink TEXT, units REAL, kcal INTEGER)''')
    today = date.today().isoformat()
    c.execute("SELECT SUM(units), SUM(kcal) FROM alcohol_log WHERE user_id=? AND date=?",
              (uid, today))
    row = c.fetchone(); conn.close()
    return (row[0] or 0, row[1] or 0)

def build_alcohol_menu(uid):
    today_u, today_kcal = get_alcohol_today(uid)
    safe_units = 14  # UK рекомендация в неделю
    lines = [f"🍺 *Алкоголь-трекер*\n",
             f"Сегодня: *{today_u:.1f}* ед. / {today_kcal} ккал"]
    if today_u >= 4:
        lines.append("⚠️ Превышена дневная норма (4 ед.)")
    lines.append("\nДобавить напиток:")
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(v["label"], callback_data=f"alcohol:{k}")
            for k, v in ALCOHOL_UNITS.items()]
    for i in range(0, len(btns), 2):
        kb.add(*btns[i:i+2])
    kb.add(types.InlineKeyboardButton("📊 История за неделю", callback_data="alcohol_history"))
    return "\n".join(lines), kb

def build_alcohol_history(uid):
    conn = sqlite3.connect("weight_tracker.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS alcohol_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        date TEXT, drink TEXT, units REAL, kcal INTEGER)''')
    c.execute('''SELECT date, SUM(units), SUM(kcal) FROM alcohol_log
                 WHERE user_id=? AND date >= date('now','-7 days')
                 GROUP BY date ORDER BY date DESC''', (uid,))
    rows = c.fetchall(); conn.close()
    if not rows:
        return "За последние 7 дней алкоголь не фиксировался. 👍"
    total_u = sum(r[1] for r in rows)
    lines = [f"📊 *Алкоголь за 7 дней* — {total_u:.1f} ед. суммарно\n"]
    for d, units, kcal in rows:
        bar = "🟥" * min(int(units), 10)
        lines.append(f"{d[5:]} {bar} {units:.1f} ед. / {kcal} ккал")
    if total_u > 14:
        lines.append("\n⚠️ Превышена недельная норма ВОЗ (14 ед.)")
    return "\n".join(lines)


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
#  ДНЕВНИК ПИТАНИЯ
# ─────────────────────────────────────────

def add_food_entry(uid, meal, product, grams, kcal):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("INSERT INTO food_diary (user_id,meal,product,grams,kcal,date) VALUES (?,?,?,?,?,?)",
                 (uid, meal, product, grams, kcal, now_samara().strftime("%Y-%m-%d")))
    conn.commit(); conn.close()

def get_food_today(uid):
    today = now_samara().strftime("%Y-%m-%d")
    conn  = sqlite3.connect("weight_tracker.db")
    rows  = conn.execute("SELECT meal,product,grams,kcal FROM food_diary WHERE user_id=? AND date=? ORDER BY id",
                         (uid, today)).fetchall()
    conn.close()
    return rows

def get_kcal_today(uid):
    rows = get_food_today(uid)
    return round(sum(r[3] for r in rows))

# ─────────────────────────────────────────
#  ЖУРНАЛ ВЕСОВ В УПРАЖНЕНИЯХ
# ─────────────────────────────────────────

def log_exercise_weight(uid, exercise, weight_kg, reps, sets):
    conn = sqlite3.connect("weight_tracker.db")
    conn.execute("INSERT INTO workout_weights (user_id,exercise,weight_kg,reps,sets,date) VALUES (?,?,?,?,?,?)",
                 (uid, exercise, weight_kg, reps, sets, now_samara().strftime("%Y-%m-%d")))
    conn.commit(); conn.close()

def get_exercise_history(uid, exercise, limit=5):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute("SELECT weight_kg,reps,sets,date FROM workout_weights WHERE user_id=? AND exercise=? ORDER BY id DESC LIMIT ?",
                        (uid, exercise, limit)).fetchall()
    conn.close()
    return list(reversed(rows))

def get_all_exercises(uid):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute("SELECT DISTINCT exercise FROM workout_weights WHERE user_id=? ORDER BY exercise",
                        (uid,)).fetchall()
    conn.close()
    return [r[0] for r in rows]

# ─────────────────────────────────────────
#  ТРЕКЕР САМОЧУВСТВИЯ
# ─────────────────────────────────────────

def log_wellbeing(uid, mood, energy, stress):
    today = now_samara().strftime("%Y-%m-%d")
    conn  = sqlite3.connect("weight_tracker.db")
    ex    = conn.execute("SELECT id FROM wellbeing WHERE user_id=? AND date=?", (uid, today)).fetchone()
    if ex:
        conn.execute("UPDATE wellbeing SET mood=?,energy=?,stress=? WHERE id=?",
                     (mood, energy, stress, ex[0]))
    else:
        conn.execute("INSERT INTO wellbeing (user_id,mood,energy,stress,date) VALUES (?,?,?,?,?)",
                     (uid, mood, energy, stress, today))
    conn.commit(); conn.close()

def get_wellbeing_history(uid, limit=7):
    conn = sqlite3.connect("weight_tracker.db")
    rows = conn.execute("SELECT mood,energy,stress,date FROM wellbeing WHERE user_id=? ORDER BY id DESC LIMIT ?",
                        (uid, limit)).fetchall()
    conn.close()
    return list(reversed(rows))

# ─────────────────────────────────────────
#  STREAK — СЕРИЯ ДНЕЙ
# ─────────────────────────────────────────

def update_streak(uid):
    today = now_samara().strftime("%Y-%m-%d")
    conn  = sqlite3.connect("weight_tracker.db")
    row   = conn.execute("SELECT last_entry_date,current_streak,best_streak FROM streak WHERE user_id=?",
                         (uid,)).fetchone()
    if not row:
        conn.execute("INSERT INTO streak (user_id,last_entry_date,current_streak,best_streak) VALUES (?,?,1,1)",
                     (uid, today))
        conn.commit(); conn.close()
        return 1, 1
    last_date, current, best = row
    try:
        last_dt = datetime.strptime(last_date, "%Y-%m-%d")
        today_dt = datetime.strptime(today, "%Y-%m-%d")
        delta = (today_dt - last_dt).days
    except Exception:
        delta = 999
    if delta == 0:
        conn.close()
        return current, best
    elif delta == 1:
        current += 1
    else:
        current = 1
    best = max(best, current)
    conn.execute("UPDATE streak SET last_entry_date=?,current_streak=?,best_streak=? WHERE user_id=?",
                 (today, current, best, uid))
    conn.commit(); conn.close()
    return current, best

def get_streak(uid):
    conn = sqlite3.connect("weight_tracker.db")
    row  = conn.execute("SELECT current_streak,best_streak FROM streak WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return (row[0], row[1]) if row else (0, 0)

# ─────────────────────────────────────────
#  ПРОГНОЗ ДАТЫ ЦЕЛИ
# ─────────────────────────────────────────

def calc_goal_date(uid):
    """Считает прогнозируемую дату достижения цели по реальному темпу"""
    profile = get_profile(uid)
    if not profile: return None, None
    wd = get_weights(uid)
    if len(wd) < 2: return None, None
    target = profile.get("target_weight") or 92
    curr_w = wd[-1][0]
    if curr_w <= target: return None, None
    # Считаем средний темп по всем взвешиваниям
    try:
        first_dt = datetime.strptime(wd[0][1][:10], "%Y-%m-%d")
        last_dt  = datetime.strptime(wd[-1][1][:10], "%Y-%m-%d")
        days     = max((last_dt - first_dt).days, 1)
        total_loss = wd[0][0] - curr_w
        daily_loss = total_loss / days
        if daily_loss <= 0: return None, None
        days_left = (curr_w - target) / daily_loss
        goal_date = last_dt + timedelta(days=int(days_left))
        weeks_left = round(days_left / 7, 1)
        return goal_date.strftime("%d.%m.%Y"), weeks_left
    except Exception:
        return None, None

# ─────────────────────────────────────────
#  СПИСОК ПОКУПОК
# ─────────────────────────────────────────

def build_shopping_list(uid):
    """Генерирует список покупок на неделю по рациону"""
    profile = get_profile(uid)
    if not profile: return None
    plan = get_user_plan(uid, profile)
    p    = get_portions(plan["calories"])
    breast_week = round(p["breast"] * 7 / 100) * 100
    carb_week   = round(p["carb"] * 7 / 50) * 50
    oats_week   = 420
    eggs_week   = 21
    return (
        "🛒 *СПИСОК ПОКУПОК НА НЕДЕЛЮ*\n" + "─"*24 + "\n\n"
        "🍗 *Белок:*\n"
        f"• Куриная грудка — *{breast_week}г* (~{breast_week//100} упак.)\n"
        f"• Яйца — *{eggs_week} шт* (3 упаковки)\n"
        "• Консервированная курица — *2-3 банки*\n\n"
        "🍚 *Углеводы:*\n"
        f"• Гречка — *{carb_week}г*\n"
        f"• Овсянка долгой варки — *{oats_week}г*\n"
        "• Рис в пакетах — *7 пакетов*\n\n"
        "🥦 *Овощи:*\n"
        "• Болгарский перец — *5-7 шт*\n"
        "• Морковь — *500г*\n"
        "• Огурцы — *7 шт*\n"
        "• Помидоры — *7 шт*\n"
        "• Замороженная овощная смесь — *1-2 пакета*\n"
        "• Шпинат замороженный — *400г*\n\n"
        "🍎 *Фрукты и орехи:*\n"
        "• Яблоки или груши — *7 шт*\n"
        "• Миндаль/грецкий орех — *140г* (20г × 7)\n\n"
        "🧂 *Специи и масло:*\n"
        "• Оливковое масло — *1 бут.*\n"
        "• Соль, перец, паприка, чеснок\n\n"
        + "─"*24 + "\n"
        "💰 Примерный бюджет: *1 500-2 500 ₽/неделю*\n"
        "⏱️ Готовь в воскресенье на 3-4 дня вперёд!"
    )

WARMUP = (
    "🔥 *РАЗМИНКА ПЕРЕД ТРЕНИРОВКОЙ (5-7 мин)*\n\n"
    "Выполняй каждое упражнение по *30-45 сек:*\n\n"
    "1. *Ходьба на месте* с высоким подъёмом колен\n"
    "   👉 Разогревает сердечно-сосудистую систему\n\n"
    "2. *Вращение плечами* вперёд и назад\n"
    "   👉 По 10 раз в каждую сторону\n\n"
    "3. *Вращение бёдрами* (как обруч)\n"
    "   👉 По 10 раз в каждую сторону\n\n"
    "4. *Наклоны в стороны* с поднятой рукой\n"
    "   👉 По 10 раз на каждую сторону\n\n"
    "5. *Приседания без нагрузки* — медленно\n"
    "   👉 15 раз, колени над носками\n\n"
    "6. *Махи руками* скрест перед грудью\n"
    "   👉 20 раз — разогревает плечи\n\n"
    "7. *Лёгкие прыжки* на месте — 30 сек\n\n"
    "✅ Тело готово! Начинай тренировку."
)

COOLDOWN = (
    "🧘 *ЗАМИНКА ПОСЛЕ ТРЕНИРОВКИ (7-10 мин)*\n\n"
    "Держи каждую позицию *30-45 сек:*\n\n"
    "1. *Растяжка квадрицепса* стоя\n"
    "   👉 Подтяни пятку к ягодице — 30 сек каждая нога\n\n"
    "2. *Наклон к ногам* сидя\n"
    "   👉 Ноги прямые, тянись к носкам — расслабляет поясницу\n\n"
    "3. *Растяжка грудных* у стены\n"
    "   👉 Рука на стене 90°, разворачивай корпус — 30 сек каждая\n\n"
    "4. *Поза кошки/коровы* на четвереньках\n"
    "   👉 По 10 раз медленно — снимает напряжение со спины\n\n"
    "5. *Поза ребёнка* (Child pose)\n"
    "   👉 Сядь на пятки, руки вперёд — 45 сек\n\n"
    "6. *Растяжка плечевого пояса*\n"
    "   👉 Рука поперёк груди — 30 сек каждая\n\n"
    "7. *Скручивание позвоночника* лёжа\n"
    "   👉 Колено к груди, опускай в сторону — 30 сек каждую\n\n"
    "💧 Выпей воды. Мышцы скажут спасибо!"
)

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
    "ДА": ("🏠 Домашняя силовая А — Грудь, Трицепс, Кор",
           "1. *Отжимания широким хватом* — 4×15\n"
           "   👉 Руки чуть шире плеч, локти в стороны, грудь касается пола\n\n"
           "2. *Отжимания узким хватом (трицепс)* — 3×12\n"
           "   👉 Руки под плечами, локти вдоль тела, не расставлять в стороны\n\n"
           "3. *Отжимания с ногами на диване* — 3×10\n"
           "   👉 Ноги на диване/стуле, тело под углом 30°, усиленная нагрузка на верх груди\n\n"
           "4. *Планка на предплечьях* — 3×60 сек\n"
           "   👉 Предплечья на полу, тело прямое, не поднимать таз, смотреть в пол\n\n"
           "5. *Скручивания на пресс* — 4×20\n"
           "   👉 Лёжа на спине, руки за голову, подними лопатки от пола — НЕ весь корпус\n\n"
           "6. *Подъём ног лёжа* — 3×15\n"
           "   👉 Лёжа, руки под ягодицами, поднимай прямые ноги до 90° и медленно опускай\n\n"
           "⏱️ Отдых 60 сек. Всего ~35 мин. ~180-220 ккал"),
    "ДБ": ("🏠 Домашняя силовая Б — Ноги, Ягодицы, Спина",
           "1. *Приседания* — 4×20\n"
           "   👉 Ноги на ширине плеч, носки чуть в стороны, колени НЕ заваливать внутрь, спина прямая\n\n"
           "2. *Выпады поочерёдно* — 3×12 на каждую ногу\n"
           "   👉 Шаг вперёд, заднее колено почти касается пола, корпус вертикально\n\n"
           "3. *Ягодичный мост* — 4×20\n"
           "   👉 Лёжа, ноги согнуты, поднимай таз — сжимай ягодицы в верхней точке, держи 1 сек\n\n"
           "4. *Супермен* — 3×15\n"
           "   👉 Лёжа на животе, одновременно поднимай руки и ноги, держи 2 сек — укрепляет поясницу\n\n"
           "5. *Боковые выпады* — 3×12 на каждую сторону\n"
           "   👉 Шаг в сторону, сгибай рабочую ногу, другая прямая — хорошо для внутренней поверхности бедра\n\n"
           "6. *Стульчик у стены* — 3×45 сек\n"
           "   👉 Спина к стене, бёдра параллельно полу — статическая нагрузка на квадрицепс\n\n"
           "⏱️ Отдых 60 сек. Всего ~40 мин. ~200-250 ккал"),
    "ДВ": ("🏠 Домашняя силовая В — Всё тело + Кардио",
           "1. *Берпи* — 3×10\n"
           "   👉 Из стойки — упор лёжа — отжимание (по желанию) — прыжок вверх со взмахом рук\n"
           "   💡 Если тяжело — убери прыжок, просто встань\n\n"
           "2. *Приседания с прыжком* — 3×15\n"
           "   👉 Присядь до параллели, резко выпрыгни вверх, мягко приземлись на носки\n\n"
           "3. *Отжимания* — 3×12\n"
           "   👉 Держи корпус прямым, не провисай в пояснице\n\n"
           "4. *Альпинист* — 3×20 (на каждую ногу)\n"
           "   👉 Планка на прямых руках, поочерёдно подтягивай колени к груди — быстро\n\n"
           "5. *Джампинг джек* — 3×30 сек\n"
           "   👉 Прыжки с разведением рук и ног в стороны одновременно\n\n"
           "6. *Планка + боковая планка* — 2×45 сек каждая\n"
           "   👉 Сначала основная, потом переворот на бок — держи бёдра не опуская\n\n"
           "⏱️ Отдых 45 сек. Всего ~30 мин. ~280-350 ккал"),
    "ДК": ("🏠 Домашнее кардио",
           "Выбери любые 3-4 блока по 10 мин:\n\n"
           "🚶 *Ходьба с высоким подъёмом колен* — 10 мин\n"
           "   👉 На месте, колени поднимай выше пояса, руки работают как при беге\n\n"
           "🪢 *Прыжки (скакалка или без)* — 10 мин\n"
           "   👉 Без скакалки — просто прыгай на месте на носках, руки имитируют вращение\n\n"
           "💃 *Танцы под музыку* — 15 мин\n"
           "   👉 Просто двигайся в удовольствие — это реальное кардио ~150 ккал/30 мин\n\n"
           "🔄 *Джампинг джек* — 10 мин (3×30 сек с отдыхом 30 сек)\n\n"
           "🪜 *Ходьба по лестнице* (если есть) — 10 мин\n"
           "   👉 Нормальный темп, держись за перила если нужно\n\n"
           "⏱️ Итого ~40-45 мин. ~200-300 ккал."),
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
    """
    Возвращает расписание тренировок.
    Если включены домашние тренировки — в дни отдыха от зала подставляем домашние.
    """
    mode      = auto_select_workout(profile)
    gd        = min(gym_days, 5)
    home_mode = int((profile or {}).get("home_workouts") or 0)

    if mode == "кардио_акцент":
        s = {1:{2:"К"},2:{1:"К",4:"К"},3:{1:"К",3:"К",5:"А"},
             4:{0:"К",2:"К",4:"К",5:"А"},5:{0:"К",1:"К",2:"А",3:"К",4:"К"}}
    else:
        s = {1:{2:"А"},2:{1:"К",3:"А"},3:{0:"А",2:"К",4:"Б"},
             4:{0:"А",1:"К",3:"Б",4:"К"},5:{0:"А",1:"К",2:"Б",3:"К",4:"В"}}

    # Режим «только домашние» (home_workouts == 2) — зал не нужен вообще
    if home_mode == 2:
        home_only_rotation = ["ДА","ДБ","ДК","ДВ","ДА","ДК","ДБ"]
        schedule = {}
        for day in range(7):
            schedule[day] = home_only_rotation[day % len(home_only_rotation)]
        return schedule

    schedule = dict(s.get(gd, s.get(3, {})))

    # Если домашние тренировки включены (home_workouts == 1) — добавляем в дни отдыха
    if home_mode == 1:
        home_rotation = ["ДА","ДБ","ДВ","ДК"]
        home_idx = 0
        for day in range(7):
            if day not in schedule:
                if home_idx % 2 == 0:
                    schedule[day] = home_rotation[(home_idx // 2) % len(home_rotation)]
                home_idx += 1
    return schedule

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

def filter_banned_exercises(exercises_text, profile):
    """Убирает из текста тренировки строки с запрещёнными по здоровью упражнениями"""
    banned = get_banned_exercises(profile)
    if not banned:
        return exercises_text, False
    lines = exercises_text.split("\n")
    kept_lines = []
    removed = False
    for line in lines:
        if any(ex.lower() in line.lower() for ex in banned):
            removed = True
            continue
        kept_lines.append(line)
    return "\n".join(kept_lines), removed

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

    # Применяем фильтр по медицинским ограничениям
    exercises, removed = filter_banned_exercises(exercises, profile)
    health_workout_notes = get_health_workout_notes(profile)
    health_note_block = ""
    if removed or health_workout_notes:
        health_note_block = "\n\n⚠️ *Учтены твои ограничения по здоровью:*"
        if removed:
            health_note_block += "\n• Часть упражнений убрана из тренировки как небезопасная"
        for note in health_workout_notes:
            health_note_block += f"\n• {note}"

    tag  = "🔵" if adj_key == "К" else "🟢"
    orig = f" *(заменена с {wkey} из-за усталости)*" if adj_key != wkey else ""

    # Подсказка по последнему замеру InBody — если висцеральный жир высокий,
    # напоминаем что кардио снижает его быстрее силовых
    inbody_note = ""
    inbody_data = get_last_inbody_dict(uid)
    if inbody_data and inbody_data.get("visceral_fat") and inbody_data["visceral_fat"] > 10 and adj_key in ("А","Б","В","ДА","ДБ","ДВ"):
        inbody_note = (f"\n\n📋 *По данным InBody:* висцеральный жир *{inbody_data['visceral_fat']}* "
                       f"(выше нормы). Кардио снижает его быстрее силовых — не пропускай кардио-дни.")

    text = (f"{tag} *ТРЕНИРОВКА СЕГОДНЯ{orig}*\n*{name}*\n\n"
            f"{fnote}\n\n🏋️ *Упражнения:*\n{exercises}"
            f"{health_note_block}{inbody_note}\n\n"
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
    plan    = get_user_plan(uid, profile)
    cal     = plan["calories"]
    weights = get_weights(uid)
    analysis = analyze_progress(weights) if len(weights) >= 2 else None
    if analysis: cal += analysis["cal_change"]
    fatigue = int(profile.get("fatigue") or 0)
    fat_note = ""
    if fatigue >= 4: cal += 100; fat_note = "\n🔴 *+100 ккал на восстановление* (высокая усталость)"
    elif fatigue == 3: fat_note = "\n🟡 Умеренная усталость — не пропускай приёмы"
    p = get_portions(cal)
    status = ""
    if analysis and not for_tomorrow:
        icons = {"fast":"📈","good":"✅","slow":"📉","plateau":"🪨","gain":"🚨"}
        status = f"{icons.get(analysis['status'],'')} {analysis['advice']}\n\n"
    prefix = "📅 *РАЦИОН НА ЗАВТРА*\n" if for_tomorrow else ""

    # Определяем день недели — для "на завтра" берём следующий день
    weekday = now_samara().weekday()
    if for_tomorrow:
        weekday = (weekday + 1) % 7

    breakfast, breakfast_fast = get_day_meal(BREAKFAST_ROTATION, weekday)
    lunch, lunch_fast         = get_day_meal(LUNCH_ROTATION, weekday, breast=p['breast'], carb=p['carb'])
    snack, snack_fast         = get_day_meal(SNACK_ROTATION, weekday, snack=p['snack'])
    dinner, dinner_fast       = get_day_meal(DINNER_ROTATION, weekday, dinner=p['dinner'])

    # Применяем медицинские ограничения — заменяем опасные продукты
    breakfast, _ = apply_health_filter(profile, breakfast)
    breakfast_fast, _ = apply_health_filter(profile, breakfast_fast)
    lunch, _ = apply_health_filter(profile, lunch)
    lunch_fast, _ = apply_health_filter(profile, lunch_fast)
    snack, _ = apply_health_filter(profile, snack)
    snack_fast, _ = apply_health_filter(profile, snack_fast)
    dinner, _ = apply_health_filter(profile, dinner)
    dinner_fast, _ = apply_health_filter(profile, dinner_fast)

    health_notes = get_health_food_notes(profile)
    health_block = ("\n" + "\n".join(health_notes) + "\n") if health_notes else ""

    ration = (
        f"{prefix}{status}"
        f"🍳 *Завтрак:* {breakfast}\n"
        f"  💡 Быстро: {breakfast_fast}\n"
        f"🍗 *Обед:* {lunch}\n"
        f"  💡 Быстро: {lunch_fast}\n"
        f"🍎 *Полдник:* {snack}\n"
        f"  💡 Быстро: {snack_fast}\n"
        f"🌙 *Ужин:* {dinner}\n"
        f"  💡 Быстро: {dinner_fast}\n\n"
        f"🎯 *~{cal} ккал* | 💪 *~{plan['protein']}г белка*"
        f"{fat_note}\n"
        f"🚶 +1 500 шагов сверх нормы"
        f"{health_block}\n"
        f"📖 Рецепты блюд — кнопка *«🍝 Рецепты блюд»*"
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
    p = get_portions(cal)
    shopping = (
        f"\n\n🛒 *ЧТО НУЖНО ДЛЯ ЗАВТРАШНЕГО РАЦИОНА:*\n"
        f"• Белок (курица/индейка/говядина) — ~{p['breast']+p['snack']}г\n"
        f"• Яйца — 2-3 шт (если завтрак с яйцами)\n"
        f"• Гречка/рис/булгур/макароны — ~{p['carb']}г\n"
        f"• Свежие/замороженные овощи — 400г\n"
        f"• Фрукт — 1 шт\n"
        f"• Орехи — 20г\n\n"
        f"⏱️ *Совет:* посмотри рецепт завтрашнего блюда в *«🍝 Рецепты блюд»* "
        f"и приготовь белок заранее сегодня вечером — сэкономишь время утром."
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
    plan    = get_user_plan(uid, profile)
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
    plan     = get_user_plan(uid, profile)
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
#  РЕЦЕПТЫ НОВЫХ БЛЮД
# ─────────────────────────────────────────

# ─────────────────────────────────────────
#  УМНЫЙ ВЫБОР БЛЮДА ПО КАЛОРАЖУ
# ─────────────────────────────────────────

SMART_MENU_CATEGORIES = {
    "🍳 Завтраки": [
        "овсяная каша на воде","омлет (2 яйца)","протеиновые оладьи",
        "творожная запеканка","сырники из творога","яичница (2 яйца)",
        "протеиновый милкшейк ваниль","протеиновый милкшейк шоколад",
        "банановый милкшейк (без сахара)","ягодный смузи","зелёный смузи",
    ],
    "🍗 Обеды": [
        "куриная грудка отварная","куриное бедро запечённое",
        "говядина тушёная","индейка запечённая","тефтели куриные домашние",
        "плов с курицей","плов с говядиной","плов с бараниной",
        "куриный суп с овощами","борщ без картофеля","томатный суп",
        "гречневая каша","бурый рис отварной","картофельное пюре",
        "кускус","полба",
    ],
    "🥗 Ужины": [
        "куриная грудка отварная","говядина тушёная","индейка запечённая",
        "тунец консервированный","тилапия запечённая","лосось запечённый",
        "стручковая фасоль","брокколи отварная","цветная капуста",
        "овощи тушёные","греческий салат",
    ],
    "🍎 Перекусы": [
        "творог 5%","кефир 1%","натуральный йогурт без сахара","ряженка 2.5%",
        "яблоко","банан","апельсин","груша","черника","клубника",
        "миндаль","грецкие орехи","рисовые хлебцы","цельнозерновые хлебцы",
        "авокадо","хумус","протеиновый батончик",
    ],
    "🍝 Гарниры": [
        "гречневая каша","бурый рис отварной","макароны цельнозерновые",
        "картофельное пюре","запечённый картофель","кускус","полба",
        "овощи тушёные","брокколи отварная","стручковая фасоль",
    ],
    "🥤 Напитки и смузи": [
        "протеиновый милкшейк ваниль","протеиновый милкшейк шоколад",
        "протеиновый милкшейк клубника","банановый милкшейк (без сахара)",
        "ягодный смузи","зелёный смузи","кефир 1%","ряженка 2.5%",
        "натуральный йогурт без сахара",
    ],
}

def calc_smart_portion(food_name, target_kcal):
    """Считает порцию блюда под заданный калораж"""
    kcal_per_100 = KCAL_PER_100G.get(food_name)
    if not kcal_per_100 or kcal_per_100 == 0:
        return None, None
    grams = round((target_kcal / kcal_per_100) * 100)
    grams = max(50, min(grams, 600))  # Ограничение разумной порции
    actual_kcal = round(grams * kcal_per_100 / 100)
    return grams, actual_kcal

def build_smart_food_menu(category=None):
    """Строит меню выбора блюда"""
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if category is None:
        for cat in SMART_MENU_CATEGORIES:
            m.add(types.KeyboardButton(cat))
        m.add(types.KeyboardButton("❌ Отмена"))
    else:
        foods = SMART_MENU_CATEGORIES.get(category, [])
        for food in foods:
            m.add(types.KeyboardButton(f"🍴 {food}"))
        m.add(types.KeyboardButton("◀️ Назад к категориям"))
        m.add(types.KeyboardButton("❌ Отмена"))
    return m


RECIPES = {
    "макароны с куриным фаршем": {
        "emoji": "🍝",
        "ingredients": "• 200г куриного фарша\n• 80г макарон (твёрдые сорта)\n• 1 луковица\n• 1 помидор или 1 ст.л. томатной пасты\n• Соль, перец, оливковое масло 1 ч.л.",
        "steps": "1. Отвари макароны до готовности.\n2. Обжарь лук на сухой сковороде 3 мин.\n3. Добавь фарш, разбей вилкой, жарь 7-10 мин.\n4. Добавь помидор/пасту, соль, перец.\n5. Смешай с макаронами.",
        "time": "20 мин",
        "kcal_portion": "~510 ккал (350г)",
        "tip": "💡 Без соусов! Томатная паста — только для вкуса, минимальное количество.",
    },
    "макароны с котлетой": {
        "emoji": "🍝",
        "ingredients": "• 1 котлета куриная запечённая (100г)\n• 80г макарон (твёрдые сорта)\n• Соль, зелень",
        "steps": "1. Отвари макароны.\n2. Подай рядом с запечённой котлетой.\n3. Можно добавить свежие овощи.",
        "time": "15 мин (+ время на котлету)",
        "kcal_portion": "~560 ккал (350г)",
        "tip": "💡 Котлета — только запечённая в духовке, без панировки и масла.",
    },
    "тефтели куриные домашние": {
        "emoji": "🍖",
        "ingredients": "• 500г куриного фарша\n• 1 яйцо\n• 1 луковица (тёртая)\n• Соль, перец, зелень",
        "steps": "1. Смешай фарш, яйцо, лук, специи.\n2. Слепи шарики ~40г.\n3. Выложи на противень с пергаментом.\n4. Запекай 25-30 мин при 190°C.\n5. Можно тушить в небольшом количестве воды 20 мин.",
        "time": "35 мин",
        "kcal_portion": "~260 ккал (200г = 5 тефтелей)",
        "tip": "💡 Делай сразу на 3-4 дня — хранить в холодильнике 3 дня. Удобно для рациона!",
    },
    "тефтели говяжьи домашние": {
        "emoji": "🍖",
        "ingredients": "• 500г говяжьего фарша (нежирный)\n• 1 яйцо\n• 1 луковица (тёртая)\n• Соль, перец",
        "steps": "1. Смешай фарш, яйцо, лук, специи.\n2. Слепи шарики ~40г.\n3. Запекай 30-35 мин при 190°C.\n4. Или тушить в воде 25 мин.",
        "time": "40 мин",
        "kcal_portion": "~350 ккал (200г = 5 тефтелей)",
        "tip": "💡 Говяжий фарш — нежирный (не более 15% жира). Смотри состав на упаковке.",
    },
    "омлет (2 яйца)": {
        "emoji": "🍳",
        "ingredients": "• 2 яйца\n• 30мл воды или миндального молока\n• Соль, зелень\n• Помидор, шпинат (по желанию)",
        "steps": "1. Взбей яйца с водой и солью.\n2. Вылей на разогретую сковороду (без масла или 0.5 ч.л.).\n3. Накрой крышкой, жарь 3-4 мин на среднем огне.\n4. Добавь овощи перед складыванием.",
        "time": "7 мин",
        "kcal_portion": "~195 ккал (130г)",
        "tip": "💡 Отличная замена яичнице — меньше холестерина. Добавляй шпинат — +железо и магний.",
    },
    "запечённая говядина": {
        "emoji": "🥩",
        "ingredients": "• 500г говядины (цельный кусок)\n• Соль, перец, чеснок, розмарин\n• 1 ч.л. оливкового масла",
        "steps": "1. Натри мясо специями и маслом.\n2. Дай постоять 30 мин.\n3. Запекай при 180°C: 500г — 40-45 мин.\n4. Дай отдохнуть 10 мин перед нарезкой.",
        "time": "55 мин",
        "kcal_portion": "~320 ккал (180г)",
        "tip": "💡 Готовь сразу 500-700г — хватит на 3-4 приёма. Нарезай порциями и храни в холодильнике.",
    },
    "запечённая куриная грудка": {
        "emoji": "🍗",
        "ingredients": "• 1-2 куриных грудки\n• Соль, перец, паприка, чеснок\n• 0.5 ч.л. оливкового масла",
        "steps": "1. Отбей грудку до одинаковой толщины.\n2. Натри специями.\n3. Запекай при 180°C 25-30 мин.\n4. Или в фольге — сочнее, 35 мин.",
        "time": "35 мин",
        "kcal_portion": "~253 ккал (220г)",
        "tip": "💡 В фольге с луком — намного сочнее! Запекай сразу 3-4 грудки на неделю.",
    },

    # ── Завтраки ──
    "яйца варёные": {
        "emoji": "🥚",
        "ingredients": "• 3 яйца\n• Вода, соль",
        "steps": "1. Залей яйца холодной водой.\n2. Доведи до кипения.\n3. Варка: всмятку — 4 мин, в мешочек — 6 мин, вкрутую — 9 мин.\n4. Переложи в холодную воду на 2 мин — легче чистить.",
        "time": "10 мин",
        "kcal_portion": "~234 ккал (186г = 3 яйца)",
        "tip": "💡 Вкрутую хранятся в холодильнике до 7 дней — удобно готовить на неделю.",
    },
    "омлет с овощами": {
        "emoji": "🍳",
        "ingredients": "• 3 яйца\n• 50мл воды\n• 1 помидор\n• Горсть шпината\n• Соль, перец, зелень",
        "steps": "1. Взбей яйца с водой, солью, перцем.\n2. Нарежь помидор, шпинат.\n3. Разогрей сковороду, влей яйца.\n4. Выложи овощи на половину омлета.\n5. Накрой крышкой, 3-4 мин на среднем огне.\n6. Сложи пополам.",
        "time": "8 мин",
        "kcal_portion": "~270 ккал (200г)",
        "tip": "💡 Шпинат + яйца = лучший утренний белок. Добавляй любые овощи из списка.",
    },
    "овсянка на воде": {
        "emoji": "🥣",
        "ingredients": "• 60г овсяных хлопьев (долгая варка)\n• 300мл воды\n• Щепотка соли\n• 1 ч.л. мёда или ягоды по желанию",
        "steps": "1. Вскипяти воду, добавь соль.\n2. Всыпь овсянку, помешивая вари 5-7 мин.\n3. Накрой крышкой, дай постоять 2 мин.\n4. Добавь мёд или ягоды по желанию.",
        "time": "10 мин",
        "kcal_portion": "~211 ккал (60г сухой)",
        "tip": "💡 Хлопья ДОЛГОЙ варки (не быстрые!) — ГИ намного ниже, дольше держат сытость.",
    },

    # ── Обеды ──
    "гречка с куриной грудкой": {
        "emoji": "🍗",
        "ingredients": "• 230г куриной грудки\n• 65г гречки\n• Соль, перец, паприка\n• Зелень, огурец",
        "steps": "1. Залей гречку 130мл воды, соль, доведи до кипения.\n2. Убавь огонь, вари 15 мин под крышкой.\n3. Грудку отбей, натри специями.\n4. Запекай 25 мин при 180°C или отвари.\n5. Нарежь, подай с гречкой и свежим огурцом.",
        "time": "30 мин",
        "kcal_portion": "~460 ккал",
        "tip": "💡 Готовь гречку и грудку сразу на 2-3 дня — основа быстрого рациона.",
    },
    "рис с куриным бедром": {
        "emoji": "🍚",
        "ingredients": "• 230г куриного бедра без кожи\n• 65г бурого риса\n• Чеснок, паприка, соль\n• Болгарский перец",
        "steps": "1. Бурый рис залей 150мл воды, вари 25-30 мин.\n2. Бедро натри чесноком и паприкой.\n3. Запекай в фольге 35 мин при 180°C.\n4. Перец нарежь, подай сырым или запечённым рядом.",
        "time": "40 мин",
        "kcal_portion": "~480 ккал",
        "tip": "💡 Бурый рис — обязательно, не белый. Намного медленнее усваивается — дольше сытость.",
    },
    "индейка с булгуром": {
        "emoji": "🦃",
        "ingredients": "• 230г филе индейки\n• 65г булгура\n• Соль, куркума, перец\n• Помидор, зелень",
        "steps": "1. Булгур залей 130мл кипятка, соль, накрой — 15 мин без огня.\n2. Индейку нарежь кубиками.\n3. Обжарь на сухой сковороде 8-10 мин до золотистого.\n4. Добавь специи в конце.\n5. Подай с булгуром и свежим помидором.",
        "time": "25 мин",
        "kcal_portion": "~430 ккал",
        "tip": "💡 Булгур не нужно варить — просто залить кипятком. Экономия времени!",
    },
    "говядина тушёная с овощами": {
        "emoji": "🥩",
        "ingredients": "• 200г говядины (нежирная)\n• 1 морковь\n• 1 болгарский перец\n• Соль, перец, лавровый лист\n• 100мл воды",
        "steps": "1. Нарежь говядину кубиками 3-4 см.\n2. Обжарь на сухой сковороде до корочки (3 мин).\n3. Добавь нарезанные овощи, воду, специи.\n4. Туши под крышкой на малом огне 40-50 мин.\n5. Подавай без гарнира или с гречкой.",
        "time": "55 мин",
        "kcal_portion": "~380 ккал (400г)",
        "tip": "💡 Говядина раскрывается при тушении — не торопись, чем дольше тем мягче.",
    },
    "консервированная курица с гречкой": {
        "emoji": "🥫",
        "ingredients": "• 185г консервированной курицы (в с/с)\n• 65г гречки в пакете\n• Огурец, зелень\n• Соль",
        "steps": "1. Брось пакет гречки в кипящую воду на 15 мин.\n2. Открой консерву, слей сок.\n3. Разогрей курицу на сковороде 2 мин.\n4. Подай с готовой гречкой и нарезанным огурцом.",
        "time": "17 мин",
        "kcal_portion": "~410 ккал",
        "tip": "💡 Самый быстрый обед в рационе — 17 минут от начала до тарелки.",
    },

    # ── Полдники ──
    "творог с ягодами": {
        "emoji": "🧀",
        "ingredients": "• 150г высокобелкового творога (0%)\n• 100г ягод (черника, клубника)\n• 1 ч.л. мёда",
        "steps": "1. Выложи творог в тарелку.\n2. Добавь ягоды сверху.\n3. Полей мёдом по желанию.",
        "time": "2 мин",
        "kcal_portion": "~185 ккал",
        "tip": "💡 Лучший полдник по скорости и нутриентам. Белок + антиоксиданты + нет лактозных проблем при 0% жирности.",
    },
    "протеиновый коктейль": {
        "emoji": "🥤",
        "ingredients": "• 30г сывороточного протеина\n• 250мл воды или миндального молока\n• Лёд по желанию",
        "steps": "1. Насыпь протеин в шейкер.\n2. Добавь воду или молоко.\n3. Взболтай 10-15 секунд.\n4. Выпей сразу после тренировки.",
        "time": "1 мин",
        "kcal_portion": "~115 ккал",
        "tip": "💡 Принимай в течение 30 мин после тренировки — белковое окно. На воде — меньше калорий, на миндальном молоке — вкуснее.",
    },

    # ── Ужины ──
    "куриная грудка с тушёными овощами": {
        "emoji": "🍗",
        "ingredients": "• 180г куриной грудки\n• 300г смеси овощей (перец, морковь, шпинат)\n• 1 ч.л. оливкового масла\n• Соль, перец, чеснок",
        "steps": "1. Грудку нарежь полосками.\n2. Обжарь на сухой сковороде 5-6 мин.\n3. Добавь нарезанные овощи, масло, специи.\n4. Туши под крышкой 7-8 мин.\n5. В конце добавь чеснок.",
        "time": "20 мин",
        "kcal_portion": "~290 ккал",
        "tip": "💡 Замороженные овощи работают так же хорошо — высыпай прямо из пакета.",
    },
    "куриные котлеты запечённые": {
        "emoji": "🍖",
        "ingredients": "• 500г куриного фарша\n• 1 яйцо\n• 1 луковица\n• Соль, перец, паприка\n• Зелень по желанию",
        "steps": "1. Смешай фарш, яйцо, тёртый лук, специи.\n2. Слепи котлеты — мокрыми руками, ~80г каждая.\n3. Выложи на противень с пергаментом.\n4. Запекай 30 мин при 180°C, перевернув раз.\n5. Готово когда сок прозрачный.",
        "time": "40 мин",
        "kcal_portion": "~340 ккал (2 котлеты)",
        "tip": "💡 Делай сразу 10-12 штук. 4 дня в холодильнике, 3 месяца в морозилке. Экономит время!",
    },
    "гречка с замороженными овощами": {
        "emoji": "🍲",
        "ingredients": "• 65г гречки в пакете\n• 250г замороженной овощной смеси\n• Соль, перец\n• 1 ч.л. оливкового масла",
        "steps": "1. Брось пакет гречки в кипящую воду на 15 мин.\n2. Овощную смесь высыпь на сковороду без масла.\n3. Туши под крышкой 7-10 мин, помешивая.\n4. Добавь масло, соль в конце.\n5. Подай с гречкой.",
        "time": "17 мин",
        "kcal_portion": "~280 ккал",
        "tip": "💡 Самый быстрый ужин. Замороженные овощи не хуже свежих — витамины сохраняются при заморозке.",
    },

    # ── Больничный рацион ──
    "куриный бульон": {
        "emoji": "🍵",
        "ingredients": "• 300г куриной грудки (или готовой курицы)\n• 1.5л воды\n• 1 морковь\n• Соль, лавровый лист, перец горошком\n• Зелень",
        "steps": "1. Залей курицу холодной водой, доведи до кипения.\n2. Слей первый бульон (убирает лишний жир).\n3. Залей снова 1.5л воды, добавь морковь и специи.\n4. Вари 30-40 мин на малом огне.\n5. Процеди, посоли, добавь зелень.",
        "time": "45 мин",
        "kcal_portion": "~80 ккал (400мл бульона)",
        "tip": "💡 При болезни — основа питания. Восполняет жидкость и электролиты. Курицу съешь отдельно.",
    },
    # ── Белковые блюда ──
    "куриная грудка отварная": {
        "emoji": "🍗",
        "ingredients": "• 230г куриной грудки\n• Вода, соль\n• Лавровый лист, перец горошком",
        "steps": "1. Залей грудку холодной водой, доведи до кипения.\n2. Сними пену, убавь огонь.\n3. Добавь соль, лавровый лист.\n4. Вари 25-30 мин на малом огне.\n5. Дай остыть в бульоне — будет сочнее.",
        "time": "35 мин",
        "kcal_portion": "~253 ккал (230г)",
        "tip": "💡 Вари сразу 4-5 грудок. Храни в бульоне — не пересыхает 4 дня в холодильнике.",
    },
    "куриное бедро запечённое": {
        "emoji": "🍗",
        "ingredients": "• 230г куриного бедра без кожи\n• Чеснок 2 зубчика\n• Паприка, соль, перец\n• 0.5 ч.л. оливкового масла",
        "steps": "1. Сними кожу с бедра, сделай надрезы.\n2. Натри чесноком, паприкой, солью, маслом.\n3. Маринуй 15 мин.\n4. Запекай при 200°C 35-40 мин.\n5. Готово когда сок при проколе прозрачный.",
        "time": "50 мин",
        "kcal_portion": "~426 ккал (230г)",
        "tip": "💡 Бедро сочнее грудки и не пересыхает при запекании. Без кожи — жирность близка к грудке.",
    },
    "индейка отварная": {
        "emoji": "🦃",
        "ingredients": "• 230г филе индейки\n• Вода, соль\n• Перец горошком, лавровый лист",
        "steps": "1. Нарежь филе кусками по 100г.\n2. Залей холодной водой, доведи до кипения.\n3. Убавь огонь, вари 25 мин.\n4. Посоли за 5 мин до готовности.\n5. Дай остыть в бульоне.",
        "time": "30 мин",
        "kcal_portion": "~265 ккал (230г)",
        "tip": "💡 Индейка — самый нежирный белок. Отличная замена когда надоела курица.",
    },
    "говядина отварная": {
        "emoji": "🥩",
        "ingredients": "• 200г говядины (нежирный кусок)\n• Вода, соль\n• Лук, морковь, перец горошком\n• Лавровый лист",
        "steps": "1. Залей мясо холодной водой.\n2. Доведи до кипения, сними пену.\n3. Добавь лук, морковь, специи.\n4. Вари 60-80 мин на малом огне.\n5. Посоли за 10 мин до готовности.",
        "time": "80 мин",
        "kcal_portion": "~374 ккал (200г)",
        "tip": "💡 Готовь 400-500г сразу. Хранится в бульоне 4-5 дней — нарезай порционно.",
    },
    "яичница": {
        "emoji": "🍳",
        "ingredients": "• 3 яйца\n• Соль, перец\n• Помидор, зелень по желанию",
        "steps": "1. Разогрей сухую антипригарную сковороду.\n2. Разбей яйца аккуратно, не ломая желток.\n3. Посоли, накрой крышкой.\n4. Жарь 3-4 мин до желаемой степени.\n5. Подавай с нарезанным помидором.",
        "time": "5 мин",
        "kcal_portion": "~234 ккал (3 яйца)",
        "tip": "💡 На антипригарной сковороде масло не нужно. Самый быстрый завтрак — 5 минут.",
    },
    # ── Гарниры ──
    "гречка варёная": {
        "emoji": "🍚",
        "ingredients": "• 65г гречки\n• 130мл воды\n• Щепотка соли",
        "steps": "1. Промой гречку под холодной водой.\n2. Залей водой 1:2, посоли.\n3. Доведи до кипения, убавь до минимума.\n4. Вари под крышкой 15 мин — не открывай.\n5. Дай постоять 5 мин.",
        "time": "20 мин",
        "kcal_portion": "~203 ккал (65г сухой)",
        "tip": "💡 Заливай кипятком вечером в термосе — утром готова! Или вари сразу 200г на 3 дня.",
    },
    "бурый рис варёный": {
        "emoji": "🍚",
        "ingredients": "• 65г бурого риса\n• 150мл воды\n• Щепотка соли",
        "steps": "1. Промой рис до прозрачной воды.\n2. Замочи на 30 мин — ускоряет варку.\n3. Залей свежей водой 1:2.5, посоли.\n4. Вари под крышкой 25-30 мин.\n5. Дай постоять 10 мин.",
        "time": "40 мин",
        "kcal_portion": "~219 ккал (65г сухого)",
        "tip": "💡 Замачивание обязательно! Готовь сразу 200г на 3-4 дня.",
    },
    "булгур": {
        "emoji": "🌾",
        "ingredients": "• 65г булгура\n• 130мл кипятка\n• Щепотка соли",
        "steps": "1. Насыпь булгур в миску, посоли.\n2. Залей кипятком.\n3. Накрой крышкой или тарелкой.\n4. Оставь на 15-20 мин — варить не нужно!\n5. Разрыхли вилкой перед подачей.",
        "time": "20 мин (без плиты!)",
        "kcal_portion": "~222 ккал (65г сухого)",
        "tip": "💡 Самый быстрый гарнир — просто залей кипятком. Ни плита, ни кастрюля не нужны.",
    },
    "макароны": {
        "emoji": "🍝",
        "ingredients": "• 85г макарон твёрдых сортов\n• 1л воды\n• 1 ч.л. соли",
        "steps": "1. Вскипяти воду, посоли.\n2. Брось макароны, помешай.\n3. Вари по времени на упаковке минус 1 мин.\n4. Слей через дуршлаг — не промывай!\n5. Сразу смешай с белком или овощами.",
        "time": "12 мин",
        "kcal_portion": "~298 ккал (85г сухих)",
        "tip": "💡 Только твёрдые сорта (durum) — написано на упаковке. Не промывай — смоешь крахмал.",
    },
    # ── Овощные блюда ──
    "тушёные овощи": {
        "emoji": "🥦",
        "ingredients": "• 300г любых овощей (перец, морковь, брокколи, шпинат)\n• 1 ч.л. оливкового масла\n• Соль, перец, чеснок\n• 50мл воды",
        "steps": "1. Нарежь твёрдые овощи кубиками.\n2. Разогрей сковороду с маслом.\n3. Сначала твёрдые — 3-4 мин.\n4. Добавь мягкие (шпинат, брокколи).\n5. Влей воду, туши под крышкой 5-7 мин.\n6. Соль, чеснок — в конце.",
        "time": "15 мин",
        "kcal_portion": "~75 ккал (300г)",
        "tip": "💡 Замороженные овощи — высыпай прямо из пакета без разморозки. Работает так же.",
    },
    "свежий салат": {
        "emoji": "🥗",
        "ingredients": "• 1 огурец\n• 2 помидора\n• 1 болгарский перец\n• Зелень (петрушка, укроп)\n• Соль, 1 ч.л. оливкового масла",
        "steps": "1. Нарежь все овощи.\n2. Посоли, дай постоять 2 мин.\n3. Заправь маслом.\n4. Зелень добавь перед подачей.",
        "time": "5 мин",
        "kcal_portion": "~80 ккал (300г)",
        "tip": "💡 Готовь прямо перед едой — нарезанные овощи теряют витамины за 30 мин.",
    },
    "брокколи на пару": {
        "emoji": "🥦",
        "ingredients": "• 200г брокколи (свежей или замороженной)\n• Соль, лимонный сок по желанию",
        "steps": "1. Раздели на соцветия.\n2. В кастрюлю — 2-3 см воды, доведи до кипения.\n3. Положи брокколи в дуршлаг над паром.\n4. Накрой крышкой, готовь 5-7 мин.\n5. Ярко-зелёная с хрустом = готова.",
        "time": "10 мин",
        "kcal_portion": "~68 ккал (200г)",
        "tip": "💡 Не переваривай! Серо-зелёная = все витамины разрушены. Ярко-зелёная с хрустом = идеал.",
    },
    "шпинат тушёный": {
        "emoji": "🥬",
        "ingredients": "• 200г шпината (свежего или замороженного)\n• 1 зубчик чеснока\n• Соль, щепотка мускатного ореха\n• 0.5 ч.л. оливкового масла",
        "steps": "1. Разогрей сковороду с маслом.\n2. Обжарь чеснок 30 сек.\n3. Добавь шпинат (замороженный — сразу из пакета).\n4. Туши помешивая 3-5 мин.\n5. Посоли, добавь мускатный орех.",
        "time": "7 мин",
        "kcal_portion": "~55 ккал (200г)",
        "tip": "💡 Свежий шпинат уменьшается в 5-6 раз — бери с запасом. Замороженный удобнее.",
    },
    "стручковая фасоль": {
        "emoji": "🫛",
        "ingredients": "• 200г стручковой фасоли\n• Чеснок 1 зубчик\n• Соль, перец\n• 0.5 ч.л. оливкового масла\n• 50мл воды",
        "steps": "1. Разогрей сковороду с маслом.\n2. Добавь фасоль (замороженную без разморозки).\n3. Обжаривай 3-4 мин.\n4. Влей воду, туши под крышкой 5-7 мин.\n5. Чеснок, соль, перец — в конце.",
        "time": "12 мин",
        "kcal_portion": "~65 ккал (200г)",
        "tip": "💡 Не переваривай — должна хрустеть. Отличный гарнир к любому мясу.",
    },
    # ── Полдники ──
    "орехи с фруктом": {
        "emoji": "🍎",
        "ingredients": "• 20г орехов (миндаль/грецкий/кешью)\n• 1 фрукт (яблоко, груша и т.д.)\n• Вода 300мл",
        "steps": "Ничего готовить не нужно!\n1. Отмерь 20г орехов.\n2. Возьми фрукт.\n3. Ешь орехи ПЕРЕД фруктом.\n4. Запей водой.",
        "time": "0 мин",
        "kcal_portion": "~230 ккал",
        "tip": "💡 Ешь орехи ДО фрукта — жиры замедляют усвоение сахара, снижается инсулиновый скачок.",
    },
    "консервированная курица с овощами": {
        "emoji": "🥫",
        "ingredients": "• 185г консервированной курицы\n• 1 огурец\n• 1 помидор\n• Зелень, соль",
        "steps": "1. Открой консерву, слей лишний сок.\n2. Выложи курицу в тарелку.\n3. Нарежь огурец и помидор.\n4. Посоли, добавь зелень.",
        "time": "3 мин",
        "kcal_portion": "~330 ккал",
        "tip": "💡 Идеальный полдник в дороге для водителя — открыл банку, нарезал, съел.",
    },
    # ── Для водителя ──
    "обед в контейнере": {
        "emoji": "🚗",
        "ingredients": "• 150г куриной грудки отварной\n• 65г гречки\n• 1 огурец + 1 помидор\n• 20г орехов\n• 1 яблоко",
        "steps": "Готовится вечером!\n1. Отвари грудку и гречку.\n2. Нарежь грудку порционно.\n3. Контейнер 1: мясо + гречка.\n4. Контейнер 2: нарезанные овощи.\n5. Пакет: орехи + фрукт.\n6. Утром забрал — в обед поел.",
        "time": "30 мин (вечером)",
        "kcal_portion": "~550 ккал (полный обед)",
        "tip": "💡 Для водителя — обязательно! Холодная грудка с гречкой вкусная и без разогрева. Готовь 2-3 контейнера на неделю.",
    },

    # ══════════════════════════════════════════
    #  ПЛОВ
    # ══════════════════════════════════════════
    "плов с курицей": {
        "emoji": "🍚", "time": "50 мин",
        "kcal_portion": "~540 ккал (300г)",
        "ingredients": "• 200г куриное бедро без кости\n• 100г рис длиннозерный\n• 1 морковь\n• 1 луковица\n• 2 зубчика чеснока\n• 1 ст.л. растительного масла\n• Зира, куркума, соль, перец",
        "steps": "1. Нарезать курицу кусочками, обжарить 5 мин.\n2. Добавить лук и морковь, жарить ещё 5 мин.\n3. Всыпать рис, специи, залить водой (2:1).\n4. Тушить под крышкой 25–30 мин на слабом огне.\n5. Добавить чеснок целыми зубчиками, укутать на 10 мин.",
        "tip": "💡 Используй пропаренный рис — он не разварится. Зира обязательна для аутентичного вкуса.",
    },
    "плов с говядиной": {
        "emoji": "🍚", "time": "70 мин",
        "kcal_portion": "~600 ккал (300г)",
        "ingredients": "• 200г говядина (лопатка)\n• 100г рис длиннозерный\n• 1 морковь\n• 1 луковица\n• 3 зубчика чеснока\n• 1 ст.л. растительного масла\n• Зира, барбарис, соль",
        "steps": "1. Нарезать говядину кубиками 3×3 см.\n2. Обжарить на сильном огне до корочки.\n3. Добавить лук и морковь (соломкой), жарить 7 мин.\n4. Всыпать рис, специи, залить горячей водой.\n5. Варить под крышкой 35–40 мин.",
        "tip": "💡 Говядину можно заменить телятиной — быстрее готовится и нежнее.",
    },
    "плов с бараниной": {
        "emoji": "🍚", "time": "80 мин",
        "kcal_portion": "~630 ккал (300г)",
        "ingredients": "• 200г баранина (шея/лопатка)\n• 100г рис девзира или длиннозерный\n• 1 крупная морковь\n• 1 луковица\n• Целая головка чеснока\n• Зира, куркума, острый перец",
        "steps": "1. Вытопить жир из баранины, добавить масло.\n2. Обжарить лук до золотого, добавить баранину.\n3. Добавить морковь соломкой, жарить 10 мин.\n4. Всыпать промытый рис, специи, воду (покрыть на 2 см).\n5. Варить 40 мин, в конце воткнуть головку чеснока.",
        "tip": "💡 Классический узбекский плов. Головка чеснока целиком — главный секрет аромата.",
    },

    # ══════════════════════════════════════════
    #  МИЛКШЕЙКИ И СМУЗИ
    # ══════════════════════════════════════════
    "протеиновый милкшейк ваниль": {
        "emoji": "🥤", "time": "3 мин",
        "kcal_portion": "~285 ккал (300мл)",
        "ingredients": "• 300 мл молока 1.5%\n• 30г ванильного протеина\n• 1 ч.л. мёда (по желанию)\n• Щепотка корицы\n• 3–4 кубика льда",
        "steps": "1. Влить молоко в блендер.\n2. Добавить протеин и мёд.\n3. Добавить лёд.\n4. Взбить 30–60 секунд до однородности.\n5. Перелить в стакан и сразу пить.",
        "tip": "💡 Лучшее время — после тренировки (в течение 30 мин). Белок: ~32г.",
    },
    "протеиновый милкшейк шоколад": {
        "emoji": "🍫", "time": "3 мин",
        "kcal_portion": "~300 ккал (300мл)",
        "ingredients": "• 300 мл молока 1.5%\n• 30г шоколадного протеина\n• 1 ч.л. какао-порошка\n• 1 банан (по желанию, +89 ккал)\n• 3–4 кубика льда",
        "steps": "1. Смешать молоко, протеин и какао в блендере.\n2. Добавить банан если хочешь углеводы (после тренировки).\n3. Добавить лёд, взбить 45 секунд.",
        "tip": "💡 Без банана — чисто протеиновый коктейль. С бананом — восстановительный после тренировки.",
    },
    "протеиновый милкшейк клубника": {
        "emoji": "🍓", "time": "3 мин",
        "kcal_portion": "~270 ккал (300мл)",
        "ingredients": "• 250 мл молока 1.5%\n• 30г клубничного протеина\n• 100г клубники (свежей или замороженной)\n• 3 кубика льда",
        "steps": "1. Все ингредиенты в блендер.\n2. Взбить до однородности 45–60 сек.\n3. Пить сразу — клубника быстро окисляется.",
        "tip": "💡 Замороженная клубника даёт более густую текстуру — как мягкое мороженое.",
    },
    "банановый милкшейк (без сахара)": {
        "emoji": "🍌", "time": "5 мин",
        "kcal_portion": "~255 ккал (300мл)",
        "ingredients": "• 250 мл молока 1.5%\n• 1 спелый банан (~100г)\n• 20г ванильного протеина\n• Щепотка корицы\n• 2 кубика льда",
        "steps": "1. Банан нарезать кусочками (можно заморозить заранее).\n2. Все ингредиенты в блендер.\n3. Взбить до однородности.\n4. Сразу пить — банан темнеет.",
        "tip": "💡 Замороженный банан = кремовая текстура без мороженого. Отличный вариант перед тренировкой.",
    },
    "ягодный смузи": {
        "emoji": "🫐", "time": "5 мин",
        "kcal_portion": "~195 ккал (350мл)",
        "ingredients": "• 150г замороженных ягод (черника, малина, клубника)\n• 200 мл кефира 1%\n• 1 ч.л. мёда\n• 20г протеина (по желанию)\n• Горсть шпината (по желанию, вкус не чувствуется)",
        "steps": "1. Ягоды достать из морозилки на 5 мин.\n2. Все ингредиенты в блендер.\n3. Взбить 60 секунд.\n4. Пить сразу — смузи расслоится через 10 мин.",
        "tip": "💡 Шпинат не чувствуется, но добавляет железо и клетчатку. Отличный завтрак.",
    },
    "зелёный смузи": {
        "emoji": "🥬", "time": "5 мин",
        "kcal_portion": "~165 ккал (350мл)",
        "ingredients": "• 2 горсти шпината (~60г)\n• 1 яблоко (~150г)\n• ½ банана\n• 200 мл воды или миндального молока\n• Сок ½ лимона\n• Кусочек имбиря (по желанию)",
        "steps": "1. Шпинат и жидкость сначала в блендер — взбить до однородности.\n2. Добавить фрукты, взбить ещё 30 сек.\n3. Добавить лимонный сок.\n4. Пить охлаждённым.",
        "tip": "💡 Лимон нейтрализует вкус шпината. Начни с малого количества и постепенно увеличивай.",
    },

    # ══════════════════════════════════════════
    #  СУПЫ
    # ══════════════════════════════════════════
    "куриный суп с овощами": {
        "emoji": "🍲", "time": "40 мин",
        "kcal_portion": "~180 ккал (400мл)",
        "ingredients": "• 200г куриная грудка\n• 1 морковь\n• 1 луковица\n• 2 стебля сельдерея\n• 1 картофелина (по желанию, +83 ккал)\n• Зелень, соль, лавровый лист",
        "steps": "1. Залить курицу холодной водой (1.5л), довести до кипения.\n2. Снять пену, добавить лук и морковь целиком.\n3. Варить 20 мин, вынуть курицу, нарвать на куски.\n4. Добавить нарезанные овощи, варить ещё 10 мин.\n5. Вернуть курицу, добавить зелень.",
        "tip": "💡 Без картофеля — диетический суп всего 45 ккал/100мл. Идеально в период сушки.",
    },
    "борщ без картофеля": {
        "emoji": "🥣", "time": "60 мин",
        "kcal_portion": "~160 ккал (400мл)",
        "ingredients": "• 300г говядина или курица\n• 1 свёкла (~200г)\n• ½ кочана капусты\n• 1 морковь\n• 1 луковица\n• 2 ст.л. томатной пасты\n• Чеснок, соль, перец",
        "steps": "1. Сварить бульон из мяса (30 мин).\n2. Свёклу натереть, обжарить с томатной пастой 5 мин.\n3. Добавить лук и морковь, жарить 5 мин.\n4. Нашинковать капусту, добавить в бульон.\n5. Через 10 мин добавить зажарку со свёклой.\n6. Варить ещё 10 мин, добавить чеснок.",
        "tip": "💡 Без картофеля снижаем ГИ. Добавь ложку сметаны 10% — +30 ккал и гораздо вкуснее.",
    },
    "томатный суп": {
        "emoji": "🍅", "time": "25 мин",
        "kcal_portion": "~140 ккал (400мл)",
        "ingredients": "• 500г помидоры (или 400мл консервированных)\n• 1 луковица\n• 3 зубчика чеснока\n• 500мл куриного бульона\n• 1 ч.л. оливкового масла\n• Базилик, орегано, соль",
        "steps": "1. Лук и чеснок обжарить на масле 3 мин.\n2. Добавить помидоры, тушить 5 мин.\n3. Добавить бульон, специи. Варить 15 мин.\n4. Взбить погружным блендером до однородности.\n5. Подавать с базиликом.",
        "tip": "💡 Можно добавить 50мл сливок 10% — суп станет кремовым (+50 ккал). Очень сытный при малой калорийности.",
    },
    "суп из чечевицы": {
        "emoji": "🫘", "time": "35 мин",
        "kcal_portion": "~380 ккал (400мл)",
        "ingredients": "• 150г красная чечевица\n• 1 луковица\n• 1 морковь\n• 3 зубчика чеснока\n• 1 ч.л. куркумы\n• 1 ч.л. зиры\n• Сок ½ лимона\n• 800мл воды",
        "steps": "1. Промыть чечевицу.\n2. Обжарить лук и морковь 5 мин, добавить специи.\n3. Добавить чечевицу, залить водой.\n4. Варить 20–25 мин до мягкости.\n5. Частично взбить блендером (можно оставить кусочки).\n6. Добавить лимонный сок.",
        "tip": "💡 Красная чечевица варится быстро и не требует замачивания. Высокий белок — 9г/100мл.",
    },

    # ══════════════════════════════════════════
    #  ЗАВТРАКИ
    # ══════════════════════════════════════════
    "творожная запеканка": {
        "emoji": "🧁", "time": "40 мин",
        "kcal_portion": "~420 ккал (300г)",
        "ingredients": "• 400г творог 5%\n• 2 яйца\n• 3 ст.л. манки или овсяной муки\n• 2 ст.л. сахара (или эритрита)\n• Ваниль\n• Щепотка соли\n• Ягоды для начинки (по желанию)",
        "steps": "1. Творог, яйца, манку, сахар, ваниль — смешать до однородности.\n2. Форму смазать, вылить тесто.\n3. Выпекать при 180°C 30–35 мин.\n4. Остудить 10 мин перед нарезкой.",
        "tip": "💡 Манку можно заменить протеином — получишь высокобелковую запеканку (белок +15г).",
    },
    "сырники из творога": {
        "emoji": "🥞", "time": "20 мин",
        "kcal_portion": "~370 ккал (150г, 3 шт)",
        "ingredients": "• 300г творог 5%\n• 1 яйцо\n• 3 ст.л. муки (+ для обвалки)\n• 1 ст.л. сахара\n• Ваниль, щепотка соли",
        "steps": "1. Смешать творог, яйцо, муку, сахар, ваниль.\n2. Руками формировать шарики, обвалять в муке.\n3. Придать форму лепёшек толщиной 1.5 см.\n4. Жарить на антипригарной сковороде без масла 3–4 мин с каждой стороны.\n5. Подавать с нежирной сметаной или ягодами.",
        "tip": "💡 Для низкокалорийных сырников — запечь в духовке при 200°C 15 мин вместо жарки.",
    },
    "протеиновые оладьи": {
        "emoji": "🥞", "time": "15 мин",
        "kcal_portion": "~310 ккал (150г, 4 шт)",
        "ingredients": "• 100г творог 0%\n• 2 яйца\n• 30г протеина ванильного\n• 50мл молока\n• ½ ч.л. разрыхлителя\n• Корица по вкусу",
        "steps": "1. Смешать все ингредиенты блендером до однородности.\n2. Разогреть антипригарную сковороду.\n3. Жарить без масла по 2 мин с каждой стороны.\n4. Подавать с ягодами или греческим йогуртом.",
        "tip": "💡 Белок: ~35г на порцию. Идеальный завтрак после утренней тренировки.",
    },
    "яичница (2 яйца)": {
        "emoji": "🍳", "time": "5 мин",
        "kcal_portion": "~180 ккал",
        "ingredients": "• 2 яйца С0\n• 1 ч.л. растительного масла\n• Соль, перец\n• Зелёный лук, помидор черри (по желанию)",
        "steps": "1. Разогреть сковороду на среднем огне.\n2. Добавить минимум масла.\n3. Разбить яйца, не перемешивать.\n4. Накрыть крышкой на 2 мин — белок схватится, желток останется жидким.\n5. Посолить только белок — соль на желтке даёт пятна.",
        "tip": "💡 Глазунья с жидким желтком усваивается лучше всего. Добавь помидор черри — минимум калорий, максимум вкуса.",
    },

    # ══════════════════════════════════════════
    #  РЫБА
    # ══════════════════════════════════════════
    "лосось запечённый": {
        "emoji": "🐟", "time": "20 мин",
        "kcal_portion": "~375 ккал (180г)",
        "ingredients": "• 180г филе лосося\n• 1 ч.л. оливкового масла\n• Сок ½ лимона\n• 2 зубчика чеснока\n• Розмарин, соль, перец",
        "steps": "1. Филе промыть, обсушить бумажным полотенцем.\n2. Смешать масло, лимон, чеснок, специи.\n3. Натереть рыбу маринадом.\n4. Запекать при 200°C 12–15 мин.\n5. Подавать со свежим лимоном и зеленью.",
        "tip": "💡 Лосось готов, когда легко расслаивается вилкой. Омега-3 — самый ценный жир для сжигания жира.",
    },
    "тунец консервированный": {
        "emoji": "🥫", "time": "5 мин",
        "kcal_portion": "~178 ккал (185г банка)",
        "ingredients": "• 1 банка тунца в собственном соку (185г)\n• 2 яйца варёных\n• 1 огурец\n• 1 помидор\n• 1 ч.л. оливкового масла\n• Лимон, соль",
        "steps": "1. Тунец слить, размять вилкой.\n2. Яйца и овощи нарезать кубиками.\n3. Смешать все ингредиенты.\n4. Заправить маслом и лимонным соком.\n5. Подавать сразу.",
        "tip": "💡 Готово за 5 минут. Белок: ~38г. Идеально в контейнер на работу.",
    },
    "тилапия запечённая": {
        "emoji": "🐠", "time": "20 мин",
        "kcal_portion": "~256 ккал (200г)",
        "ingredients": "• 200г филе тилапии\n• 1 ч.л. оливкового масла\n• Паприка, чесночный порошок\n• Сок лимона, соль\n• Веточки тимьяна",
        "steps": "1. Натереть рыбу специями и маслом.\n2. Выложить на фольгу.\n3. Запекать при 200°C 15–18 мин.\n4. Подавать с овощами на пару.",
        "tip": "💡 Тилапия — самая бюджетная нежирная рыба. Белок 26г/100г, жиры всего 3г.",
    },

    # ══════════════════════════════════════════
    #  ГАРНИРЫ И ОСНОВНЫЕ БЛЮДА
    # ══════════════════════════════════════════
    "картофельное пюре": {
        "emoji": "🥔", "time": "25 мин",
        "kcal_portion": "~165 ккал (200г)",
        "ingredients": "• 400г картофель\n• 100мл молока тёплого\n• 1 ч.л. сливочного масла\n• Соль",
        "steps": "1. Картофель очистить, нарезать, залить холодной водой.\n2. Варить 20 мин до мягкости.\n3. Слить воду, немного подсушить на огне 1 мин.\n4. Добавить тёплое молоко и масло, толочь до однородности.\n5. Посолить, взбить до воздушности.",
        "tip": "💡 Холодное молоко сделает пюре серым. Только тёплое! Картофель лучше есть в обед — высокий ГИ.",
    },
    "запечённый картофель": {
        "emoji": "🥔", "time": "45 мин",
        "kcal_portion": "~186 ккал (200г)",
        "ingredients": "• 2 картофелины (~200г)\n• 1 ч.л. оливкового масла\n• Паприка, розмарин, чесночный порошок\n• Соль",
        "steps": "1. Нарезать дольками или кубиками.\n2. Смешать с маслом и специями.\n3. Выложить на противень в один слой.\n4. Запекать при 220°C 35–40 мин, перевернуть на полпути.",
        "tip": "💡 Дольки = красивая корочка. Предварительно отварить 5 мин — и время в духовке сократится до 20 мин.",
    },
    "кускус": {
        "emoji": "🌾", "time": "10 мин",
        "kcal_portion": "~244 ккал (65г сухого)",
        "ingredients": "• 65г кускус\n• 130мл кипятка или бульона\n• 1 ч.л. оливкового масла\n• Соль, специи",
        "steps": "1. Кускус залить кипящим бульоном, добавить масло и соль.\n2. Накрыть крышкой на 5 мин.\n3. Разрыхлить вилкой.\n4. Подавать сразу.",
        "tip": "💡 Самый быстрый гарнир. Заваривается как чай. Хорошо сочетается с индейкой и овощами.",
    },
    "полба": {
        "emoji": "🌾", "time": "30 мин",
        "kcal_portion": "~220 ккал (65г сухого)",
        "ingredients": "• 65г полба\n• 200мл воды\n• Щепотка соли\n• 1 ч.л. оливкового масла",
        "steps": "1. Промыть полбу.\n2. Залить водой, довести до кипения.\n3. Убавить огонь, варить 25–30 мин.\n4. Добавить масло и соль.",
        "tip": "💡 Полба = прародитель пшеницы. Медленные углеводы с высоким белком (15г/100г). Отличная альтернатива рису.",
    },

    # ══════════════════════════════════════════
    #  ПЕРЕКУСЫ
    # ══════════════════════════════════════════
    "хумус": {
        "emoji": "🫘", "time": "10 мин (из банки) / 30 мин",
        "kcal_portion": "~142 ккал (80г)",
        "ingredients": "• 240г нут консервированный\n• 2 ст.л. тахини (кунжутная паста)\n• Сок 1 лимона\n• 2 зубчика чеснока\n• 2 ст.л. оливкового масла\n• Соль, паприка",
        "steps": "1. Нут слить, промыть, оставить немного жидкости.\n2. Все ингредиенты в блендер.\n3. Взбивать 2–3 мин, добавляя жидкость от нута для нужной консистенции.\n4. Подавать с паприкой и маслом сверху.",
        "tip": "💡 Хумус из банки — полноценный вариант. Ешь с морковными палочками или цельнозерновыми хлебцами.",
    },
    "рисовые хлебцы": {
        "emoji": "🍘", "time": "0 мин",
        "kcal_portion": "~125 ккал (40г, 4 шт)",
        "ingredients": "• 4 рисовых хлебца\n• 50г творог 5%\n• 1 ч.л. мёда или варенья без сахара\n• Черника или ягоды для украшения",
        "steps": "1. Намазать хлебцы творогом.\n2. Полить мёдом.\n3. Сверху положить ягоды.",
        "tip": "💡 Перекус за 1 минуту. Творог + хлебцы = белок + медленные углеводы. Идеально между приёмами.",
    },
    "авокадо": {
        "emoji": "🥑", "time": "3 мин",
        "kcal_portion": "~240 ккал (150г, ½ авокадо)",
        "ingredients": "• ½ авокадо (~150г)\n• Сок ½ лимона\n• Щепотка соли и перца\n• 1–2 яйца варёных (по желанию)",
        "steps": "1. Разрезать авокадо пополам, удалить косточку.\n2. Сбрызнуть лимоном — не потемнеет.\n3. Посолить, поперчить.\n4. Есть ложкой прямо из кожуры.",
        "tip": "💡 Авокадо = полезные жиры омега-9. Усиливает усвоение жирорастворимых витаминов из других продуктов.",
    },
    "греческий салат": {
        "emoji": "🥗", "time": "10 мин",
        "kcal_portion": "~220 ккал (250г)",
        "ingredients": "• 2 помидора\n• 1 огурец\n• ½ сладкого перца\n• 80г сыр фета\n• 8–10 оливок\n• 1 ст.л. оливкового масла\n• Орегано, соль",
        "steps": "1. Нарезать овощи крупными кусками.\n2. Добавить оливки и кубики феты.\n3. Полить маслом, посыпать орегано.\n4. Не перемешивать до подачи — овощи дадут сок.",
        "tip": "💡 Без заправки уксусом — только оливковое масло. Фета кладётся сверху целым куском, а не крошится.",
    },

    # ══════════════════════════════════════════
    #  НАПИТКИ
    # ══════════════════════════════════════════
    "кефир 1%": {
        "emoji": "🥛", "time": "0 мин",
        "kcal_portion": "~100 ккал (250мл)",
        "ingredients": "• 250мл кефир 1%\n• Корица (по желанию)\n• Щепотка имбиря (по желанию)",
        "steps": "1. Налить кефир в стакан.\n2. По желанию — добавить щепотку корицы.\n3. Выпить медленно.",
        "tip": "💡 Кефир перед сном снижает аппетит и поддерживает микробиом. Корица дополнительно снижает сахар крови.",
    },
    "натуральный йогурт без сахара": {
        "emoji": "🍶", "time": "0 мин",
        "kcal_portion": "~102 ккал (200г)",
        "ingredients": "• 200г греческий йогурт 0–2%\n• 1 ч.л. мёда\n• Горсть ягод или орехов",
        "steps": "1. Выложить йогурт в миску.\n2. Добавить мёд и топпинги.\n3. Есть сразу.",
        "tip": "💡 Греческий йогурт = обычный йогурт с отжатой сывороткой. Белка в 2 раза больше. Выбирай 2% жирности.",
    },

    # ══════════════════════════════════════════
    #  ПАСТА И ИТАЛЬЯНСКАЯ КУХНЯ
    # ══════════════════════════════════════════
    "паста болоньезе (лайт)": {
        "emoji": "🍝", "time": "35 мин",
        "kcal_portion": "~480 ккал (300г)",
        "ingredients": "• 100г макароны цельнозерновые\n• 150г говяжий фарш (5% жирности)\n• 200г томаты в собственном соку\n• 1 луковица\n• 2 зубчика чеснока\n• 1 ч.л. оливкового масла\n• Орегано, базилик, соль",
        "steps": "1. Лук и чеснок обжарить на масле 3 мин.\n2. Добавить фарш, жарить 7 мин помешивая.\n3. Добавить томаты и специи, тушить 15 мин.\n4. Отварить пасту аль денте.\n5. Смешать соус с пастой.",
        "tip": "💡 Цельнозерновые макароны = медленные углеводы. Белок фарша 5% жирности почти как у куриной грудки.",
    },
    "паста карбонара (лайт)": {
        "emoji": "🍝", "time": "20 мин",
        "kcal_portion": "~460 ккал (300г)",
        "ingredients": "• 100г спагетти цельнозерновые\n• 80г куриная грудка или индейка\n• 2 яйца\n• 30г пармезан тёртый\n• 1 зубчик чеснока\n• Чёрный перец, соль",
        "steps": "1. Отварить спагетти аль денте, сохранить стакан воды от варки.\n2. Грудку нарезать, обжарить с чесноком.\n3. Взбить яйца с сыром и перцем.\n4. Соединить горячую пасту с курицей.\n5. Снять с огня, добавить яично-сырную смесь, быстро перемешать — яйца не должны свернуться.",
        "tip": "💡 Главное — убрать с огня перед добавлением яиц. Вода от пасты регулирует густоту соуса.",
    },
    "паста примавера": {
        "emoji": "🍝", "time": "20 мин",
        "kcal_portion": "~380 ккал (300г)",
        "ingredients": "• 100г пенне цельнозерновые\n• 100г брокколи\n• 1 болгарский перец\n• 1 цукини\n• 100г черри-помидоры\n• 2 зубчика чеснока\n• 1 ст.л. оливкового масла\n• Базилик, пармезан",
        "steps": "1. Отварить пасту аль денте.\n2. Овощи нарезать, обжарить на масле с чесноком 5–7 мин.\n3. Добавить черри, прогреть 2 мин.\n4. Смешать с пастой, посыпать пармезаном и базиликом.",
        "tip": "💡 Овощная паста без мяса — отличный вариант в дни без тренировок. Максимум клетчатки.",
    },
    "шакшука": {
        "emoji": "🍳", "time": "20 мин",
        "kcal_portion": "~320 ккал (2 яйца + соус)",
        "ingredients": "• 3 яйца\n• 400г томаты консервированные\n• 1 болгарский перец\n• 1 луковица\n• 3 зубчика чеснока\n• 1 ч.л. паприки\n• Щепотка зиры и куркумы\n• 1 ч.л. оливкового масла\n• Зелень для подачи",
        "steps": "1. Лук и перец обжарить на масле 5 мин.\n2. Добавить чеснок и специи, жарить 1 мин.\n3. Влить томаты, тушить 10 мин до загустения.\n4. Сделать лунки ложкой, вбить яйца.\n5. Накрыть крышкой, готовить 5–7 мин до нужной готовности желтка.",
        "tip": "💡 Ближневосточный завтрак. Подавай прямо в сковороде с цельнозерновым хлебом.",
    },
    "лазанья куриная (лайт)": {
        "emoji": "🫕", "time": "60 мин",
        "kcal_portion": "~420 ккал (250г)",
        "ingredients": "• 6 листов лазаньи\n• 300г куриный фарш\n• 300г томатный соус\n• 200г творог 0% (вместо бешамель)\n• 50г моцарелла\n• Лук, чеснок, специи",
        "steps": "1. Фарш обжарить с луком и чесноком.\n2. Смешать с томатным соусом.\n3. Слоями: соус — листы — творог — снова соус.\n4. Сверху моцарелла.\n5. Запекать при 180°C 35–40 мин.",
        "tip": "💡 Творог вместо бешамеля экономит ~200 ккал и добавляет 20г белка на порцию.",
    },

    # ══════════════════════════════════════════
    #  АЗИАТСКАЯ КУХНЯ
    # ══════════════════════════════════════════
    "вок с курицей и овощами": {
        "emoji": "🥢", "time": "15 мин",
        "kcal_portion": "~350 ккал (300г)",
        "ingredients": "• 200г куриная грудка\n• 150г замороженная овощная смесь (брокколи, морковь, перец)\n• 2 зубчика чеснока\n• 1 ч.л. соевого соуса\n• 1 ч.л. кунжутного масла\n• Имбирь тёртый\n• 100г рис отварной",
        "steps": "1. Курицу нарезать полосками.\n2. Разогреть вок или глубокую сковороду до максимума.\n3. Обжарить курицу 3 мин на сильном огне.\n4. Добавить овощи, жарить 3 мин мешая.\n5. Добавить чеснок, имбирь, соевый соус.\n6. Подавать с рисом, сбрызнуть кунжутным маслом.",
        "tip": "💡 Сильный огонь — главный секрет вока. Всё готовится быстро и сохраняет текстуру.",
    },
    "рис с яйцом по-японски": {
        "emoji": "🍱", "time": "10 мин",
        "kcal_portion": "~380 ккал (300г)",
        "ingredients": "• 150г отварной рис\n• 2 яйца\n• 1 ч.л. соевого соуса\n• 1 ч.л. кунжутного масла\n• Зелёный лук\n• Кунжут",
        "steps": "1. Разогреть масло в сковороде.\n2. Добавить рис, жарить 2 мин помешивая.\n3. Сдвинуть рис, вбить яйца, быстро перемешать.\n4. Добавить соевый соус, хорошо перемешать.\n5. Посыпать луком и кунжутом.",
        "tip": "💡 Простейший быстрый обед. Вчерашний холодный рис жарится лучше — не слипается.",
    },
    "рамен домашний (лайт)": {
        "emoji": "🍜", "time": "25 мин",
        "kcal_portion": "~420 ккал (400мл + лапша)",
        "ingredients": "• 80г гречневая лапша (соба)\n• 150г куриная грудка\n• 1 яйцо варёное\n• 800мл куриный бульон\n• 2 ст.л. соевого соуса\n• 1 ч.л. мисо-пасты\n• Шпинат, зелёный лук\n• Кунжутное масло",
        "steps": "1. Отварить лапшу по инструкции.\n2. Куриный бульон довести до кипения.\n3. Добавить соевый соус и мисо, помешать.\n4. Разложить лапшу по мискам.\n5. Залить бульоном.\n6. Добавить тонко нарезанную грудку, половинку яйца, шпинат.",
        "tip": "💡 Мисо-паста содержит пробиотики — добавляй в конце чтобы не разрушить культуры.",
    },
    "курица терияки": {
        "emoji": "🍗", "time": "20 мин",
        "kcal_portion": "~340 ккал (200г курицы + соус)",
        "ingredients": "• 200г куриное бедро без кости\n• 2 ст.л. соевого соуса\n• 1 ст.л. мёда\n• 1 ч.л. рисового уксуса\n• 1 зубчик чеснока\n• Имбирь тёртый\n• Кунжут, зелёный лук",
        "steps": "1. Смешать соевый соус, мёд, уксус, чеснок, имбирь.\n2. Замариновать курицу 10 мин.\n3. Обжарить на сковороде по 4 мин с каждой стороны.\n4. Влить остаток маринада, карамелизировать 2 мин.\n5. Посыпать кунжутом и луком.",
        "tip": "💡 Подавай с рисом и кунжутом. Терияки — один из самых вкусных способов приготовить куриное бедро.",
    },

    # ══════════════════════════════════════════
    #  МЕКСИКАНСКАЯ КУХНЯ
    # ══════════════════════════════════════════
    "буррито с курицей": {
        "emoji": "🌯", "time": "20 мин",
        "kcal_portion": "~520 ккал (1 шт)",
        "ingredients": "• 1 цельнозерновой тортилья\n• 150г куриная грудка\n• 80г консервированная фасоль\n• 50г рис отварной\n• Авокадо ¼\n• 2 ст.л. греческий йогурт (вместо сметаны)\n• Латук, помидор\n• Лайм, кинза, специи",
        "steps": "1. Грудку обжарить с паприкой и куминым.\n2. На тортилью выложить рис и фасоль.\n3. Добавить курицу, авокадо, овощи.\n4. Йогурт вместо сметаны сверху.\n5. Завернуть конвертом, обжарить на сухой сковороде 1 мин с каждой стороны.",
        "tip": "💡 Греческий йогурт = сметана с в 3 раза меньше калорий. Вкус не отличишь.",
    },
    "тако с говядиной": {
        "emoji": "🌮", "time": "20 мин",
        "kcal_portion": "~480 ккал (2 шт)",
        "ingredients": "• 2 тортильи кукурузные\n• 150г говяжий фарш\n• 1 ч.л. паприки\n• ½ ч.л. куркумы, зиры\n• Помидор, латук, авокадо\n• Лайм, кинза",
        "steps": "1. Фарш обжарить со специями 7 мин.\n2. Тортильи прогреть на сухой сковороде 30 сек.\n3. На каждую тортилью — фарш, овощи, авокадо.\n4. Полить соком лайма.",
        "tip": "💡 Кукурузные тортильи = меньше глютена и калорий чем пшеничные. Ешь 2 шт — насыщает надолго.",
    },
    "гуакамоле": {
        "emoji": "🥑", "time": "10 мин",
        "kcal_portion": "~200 ккал (100г)",
        "ingredients": "• 2 спелых авокадо\n• 1 помидор\n• ¼ луковицы\n• Сок 1 лайма\n• Кинза\n• Соль, перец\n• Щепотка острого перца",
        "steps": "1. Авокадо размять вилкой (не блендером — нужна текстура).\n2. Добавить мелко нарезанный помидор без семян.\n3. Добавить лук, кинзу, лайм.\n4. Приправить, перемешать.\n5. Подавать сразу — темнеет.",
        "tip": "💡 Косточка авокадо в миске замедляет потемнение. Лайм обязателен — без него невкусно.",
    },

    # ══════════════════════════════════════════
    #  БЛИЖНЕВОСТОЧНАЯ И СРЕДИЗЕМНОМОРСКАЯ
    # ══════════════════════════════════════════
    "долма (голубцы в виноградных листьях)": {
        "emoji": "🫙", "time": "60 мин",
        "kcal_portion": "~360 ккал (6 шт)",
        "ingredients": "• 20–24 виноградных листа (маринованных)\n• 200г говяжий фарш\n• 80г рис\n• 1 луковица\n• Мята, петрушка\n• Сок 1 лимона\n• Соль, перец",
        "steps": "1. Фарш смешать с рисом, луком, зеленью, специями.\n2. На каждый лист положить 1 ч.л. начинки.\n3. Завернуть плотно.\n4. Уложить в кастрюлю, залить бульоном на 2 см.\n5. Варить 40 мин на слабом огне.",
        "tip": "💡 Виноградные листья — отличная замена капусте в голубцах. Меньше калорий, интересный вкус.",
    },
    "фалафель запечённый": {
        "emoji": "🧆", "time": "40 мин",
        "kcal_portion": "~280 ккал (6 шт)",
        "ingredients": "• 240г нут консервированный\n• ¼ луковицы\n• 2 зубчика чеснока\n• Кинза, петрушка\n• 1 ч.л. зиры\n• 1 ст.л. муки\n• Соль",
        "steps": "1. Нут слить, промыть, обсушить.\n2. Все ингредиенты пробить блендером — не до пюре, нужна текстура.\n3. Сформировать шарики размером с грецкий орех.\n4. Выложить на пергамент, смазать маслом.\n5. Запечь при 200°C 25 мин, перевернуть на полпути.",
        "tip": "💡 Запечённый фалафель = жареный на 40% меньше калорий. Подавай с хумусом и огурцом.",
    },
    "греческий йогурт с мёдом и орехами": {
        "emoji": "🍯", "time": "3 мин",
        "kcal_portion": "~290 ккал (200г + топпинги)",
        "ingredients": "• 200г греческий йогурт 2%\n• 1 ч.л. мёда\n• 20г грецких орехов\n• Горсть черники\n• Щепотка корицы",
        "steps": "1. Выложить йогурт в красивую тарелку.\n2. Полить мёдом.\n3. Посыпать орехами и черникой.\n4. Корица сверху.",
        "tip": "💡 Идеальный перекус или лёгкий завтрак. Белок 15г, полезные жиры, антиоксиданты.",
    },

    # ══════════════════════════════════════════
    #  ЗДОРОВЫЕ БУРГЕРЫ И СЭНДВИЧИ
    # ══════════════════════════════════════════
    "бургер куриный домашний": {
        "emoji": "🍔", "time": "25 мин",
        "kcal_portion": "~480 ккал (1 шт)",
        "ingredients": "• 150г куриный фарш\n• 1 цельнозерновая булочка\n• Латук, помидор, огурец\n• 1 ст.л. греческий йогурт (соус)\n• Дижонская горчица\n• Чесночный порошок, паприка, соль",
        "steps": "1. Фарш смешать со специями, сформировать котлету.\n2. Обжарить на антипригарной сковороде 4 мин с каждой стороны.\n3. Булочку слегка подсушить.\n4. Соус: йогурт + горчица + чеснок.\n5. Собрать: булочка — соус — латук — котлета — овощи.",
        "tip": "💡 Домашний бургер vs фастфуд: -300 ккал, +20г белка, без трансжиров.",
    },
    "сэндвич с тунцом": {
        "emoji": "🥪", "time": "5 мин",
        "kcal_portion": "~360 ккал",
        "ingredients": "• 2 куска цельнозернового хлеба\n• 1 банка тунца (185г)\n• 1 ст.л. греческий йогурт\n• Горчица\n• Огурец, помидор, латук\n• Сок лимона",
        "steps": "1. Тунец слить, размять с йогуртом и горчицей.\n2. Хлеб можно подсушить в тостере.\n3. На хлеб — латук, тунец, огурец, помидор.\n4. Сбрызнуть лимоном.",
        "tip": "💡 Готовится за 5 минут, белка больше чем в двух яйцах. Идеально в контейнер.",
    },
    "пита с куриной грудкой": {
        "emoji": "🫓", "time": "15 мин",
        "kcal_portion": "~400 ккал",
        "ingredients": "• 1 питта цельнозерновая\n• 150г куриная грудка отварная\n• 2 ст.л. хумус\n• Огурец, помидор черри\n• Шпинат\n• Сок лимона, паприка",
        "steps": "1. Питту слегка прогреть.\n2. Разрезать пополам, открыть кармашки.\n3. Намазать хумусом внутри.\n4. Вложить курицу, овощи, шпинат.\n5. Сбрызнуть лимоном.",
        "tip": "💡 Питта с хумусом = средиземноморский фастфуд. Быстро, вкусно, правильный баланс БЖУ.",
    },

    # ══════════════════════════════════════════
    #  ПРОТЕИНОВАЯ ВЫПЕЧКА
    # ══════════════════════════════════════════
    "протеиновые маффины (шоколад)": {
        "emoji": "🧁", "time": "30 мин",
        "kcal_portion": "~180 ккал (1 маффин)",
        "ingredients": "• 50г протеин шоколадный\n• 100г овсяная мука\n• 2 яйца\n• 150г творог 0%\n• 2 ст.л. какао\n• 1 ч.л. разрыхлителя\n• 100мл молока\n• Подсластитель по вкусу",
        "steps": "1. Смешать сухие ингредиенты: протеин, муку, какао, разрыхлитель.\n2. Смешать влажные: яйца, творог, молоко.\n3. Соединить, не перемешивать слишком долго.\n4. Разлить по формочкам (6 шт).\n5. Выпекать при 180°C 20–22 мин.",
        "tip": "💡 Белок на маффин: ~18г. Замораживай партию на неделю — разогрев 1 мин в микроволновке.",
    },
    "банановые протеиновые блины": {
        "emoji": "🥞", "time": "15 мин",
        "kcal_portion": "~320 ккал (4–5 блинов)",
        "ingredients": "• 1 банан\n• 2 яйца\n• 30г протеина ванильного\n• 50мл молока\n• Щепотка разрыхлителя\n• Корица",
        "steps": "1. Банан размять вилкой.\n2. Добавить яйца, протеин, молоко, разрыхлитель.\n3. Взбить блендером.\n4. Жарить без масла на антипригарной сковороде по 2 мин с каждой стороны.\n5. Подавать с ягодами.",
        "tip": "💡 3 ингредиента — банан, яйца, протеин. Белок ~28г. Вкуснее чем обычные блины.",
    },
    "протеиновое печенье (овсяное)": {
        "emoji": "🍪", "time": "20 мин",
        "kcal_portion": "~120 ккал (1 печенье)",
        "ingredients": "• 100г овсяные хлопья\n• 30г протеин ванильный\n• 2 ст.л. арахисовая паста\n• 1 яйцо\n• 1 ч.л. мёда\n• Горсть шоколадных капель (по желанию)",
        "steps": "1. Смешать все ингредиенты.\n2. Если смесь сухая — добавить 1–2 ст.л. молока.\n3. Скатать шарики, расплюснуть.\n4. Выпекать при 170°C 12–14 мин.\n5. Не перепекать — печенье затвердеет при остывании.",
        "tip": "💡 Делай партию из 12 штук — хранится в контейнере 5–7 дней. Идеальный перекус без чувства вины.",
    },
    "овсяные кексы с черникой": {
        "emoji": "🫐", "time": "30 мин",
        "kcal_portion": "~160 ккал (1 кекс)",
        "ingredients": "• 150г овсяная мука\n• 2 яйца\n• 100г греческий йогурт\n• 2 ст.л. мёда\n• 100г черника (свежая или замороженная)\n• 1 ч.л. разрыхлителя\n• Ваниль",
        "steps": "1. Смешать муку и разрыхлитель.\n2. Взбить яйца с мёдом, добавить йогурт и ваниль.\n3. Соединить сухое с влажным.\n4. Добавить чернику, осторожно перемешать.\n5. Разлить по формочкам, выпекать при 180°C 22–25 мин.",
        "tip": "💡 Замороженную чернику не размораживай — кексы будут красивее и не окрасятся.",
    },

    # ══════════════════════════════════════════
    #  САЛАТЫ И ЛЁГКИЕ БЛЮДА
    # ══════════════════════════════════════════
    "салат с тунцом и яйцом": {
        "emoji": "🥗", "time": "10 мин",
        "kcal_portion": "~310 ккал (300г)",
        "ingredients": "• 1 банка тунца (185г)\n• 2 яйца варёных\n• 1 огурец\n• Листья салата\n• 8 оливок\n• 1 ч.л. оливкового масла\n• Лимон, соль",
        "steps": "1. Листья салата порвать, выложить на тарелку.\n2. Яйца нарезать дольками, огурец — кружками.\n3. Тунец слить, выложить кусочками.\n4. Оливки добавить целыми.\n5. Заправить маслом и лимоном.",
        "tip": "💡 Белок почти 40г на салат. Можно съесть как полноценный обед без гарнира.",
    },
    "салат цезарь с курицей (лайт)": {
        "emoji": "🥗", "time": "15 мин",
        "kcal_portion": "~380 ккал (300г)",
        "ingredients": "• 150г куриная грудка\n• Листья романо\n• 20г пармезан\n• Цельнозерновые гренки\n• Соус: 3 ст.л. греческий йогурт + 1 ч.л. горчица + 1 ч.л. лимон + чеснок",
        "steps": "1. Грудку обжарить или отварить, нарезать.\n2. Листья порвать на куски.\n3. Приготовить соус — смешать все ингредиенты.\n4. Смешать салат, курицу, соус.\n5. Посыпать пармезаном и гренками.",
        "tip": "💡 Йогуртовый соус вместо майонезного: -200 ккал на порцию, такой же вкус.",
    },
    "боул с лососем и авокадо": {
        "emoji": "🍱", "time": "15 мин",
        "kcal_portion": "~520 ккал (400г)",
        "ingredients": "• 150г лосось запечённый\n• 100г бурый рис отварной\n• ½ авокадо\n• Огурец, редис\n• Кунжут, соевый соус\n• Листья шпината",
        "steps": "1. Рис выложить в основу боула.\n2. Разложить по секторам: лосось, авокадо, огурец, редис, шпинат.\n3. Полить соевым соусом.\n4. Посыпать кунжутом.",
        "tip": "💡 Боул — это и красиво и правильный баланс БЖУ в одной миске. Готовится за 15 мин если рис уже сварен.",
    },
    "салат с нутом и овощами": {
        "emoji": "🥗", "time": "10 мин",
        "kcal_portion": "~320 ккал (300г)",
        "ingredients": "• 240г нут консервированный\n• 1 огурец\n• 2 помидора\n• ½ красной луковицы\n• Петрушка\n• 1 ч.л. оливкового масла\n• Лимон, зира, соль",
        "steps": "1. Нут слить, промыть.\n2. Овощи нарезать кубиками.\n3. Смешать нут, овощи, петрушку.\n4. Заправить маслом и лимоном, добавить зиру.",
        "tip": "💡 Нут = белок + клетчатка. Отличный веганский обед или гарнир к мясу.",
    },

    # ══════════════════════════════════════════
    #  МЯСНЫЕ БЛЮДА
    # ══════════════════════════════════════════
    "куриные котлеты на пару": {
        "emoji": "🍗", "time": "30 мин",
        "kcal_portion": "~220 ккал (2 шт, 150г)",
        "ingredients": "• 300г куриный фарш\n• 1 яйцо\n• 1 луковица\n• 2 ст.л. овсяных хлопьев\n• Соль, перец, укроп",
        "steps": "1. Лук натереть на тёрке.\n2. Смешать фарш, яйцо, лук, хлопья, специи.\n3. Сформировать котлеты.\n4. Готовить в пароварке или мультиварке 25 мин.\n5. Или запечь при 200°C 20–22 мин.",
        "tip": "💡 На пару = без масла, -80 ккал по сравнению с жаркой. Сочные внутри — лук даёт влагу.",
    },
    "говяжьи стейки (лайт)": {
        "emoji": "🥩", "time": "15 мин",
        "kcal_portion": "~300 ккал (150г)",
        "ingredients": "• 150г говяжья вырезка или лопатка\n• Крупная соль\n• Чёрный перец\n• 1 зубчик чеснока\n• Веточка розмарина",
        "steps": "1. Мясо достать за 30 мин до готовки (комнатная температура).\n2. Посолить крупной солью непосредственно перед жаркой.\n3. Разогреть сковороду до максимума — должна дымить.\n4. Жарить 3 мин без касания, перевернуть.\n5. Ещё 2–3 мин. Дать отдохнуть 5 мин под фольгой.",
        "tip": "💡 Стейк medium rare = розовый внутри. Именно так он сочный и вкусный. Не пережаривай.",
    },
    "индейка с грибами": {
        "emoji": "🍄", "time": "25 мин",
        "kcal_portion": "~280 ккал (250г)",
        "ingredients": "• 200г индейка (грудка или бедро)\n• 150г шампиньоны\n• 1 луковица\n• 100мл нежирные сливки 10%\n• Чеснок, тимьян, соль",
        "steps": "1. Индейку нарезать кусочками, обжарить 5 мин.\n2. Добавить лук и грибы, жарить 7 мин.\n3. Добавить чеснок и тимьян.\n4. Влить сливки, тушить 5 мин.\n5. Подавать с гречкой или рисом.",
        "tip": "💡 Грибы выделяют влагу — не мешай первые 3 минуты, дай воде испариться.",
    },
    "куриная грудка в горчичном соусе": {
        "emoji": "🍗", "time": "20 мин",
        "kcal_portion": "~260 ккал (200г)",
        "ingredients": "• 200г куриная грудка\n• 1 ст.л. дижонская горчица\n• 100мл куриный бульон\n• 1 ч.л. мёда\n• 1 зубчик чеснока\n• Тимьян, соль",
        "steps": "1. Грудку отбить до толщины 1.5 см.\n2. Обжарить 4 мин с каждой стороны, отложить.\n3. В ту же сковороду добавить чеснок, горчицу, мёд.\n4. Влить бульон, уварить до соуса 3 мин.\n5. Вернуть курицу, прогреть в соусе 2 мин.",
        "tip": "💡 Горчичный соус без сливок — всего 40 ккал. Поливай рис или гречку этим соусом.",
    },

    # ══════════════════════════════════════════
    #  ЗАВТРАКИ (ДОПОЛНИТЕЛЬНЫЕ)
    # ══════════════════════════════════════════
    "овсянка на молоке с бананом": {
        "emoji": "🥣", "time": "10 мин",
        "kcal_portion": "~360 ккал (300г)",
        "ingredients": "• 60г овсяные хлопья (не быстрые)\n• 200мл молоко 1.5%\n• 1 банан\n• 1 ч.л. мёда\n• Корица\n• Горсть орехов",
        "steps": "1. Молоко довести почти до кипения.\n2. Всыпать хлопья, варить 5–7 мин помешивая.\n3. Снять с огня, накрыть на 2 мин.\n4. Выложить в тарелку, добавить нарезанный банан.\n5. Полить мёдом, посыпать орехами и корицей.",
        "tip": "💡 Не быстрые хлопья! Цельные или 'Геркулес' — ГИ в 2 раза ниже. Насыщают на 3–4 часа.",
    },
    "творог с орехами и мёдом": {
        "emoji": "🍯", "time": "3 мин",
        "kcal_portion": "~280 ккал (200г)",
        "ingredients": "• 200г творог 5%\n• 20г грецких орехов\n• 1 ч.л. мёда\n• Корица\n• Горсть ягод",
        "steps": "1. Творог выложить в миску.\n2. Сверху орехи, мёд, корицу.\n3. Добавить ягоды.",
        "tip": "💡 Идеальный завтрак если нет времени: 5 минут, белок 24г, полезные жиры. Казеин насыщает надолго.",
    },
    "каша пшённая с тыквой": {
        "emoji": "🎃", "time": "30 мин",
        "kcal_portion": "~300 ккал (250г)",
        "ingredients": "• 60г пшено\n• 150г тыква\n• 200мл молоко\n• 100мл вода\n• 1 ч.л. сливочного масла\n• Соль, мёд",
        "steps": "1. Тыкву нарезать кубиками, варить 10 мин в воде.\n2. Промыть пшено.\n3. Добавить к тыкве, влить молоко.\n4. Варить на малом огне 20 мин помешивая.\n5. Добавить масло и мёд.",
        "tip": "💡 Пшено богато железом и витамином B — особенно важно в период дефицита калорий.",
    },

    # ══════════════════════════════════════════
    #  НАПИТКИ И СМУЗИ (ДОПОЛНИТЕЛЬНЫЕ)
    # ══════════════════════════════════════════
    "имбирный лимонад (без сахара)": {
        "emoji": "🍋", "time": "10 мин",
        "kcal_portion": "~25 ккал (300мл)",
        "ingredients": "• 500мл вода\n• Сок 1 лимона\n• 2–3 см свежий имбирь\n• Мята (несколько листьев)\n• Подсластитель или 1 ч.л. мёда\n• Лёд",
        "steps": "1. Имбирь натереть, смешать с лимонным соком.\n2. Добавить воду и подсластитель.\n3. Настоять 5 мин.\n4. Процедить, добавить мяту и лёд.",
        "tip": "💡 Имбирь ускоряет метаболизм и снижает аппетит. Замени газировку этим лимонадом.",
    },
    "смузи манго-куркума": {
        "emoji": "🥭", "time": "5 мин",
        "kcal_portion": "~195 ккал (300мл)",
        "ingredients": "• 150г манго\n• 200мл молоко кокосовое (лёгкое)\n• ½ ч.л. куркумы\n• Щепотка чёрного перца (активирует куркуму)\n• 1 ч.л. мёда\n• Лёд",
        "steps": "1. Все ингредиенты в блендер.\n2. Взбить до однородности.\n3. Пить сразу.",
        "tip": "💡 Куркума + чёрный перец = мощный противовоспалительный дуэт. Перец увеличивает усвоение куркумина на 2000%.",
    },
    "протеиновый смузи со шпинатом": {
        "emoji": "🥬", "time": "5 мин",
        "kcal_portion": "~240 ккал (350мл)",
        "ingredients": "• 2 горсти шпината\n• 1 банан замороженный\n• 30г протеин ванильный\n• 250мл миндальное молоко\n• 1 ч.л. арахисовой пасты",
        "steps": "1. Шпинат и молоко в блендер, взбить первыми.\n2. Добавить банан, протеин, пасту.\n3. Взбить до однородности.\n4. Пить сразу.",
        "tip": "💡 Зелёный цвет пугает, но вкус — банановый. Проверено. Белок 30г + железо из шпината.",
    },

    # ══════════════════════════════════════════
    #  ДОДО ПИЦЦА
    # ══════════════════════════════════════════
    "додо пицца пепперони": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~284 ккал/100г | ~455 ккал/кусок (~160г)",
        "ingredients": "• Тесто традиционное\n• Пепперони\n• Моцарелла\n• Томатный соус",
        "steps": "Заказать в приложении Додо Пицца или на сайте dodopizza.ru",
        "tip": "💡 Б:11.5г Ж:11.4г У:31.9г / 100г. Один кусок ~455 ккал. Пицца 8 кусков ≈ 3650 ккал.",
    },
    "додо пицца маргарита": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~235 ккал/100г | ~375 ккал/кусок",
        "ingredients": "• Тесто традиционное\n• Моцарелла\n• Томатный соус\n• Орегано",
        "steps": "Заказать в приложении Додо Пицца или на сайте dodopizza.ru",
        "tip": "💡 Б:9.8г Ж:7.6г У:30.5г / 100г. Самая лёгкая из классических. Лучший выбор при дефиците.",
    },
    "додо пицца сырная": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~293 ккал/100г | ~470 ккал/кусок",
        "ingredients": "• Тесто традиционное\n• Моцарелла\n• Сырный соус\n• Чеснок",
        "steps": "Заказать в приложении Додо Пицца или на сайте dodopizza.ru",
        "tip": "💡 Б:10.8г Ж:10.6г У:36.7г / 100г. Много углеводов — ешь в день тренировки.",
    },
    "додо пицца мясная": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~260 ккал/100г | ~415 ккал/кусок",
        "ingredients": "• Тесто традиционное\n• Говядина, курица, бекон\n• Моцарелла\n• Томатный соус",
        "steps": "Заказать в приложении Додо Пицца или на сайте dodopizza.ru",
        "tip": "💡 Б:13г Ж:7г У:36г / 100г. Самый высокий белок среди классических пицц Додо.",
    },
    "додо пицца гавайская": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~216 ккал/100г | ~345 ккал/кусок",
        "ingredients": "• Тесто традиционное\n• Курица\n• Ананас\n• Моцарелла\n• Томатный соус",
        "steps": "Заказать в приложении Додо Пицца или на сайте dodopizza.ru",
        "tip": "💡 Б:12.2г Ж:7.4г У:25г / 100г. Одна из самых лёгких пицц — хорошо вписывается в дефицит.",
    },
    "додо пицца 4 сыра": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~200 ккал/100г | ~320 ккал/кусок",
        "ingredients": "• Тесто\n• Моцарелла\n• Чеддер\n• Дор блю\n• Пармезан",
        "steps": "Заказать в приложении Додо Пицца или на сайте dodopizza.ru",
        "tip": "💡 Б:8.8г Ж:7.4г У:24.4г / 100г. Много кальция, умеренная калорийность для сырной пиццы.",
    },
    "додо пицца чизбургер": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~207 ккал/100г | ~330 ккал/кусок",
        "ingredients": "• Тесто\n• Говяжий фарш\n• Томаты\n• Огурцы маринованные\n• Лук\n• Моцарелла\n• Горчица и томатный соус",
        "steps": "Заказать в приложении Додо Пицца или на сайте dodopizza.ru",
        "tip": "💡 Б:7.5г Ж:9.8г У:22.6г / 100г. Вкус чизбургера — в формате пиццы.",
    },
    "додо пицца супермясная": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~280 ккал/100г | ~450 ккал/кусок",
        "ingredients": "• Тесто\n• Пепперони\n• Бекон\n• Ветчина\n• Говядина\n• Моцарелла",
        "steps": "Заказать в приложении Додо Пицца или на сайте dodopizza.ru",
        "tip": "💡 Б:11.2г Ж:15.1г У:24.8г / 100г. Максимум белка и жира — только после тренировки.",
    },
    "додо пицца дон бекон": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~274 ккал/100г | ~440 ккал/кусок",
        "ingredients": "• Тесто\n• Бекон\n• Моцарелла\n• Сливочный соус\n• Лук",
        "steps": "Заказать в приложении Додо Пицца или на сайте dodopizza.ru",
        "tip": "💡 Б:9.8г Ж:14.8г У:25.2г / 100г. Высокий % жиров — ограничивай 1-2 кусками.",
    },
    "додо пицца цыплёнок барбекю": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~232 ккал/100г | ~370 ккал/кусок",
        "ingredients": "• Тесто\n• Куриное филе\n• Соус барбекю\n• Моцарелла\n• Лук красный",
        "steps": "Заказать в приложении Додо Пицца или на сайте dodopizza.ru",
        "tip": "💡 Б:12г Ж:5.5г У:32г / 100г. Хорошее соотношение белок/жир среди всех пицц.",
    },
    "додо пицца ветчина и сыр": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~282 ккал/100г | ~450 ккал/кусок",
        "ingredients": "• Тесто\n• Ветчина\n• Моцарелла\n• Томатный соус",
        "steps": "Заказать в приложении Додо Пицца или на сайте dodopizza.ru",
        "tip": "💡 Б:10.7г Ж:9.8г У:35.9г / 100г. Классическое сочетание. Любимая у детей и взрослых.",
    },
    "додо пицца бефстроганов": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~217 ккал/100г | ~553 ккал/порция (255г)",
        "ingredients": "• Тесто\n• Говядина в сливочном соусе\n• Шампиньоны\n• Моцарелла\n• Соус бефстроганов",
        "steps": "Заказать в приложении Додо Пицца или на сайте dodopizza.ru",
        "tip": "💡 Б:13.3г Ж:11.4г У:15.2г / 100г. Самый низкоуглеводный вариант — отличный выбор при дефиците.",
    },

    # ══════════════════════════════════════════
    #  ТАШИР ПИЦЦА
    # ══════════════════════════════════════════
    "ташир пицца маргарита": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~220 ккал/100г | ~350 ккал/кусок",
        "ingredients": "• Тесто\n• Томаты\n• Моцарелла\n• Томатный соус\n• Соус маджорио\n• Орегано",
        "steps": "Заказать на сайте tashirpizza.ru или в приложении",
        "tip": "💡 Классика — самая лёгкая пицца в меню Ташир. Томатный соус богат ликопином.",
    },
    "ташир пицца пепперони": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~255 ккал/100г | ~410 ккал/кусок",
        "ingredients": "• Тесто\n• Пепперони\n• Моцарелла\n• Томатный соус",
        "steps": "Заказать на сайте tashirpizza.ru или в приложении",
        "tip": "💡 Один из хитов меню. Пепперони богата жирами — 2 куска = хороший перекус после тренировки.",
    },
    "ташир пицца четыре сыра": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~265 ккал/100г | ~425 ккал/кусок",
        "ingredients": "• Тесто\n• Моцарелла\n• Брынза\n• Дор блю\n• Чеддер\n• Пармезан",
        "steps": "Заказать на сайте tashirpizza.ru или в приложении",
        "tip": "💡 Пять видов сыра! Высокий кальций и белок. Один кусок — дневная норма насыщенных жиров.",
    },
    "ташир пицца карбонара": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~245 ккал/100г | ~390 ккал/кусок",
        "ingredients": "• Тесто\n• Ветчина\n• Бекон\n• Шампиньоны\n• Лук\n• Моцарелла\n• Соус маджорио",
        "steps": "Заказать на сайте tashirpizza.ru или в приложении",
        "tip": "💡 Грибы + мясо = хорошее насыщение. Популярный выбор среди мужчин.",
    },
    "ташир пицца мясной пир": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~270 ккал/100г | ~430 ккал/кусок",
        "ingredients": "• Тесто\n• Пепперони\n• Ветчина\n• Сервелат\n• Бекон\n• Маслины\n• Моцарелла",
        "steps": "Заказать на сайте tashirpizza.ru или в приложении",
        "tip": "💡 Максимум мяса в одной пицце. Высококалорийная — идеально в день силовой тренировки.",
    },
    "ташир пицца чикен барбекю": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~238 ккал/100г | ~380 ккал/кусок",
        "ingredients": "• Тесто\n• Цыплёнок\n• Бекон\n• Болгарский перец\n• Моцарелла\n• Соус барбекю",
        "steps": "Заказать на сайте tashirpizza.ru или в приложении",
        "tip": "💡 Курица + барбекю — один из лучших вариантов по соотношению вкус/калории в меню.",
    },
    "ташир пицца гавайская": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~230 ккал/100г | ~368 ккал/кусок",
        "ingredients": "• Тесто\n• Цыплёнок\n• Моцарелла\n• Томатный соус\n• Соус маджорио\n• Укроп",
        "steps": "Заказать на сайте tashirpizza.ru или в приложении",
        "tip": "💡 Лёгкая куриная пицца. Хороший выбор для тех, кто следит за калориями.",
    },
    "ташир пицца барбекю с халапеньо": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~260 ккал/100г | ~415 ккал/кусок",
        "ingredients": "• Тесто\n• Ветчина\n• Бекон\n• Буженина\n• Перец халапеньо\n• Моцарелла\n• Соус барбекю",
        "steps": "Заказать на сайте tashirpizza.ru или в приложении",
        "tip": "💡 Острая! Капсаицин из халапеньо слегка ускоряет метаболизм.",
    },
    "ташир пицца том ям": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~235 ккал/100г | ~375 ккал/кусок",
        "ingredients": "• Тесто\n• Цыплёнок\n• Шампиньоны\n• Болгарский перец\n• Помидоры черри\n• Моцарелла\n• Соус том ям",
        "steps": "Заказать на сайте tashirpizza.ru или в приложении",
        "tip": "💡 Азиатский вкус на итальянской основе. Один из самых необычных вариантов в меню.",
    },
    "ташир пицца ассорти": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~240 ккал/100г | ~384 ккал/кусок",
        "ingredients": "• Тесто\n• Сервелат\n• Шампиньоны\n• Томаты\n• Моцарелла\n• Томатный соус\n• Соус маджорио",
        "steps": "Заказать на сайте tashirpizza.ru или в приложении",
        "tip": "💡 Сбалансированное сочетание овощей и мяса. Средняя калорийность.",
    },
    "ташир пицца сливочная с курицей": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~235 ккал/100г | ~375 ккал/кусок",
        "ingredients": "• Тесто\n• Цыплёнок\n• Моцарелла\n• Соус маджорио\n• Соус альфредо\n• Орегано",
        "steps": "Заказать на сайте tashirpizza.ru или в приложении",
        "tip": "💡 Нежный сливочный вкус. Соус альфредо делает пиццу мягкой и насыщенной.",
    },
    "ташир пицца цыплёнок с песто": {
        "emoji": "🍕", "time": "доставка",
        "kcal_portion": "~242 ккал/100г | ~387 ккал/кусок",
        "ingredients": "• Тесто\n• Цыплёнок\n• Ветчина\n• Томаты\n• Моцарелла\n• Соус песто\n• Соус альфредо",
        "steps": "Заказать на сайте tashirpizza.ru или в приложении",
        "tip": "💡 Итальянская классика — базиликовый песто придаёт уникальный аромат.",
    },
}

def build_recipe_card(dish_name, profile=None):
    """Строит карточку рецепта блюда с учётом ограничений здоровья"""
    r = RECIPES.get(dish_name)
    if not r:
        return None
    # Проверяем запрещённые ингредиенты
    health_warn = ""
    if profile:
        banned = get_banned_foods(profile)
        found_banned = [f for f in banned if f in r.get("ingredients","")]
        if found_banned:
            alts = [get_safe_replacement(profile, f) for f in found_banned]
            health_warn = (f"\n\n⚠️ *Внимание по твоим ограничениям здоровья:*\n"
                          f"Замени *{', '.join(found_banned)}* на *{', '.join(alts)}*")
    grams = DEFAULT_PORTIONS.get(dish_name, 200)
    return (
        f"{r['emoji']} *{dish_name.upper()}*\n{'─'*22}\n\n"
        f"⏱️ Время приготовления: *{r['time']}*\n"
        f"🔥 Калорийность порции: *{r['kcal_portion']}*\n\n"
        f"🛒 *Ингредиенты:*\n{r['ingredients']}\n\n"
        f"👨‍🍳 *Приготовление:*\n{r['steps']}\n\n"
        f"{r['tip']}{health_warn}"
    )


def get_ration_recipe_buttons(ration_text):
    """Ищет в тексте рациона блюда из RECIPES и возвращает inline-кнопки"""
    buttons = []
    for dish in RECIPES:
        if dish.lower() in ration_text.lower():
            buttons.append(dish)
    return buttons[:8]  # максимум 8 кнопок

def ration_recipe_inline(ration_text):
    """Строит InlineKeyboardMarkup с рецептами из рациона"""
    dishes = get_ration_recipe_buttons(ration_text)
    if not dishes:
        return None
    kb = types.InlineKeyboardMarkup(row_width=2)
    for dish in dishes:
        short = dish[:28] + "…" if len(dish) > 28 else dish
        kb.add(types.InlineKeyboardButton(f"📖 {short}", callback_data=f"recipe:{dish}"))
    return kb

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
    ("setup_home",     "🏠 Как ты планируешь тренироваться?\n\n"
                       "1 — 🏋️ Только зал\n"
                       "2 — 🏋️🏠 Зал + иногда дома\n"
                       "3 — 🏠 Только дома (без зала)"),
    ("setup_driver",   "🚗 Ты водитель или работаешь в основном сидя?\n\n1 — Да (водитель, офис)\n2 — Нет, есть физическая активность на работе"),
    ("setup_health",   "🏥 Есть ли у тебя ограничения по здоровью? Бот будет автоматически исключать опасные продукты и упражнения.\n\n"
                       "Выбери цифры через запятую (например: `1,3`) или `0` если ограничений нет:\n\n"
                       "1 — 🩸 Сахарный диабет\n"
                       "2 — 🌾 Аллергия на глютен\n"
                       "3 — 🥛 Непереносимость лактозы\n"
                       "4 — 🥜 Аллергия на орехи\n"
                       "5 — 💔 Высокое давление/сердечные\n"
                       "6 — 🦴 Проблемы с суставами/связками\n"
                       "7 — 🫁 Астма / затруднённое дыхание\n"
                       "0 — Нет ограничений"),
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
        elif state == "setup_home":
            assert text in ("1","2","3")
            hw_map = {"1": 0, "2": 1, "3": 2}
            save_profile(cid, home_workouts=hw_map[text])
        elif state == "setup_driver":
            assert text in ("1","2"); save_profile(cid,is_driver=1 if text=="1" else 0)
        elif state == "setup_health":
            condition_map = {"1":"диабет","2":"аллергия_глютен","3":"аллергия_лактоза",
                             "4":"аллергия_орехи","5":"давление","6":"суставы","7":"астма"}
            cleaned = text.replace(" ", "")
            if cleaned == "0":
                save_profile(cid, health_conditions="")
            else:
                nums = cleaned.split(",")
                assert all(n in condition_map for n in nums)
                conditions = [condition_map[n] for n in nums]
                save_profile(cid, health_conditions=",".join(conditions))
    except Exception:
        hints = {"setup_weight":"Вес числом: 107","setup_target":"Цель числом: 92",
                 "setup_height":"Рост в см: 194","setup_age":"Возраст: 24",
                 "setup_gymdays":"Число 1-5","setup_pref":"Введи 1, 2 или 3",
                 "setup_deadline":"Недели: 12","setup_home":"Введи 1, 2 или 3","setup_driver":"Введи 1 или 2",
                 "setup_health":"Введи цифры через запятую (1,3) или 0"}
        bot.send_message(cid, f"⚠️ {hints.get(state,'Некорректный ввод')}", reply_markup=cancel_menu())
        return False
    if idx+1 < len(ONBOARDING_STEPS):
        ns,np = ONBOARDING_STEPS[idx+1]
        # Если выбрали "только дома" — пропускаем setup_gymdays и setup_pref
        if state == "setup_home" and text == "3":
            save_profile(cid, gym_days=0)
            skip_states = {"setup_gymdays", "setup_pref"}
            next_idx = idx + 1
            while next_idx < len(ONBOARDING_STEPS) and ONBOARDING_STEPS[next_idx][0] in skip_states:
                next_idx += 1
            if next_idx < len(ONBOARDING_STEPS):
                ns, np = ONBOARDING_STEPS[next_idx]
                set_state(cid, ns, extra=extra)
                bot.send_message(cid, np, parse_mode="Markdown", reply_markup=cancel_menu())
                return False
        set_state(cid, ns, extra=extra)
        bot.send_message(cid, np, parse_mode="Markdown", reply_markup=cancel_menu())
        return False
    set_state(cid, "idle")
    profile = get_profile(cid)
    plan    = get_user_plan(cid, profile)
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
    """Главное меню — 6 категорий + быстрые действия"""
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    profile = get_profile(uid) if uid else None
    # Быстрые действия (топ)
    if profile and profile.get("is_sick"):
        m.add(types.KeyboardButton("💊 Режим болезни"), types.KeyboardButton("✅ Я выздоровел"))
    else:
        m.add(types.KeyboardButton("🟢 Тренировка сегодня"), types.KeyboardButton("✅ Тренировка завершена"))
    m.add(types.KeyboardButton("⚖️ Внести вес"), types.KeyboardButton("📋 Сводка за день"))
    # Категории
    m.add(types.KeyboardButton("🍽️ Питание"), types.KeyboardButton("🏋️ Тренировки"))
    m.add(types.KeyboardButton("📊 Моё тело"), types.KeyboardButton("📈 Аналитика"))
    m.add(types.KeyboardButton("😴 Здоровье"), types.KeyboardButton("⚙️ Настройки"))
    # Помощь
    m.add(types.KeyboardButton("❓ Помощь / команды"))
    return m

def menu_pitanie():
    """Подменю — Питание"""
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(types.KeyboardButton("🍽️ Рацион сегодня"), types.KeyboardButton("📅 Рацион на завтра"))
    m.add(types.KeyboardButton("🍴 Выбрать блюдо"), types.KeyboardButton("🔄 Заменить блюдо"))
    m.add(types.KeyboardButton("📓 Дневник питания"), types.KeyboardButton("➕ Записать приём пищи"))
    m.add(types.KeyboardButton("🍽️ Калории сегодня"), types.KeyboardButton("⚖️ Баланс калорий"))
    m.add(types.KeyboardButton("💧 Вода (мл)"), types.KeyboardButton("📦 Штрихкод"))
    m.add(types.KeyboardButton("🥩 Полуфабрикаты"), types.KeyboardButton("🍝 Рецепты блюд"))
    m.add(types.KeyboardButton("🍕 Читмил"), types.KeyboardButton("🧮 Калькулятор ккал"))
    m.add(types.KeyboardButton("🍫 Сладкое"), types.KeyboardButton("🍓 Фрукты"))
    m.add(types.KeyboardButton("🔥 Жиросжигающие"), types.KeyboardButton("💪 Спортпит"))
    m.add(types.KeyboardButton("🗓️ Меню на неделю"), types.KeyboardButton("🛒 Список покупок"))
    m.add(types.KeyboardButton("⭐ Избранные блюда"), types.KeyboardButton("📋 Шаблоны еды"))
    m.add(types.KeyboardButton("📊 Макронутриенты"), types.KeyboardButton("🍎 ГИ продукта"))
    m.add(types.KeyboardButton("💊 Мои добавки"), types.KeyboardButton("💊 Лекарства"))
    m.add(types.KeyboardButton("🏆 Режим сушки"), types.KeyboardButton("🎮 Угадай калории"))
    m.add(types.KeyboardButton("⏳ Интервальное голодание"), types.KeyboardButton("📊 День vs вчера"))
    m.add(types.KeyboardButton("🍺 Алкоголь-трекер"))
    m.add(types.KeyboardButton("🏠 Главное меню"))
    return m

def menu_trenirovki():
    """Подменю — Тренировки"""
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(types.KeyboardButton("🟢 Тренировка сегодня"), types.KeyboardButton("✅ Тренировка завершена"))
    m.add(types.KeyboardButton("📅 Фаза тренировок"), types.KeyboardButton("📅 Программа на 8 нед"))
    m.add(types.KeyboardButton("🕐 Расписание дня"), types.KeyboardButton("🏠 Тренировка дома"))
    m.add(types.KeyboardButton("🏠 Домашние тренировки"), types.KeyboardButton("🔥 Разминка"))
    m.add(types.KeyboardButton("🧘 Заминка"), types.KeyboardButton("💪 Супер-сеты"))
    m.add(types.KeyboardButton("❤️ Заменить кардио"), types.KeyboardButton("⏱️ Таймер отдыха"))
    m.add(types.KeyboardButton("🏃 Кардио таймер"), types.KeyboardButton("💪 Прогресс упражнений"))
    m.add(types.KeyboardButton("➕ Добавить упражнение"), types.KeyboardButton("🏆 Рекорды (1RM)"))
    m.add(types.KeyboardButton("🛁 Расслабляющая ванна"), types.KeyboardButton("💪 Восстановление"))
    m.add(types.KeyboardButton("🤖 Тренер"), types.KeyboardButton("💬 Цитата дня"))
    m.add(types.KeyboardButton("📒 Журнал упражнений"), types.KeyboardButton("🔥 Стрик активности"))
    m.add(types.KeyboardButton("🤸 Разминка по мышцам"), types.KeyboardButton("❤️ Пульсовые зоны"))
    m.add(types.KeyboardButton("🏠 Главное меню"))
    return m

def menu_telo():
    """Подменю — Моё тело"""
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(types.KeyboardButton("⚖️ Внести вес"), types.KeyboardButton("📈 Мой прогресс"))
    m.add(types.KeyboardButton("📊 График веса"), types.KeyboardButton("👟 Внести шаги"))
    m.add(types.KeyboardButton("👣 Мои шаги"), types.KeyboardButton("💧 Внести воду"))
    m.add(types.KeyboardButton("📏 Обхват талии"), types.KeyboardButton("📏 Обхваты"))
    m.add(types.KeyboardButton("📋 Загрузить InBody"), types.KeyboardButton("📊 История InBody"))
    m.add(types.KeyboardButton("📷 Фото-прогресс"), types.KeyboardButton("📸 Карточка прогресса"))
    m.add(types.KeyboardButton("😊 Самочувствие"), types.KeyboardButton("🩺 Давление/пульс"))
    m.add(types.KeyboardButton("🏥 Мои ограничения"), types.KeyboardButton("🏆 Мои ачивки"))
    m.add(types.KeyboardButton("🏅 Мои достижения"), types.KeyboardButton("🔥 Серия дней"))
    m.add(types.KeyboardButton("👫 Партнёр"))
    m.add(types.KeyboardButton("📐 % Жира"), types.KeyboardButton("📊 Прогресс обхватов"))
    m.add(types.KeyboardButton("🌳 Дерево достижений"), types.KeyboardButton("🔮 Биоритмы"))
    m.add(types.KeyboardButton("🏠 Главное меню"))
    return m

def menu_analitika():
    """Подменю — Аналитика"""
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(types.KeyboardButton("📈 Инфографика"), types.KeyboardButton("📅 Прогноз по неделям"))
    m.add(types.KeyboardButton("🎯 Прогноз цели"), types.KeyboardButton("🔮 Прогноз «Что если»"))
    m.add(types.KeyboardButton("🤖 ИИ-анализ недели"), types.KeyboardButton("🔬 Корреляции"))
    m.add(types.KeyboardButton("📬 Отчёт за неделю"), types.KeyboardButton("📋 Отчёт за месяц"))
    m.add(types.KeyboardButton("⚡ Мой уровень XP"), types.KeyboardButton("🏆 Челленджи"))
    m.add(types.KeyboardButton("📤 Экспорт CSV"), types.KeyboardButton("🤖 Совет на день"))
    m.add(types.KeyboardButton("🏠 Главное меню"))
    return m

def menu_zdorovie():
    """Подменю — Здоровье"""
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(types.KeyboardButton("😴 Лечь спать"), types.KeyboardButton("⏰ Проснулся"))
    m.add(types.KeyboardButton("💤 История сна"), types.KeyboardButton("😊 Самочувствие"))
    m.add(types.KeyboardButton("🧠 Стресс"), types.KeyboardButton("🩸 Цикл"))
    m.add(types.KeyboardButton("💓 HRV / Пульс"), types.KeyboardButton("🩺 Давление/пульс"))
    m.add(types.KeyboardButton("🏥 Мои ограничения"), types.KeyboardButton("💊 Лекарства"))
    m.add(types.KeyboardButton("🤒 Я заболел"), types.KeyboardButton("⏰ Напоминания"))
    m.add(types.KeyboardButton("📥 Импорт Health/Fit"), types.KeyboardButton("🏠 Главное меню"))
    return m

def menu_nastroyki():
    """Подменю — Настройки"""
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(types.KeyboardButton("👤 Мой профиль"), types.KeyboardButton("⚙️ Изменить профиль"))
    m.add(types.KeyboardButton("⏰ Напоминания"), types.KeyboardButton("🔔 Напоминания"))
    m.add(types.KeyboardButton("🏠 Домашние тренировки"), types.KeyboardButton("👫 Партнёр"))
    m.add(types.KeyboardButton("📤 Экспорт CSV"), types.KeyboardButton("🏠 Главное меню"))
    return m

# Набор всех кнопок-категорий для роутинга
MENU_CATEGORIES = {"🍽️ Питание", "🏋️ Тренировки", "📊 Моё тело", "📈 Аналитика", "😴 Здоровье", "⚙️ Настройки"}

def cancel_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(types.KeyboardButton("❌ Отмена"))
    return m

def inbody_choice_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(types.KeyboardButton("✏️ Ввести вручную"))
    m.add(types.KeyboardButton("❌ Отмена"))
    return m

def skip_or_cancel_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(types.KeyboardButton("⏭️ Пропустить"))
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
    (7,  0,  "🍳 *Доброе утро!* Время завтрака!\n\n3 яйца + 60г овсянки + помидор\n\n{quote}\n\n{drying_note}"),
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
                    # Автобэкап данных каждое воскресенье
                    wd2 = get_weights(uid); sd2 = get_steps(uid, limit=200)
                    sl2 = get_sleep_history(uid, limit=50)
                    out = io.StringIO(); wr = csv.writer(out)
                    wr.writerow(["Тип","Значение","Дата"])
                    for wv,d in wd2: wr.writerow(["вес",wv,d])
                    for sv,d in sd2: wr.writerow(["шаги",sv,d])
                    for st,wt,dur,qual,d in sl2: wr.writerow(["сон",f"{dur}ч кач:{qual}",d])
                    out.seek(0)
                    bio = io.BytesIO(out.getvalue().encode("utf-8-sig"))
                    bio.name = f"backup_{now.strftime('%Y%m%d')}.csv"
                    bot.send_document(uid, bio,
                        caption="💾 *Еженедельный бэкап данных*\n\nВсе твои данные за неделю. Сохрани файл на всякий случай.",
                        parse_mode="Markdown")
                except Exception:
                    pass
        time.sleep(30)

# ─────────────────────────────────────────
#  ХЭНДЛЕРЫ
# ─────────────────────────────────────────

@bot.message_handler(commands=['summary', 'today', 'итог'])
def cmd_summary(message):
    bot.send_message(message.chat.id, build_today_summary(message.chat.id), parse_mode="Markdown")

@bot.message_handler(commands=['receipt', 'chek'])
def cmd_receipt(message):
    set_state(message.chat.id, "waiting_receipt_photo")
    bot.send_message(message.chat.id,
        "🧾 *Анализ чека*\n\nОтправь фото кассового чека — распознаю продукты и их калорийность.",
        parse_mode="Markdown", reply_markup=cancel_menu())

@bot.message_handler(commands=['partner', 'pair'])
def cmd_partner(message):
    cid = message.chat.id
    partner_id = get_partner(cid)
    kb_pair = types.InlineKeyboardMarkup()
    if partner_id:
        kb_pair.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="partner_refresh"))
        kb_pair.add(types.InlineKeyboardButton("❌ Отвязать", callback_data="partner_unlink"))
    else:
        kb_pair.add(types.InlineKeyboardButton("🔗 Подключить партнёра", callback_data="partner_link"))
    bot.send_message(cid, build_partner_comparison(cid), parse_mode="Markdown", reply_markup=kb_pair)

@bot.message_handler(commands=['note', 'заметка'])
def cmd_note(message):
    """/note текст — добавить быструю заметку"""
    cid = message.chat.id
    parts = message.text.strip().split(None, 1)
    if len(parts) < 2:
        bot.send_message(cid, "📝 Формат: `/note купить протеин`", parse_mode="Markdown")
        return
    text_note = parts[1].strip()
    add_quick_note(cid, text_note)
    add_xp(cid, 1)
    bot.send_message(cid, f"📝 Заметка добавлена:\n_{text_note}_\n\nПосмотреть все: *«📝 Заметки»*",
                     parse_mode="Markdown", reply_markup=main_menu(cid))

@bot.message_handler(commands=['hrv'])
def cmd_hrv(message):
    """/hrv 65 55 — записать HRV и пульс покоя"""
    cid = message.chat.id
    parts = message.text.strip().split()
    if len(parts) >= 2:
        try:
            hrv = int(parts[1]) if len(parts) > 1 else 0
            pulse = int(parts[2]) if len(parts) > 2 else 0
            log_hrv(cid, hrv, pulse)
            bot.send_message(cid,
                f"💓 Записано: HRV *{hrv}*, пульс покоя *{pulse} уд/мин*",
                parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "⚠️ Формат: /hrv 65 55\n(HRV и пульс покоя)", reply_markup=main_menu(cid))
    else:
        set_state(cid, "waiting_hrv")
        bot.send_message(cid, "💓 Введи HRV и пульс покоя через пробел:\nНапример: `65 55`",
                         parse_mode="Markdown", reply_markup=cancel_menu())

@bot.message_handler(commands=['1rm', 'orm'])
def cmd_1rm(message):
    """/1rm жим лёжа 100 5 — записать 1RM"""
    cid = message.chat.id
    parts = message.text.strip().split()
    if len(parts) >= 4:
        try:
            # /1rm жим лёжа 100 5
            reps = int(parts[-1])
            weight = float(parts[-2])
            exercise = " ".join(parts[1:-2])
            one_rm = log_1rm(cid, exercise, weight, reps)
            bot.send_message(cid,
                f"🏋️ *{exercise.capitalize()}*\n"
                f"{weight}кг × {reps} повт.\n"
                f"Расчётный 1RM: *{one_rm} кг* 💪",
                parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "⚠️ Формат: /1rm жим лёжа 100 5\n(упражнение, вес кг, повторений)")
    else:
        bot.send_message(cid,
            "🏋️ *Расчёт 1RM*\n\nФормат: `/1rm жим лёжа 100 5`\n_(упражнение, вес кг, кол-во повторений)_",
            parse_mode="Markdown")

@bot.message_handler(commands=['w', 'weight', 'ves'])
def cmd_weight(message):
    """Быстрая команда /w 105.7"""
    cid = message.chat.id
    parts = message.text.strip().split()
    if len(parts) >= 2:
        try:
            w = float(parts[1].replace(",", "."))
            assert 30 < w < 300
            add_weight(cid, w); save_profile(cid, current_weight=w)
            try: update_streak(cid)
            except: pass
            bot.send_message(cid, f"✅ Вес *{w} кг* сохранён!", parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "❌ Пример: `/w 105.7`", parse_mode="Markdown")
    else:
        set_state(cid, "waiting_weight")
        bot.send_message(cid, "⚖️ Введи вес (например: *105.7*)", parse_mode="Markdown", reply_markup=cancel_menu())

@bot.message_handler(commands=['s', 'steps', 'shagi'])
def cmd_steps(message):
    """Быстрая команда /s 8500"""
    cid = message.chat.id
    parts = message.text.strip().split()
    if len(parts) >= 2:
        try:
            s = int(parts[1].replace(" ", ""))
            assert 0 < s < 100000
            add_steps(cid, s)
            v = ("🔥 Отлично!" if s >= 12000 else "✅ Хорошо!" if s >= 8000 else "🟡 Добавь прогулку." if s >= 5000 else "🔴 Мало движения.")
            bot.send_message(cid, f"👟 *{s:,} шагов* {v}".replace(",", " "), parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "❌ Пример: `/s 8500`", parse_mode="Markdown")
    else:
        set_state(cid, "waiting_steps")
        bot.send_message(cid, "👟 Введи шаги:", reply_markup=cancel_menu())

@bot.message_handler(commands=['water', 'voda'])
def cmd_water(message):
    """Быстрая команда /water 3"""
    cid = message.chat.id
    parts = message.text.strip().split()
    if len(parts) >= 2:
        try:
            g = int(parts[1])
            assert 0 < g <= 20
            add_water(cid, g)
            total = get_water_today(cid)
            bot.send_message(cid, f"💧 +{g} стак. Сегодня: *{total}/8*", parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "❌ Пример: `/water 3`", parse_mode="Markdown")
    else:
        set_state(cid, "waiting_water")
        bot.send_message(cid, "💧 Сколько стаканов?", reply_markup=cancel_menu())

@bot.message_handler(commands=['start','help'])
def send_welcome(message):
    cid = message.chat.id
    profile = get_profile(cid)

    DISCLAIMER = (
        "⚠️ *Важная информация*\n\n"
        "Этот бот — вспомогательный инструмент для отслеживания питания и тренировок. "
        "Он *не является медицинским приложением* и не заменяет консультацию врача.\n\n"
        "📌 *Пожалуйста, учти:*\n"
        "• Все рекомендации по питанию и калоражу носят *общий характер*\n"
        "• Рекомендации по тренировкам не учитывают индивидуальные травмы и противопоказания\n"
        "• При наличии хронических заболеваний *обязательно согласуй план с врачом*\n"
        "• Медицинские ограничения в боте — подсказки, а не диагноз\n\n"
        "💬 Используя бота, ты соглашаешься принимать решения *самостоятельно и на свой риск*."
    )

    if not profile:
        bot.send_message(cid, DISCLAIMER, parse_mode="Markdown")
        bot.send_message(cid,
            "👋 Привет! Я *Инженерный трекер жиросжигания PRO v7*\n\n"
            "Давай настроим твой персональный план 👇",
            parse_mode="Markdown")
        start_onboarding(cid)
    else:
        plan = get_user_plan(cid, profile)
        sick = "\n\n🤒 *Режим болезни активен*" if profile.get("is_sick") else ""
        bot.send_message(cid,
            f"👋 С возвращением!\n\n"
            f"🎯 Цель: *{profile['current_weight']} → {profile['target_weight']} кг*\n"
            f"🔥 Калории: *{plan['calories']} ккал/день*\n"
            f"📈 Темп: *~{plan['weekly_loss']} кг/нед*{sick}",
            parse_mode="Markdown", reply_markup=main_menu(cid))

@bot.message_handler(content_types=['document'])
def handle_document(message):
    cid = message.chat.id
    state, extra = get_state(cid)

    # ── Импорт Apple Health / Google Fit CSV ──
    if state == "waiting_health_import":
        doc = message.document
        if not doc.file_name.lower().endswith(".csv"):
            bot.send_message(cid, "⚠️ Нужен CSV-файл. Попробуй ещё раз или нажми ❌ Отмена.",
                             reply_markup=cancel_menu())
            return
        bot.send_message(cid, "⏳ Импортирую данные...")
        try:
            file_info = bot.get_file(doc.file_id)
            file_bytes = bot.download_file(file_info.file_path)
            fname = doc.file_name.lower()
            source = "apple" if "apple" in fname or "export" in fname else "google"
            imported = import_health_csv(cid, file_bytes, source)
            set_state(cid, "idle")
            if imported > 0:
                bot.send_message(cid,
                    f"✅ *Импорт завершён!*\n\nЗагружено записей: *{imported}*\n"
                    f"Источник: {'Apple Health' if source=='apple' else 'Google Fit'}\n\n"
                    f"Данные появятся в разделах «Шаги» и «График веса».",
                    parse_mode="Markdown", reply_markup=main_menu(cid))
            else:
                bot.send_message(cid,
                    "⚠️ Не удалось импортировать данные.\n\n"
                    "Убедись что файл из Apple Health (Экспорт данных) или Google Fit (Google Takeout).",
                    reply_markup=main_menu(cid))
        except Exception as e:
            set_state(cid, "idle")
            bot.send_message(cid, f"❌ Ошибка импорта. Попробуй ещё раз.", reply_markup=main_menu(cid))
        return

    if state != "waiting_inbody_pdf":
        bot.send_message(cid,
            "📎 Файл получен, но я не ожидаю документ сейчас.\n\n"
            "Если это отчёт InBody — нажми сначала *«📋 Загрузить InBody»*.\n"
            "Для импорта Health/Fit — нажми *«📥 Импорт Health/Fit»*.",
            parse_mode="Markdown", reply_markup=main_menu(cid))
        return

    doc = message.document
    if not doc.file_name.lower().endswith(".pdf"):
        bot.send_message(cid, "⚠️ Нужен файл в формате PDF. Попробуй ещё раз.",
                         reply_markup=cancel_menu())
        return

    bot.send_message(cid, "⏳ Читаю отчёт...", reply_markup=cancel_menu())

    try:
        file_info = bot.get_file(doc.file_id)
        downloaded = bot.download_file(file_info.file_path)
        tmp_path = f"/tmp/inbody_{cid}.pdf"
        with open(tmp_path, "wb") as f:
            f.write(downloaded)
    except Exception as e:
        bot.send_message(cid, f"❌ Не удалось скачать файл: {e}", reply_markup=main_menu(cid))
        set_state(cid, "idle")
        return

    data, error = parse_inbody_pdf(tmp_path)

    try:
        import os as _os
        _os.remove(tmp_path)
    except Exception:
        pass

    set_state(cid, "idle")

    if error or not data:
        bot.send_message(cid,
            f"❌ *Не удалось распознать отчёт.*\n\n{error or 'Неизвестная ошибка.'}\n\n"
            f"Убедись что это PDF-отчёт именно из приложения DDX Fitness с InBody.",
            parse_mode="Markdown", reply_markup=main_menu(cid))
        return

    # Строим отчёт ДО сохранения — чтобы сравнение с прошлым замером было корректным
    report = build_inbody_report(cid, data)

    add_inbody_record(cid, data)
    update_streak(cid)

    # Синхронизируем текущий вес в профиле с данными InBody (более точные весы)
    profile = get_profile(cid)
    if profile and data.get("weight"):
        add_weight(cid, data["weight"])
        save_profile(cid, current_weight=data["weight"])

    bot.send_message(cid, report, parse_mode="Markdown", reply_markup=main_menu(cid))

ADMIN_UID = None  # Установи свой Telegram ID для получения уведомлений об ошибках


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    cid = call.message.chat.id
    data = call.data

    # ── Открытие рецепта из рациона ──
    if data.startswith("recipe:"):
        dish = data[7:]
        card = build_recipe_card(dish, get_profile(cid))
        if card:
            kb_inline = types.InlineKeyboardMarkup()
            kb_inline.add(
                types.InlineKeyboardButton("➕ Добавить в дневник", callback_data=f"add_to_diary:{dish}"),
                types.InlineKeyboardButton("✅ Понятно", callback_data="close"),
            )
            bot.answer_callback_query(call.id)
            bot.send_message(cid, card, parse_mode="Markdown", reply_markup=kb_inline)
        else:
            bot.answer_callback_query(call.id, "Рецепт не найден")

    # ── Добавить в дневник питания ──
    elif data.startswith("add_to_diary:"):
        payload = data[13:]  # может быть "dish" или "dish:grams"
        payload_parts = payload.rsplit(":", 1)
        dish = payload_parts[0]
        if len(payload_parts) == 2:
            try:
                portion = int(payload_parts[1])
            except Exception:
                portion = DEFAULT_PORTIONS.get(dish, 100)
        else:
            portion = DEFAULT_PORTIONS.get(dish, 100)
        kcal_per_100 = KCAL_PER_100G.get(dish, 0)
        kcal_portion = round(kcal_per_100 * portion / 100)
        log_meal_entry(cid, "🍽️ Прочее", dish, portion, kcal_portion)
        bot.answer_callback_query(call.id, f"✅ Записано!")
        bot.send_message(cid,
            f"✅ *{dish.capitalize()}* добавлено в дневник\n\n"
            f"📏 Порция: *{portion} г* | 🔥 *{kcal_portion} ккал*",
            parse_mode="Markdown", reply_markup=main_menu(cid))

    # ── Открыть рацион ──
    elif data == "open_ration":
        bot.answer_callback_query(call.id)
        profile = get_profile(cid)
        if not profile:
            bot.send_message(cid, "Сначала настрой профиль."); return
        ration, cal = build_ration(cid)
        ration_kb = ration_recipe_inline(ration)
        bot.send_message(cid,
            f"🍽️ *РАЦИОН НА СЕГОДНЯ*\n─────────────\n{ration}",
            parse_mode="Markdown",
            reply_markup=ration_kb if ration_kb else main_menu(cid))
        if ration_kb:
            bot.send_message(cid, "⬆️ Рецепты из рациона:", reply_markup=main_menu(cid))

    # ── Закрыть ──
    elif data == "close":
        bot.answer_callback_query(call.id, "Ок!")
        try: bot.delete_message(cid, call.message.message_id)
        except: pass

    # ── Давление: открыть форму ввода ──
    elif data == "pressure_add":
        bot.answer_callback_query(call.id)
        set_state(cid, "waiting_pressure")
        bot.send_message(cid,
            "🩺 Введи давление в формате:\n*120/80* или *120/80/72* (с пульсом)",
            parse_mode="Markdown", reply_markup=cancel_menu())

    # ── Лекарство: принял ──
    elif data.startswith("med_take:"):
        mid = int(data.split(":")[1])
        log_medication_taken(cid, mid)
        bot.answer_callback_query(call.id, "✅ Отмечено!")
        bot.send_message(cid, build_medications_today(cid), parse_mode="Markdown")

    # ── Лекарство: добавить новое ──
    elif data == "med_add":
        bot.answer_callback_query(call.id)
        set_state(cid, "med_add_name")
        bot.send_message(cid, "💊 Введи название лекарства:", reply_markup=cancel_menu())

    # ── Обхваты: выбор части тела ──
    elif data == "measure_add":
        bot.answer_callback_query(call.id)
        kb2 = types.InlineKeyboardMarkup(row_width=2)
        for key, label in MEASUREMENTS_LIST:
            kb2.add(types.InlineKeyboardButton(label, callback_data=f"measure_part:{key}"))
        bot.send_message(cid, "📏 Что измеряем?", reply_markup=kb2)

    elif data.startswith("measure_part:"):
        part_key = data.split(":")[1]
        bot.answer_callback_query(call.id)
        label = dict(MEASUREMENTS_LIST).get(part_key, part_key)
        set_state(cid, "waiting_measurement", extra=part_key)
        bot.send_message(cid,
            f"📏 *{label}*\n\nВведи значение в сантиметрах:",
            parse_mode="Markdown", reply_markup=cancel_menu())

    # ── Супер-сет выбор ──
    elif data.startswith("superset:"):
        name = data[9:]
        bot.answer_callback_query(call.id)
        text_ss = build_superset_text(name)
        # Кнопка добавить в избранное
        kb_ss = types.InlineKeyboardMarkup()
        bot.send_message(cid, text_ss, parse_mode="Markdown", reply_markup=kb_ss,
                         disable_web_page_preview=True)

    # ── Напоминания: добавить ──
    elif data == "reminder_add":
        bot.answer_callback_query(call.id)
        set_state(cid, "reminder_add_text")
        bot.send_message(cid,
            "⏰ *Новое напоминание*\n\nВведи текст напоминания\n(например: *Взвеситься*):",
            parse_mode="Markdown", reply_markup=cancel_menu())

    # ── Напоминания: удалить ──
    elif data.startswith("reminder_del:"):
        rid = int(data.split(":")[1])
        delete_user_reminder(cid, rid)
        bot.answer_callback_query(call.id, "Напоминание удалено")
        rows = get_user_reminders(cid)
        kb_rem = types.InlineKeyboardMarkup()
        kb_rem.add(types.InlineKeyboardButton("➕ Добавить напоминание", callback_data="reminder_add"))
        for r_id, rtxt, rh, rm in rows:
            kb_rem.add(types.InlineKeyboardButton(
                f"🗑 {rh:02d}:{rm:02d} {rtxt}", callback_data=f"reminder_del:{r_id}"))
        bot.edit_message_text(build_reminders_list(cid), cid, call.message.message_id,
                              parse_mode="Markdown", reply_markup=kb_rem)

    # ── Плато-советы ──
    elif data == "plateau_tips":
        bot.answer_callback_query(call.id)
        bot.send_message(cid, build_plateau_plan(), parse_mode="Markdown")

    # ── Добавить в избранное (из калькулятора) ──
    elif data.startswith("fav_add:"):
        dish = data[8:]
        add_favorite_dish(cid, dish)
        bot.answer_callback_query(call.id, f"⭐ {dish} добавлен в избранное!")

    # ── Режим тренировок (домашние) ──
    elif data.startswith("hw_mode:"):
        mode = int(data.split(":")[1])
        save_profile(cid, home_workouts=mode)
        labels = {0: "🏋️ Только зал", 1: "🏠+🏋️ Зал + домашние", 2: "🏠 Только домашние"}
        bot.answer_callback_query(call.id, f"✅ {labels[mode]}")
        kb_hw = types.InlineKeyboardMarkup()
        kb_hw.add(
            types.InlineKeyboardButton("🏋️ Только зал" + (" ✅" if mode==0 else ""), callback_data="hw_mode:0"),
            types.InlineKeyboardButton("🏠+🏋️ Зал + дома" + (" ✅" if mode==1 else ""), callback_data="hw_mode:1"),
        )
        kb_hw.add(types.InlineKeyboardButton("🏠 Только дома" + (" ✅" if mode==2 else ""), callback_data="hw_mode:2"))
        try:
            bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=kb_hw)
        except Exception:
            pass

    # ── Кардио: старт/стоп ──
    elif data == "cardio_start":
        start_cardio_timer(cid)
        bot.answer_callback_query(call.id, "▶️ Начато!")
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⏹ Остановить", callback_data="cardio_stop"))
        bot.edit_message_text("🏃 *Кардио идёт!* Нажми Остановить когда закончишь.",
                              cid, call.message.message_id, parse_mode="Markdown", reply_markup=kb)

    elif data == "cardio_stop":
        result = stop_cardio_timer(cid)
        bot.answer_callback_query(call.id)
        if result:
            minutes, kcal = result
            bot.send_message(cid,
                f"⏹ *Кардио завершено!*\n\n⏱ Время: *{minutes} мин*\n🔥 Сожжено: *~{kcal} ккал*\n\n"
                f"_Записано в дневник._",
                parse_mode="Markdown", reply_markup=main_menu(cid))
            add_xp(cid, "cardio", 15)
        else:
            bot.send_message(cid, "Активной сессии нет.")

    # ── Шаблоны еды ──
    elif data.startswith("tpl_apply:"):
        name = data[10:]
        total = apply_meal_template(cid, name)
        bot.answer_callback_query(call.id, f"✅ Добавлено!")
        bot.send_message(cid, f"✅ Шаблон *«{name}»* добавлен в дневник — *{total} ккал*", parse_mode="Markdown")

    elif data.startswith("tpl_del:"):
        name = data[8:]
        delete_meal_template(cid, name)
        bot.answer_callback_query(call.id, "🗑 Удалено")
        kb_tpl = types.InlineKeyboardMarkup()
        for tname, items in get_meal_templates(cid):
            total = sum(c for _, c in items)
            kb_tpl.add(
                types.InlineKeyboardButton(f"▶️ {tname} ({total}ккал)", callback_data=f"tpl_apply:{tname}"),
                types.InlineKeyboardButton("🗑", callback_data=f"tpl_del:{tname}")
            )
        kb_tpl.add(types.InlineKeyboardButton("➕ Создать шаблон", callback_data="tpl_create"))
        try:
            bot.edit_message_text(build_templates_menu(cid), cid, call.message.message_id,
                                  parse_mode="Markdown", reply_markup=kb_tpl)
        except Exception:
            pass

    elif data == "tpl_create":
        bot.answer_callback_query(call.id)
        set_state(cid, "tpl_create_name")
        bot.send_message(cid, "📋 Введи название шаблона (например: *«Мой завтрак»*):",
                         parse_mode="Markdown", reply_markup=cancel_menu())

    # ── Партнёр ──
    elif data == "partner_link":
        bot.answer_callback_query(call.id)
        set_state(cid, "partner_link_code")
        bot.send_message(cid,
            f"👫 *Подключить партнёра*\n\nТвой код: `PAIR{cid}`\n\nВведи код партнёра:",
            parse_mode="Markdown", reply_markup=cancel_menu())

    elif data == "partner_refresh":
        bot.answer_callback_query(call.id)
        bot.send_message(cid, build_partner_comparison(cid), parse_mode="Markdown")

    elif data == "partner_unlink":
        conn = sqlite3.connect("weight_tracker.db")
        conn.execute("DELETE FROM partner_links WHERE user_id=?", (cid,))
        conn.commit(); conn.close()
        bot.answer_callback_query(call.id, "Партнёр отвязан")
        bot.send_message(cid, "👫 Партнёр отвязан.", reply_markup=main_menu(cid))

    # ── Челленджи ──
    elif data.startswith("challenge_start:"):
        ch_id = data[16:]
        start_challenge(cid, ch_id)
        ch = next((c for c in WEEKLY_CHALLENGES if c["id"] == ch_id), None)
        bot.answer_callback_query(call.id, "🎯 Начато!")
        if ch:
            bot.send_message(cid,
                f"🏆 *Челлендж начат!*\n\n{ch['name']}\n_{ch['desc']}_\n\n+{ch['xp']} XP по завершению 💪",
                parse_mode="Markdown")

    # ── Вода в мл (кнопки) ──
    elif data.startswith("water_ml:"):
        val = data.split(":")[1]
        bot.answer_callback_query(call.id)
        if val == "custom":
            set_state(cid, "waiting_water_ml")
            bot.send_message(cid, "💧 Введи количество мл (например: `350`):",
                             parse_mode="Markdown", reply_markup=cancel_menu())
        else:
            ml = int(val)
            add_water_ml(cid, ml)
            bot.edit_message_text(build_water_ml_status(cid) + f"\n\n✅ +{ml} мл добавлено",
                                  cid, call.message.message_id, parse_mode="Markdown")

    # ── Штрихкод: добавить в дневник ──
    elif data.startswith("barcode_add:"):
        parts = data.split(":")
        grams = int(parts[2])
        name  = parts[3]
        kcal_per100 = int(parts[4])
        kcal = round(kcal_per100 * grams / 100)
        add_food_diary(cid, name, grams, kcal)
        update_streak(cid)
        add_xp(cid, XP_REWARDS.get("log_food", 2))
        bot.answer_callback_query(call.id, f"✅ {name} {grams}г = {kcal} ккал записано!")
        bot.edit_message_text(f"✅ *{name}* {grams}г = *{kcal} ккал* — записано в дневник!",
                              cid, call.message.message_id, parse_mode="Markdown")

    # ── Стресс: выбор уровня ──
    elif data.startswith("stress_log:"):
        level = int(data.split(":")[1])
        bot.answer_callback_query(call.id)
        set_state(cid, "waiting_stress_note", extra=str(level))
        emoji_stress = "😌" if level <= 3 else ("😐" if level <= 6 else "😰")
        bot.send_message(cid,
            f"{emoji_stress} Уровень стресса *{level}/10* выбран.\n\nДобавь заметку (или отправь «-» чтобы пропустить):",
            parse_mode="Markdown", reply_markup=cancel_menu())

    # ── Цикл: начало ──
    elif data == "cycle_start":
        bot.answer_callback_query(call.id)
        log_cycle_start(cid)
        result = get_cycle_phase(cid)
        if result:
            day, phase, text_phase = result
            bot.send_message(cid, f"🩸 Начало цикла отмечено!\n\n*День 1*\n\n{text_phase}",
                             parse_mode="Markdown")
        else:
            bot.send_message(cid, "🩸 Начало цикла записано!")

    # ── Сценарий прогноза ──
    elif data.startswith("scenario:"):
        scenario = data.split(":", 1)[1]
        bot.answer_callback_query(call.id)
        bot.send_message(cid, build_scenario_forecast(cid, scenario), parse_mode="Markdown")

    # ── Мини-игра: ответ ──
    elif data.startswith("quiz_ans:"):
        parts = data.split(":")
        chosen = int(parts[1])
        correct = int(parts[2])
        bot.answer_callback_query(call.id)
        if chosen == correct:
            add_xp(cid, 5)
            bot.send_message(cid, f"✅ *Правильно!* {correct} ккал\n\n+5 XP 🎉\n\nЕщё раз?",
                             parse_mode="Markdown",
                             reply_markup=types.InlineKeyboardMarkup().add(
                                 types.InlineKeyboardButton("🎮 Новый вопрос", callback_data="quiz_new")))
        else:
            bot.send_message(cid, f"❌ Неверно! Правильный ответ: *{correct} ккал*\n\nПопробуй ещё!",
                             parse_mode="Markdown",
                             reply_markup=types.InlineKeyboardMarkup().add(
                                 types.InlineKeyboardButton("🎮 Новый вопрос", callback_data="quiz_new")))

    # ── Мини-игра: новый вопрос ──
    elif data == "quiz_new":
        bot.answer_callback_query(call.id)
        msg, kb_quiz = build_kcal_quiz_message(cid)
        bot.send_message(cid, msg, parse_mode="Markdown", reply_markup=kb_quiz)

    # ── Привычки: отметить ──
    elif data.startswith("habit:"):
        habit_key = data.split(":", 1)[1]
        done_flag = toggle_habit(cid, habit_key)
        bot.answer_callback_query(call.id, "✅ Отмечено!" if done_flag else "↩️ Снято")
        kb_habits = build_habits_keyboard(cid)
        done = get_habits_today(cid)
        try:
            bot.edit_message_text(
                f"✔️ *Трекер привычек — сегодня*\n\nВыполнено: *{len(done)}/{len(DEFAULT_HABITS)}*\n\nНажми чтобы отметить:",
                cid, call.message.message_id, parse_mode="Markdown", reply_markup=kb_habits)
        except Exception:
            pass

    # ── Привычки: статистика ──
    elif data == "habits_stats":
        bot.answer_callback_query(call.id)
        bot.send_message(cid, build_habits_stats(cid), parse_mode="Markdown")

    # ── Заметки: выполнено ──
    elif data.startswith("note_done:"):
        nid = int(data.split(":")[1])
        conn = sqlite3.connect("weight_tracker.db")
        conn.execute("UPDATE quick_notes SET done=1 WHERE id=?", (nid,))
        conn.commit(); conn.close()
        bot.answer_callback_query(call.id, "✅ Выполнено!")
        result = build_notes_menu(cid)
        if isinstance(result, tuple):
            txt, kb_notes = result
            try:
                bot.edit_message_text(txt, cid, call.message.message_id, parse_mode="Markdown", reply_markup=kb_notes)
            except Exception:
                pass

    # ── Заметки: очистить выполненные ──
    elif data == "notes_clear":
        conn = sqlite3.connect("weight_tracker.db")
        conn.execute("DELETE FROM quick_notes WHERE user_id=? AND done=1", (cid,))
        conn.commit(); conn.close()
        bot.answer_callback_query(call.id, "🗑️ Очищено")
        result = build_notes_menu(cid)
        if isinstance(result, tuple):
            txt, kb_notes = result
            try:
                bot.edit_message_text(txt, cid, call.message.message_id, parse_mode="Markdown", reply_markup=kb_notes)
            except Exception:
                pass
        else:
            try:
                bot.edit_message_text(result, cid, call.message.message_id, parse_mode="Markdown")
            except Exception:
                pass

    # ── Помощь: раздел ──
    elif data.startswith("help_section:"):
        section = data.split(":")[1]
        bot.answer_callback_query(call.id)
        section_texts = {
            "food": ("🍽️ *Питание — что умеет бот*\n\n"
                     "• Рацион на день и завтра с расчётом КБЖУ\n• Дневник питания — вводи вручную или фото\n"
                     "• Штрихкод → КБЖУ из Open Food Facts\n• Шаблоны любимых приёмов пищи\n"
                     "• Меню на неделю + список покупок\n• Избранные блюда\n• Рецепты, полуфабрикаты, читмил\n"
                     "• Калькулятор КБЖУ: просто напиши `гречка 200`\n• Отслеживание воды в мл"),
            "workout": ("🏋️ *Тренировки — что умеет бот*\n\n"
                        "• Персональный план тренировок А/Б/В/К\n• Домашние тренировки (3 режима)\n"
                        "• 8-недельная программа с прогрессией\n• Разминка и заминка\n• Супер-сеты\n"
                        "• Таймер отдыха и кардио-таймер\n• Дневник упражнений + прогрессия весов\n"
                        "• Расчёт 1RM: `/1rm жим лёжа 100 5`\n• Виртуальный тренер с советами"),
            "body": ("📊 *Тело — что умеет бот*\n\n"
                     "• График веса с анализом тренда\n• Трекер шагов (ручной ввод или импорт)\n"
                     "• Вода: стаканы и мл, норма по весу\n• Обхваты тела (талия, грудь, бёдра...)\n"
                     "• InBody — загрузи PDF, бот разберёт\n• Фото-прогресс (#прогресс в подписи)\n"
                     "• Ачивки и достижения\n• Серия дней без пропусков\n• Партнёрский режим"),
            "analytics": ("📈 *Аналитика — что умеет бот*\n\n"
                          "• Инфографика прогресса (ASCII)\n• Прогноз даты цели\n"
                          "• Прогноз «Что если» (3 сценария)\n• ИИ-анализ недели (Anthropic API)\n"
                          "• Корреляции: сон↔вес, шаги↔вес\n• Отчёты за неделю и месяц\n"
                          "• XP, уровни, еженедельные челленджи\n• Экспорт CSV всех данных"),
            "health": ("😴 *Здоровье — что умеет бот*\n\n"
                       "• Трекер сна с анализом качества\n• Дневник стресса 1–10\n"
                       "• Менструальный цикл и фазы\n• HRV и пульс покоя\n"
                       "• Давление и пульс\n• Режим болезни\n"
                       "• Импорт из Apple Health / Google Fit\n• Напоминания по расписанию"),
            "commands": ("⚡ *Все быстрые команды*\n\n"
                         "`/w 105.7` — вес\n`/s 8500` — шаги\n`/water 3` — вода\n"
                         "`/hrv 65 55` — HRV и пульс\n`/1rm жим 100 5` — 1RM\n"
                         "`/note текст` — заметка\n`/summary` — сводка дня\n"
                         "`/receipt` — анализ чека\n`/partner` — парный режим\n\n"
                         "*Умный ввод:*\n`гречка 200` — быстрый калькулятор\n"
                         "Голосовое → бот поймёт команду\n"
                         "Фото еды → ИИ считает калории\nФото #прогресс → архив фото"),
        }
        text_help = section_texts.get(section, "Раздел не найден")
        bot.send_message(cid, text_help, parse_mode="Markdown")

    # ── Интервальное голодание ──
    elif data.startswith("if_start:"):
        protocol = data.split(":")[1]
        start_fasting(cid, protocol)
        bot.answer_callback_query(call.id, f"⏳ Голодание {protocol} начато!")
        msg, kb_if = build_fasting_status(cid)
        try:
            bot.edit_message_text(msg, cid, call.message.message_id, parse_mode="Markdown", reply_markup=kb_if)
        except Exception:
            bot.send_message(cid, msg, parse_mode="Markdown", reply_markup=kb_if)

    elif data == "if_stop":
        stop_fasting(cid)
        bot.answer_callback_query(call.id, "✅ Голодание завершено!")
        bot.send_message(cid, "✅ Голодание завершено! Можно есть. Хорошая работа 💪")

    elif data == "if_history":
        bot.answer_callback_query(call.id)
        bot.send_message(cid, build_fasting_history(cid), parse_mode="Markdown")

    # ── Алкоголь ──
    elif data.startswith("alcohol:"):
        drink_key = data.split(":", 1)[1]
        log_alcohol(cid, drink_key)
        info = ALCOHOL_UNITS.get(drink_key, {})
        bot.answer_callback_query(call.id, f"Записано: {info.get('label', drink_key)}")
        msg, kb_alc = build_alcohol_menu(cid)
        try:
            bot.edit_message_text(msg, cid, call.message.message_id, parse_mode="Markdown", reply_markup=kb_alc)
        except Exception:
            pass

    elif data == "alcohol_history":
        bot.answer_callback_query(call.id)
        bot.send_message(cid, build_alcohol_history(cid), parse_mode="Markdown")

    # ── Избранные блюда: быстрое добавление ──
    elif data.startswith("fav_add:"):
        parts = data.split(":")
        if len(parts) >= 6:
            f_name = parts[1]
            f_kcal = float(parts[2]) if parts[2] else 0
            f_prot = float(parts[3]) if parts[3] else 0
            f_fat  = float(parts[4]) if parts[4] else 0
            f_carb = float(parts[5]) if parts[5] else 0
            today  = date.today().isoformat()
            conn = sqlite3.connect("weight_tracker.db")
            conn.execute("INSERT INTO food_log (user_id, date, meal, name, kcal, protein, fat, carbs) VALUES (?,?,?,?,?,?,?,?)",
                         (cid, today, "snack", f_name, f_kcal, f_prot, f_fat, f_carb))
            conn.commit(); conn.close()
            add_xp(cid, XP_REWARDS.get("food_log", 2))
            bot.answer_callback_query(call.id, f"✅ {f_name[:20]} добавлено!")
        else:
            bot.answer_callback_query(call.id, "Ошибка данных")

    # ── Разминка ──
    elif data.startswith("warmup:"):
        muscle = data.split(":", 1)[1]
        bot.answer_callback_query(call.id)
        bot.send_message(cid, build_warmup(muscle), parse_mode="Markdown")

    # ── Суперсеты ──
    elif data.startswith("superset:"):
        template = data.split(":", 1)[1]
        bot.answer_callback_query(call.id)
        bot.send_message(cid, build_superset_plan(template), parse_mode="Markdown")

    # ── Пульс покоя ──
    elif data == "set_resting_hr":
        bot.answer_callback_query(call.id)
        bot.send_message(cid, "Введи пульс покоя (уд/мин), например `58`:", parse_mode="Markdown")
        set_state(cid, "waiting_resting_hr")

    else:
        bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    cid = message.chat.id
    state, extra = get_state(cid)
    try:
        # Берём фото наилучшего качества
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        import requests as _req
        token = bot.token
        url = f"https://api.telegram.org/file/bot{token}/{file_info.file_path}"
        r = _req.get(url, timeout=15)
        image_bytes = r.content

        caption = (message.caption or "").lower().strip()

        # Режим: сохранение фото-прогресса
        if "#прогресс" in caption or "#progress" in caption or state == "waiting_body_photo":
            note = caption.replace("#прогресс","").replace("#progress","").strip()
            save_body_photo(cid, photo.file_id, note)
            set_state(cid, "idle")
            photos = get_body_photos(cid, 2)
            count_msg = f"\n\nВсего фото: {len(get_body_photos(cid, 100))}"
            bot.send_message(cid, f"📷 Фото прогресса сохранено!" + (f"\nЗаметка: _{note}_" if note else "") + count_msg,
                             parse_mode="Markdown", reply_markup=main_menu(cid))
            return

        # Режим: чек из магазина
        if any(w in caption for w in ["чек", "чека", "магазин", "покупки"]) or state == "waiting_receipt_photo":
            bot.send_message(cid, "🧾 Анализирую чек...", parse_mode="Markdown")
            result = analyze_receipt_photo(image_bytes)
            if result:
                bot.send_message(cid, result, parse_mode="Markdown")
            else:
                bot.send_message(cid,
                    "🧾 Не удалось распознать чек.\n\n"
                    "💡 Убедись что:\n• Фото чёткое\n• Чек хорошо освещён\n• Текст читаем")
            set_state(cid, "idle")
            return

        # Режим: анализ еды (по умолчанию для любого фото)
        bot.send_message(cid, "🍽️ Анализирую фото еды...", parse_mode="Markdown")
        result = analyze_food_photo(image_bytes)
        if result:
            # Пытаемся вытащить ккал из ответа для кнопки "добавить в дневник"
            import re as _re
            kcal_match = _re.search(r"Калории.*?~?(\d+)", result)
            kb_photo = types.InlineKeyboardMarkup()
            if kcal_match:
                kcal_val = int(kcal_match.group(1))
                kb_photo.add(types.InlineKeyboardButton(
                    f"📝 Записать ~{kcal_val} ккал в дневник",
                    callback_data=f"add_to_diary:фото еды:{kcal_val}"))
            bot.send_message(cid, result, parse_mode="Markdown", reply_markup=kb_photo)
        else:
            bot.send_message(cid,
                "🍽️ *Анализ фото еды*\n\n"
                "Сервис недоступен. Убедись что переменная `ANTHROPIC_API_KEY` настроена.\n\n"
                "💡 Пока можешь вводить вручную: *гречка 200*",
                parse_mode="Markdown")
    except Exception as e:
        bot.send_message(cid, "Не удалось обработать фото. Попробуй ещё раз.")


@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    cid = message.chat.id
    try:
        file_info = bot.get_file(message.voice.file_id)
        import tempfile, requests as _requests
        token = bot.token
        url = f"https://api.telegram.org/file/bot{token}/{file_info.file_path}"
        r = _requests.get(url, timeout=15)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            f.write(r.content)
            ogg_path = f.name
        recognized = transcribe_voice_ogg(ogg_path)
        try: os.unlink(ogg_path)
        except: pass
        if not recognized:
            bot.send_message(cid,
                "🎤 *Голосовой ввод*\n\n"
                "Распознавание речи недоступно на этом сервере.\n\n"
                "💡 *Используй быстрые команды:*\n"
                "`/w 105.7` — вес\n"
                "`/s 8500` — шаги\n"
                "`/water 2` — вода (стаканы)\n"
                "Или просто напиши: `гречка 200`",
                parse_mode="Markdown")
            return
        # Распознано — парсим
        parsed = parse_voice_command(recognized)
        if parsed:
            ptype = parsed["type"]
            if ptype == "weight":
                w = parsed["value"]
                add_weight(cid, w)
                save_profile(cid, current_weight=w)
                bot.send_message(cid, f"✅ *Вес {w} кг* — записан! (голосовой ввод 🎤)",
                                 parse_mode="Markdown", reply_markup=main_menu(cid))
            elif ptype == "steps":
                s = parsed["value"]
                log_steps(cid, s)
                bot.send_message(cid, f"✅ *{s:,} шагов* — записано! (голосовой ввод 🎤)".replace(",", " "),
                                 parse_mode="Markdown", reply_markup=main_menu(cid))
            elif ptype == "water":
                cups = parsed["value"]
                log_water(cid, cups)
                bot.send_message(cid, f"✅ *{cups} стакан(а) воды* — записано! (голосовой ввод 🎤)",
                                 parse_mode="Markdown", reply_markup=main_menu(cid))
            elif ptype == "food":
                prod = parsed["product"]
                grams = parsed["grams"]
                kcal = round(KCAL_PER_100G[prod] * grams / 100)
                kb_v = types.InlineKeyboardMarkup()
                kb_v.add(types.InlineKeyboardButton("📝 Добавить в дневник",
                    callback_data=f"add_to_diary:{prod}:{grams}"))
                bot.send_message(cid,
                    f"🎤 *{prod}* {grams}г = *{kcal} ккал*\n\nДобавить в дневник питания?",
                    parse_mode="Markdown", reply_markup=kb_v)
        else:
            bot.send_message(cid,
                f"🎤 Распознано: «{recognized}»\n\n"
                "Не смог понять команду. Попробуй:\n"
                "• «Вес 105»\n• «Прошёл 8000 шагов»\n• «Выпил 3 стакана»\n• «Гречка 200»",
                parse_mode="Markdown")
    except Exception as e:
        bot.send_message(cid, "🎤 Не удалось обработать голосовое сообщение. Попробуй текстом.")


@bot.message_handler(func=lambda m: True)
def router(message):
    cid  = message.chat.id
    text = message.text.strip() if message.text else ""
    state, extra = get_state(cid)
    if text == "❌ Отмена":
        set_state(cid, "idle")
        bot.send_message(cid, "Отменено.", reply_markup=main_menu(cid))
        return

    # Кнопка возврата в главное меню из подменю
    if text == "🏠 Главное меню":
        set_state(cid, "idle")
        bot.send_message(cid, "Главное меню:", reply_markup=main_menu(cid))
        return

    # Категории главного меню → открываем подменю
    if text == "🍽️ Питание":
        bot.send_message(cid, "🍽️ *Питание* — выбери раздел:", parse_mode="Markdown", reply_markup=menu_pitanie())
        return
    if text == "🏋️ Тренировки":
        bot.send_message(cid, "🏋️ *Тренировки* — выбери раздел:", parse_mode="Markdown", reply_markup=menu_trenirovki())
        return
    if text == "📊 Моё тело":
        bot.send_message(cid, "📊 *Моё тело* — выбери раздел:", parse_mode="Markdown", reply_markup=menu_telo())
        return
    if text == "📈 Аналитика":
        bot.send_message(cid, "📈 *Аналитика* — выбери раздел:", parse_mode="Markdown", reply_markup=menu_analitika())
        return
    if text == "😴 Здоровье":
        bot.send_message(cid, "😴 *Здоровье* — выбери раздел:", parse_mode="Markdown", reply_markup=menu_zdorovie())
        return
    if text == "⚙️ Настройки":
        bot.send_message(cid, "⚙️ *Настройки* — выбери раздел:", parse_mode="Markdown", reply_markup=menu_nastroyki())
        return

    # Онбординг
    if state in [s[0] for s in ONBOARDING_STEPS]:
        handle_onboarding(cid, state, text, extra)
        return

    # Если пользователь что-то пишет пока "спит" — напомнить
    if state == "waiting_wake" and text not in ("⏰ Проснулся", "❌ Отмена"):
        bot.send_message(cid,
            "😴 Ты в режиме сна.\n\nКогда проснёшься — нажми *«⏰ Проснулся»*.\n"
            "Или нажми *«❌ Отмена»* чтобы выйти из режима сна.",
            parse_mode="Markdown", reply_markup=cancel_menu())
        return

    # ── Ручной ввод времени сна ──
    if state == "manual_sleep_entry":
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
    if state == "rate_sleep_quality":
        try:
            quality = int(text); assert 1 <= quality <= 5
            parts      = extra.split("|")
            sleep_time = parts[0] if len(parts) > 0 else "23:00"
            wake_time  = parts[1] if len(parts) > 1 else "07:00"
            duration   = float(parts[2]) if len(parts) > 2 else 7.0
            analysis   = analyze_sleep(duration, quality)
            log_sleep(cid, sleep_time, wake_time, duration, quality)
            save_profile(cid, fatigue=analysis["fat_adj"])
            set_state(cid, "idle")
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

    # Ввод веса
    if state == "waiting_weight":
        try:
            w = float(text.replace(",", "."))
            if not (30 < w < 300):
                raise ValueError("out of range")
        except Exception:
            bot.send_message(cid, "Введи число, например: *105.7*", parse_mode="Markdown")
            return

        # Сохраняем
        add_weight(cid, w)
        save_profile(cid, current_weight=w)
        set_state(cid, "idle")

        # Обновляем стрик
        try:
            update_streak(cid)
        except Exception:
            pass

        # Ачивки (старая система)
        try:
            new_ach = check_and_unlock(cid)
            if new_ach:
                for k in new_ach:
                    a_info = ACHIEVEMENTS.get(k, {})
                    bot.send_message(cid,
                        f"🎉 *{a_info.get('emoji','')} {a_info.get('name','Ачивка')}!*\n{a_info.get('desc','')}",
                        parse_mode="Markdown")
        except Exception:
            pass

        wd = get_weights(cid)
        profile = get_profile(cid)
        target = (profile.get("target_weight") or 70.0) if profile else 70.0

        # Начальный вес
        start_w = wd[0][0] if wd else w
        loss = round(start_w - w, 2)
        remain = round(w - target, 1)
        try:
            pct = round((start_w - w) / (start_w - target) * 100, 1) if abs(start_w - target) > 0.01 else 100.0
        except Exception:
            pct = 0.0

        # Тренд
        if len(wd) >= 2:
            prev_w = wd[-2][0]
            diff = round(w - prev_w, 2)
            if diff < -0.05:
                trend = f"📉 {abs(diff)} кг меньше, чем в прошлый раз"
            elif diff > 0.05:
                trend = f"📈 +{diff} кг больше, чем в прошлый раз"
            else:
                trend = "➡️ Вес не изменился с прошлого раза"
        else:
            trend = "🆕 Первая запись веса"

        resp = (f"✅ Вес *{w} кг* сохранён! ({now_samara().strftime('%d.%m.%Y')})\n\n"
                f"{trend}\n"
                f"📉 Сброшено от старта: *{loss} кг*\n"
                f"🎯 До цели ({target} кг): *{remain} кг* ({pct}%)")

        # Анализ прогресса
        try:
            if len(wd) >= 3:
                a = analyze_progress(wd)
                if a and a.get("advice"):
                    resp += f"\n\n─────────────\n🤖 {a['advice']}"
                    if a.get("cal_change", 0) != 0:
                        d = "увеличен" if a["cal_change"] > 0 else "снижен"
                        resp += f"\n📋 Рацион {d} на *{abs(a['cal_change'])} ккал*."
        except Exception:
            pass

        # Мотивационная цитата
        try:
            resp += f"\n\n{random.choice(MOTIVATIONAL_QUOTES)}"
        except Exception:
            pass

        # Прогноз даты
        try:
            if len(wd) >= 4:
                prediction = predict_goal_date(wd, target)
                if prediction:
                    resp += (f"\n\n📅 *Прогноз:* {prediction['rate_week']} кг/нед → "
                             f"цель *{prediction['date']}* (~{prediction['weeks']} нед.)")
        except Exception:
            pass

        bot.send_message(cid, resp, parse_mode="Markdown", reply_markup=main_menu(cid))

        # Ачивки (новая система)
        try:
            new_ach2 = check_and_unlock_achievements(cid)
            for name, desc, _ in new_ach2:
                bot.send_message(cid, f"🎉 *Новая ачивка: {name}!*\n_{desc}_", parse_mode="Markdown")
        except Exception:
            pass
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

    # ── Самочувствие: настроение ──
    if state == "wellbeing_mood":
        try:
            mood = int(text); assert 1 <= mood <= 5
            set_state(cid, "wellbeing_energy", extra=str(mood))
            m2 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
            m2.add(*[types.KeyboardButton(str(i)) for i in range(1,6)])
            m2.add(types.KeyboardButton("\u274c Отмена"))
            bot.send_message(cid,
                "\U0001f4aa Оцени *уровень энергии* сегодня:\n\n"
                "1 — Нет сил \U0001f634\n2 — Вялый\n3 — Нормально\n"
                "4 — Бодрый\n5 — Энергичный \u26a1",
                parse_mode="Markdown", reply_markup=m2)
        except Exception:
            bot.send_message(cid, "Введи число от 1 до 5")
        return

    # ── Самочувствие: энергия ──
    if state == "wellbeing_energy":
        try:
            energy = int(text); assert 1 <= energy <= 5
            set_state(cid, "wellbeing_stress", extra=f"{extra}|{energy}")
            m2 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
            m2.add(*[types.KeyboardButton(str(i)) for i in range(1,6)])
            m2.add(types.KeyboardButton("\u274c Отмена"))
            bot.send_message(cid,
                "\U0001f630 Оцени *уровень стресса* сегодня:\n\n"
                "1 — Нет стресса \U0001f60c\n2 — Слабый\n3 — Умеренный\n"
                "4 — Высокий\n5 — Очень высокий \U0001f624",
                parse_mode="Markdown", reply_markup=m2)
        except Exception:
            bot.send_message(cid, "Введи число от 1 до 5")
        return

    # ── Самочувствие: стресс (финал) ──
    if state == "wellbeing_stress":
        try:
            stress = int(text); assert 1 <= stress <= 5
            parts  = extra.split("|")
            mood   = int(parts[0]); energy = int(parts[1]) if len(parts)>1 else 3
            log_wellbeing(cid, mood, energy, stress)
            current, best = update_streak(cid)
            set_state(cid, "idle")
            notes = []
            if stress >= 4:
                notes.append("\U0001f630 *Высокий стресс* повышает кортизол — жир уходит медленнее. Сон до 23:00 особенно важен.")
            if energy <= 2:
                notes.append("\U0001f634 *Низкая энергия* — возможно, недоспал или мало ел. Проверь рацион.")
            if mood >= 4 and energy >= 4:
                notes.append("\U0001f31f *Отличное состояние* — идеальный день для хорошей тренировки!")
            streak_note = f"\n\U0001f525 Серия: *{current} дней подряд!*" + (" \U0001f3c6 Новый рекорд!" if current == best and current > 1 else "")
            bot.send_message(cid,
                f"\u2705 *Самочувствие записано!*\n\n"
                f"\U0001f60a Настроение: {chr(11088)*mood}\n"
                f"\U0001f4aa Энергия: {chr(9889)*energy}\n"
                f"\U0001f630 Стресс: {chr(128308)*stress}\n"
                + ("\n" + "\n".join(notes) if notes else "") + streak_note,
                parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "Введи число от 1 до 5")
        return

    # ── Журнал весов: название упражнения ──
    if state == "log_exercise_name":
        exercise = text
        set_state(cid, "log_exercise_weight", extra=exercise)
        bot.send_message(cid,
            f"Упражнение: *{exercise}*\n\nВведи через пробел: *вес повторения подходы*\n"
            "Например: *20 12 4* (20кг × 12 повт. × 4 подх.)\n"
            "Без веса: *0 15 3*",
            parse_mode="Markdown", reply_markup=cancel_menu())
        return

    # ── Журнал весов: запись результата ──
    if state == "log_exercise_weight":
        try:
            parts    = text.strip().split()
            assert len(parts) == 3
            w_kg     = float(parts[0].replace(",",".")); reps = int(parts[1]); sets = int(parts[2])
            exercise = extra
            log_exercise_weight(cid, exercise, w_kg, reps, sets)
            current, best = update_streak(cid)
            set_state(cid, "idle")
            history  = get_exercise_history(cid, exercise)
            progress = ""
            if len(history) >= 2:
                diff = round(w_kg - history[-2][0], 1)
                if diff > 0:   progress = f"\n\n\U0001f4c8 *+{diff} кг* к прошлой тренировке! \U0001f4aa"
                elif diff < 0: progress = f"\n\nНа {abs(diff)} кг меньше чем прошлый раз."
                else:          progress = "\n\nВес такой же — попробуй добавить повторение."
            bot.send_message(cid,
                f"\u2705 *{exercise}*\n{w_kg}кг × {reps} повт. × {sets} подх. — записано!{progress}\n\n\U0001f525 Серия: *{current} дней*",
                parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "Введи 3 числа: *вес повторения подходы*\nНапример: *20 12 4*", parse_mode="Markdown")
        return

    # ── Дневник: выбор приёма пищи ──
    if state == "diary_choose_meal":
        meals_text = ["🍳 Завтрак","🍗 Обед","🍎 Полдник","🌙 Ужин","🍵 Перекус"]
        if text in meals_text:
            set_state(cid, "diary_enter_food", extra=text)
            bot.send_message(cid,
                f"Приём: *{text}*\n\nВведи продукт и граммы через пробел:\n"
                "Например: *куриная грудка 200*\nИли: *гречка 65*",
                parse_mode="Markdown", reply_markup=cancel_menu())
        else:
            bot.send_message(cid, "Выбери приём пищи из кнопок.")
        return

    # ── Дневник: ввод продукта ──
    if state == "diary_enter_food":
        try:
            parts   = text.strip().rsplit(" ", 1)
            assert len(parts) == 2
            product = parts[0].lower().strip()
            grams   = float(parts[1].replace(",",".")); assert 0 < grams < 5000
            meal    = extra
            kcal_p  = KCAL_PER_100G.get(product)
            if not kcal_p:
                matches = [k for k in KCAL_PER_100G if product in k]
                if matches: product = matches[0]; kcal_p = KCAL_PER_100G[product]
                else:
                    bot.send_message(cid, f"\u2753 *{product}* не найден в базе. Попробуй ввести точнее.", parse_mode="Markdown")
                    return
            kcal = round(kcal_p * grams / 100)
            add_food_entry(cid, meal, product, grams, kcal)
            update_streak(cid)
            set_state(cid, "idle")
            total   = get_kcal_today(cid)
            profile = get_profile(cid)
            target_kcal = get_user_plan(cid, profile)["calories"] if profile else 2000
            remain  = target_kcal - total
            status  = "\u2705 Норма!" if abs(remain)<100 else (f"\u2b07\ufe0f Ещё {remain} ккал" if remain>0 else f"\u26a0\ufe0f Превышение на {abs(remain)} ккал")
            bot.send_message(cid,
                f"\u2705 Записано в {meal}:\n{product} {grams}г = *{kcal} ккал*\n\n"
                f"\U0001f525 Сегодня итого: *{total} / {target_kcal} ккал*\n{status}",
                parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "Введи продукт и граммы:\nНапример: *куриная грудка 200*", parse_mode="Markdown")
        return

    # ── Калькулятор калорий ──
    if state == "calc_product":
        try:
            parts   = text.strip().rsplit(" ", 1)
            assert len(parts) == 2
            product = parts[0].lower().strip()
            grams   = float(parts[1].replace(",",".")); assert 0 < grams < 5000
            kcal_p  = KCAL_PER_100G.get(product)
            if not kcal_p:
                matches = [k for k in KCAL_PER_100G if product in k]
                if matches: product = matches[0]; kcal_p = KCAL_PER_100G[product]
                else:
                    bot.send_message(cid, f"\u2753 *{product}* не найден.\n\nВведи ещё раз:", parse_mode="Markdown")
                    return
            kcal = round(kcal_p * grams / 100)
            protein_map = {"куриная грудка":0.231,"яйцо":0.125,"говядина":0.189,"индейка":0.194,"куриное бедро":0.18}
            protein = round(grams * protein_map.get(product, 0.05), 1)
            set_state(cid, "idle")
            bot.send_message(cid,
                f"\U0001f9ee *КАЛЬКУЛЯТОР КАЛОРИЙ*\n" + "\u2500"*20 + "\n\n"
                f"\U0001f957 Продукт: *{product}*\n"
                f"\U0001f4ca Порция: *{grams}г*\n"
                f"\U0001f525 Калории: *{kcal} ккал*\n"
                f"\U0001f4c8 Калорийность: *{kcal_p} ккал/100г*\n"
                + (f"\U0001f4aa Белок: *~{protein}г*\n" if protein > 0.1 else "") +
                "\n\U0001f4a1 Хочешь записать? Нажми *\U0001f4d3 Дневник питания*",
                parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "Введи название и граммы:\nНапример: *куриная грудка 150*", parse_mode="Markdown")
        return

    # ── Редактирование ограничений по здоровью ──
    # ── Опрос для сушки ──
    if state in ("drying_q1","drying_q2","drying_q3","drying_q4","drying_q5"):
        if text not in ("1","2","3","4"):
            bot.send_message(cid, "Введи цифру 1, 2, 3 или 4"); return
        # Сохраняем ответ в extra как JSON-подобную строку
        answers = {}
        if extra:
            for pair in extra.split("|"):
                if ":" in pair:
                    k, v = pair.split(":", 1)
                    answers[k] = v
        q_num = state[-1]
        answers[f"q{q_num}"] = text
        extra_str = "|".join(f"{k}:{v}" for k,v in answers.items())

        survey_states = [s[0] for s in DRYING_SURVEY]
        idx = survey_states.index(state)

        if idx + 1 < len(DRYING_SURVEY):
            next_state, next_prompt = DRYING_SURVEY[idx + 1]
            set_state(cid, next_state, extra=extra_str)
            bot.send_message(cid, next_prompt, parse_mode="Markdown", reply_markup=cancel_menu())
        else:
            # Опрос завершён — анализируем
            set_state(cid, "idle")
            result = analyze_drying_survey(answers)
            save_profile(cid,
                drying_mode=1,
                drying_weeks=result["weeks"],
                drying_start=now_samara().strftime("%d.%m.%Y"))
            bot.send_message(cid,
                f"🏆 *РЕЖИМ СУШКИ АКТИВИРОВАН!*\n\n"
                f"{result['desc']}\n\n"
                f"⏱️ Рекомендуемый срок: *{result['weeks']} недель*\n"
                f"🍚 Углеводы: *{result['carbs_limit']}*\n\n"
                f"✅ Что изменилось:\n"
                f"• Рацион перестроен под сушку\n"
                f"• Каждый приём пищи — 3 равнозначных варианта\n"
                f"• В утреннем напоминании — напоминание о режиме сушки\n"
                f"• Кнопка «🏆 Режим сушки» покажет текущий план\n\n"
                f"⚠️ Помни: сушка — это стресс для организма. "
                f"При плохом самочувствии — снизь дефицит или выключи режим.",
                parse_mode="Markdown", reply_markup=main_menu(cid))
            # Показываем первый рацион сразу
            ration, _ = build_drying_ration(cid)
            bot.send_message(cid, ration, parse_mode="Markdown")
        return

    if state == "edit_health":
        condition_map = {"1":"диабет","2":"аллергия_глютен","3":"аллергия_лактоза",
                         "4":"аллергия_орехи","5":"давление","6":"суставы","7":"астма"}
        cleaned = text.replace(" ", "")
        try:
            if cleaned == "0":
                save_profile(cid, health_conditions="")
                set_state(cid, "idle")
                bot.send_message(cid, "✅ Все ограничения убраны. Рацион и тренировки без фильтров.",
                                 parse_mode="Markdown", reply_markup=main_menu(cid))
            else:
                nums = cleaned.split(",")
                assert all(n in condition_map for n in nums)
                conditions = [condition_map[n] for n in nums]
                save_profile(cid, health_conditions=",".join(conditions))
                set_state(cid, "idle")
                labels = "\n".join(f"• {HEALTH_CONDITIONS[c]['label']}" for c in conditions)
                bot.send_message(cid,
                    f"✅ *Ограничения обновлены:*\n{labels}\n\n"
                    "Рацион, рецепты и тренировки теперь учитывают это автоматически.",
                    parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "Введи цифры через запятую (например: 1,3) или 0",
                             parse_mode="Markdown")
        return

    # ── Умный выбор: категория ──
    if state == "smart_food_category":
        if text in SMART_MENU_CATEGORIES:
            set_state(cid, "smart_food_pick", extra=text)
            bot.send_message(cid,
                f"🍴 *{text}*\n\nВыбери блюдо:",
                parse_mode="Markdown", reply_markup=build_smart_food_menu(text))
        elif text == "❌ Отмена":
            set_state(cid, "idle")
            bot.send_message(cid, "Отменено.", reply_markup=main_menu(cid))
        else:
            bot.send_message(cid, "Выбери категорию из кнопок.", reply_markup=build_smart_food_menu())
        return

    # ── Умный выбор: блюдо ──
    if state == "smart_food_pick":
        category = extra or ""
        if text == "◀️ Назад к категориям":
            set_state(cid, "smart_food_category")
            bot.send_message(cid, "Выбери категорию:", reply_markup=build_smart_food_menu())
            return
        if text == "❌ Отмена":
            set_state(cid, "idle")
            bot.send_message(cid, "Отменено.", reply_markup=main_menu(cid))
            return
        # Текст кнопки: "🍴 блюдо"
        food_name = text[2:].strip() if text.startswith("🍴 ") else text
        profile = get_profile(cid)
        if not profile:
            bot.send_message(cid, "Сначала заполни профиль.", reply_markup=main_menu(cid))
            set_state(cid, "idle"); return
        # Считаем остаток калорий на день
        ration_kcal = profile.get("ration_kcal") or 0
        if not ration_kcal:
            from_plan = build_ration(cid)
            # Оцениваем ~ 30% суточного на один приём
            target_kcal = round((profile.get("tdee", 2200) * 0.85) * 0.3)
        else:
            target_kcal = round(ration_kcal * 0.3)
        target_kcal = max(200, min(target_kcal, 700))
        grams, actual_kcal = calc_smart_portion(food_name, target_kcal)
        if grams is None:
            bot.send_message(cid,
                f"⚠️ Не могу рассчитать — нет данных о калорийности *{food_name}*.",
                parse_mode="Markdown", reply_markup=main_menu(cid))
            set_state(cid, "idle"); return
        # Белки / жиры / углеводы (примерные)
        macro_line = ""
        set_state(cid, "idle")
        bot.send_message(cid,
            f"🍴 *{food_name.capitalize()}*\n\n"
            f"📏 Порция: *{grams} г*\n"
            f"🔥 Калорийность: *{actual_kcal} ккал*{macro_line}\n\n"
            f"_Порция рассчитана под твой суточный калораж (~30% от нормы приёма пищи)_",
            parse_mode="Markdown", reply_markup=main_menu(cid))
        return

    # ── ГИ продукта ──
    if state == "waiting_gi_query":
        gi = get_gi_info(text.strip())
        set_state(cid, "idle")
        if gi:
            bot.send_message(cid,
                f"🍎 *{text.strip().capitalize()}*\n\n"
                f"ГИ: *{gi['gi']}* {gi['emoji']} — {gi['category']}",
                parse_mode="Markdown", reply_markup=main_menu(cid))
        else:
            bot.send_message(cid,
                f"❓ Продукт *{text.strip()}* не найден в базе ГИ.\n\nПопробуй другое название.",
                parse_mode="Markdown", reply_markup=main_menu(cid))
        return

    # ── Давление: ввод (формат: 120/80 или 120/80/72) ──
    if state == "waiting_pressure":
        try:
            parts = text.strip().replace(" ", "").split("/")
            assert len(parts) in (2, 3)
            sys_v = int(parts[0]); dia_v = int(parts[1])
            pulse_v = int(parts[2]) if len(parts) == 3 else None
            assert 50 < sys_v < 250 and 30 < dia_v < 150
            log_pressure(cid, sys_v, dia_v, pulse_v)
            set_state(cid, "idle")
            cat, tip = analyze_pressure(sys_v, dia_v)
            pulse_str = f"\n💓 Пульс: *{pulse_v}* уд/мин" if pulse_v else ""
            bot.send_message(cid,
                f"✅ *Давление записано!*\n\n"
                f"🩺 *{sys_v}/{dia_v}* — {cat}{pulse_str}\n\n"
                f"💡 {tip}",
                parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid,
                "Введи в формате *120/80* или *120/80/72* (с пульсом)",
                parse_mode="Markdown")
        return

    # ── Добавить лекарство: шаг 1 — название ──
    if state == "med_add_name":
        set_state(cid, "med_add_dose", extra=text.strip())
        bot.send_message(cid,
            f"💊 Лекарство: *{text.strip()}*\n\nВведи дозировку (например: *500мг* или *1 таблетка*):",
            parse_mode="Markdown")
        return

    # ── Добавить лекарство: шаг 2 — дозировка ──
    if state == "med_add_dose":
        set_state(cid, "med_add_times", extra=f"{extra}|{text.strip()}")
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
        kb.add(*[types.KeyboardButton(str(i)) for i in range(1, 5)])
        bot.send_message(cid,
            f"Сколько раз в день?",
            reply_markup=kb)
        return

    # ── Добавить лекарство: шаг 3 — кратность ──
    if state == "med_add_times":
        try:
            tpd = int(text.strip()); assert 1 <= tpd <= 10
            parts_extra = extra.split("|", 1)
            name = parts_extra[0]; dose = parts_extra[1] if len(parts_extra) > 1 else ""
            add_medication(cid, name, dose, tpd)
            set_state(cid, "idle")
            bot.send_message(cid,
                f"✅ *{name}* {dose} × {tpd}/день — добавлено!",
                parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "Введи число от 1 до 4.")
        return

    # ── Обхваты: ввод значения ──
    if state == "waiting_measurement":
        try:
            cm = float(text.replace(",", "."))
            assert 10 < cm < 300
            part_key = extra  # ключ части тела
            save_measurement(cid, part_key, cm)
            set_state(cid, "idle")
            label = dict(MEASUREMENTS_LIST).get(part_key, part_key)
            bot.send_message(cid,
                f"✅ *{label}: {cm} см* — сохранено!",
                parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "Введи значение в сантиметрах, например: *85.5*", parse_mode="Markdown")
        return

    # ── Шаблон еды: ввод названия ──
    if state == "tpl_create_name":
        if text:
            # Берём последние записи дневника сегодня как содержимое шаблона
            today = now_samara().date().strftime("%Y-%m-%d")
            conn = sqlite3.connect("weight_tracker.db")
            rows = conn.execute(
                "SELECT food_name, calories FROM food_diary WHERE user_id=? AND date=? AND calories > 0 ORDER BY id DESC LIMIT 10",
                (cid, today)).fetchall()
            conn.close()
            if rows:
                items = [(r[0], r[1]) for r in rows]
                save_meal_template(cid, text, items)
                total = sum(r[1] for r in rows)
                set_state(cid, "idle")
                bot.send_message(cid,
                    f"✅ Шаблон *«{text}»* сохранён!\n"
                    f"Включает {len(items)} позиций — {total} ккал",
                    parse_mode="Markdown", reply_markup=main_menu(cid))
            else:
                set_state(cid, "idle")
                bot.send_message(cid,
                    "В дневнике сегодня нет записей для шаблона.\n"
                    "Сначала внеси приём пищи, потом создавай шаблон.",
                    reply_markup=main_menu(cid))
        else:
            bot.send_message(cid, "Введи название шаблона.")
        return

    # ── Партнёр: ввод кода ──
    if state == "partner_link_code":
        ok, result = link_partner(cid, text.strip())
        if ok:
            set_state(cid, "idle")
            bot.send_message(cid,
                f"✅ *Партнёр подключён!*\n\nТеперь вы соревнуетесь вместе 💪\n"
                f"Смотри сравнение в разделе *👫 Партнёр*",
                parse_mode="Markdown", reply_markup=main_menu(cid))
        else:
            bot.send_message(cid, f"❌ {result}\n\nПопробуй ещё раз или нажми ❌ Отмена.")
        return

    # ── Напоминания: ввод текста ──
    if state == "reminder_add_text":
        if text:
            set_state(cid, "reminder_add_time", extra=text)
            bot.send_message(cid,
                f"⏰ Напоминание: *«{text}»*\n\nТеперь введи время в формате *ЧЧ:ММ*\n(например: *08:00*)",
                parse_mode="Markdown", reply_markup=cancel_menu())
        else:
            bot.send_message(cid, "Введи текст напоминания.")
        return

    # ── Напоминания: ввод времени ──
    if state == "reminder_add_time":
        import re as _re
        m2 = _re.match(r"^(\d{1,2}):(\d{2})$", text.strip())
        if m2:
            hour, minute = int(m2.group(1)), int(m2.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                reminder_text = extra or "Напоминание"
                save_user_reminder(cid, reminder_text, hour, minute)
                set_state(cid, "idle")
                bot.send_message(cid,
                    f"✅ Напоминание *«{reminder_text}»* в *{hour:02d}:{minute:02d}* сохранено!\n\n"
                    "_Бот пришлёт уведомление в нужное время._",
                    parse_mode="Markdown", reply_markup=main_menu(cid))
                return
        bot.send_message(cid, "Введи время в формате ЧЧ:ММ, например: *08:00*", parse_mode="Markdown")
        return

    # ── Настроение: шаг 1 — оценка настроения ──
    if state == "mood_step1":
        try:
            mood = int(text.strip())
            assert 1 <= mood <= 5
            set_state(cid, "mood_step2", extra=str(mood))
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
            kb.add(*[types.KeyboardButton(str(i)) for i in range(1, 6)])
            bot.send_message(cid,
                f"Настроение: {MOOD_EMOJIS[mood]} *{mood}/5*\n\n"
                "2️⃣ Оцени *уровень стресса* (1 — нет стресса, 5 — очень высокий):",
                parse_mode="Markdown", reply_markup=kb)
        except Exception:
            bot.send_message(cid, "Введи число от 1 до 5.")
        return

    # ── Настроение: шаг 2 — стресс ──
    if state == "mood_step2":
        try:
            stress = int(text.strip())
            assert 1 <= stress <= 5
            mood = int(extra)
            set_state(cid, "mood_step3", extra=f"{mood},{stress}")
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
            kb.add(*[types.KeyboardButton(str(i)) for i in range(1, 6)])
            bot.send_message(cid,
                f"Стресс: {STRESS_EMOJIS[stress]} *{stress}/5*\n\n"
                "3️⃣ Оцени *уровень энергии* (1 — совсем нет, 5 — максимум):",
                parse_mode="Markdown", reply_markup=kb)
        except Exception:
            bot.send_message(cid, "Введи число от 1 до 5.")
        return

    # ── Настроение: шаг 3 — энергия ──
    if state == "mood_step3":
        try:
            energy = int(text.strip())
            assert 1 <= energy <= 5
            parts_extra = extra.split(",")
            mood = int(parts_extra[0]); stress = int(parts_extra[1])
            log_mood(cid, mood, stress, energy)
            set_state(cid, "idle")
            advice = mood_nutrition_advice(mood, stress, energy)
            bot.send_message(cid,
                f"✅ *Самочувствие записано!*\n\n"
                f"Настроение: {MOOD_EMOJIS[mood]} {mood}/5\n"
                f"Стресс: {STRESS_EMOJIS[stress]} {stress}/5\n"
                f"Энергия: ⚡ {energy}/5\n\n"
                f"💡 *Советы по питанию:*\n{advice}",
                parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "Введи число от 1 до 5.")
        return

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

    # ── Штрихкод ──
    if state == "waiting_gi_product":
        product_name = text.strip()
        gi = get_gi(product_name)
        if gi is not None:
            bot.send_message(cid, f"🍎 *{product_name.capitalize()}*\n\n{gi_label(gi)}\n\n"
                             "💡 Низкий ГИ (≤40) — медленные углеводы, долгое насыщение\n"
                             "Средний (41–70) — умеренное влияние на сахар\n"
                             "Высокий (≥71) — быстрый рост сахара в крови",
                             parse_mode="Markdown", reply_markup=main_menu(cid))
        else:
            bot.send_message(cid, f"❓ ГИ для *{product_name}* не найден в базе.\n\n"
                             "Попробуй: гречка, рис, картофель, банан, яблоко...",
                             parse_mode="Markdown", reply_markup=main_menu(cid))
        set_state(cid, "idle")
        return

    if state == "waiting_exercise_history":
        exercise = text.strip()
        bot.send_message(cid, build_exercise_history(cid, exercise), parse_mode="Markdown",
                         reply_markup=main_menu(cid))
        set_state(cid, "idle")
        return

    if state == "waiting_resting_hr":
        try:
            rhr = int(text.strip())
            if not 30 <= rhr <= 120:
                raise ValueError
            save_profile(cid, resting_hr=rhr)
            bot.send_message(cid, f"✅ Пульс покоя сохранён: *{rhr} уд/мин*", parse_mode="Markdown",
                             reply_markup=main_menu(cid))
            result = build_hr_zones(cid)
            if isinstance(result, tuple):
                msg, kb_hr = result
                bot.send_message(cid, msg, parse_mode="Markdown", reply_markup=kb_hr)
        except ValueError:
            bot.send_message(cid, "⚠️ Введи число от 30 до 120", reply_markup=cancel_menu())
            return
        set_state(cid, "idle")
        return

    if state == "waiting_barcode":
        barcode = text.strip().replace(" ", "")
        if not barcode.isdigit():
            bot.send_message(cid, "⚠️ Введи только цифры штрихкода", reply_markup=cancel_menu())
            return
        bot.send_message(cid, "🔍 Ищу продукт...")
        info = lookup_barcode(barcode)
        if not info:
            bot.send_message(cid, f"❌ Продукт со штрихкодом *{barcode}* не найден в базе.\n\nПопробуй ввести вручную: `продукт граммы`",
                             parse_mode="Markdown", reply_markup=main_menu(cid))
        else:
            set_state(cid, "barcode_got_grams", extra=barcode + ":" + str(info['kcal']) + ":" + info['name'])
            kb_bc = types.InlineKeyboardMarkup(row_width=3)
            for g in [50, 100, 150, 200, 300]:
                kb_bc.add(types.InlineKeyboardButton(
                    f"{g}г = {round(info['kcal']*g/100)} ккал",
                    callback_data=f"barcode_add:{barcode}:{g}:{info['name']}:{info['kcal']}"))
            bot.send_message(cid, build_barcode_result(info), parse_mode="Markdown", reply_markup=kb_bc)
        set_state(cid, "idle")
        return

    # ── Вода в мл (своё значение) ──
    if state == "waiting_water_ml":
        try:
            ml = int(text); assert 50 <= ml <= 3000
            add_water_ml(cid, ml)
            set_state(cid, "idle")
            bot.send_message(cid, build_water_ml_status(cid), parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "⚠️ Введи количество мл (50–3000)", reply_markup=cancel_menu())
        return

    # ── HRV / Пульс покоя (команда /hrv) ──
    if state == "waiting_hrv":
        try:
            parts = text.strip().split()
            hrv = int(parts[0]) if len(parts) > 0 else 0
            pulse = int(parts[1]) if len(parts) > 1 else 0
            log_hrv(cid, hrv, pulse)
            set_state(cid, "idle")
            bot.send_message(cid, f"💓 Записано: HRV *{hrv}*, пульс покоя *{pulse} уд/мин*\n\n" + build_hrv_report(cid),
                             parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "⚠️ Формат: HRV пульс, например: `65 55`\nИли только пульс: `60`", reply_markup=cancel_menu())
        return

    # ── Стресс (заметка после оценки) ──
    if state == "waiting_stress_note":
        note = text.strip()
        level = int(extra) if extra and extra.isdigit() else 5
        log_stress(cid, level, note)
        set_state(cid, "idle")
        bot.send_message(cid, f"🧠 Стресс *{level}/10* записан.\n\n_{note}_", parse_mode="Markdown", reply_markup=main_menu(cid))
        return

    # ── Импорт Health CSV ──
    if state == "waiting_health_import":
        bot.send_message(cid, "⚠️ Пожалуйста, отправь файл (CSV), а не текст.", reply_markup=cancel_menu())
        return

    # ── Ввод обхвата талии ──
    if state == "waiting_waist":
        try:
            cm = float(text.replace(",", ".")); assert 40 < cm < 200
            add_waist(cid, cm)
            update_streak(cid)
            set_state(cid, "idle")
            history = get_waist_history(cid)
            diff_note = ""
            if len(history) >= 2:
                diff = round(cm - history[-2][0], 1)
                if diff < 0:   diff_note = f"\n📉 *{abs(diff)} см меньше* чем в прошлый раз! 🎉"
                elif diff > 0: diff_note = f"\n📈 На {diff} см больше чем в прошлый раз."
                else:          diff_note = "\n➡️ Без изменений."
            risk = analyze_waist(get_profile(cid), cm)
            bot.send_message(cid,
                f"📏 *Обхват талии: {cm} см* сохранён!\n\n{risk}{diff_note}",
                parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "Введи число в см, например: 95")
        return

    # ── Ручной ввод InBody: шаг 1 — вес ──
    if state == "inbody_manual_weight":
        try:
            w = float(text.replace(",", ".")); assert 30 < w < 300
            set_state(cid, "inbody_manual_muscle", extra=str(w))
            bot.send_message(cid,
                f"✅ Вес: *{w} кг*\n\n2️⃣ Введи *мышечную массу* в кг (например: `41.3`):",
                parse_mode="Markdown", reply_markup=cancel_menu())
        except Exception:
            bot.send_message(cid, "Введи вес числом, например: 108.4")
        return

    # ── Ручной ввод InBody: шаг 2 — мышечная масса ──
    if state == "inbody_manual_muscle":
        try:
            m_kg = float(text.replace(",", ".")); assert 10 < m_kg < 100
            set_state(cid, "inbody_manual_fat", extra=f"{extra}|{m_kg}")
            bot.send_message(cid,
                f"✅ Мышцы: *{m_kg} кг*\n\n3️⃣ Введи *% жира* (например: `33.1`):",
                parse_mode="Markdown", reply_markup=cancel_menu())
        except Exception:
            bot.send_message(cid, "Введи мышечную массу числом, например: 41.3")
        return

    # ── Ручной ввод InBody: шаг 3 — % жира ──
    if state == "inbody_manual_fat":
        try:
            fat = float(text.replace(",", ".")); assert 3 < fat < 60
            set_state(cid, "inbody_manual_visceral", extra=f"{extra}|{fat}")
            bot.send_message(cid,
                f"✅ Жир: *{fat}%*\n\n"
                "4️⃣ Введи *висцеральный жир* (число из отчёта, например: `16`)\n"
                "Если не знаешь — нажми «⏭️ Пропустить»:",
                parse_mode="Markdown", reply_markup=skip_or_cancel_menu())
        except Exception:
            bot.send_message(cid, "Введи % жира числом, например: 33.1")
        return

    # ── Ручной ввод InBody: шаг 4 — висцеральный жир (опционально) ──
    if state == "inbody_manual_visceral":
        try:
            parts = extra.split("|")
            w_val, m_val, fat_val = float(parts[0]), float(parts[1]), float(parts[2])
            if text == "⏭️ Пропустить":
                visceral = None
            else:
                visceral = int(float(text.replace(",", ".")))
                assert 0 < visceral < 50

            data = {
                "weight": w_val, "muscle": m_val, "fat_percent": fat_val,
                "fat_mass_kg": round(w_val * fat_val / 100, 1),
                "water": None, "protein": None, "bone": None,
                "visceral_fat": visceral, "bmi": None, "lean_mass": None,
                "bmr": None, "tdee": None, "optimal_weight": None,
                "report_date": now_samara().strftime("%d.%m.%y"),
            }

            report = build_inbody_report(cid, data)
            add_inbody_record(cid, data)
            update_streak(cid)
            profile = get_profile(cid)
            if profile:
                add_weight(cid, w_val)
                save_profile(cid, current_weight=w_val)
            set_state(cid, "idle")
            bot.send_message(cid, report, parse_mode="Markdown", reply_markup=main_menu(cid))
        except Exception:
            bot.send_message(cid, "Введи число или нажми «⏭️ Пропустить»",
                             reply_markup=skip_or_cancel_menu())
        return

    # Оценка усталости
    if state == "rate_fatigue":
        try:
            f=int(text); assert 1<=f<=5
            wtype=extra or "тренировка"
            save_profile(cid,fatigue=f,last_workout_date=now_samara().strftime("%Y-%m-%d %H:%M"))
            log_workout(cid,wtype,f); set_state(cid,"idle")
            new_ach = check_and_unlock(cid)
            if new_ach:
                for k in new_ach:
                    bot.send_message(cid, f"🎉 *{ACHIEVEMENTS[k]['emoji']} {ACHIEVEMENTS[k]['name']}!*\n{ACHIEVEMENTS[k]['desc']}", parse_mode="Markdown")
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
            profile = get_profile(cid)
            chosen = text
            health_warn = ""
            if profile and chosen in get_banned_foods(profile):
                safe_alt = get_safe_replacement(profile, chosen)
                if safe_alt != chosen:
                    chosen = safe_alt
                    health_warn = (f"\n\n⚠️ *{text} не подходит по твоим ограничениям здоровья.*\n"
                                   f"Автоматически заменил на *{safe_alt}*.")
            to_g,kcal=calc_equivalent(from_food,chosen)
            warn=SEMIFAB_WARNINGS.get(chosen,"")
            warn_text=f"\n\n{warn}" if warn else ""
            set_state(cid,"idle")
            bot.send_message(cid,
                f"✅ *Замена в {meal}:*\n\n"
                f"❌ {DEFAULT_PORTIONS.get(from_food,100)}г *{from_food}*\n"
                f"✅ {to_g}г *{chosen}*\n\n"
                f"🔁 Калорийность сохранена: *{kcal} ккал*{warn_text}{health_warn}",
                parse_mode="Markdown",reply_markup=main_menu(cid))
        else:
            bot.send_message(cid,"Выбери продукт из кнопок.")
        return

    # ════════════════════════════════════════
    #  КНОПКИ МЕНЮ
    # ════════════════════════════════════════

    # Если осталось какое-то незавершённое состояние — не обрабатываем как кнопку
    if state not in ("idle", None, ""):
        bot.send_message(cid,
            "⚠️ Я жду твоего ввода. Нажми *«❌ Отмена»* чтобы выйти.",
            parse_mode="Markdown", reply_markup=cancel_menu())
        return

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
        ration_kb = ration_recipe_inline(ration)
        extra_hint = "\n💡 Нажми на кнопку ниже чтобы открыть рецепт нужного блюда 👇" if ration_kb else ""
        bot.send_message(cid,
            f"🍽️ *РАЦИОН НА СЕГОДНЯ*\n{label}\n─────────────\n{ration}\n\n"
            f"💡 Для замены нажми «🔄 Заменить блюдо»{extra_hint}",
            parse_mode="Markdown",
            reply_markup=ration_kb if ration_kb else main_menu(cid))
        if ration_kb:
            bot.send_message(cid, "⬆️ Рецепты блюд из твоего рациона:", reply_markup=main_menu(cid))

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
        # 📅 Прогноз даты цели
        prediction = predict_goal_date(wd, target)
        if prediction:
            msg += (f"\n\n📅 *Прогноз:* при темпе {prediction['rate_week']} кг/нед\n"
                    f"цель достигнешь *{prediction['date']}* (≈{prediction['weeks']} нед.)")
        # 🪨 Антиплато
        plateau = check_plateau_advanced(wd)
        if plateau:
            msg += f"\n\n🪨 *Плато {plateau['weeks']} взвешивания подряд!*\n{plateau['tip']}"
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

    elif text=="💪 Прогресс упражнений":
        analytics = build_exercise_analytics(cid)
        if not analytics:
            bot.send_message(cid,
                "Нет данных по упражнениям.\n\nЗаписывай веса через:\n"
                "*Тренировки → Записать упражнение*",
                parse_mode="Markdown")
            return
        bot.send_message(cid, analytics, parse_mode="Markdown")

    # ── Трекер добавок ──
    elif text == "💊 Мои добавки":
        taken = get_supplements_today(cid)
        taken_set = set(taken)
        lines = []
        for s in SUPPLEMENTS_LIST:
            icon = "✅" if s in taken_set else "⬜"
            lines.append(f"{icon} {s}")
        msg = "💊 *Добавки на сегодня:*\n\n" + "\n".join(lines) + "\n\nНажми на добавку чтобы отметить приём:"
        bot.send_message(cid, msg, parse_mode="Markdown", reply_markup=build_supplements_menu())

    elif text in SUPPLEMENTS_LIST:
        taken_today = get_supplements_today(cid)
        if text in taken_today:
            bot.send_message(cid, f"✅ *{text}* уже отмечена сегодня!", parse_mode="Markdown")
        else:
            log_supplement(cid, text)
            streak = get_supplements_streak(cid, text)
            streak_str = f"\n🔥 Серия: *{streak} дней* подряд!" if streak > 1 else ""
            bot.send_message(cid, f"✅ *{text}* — принято!{streak_str}", parse_mode="Markdown")
            if streak >= 7:
                with sqlite3.connect(DB_PATH) as conn:
                    existing = {r[0] for r in conn.execute("SELECT achievement_key FROM achievements WHERE user_id=?", (cid,)).fetchall()}
                    if "supplements_7" not in existing:
                        conn.execute("INSERT INTO achievements (user_id,achievement_key,unlocked_date) VALUES (?,?,?)",
                                     (cid, "supplements_7", now_samara().strftime("%Y-%m-%d")))
                        conn.commit()
                        bot.send_message(cid, "🎉 *Новая ачивка: 💊 Неделя добавок!*\n_7 дней принимал добавки подряд_", parse_mode="Markdown")

    elif text == "📊 Статистика добавок":
        lines = []
        for s in SUPPLEMENTS_LIST:
            streak = get_supplements_streak(cid, s)
            bar = "█" * min(streak, 7) + "░" * max(0, 7 - streak)
            lines.append(f"{s}: {bar} {streak}д.")
        bot.send_message(cid, "📊 *Серии приёма добавок (макс. 7 дней):*\n\n" + "\n".join(lines), parse_mode="Markdown")

    # ── Трекер настроения ──
    elif text == "😊 Самочувствие":
        today_mood = get_mood_today(cid)
        if today_mood:
            m, s, e, note = today_mood
            history = get_mood_history(cid, 7)
            hist_lines = [f"• {hd[:10]}: {MOOD_EMOJIS.get(hm,'?')} {hm} / стресс {hs} / энергия {he}" for hm, hs, he, hd in history]
            advice = mood_nutrition_advice(m, s, e)
            bot.send_message(cid,
                f"😊 *Самочувствие сегодня:*\n\nНастроение: {MOOD_EMOJIS[m]} {m}/5\nСтресс: {STRESS_EMOJIS[s]} {s}/5\nЭнергия: ⚡ {e}/5\n\n💡 {advice}\n\n*За неделю:*\n" + "\n".join(hist_lines),
                parse_mode="Markdown")
        else:
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
            kb.add(*[types.KeyboardButton(str(i)) for i in range(1, 6)])
            set_state(cid, "mood_step1")
            bot.send_message(cid,
                "😊 *Как ты себя чувствуешь сегодня?*\n\n1️⃣ Оцени *настроение* от 1 до 5:\n1 — очень плохо  |  5 — отлично",
                parse_mode="Markdown", reply_markup=kb)

    # ── Ачивки ──
    elif text == "🏆 Мои ачивки":
        check_and_unlock_achievements(cid)
        ach = get_all_achievements(cid)
        total_ach = len(ACHIEVEMENTS_MAP)
        if not ach:
            bot.send_message(cid, "Пока ачивок нет.\n\nВноси вес, шаги и тренировки — и они появятся! 💪")
            return
        lines = [f"✅ *{name}* — _{desc}_ ({date})" for name, desc, date in ach]
        locked = total_ach - len(ach)
        bot.send_message(cid,
            f"🏆 *Твои достижения ({len(ach)}/{total_ach}):*\n\n" + "\n".join(lines) +
            (f"\n\n🔒 Ещё {locked} не разблокировано..." if locked > 0 else "\n\n🎉 Все ачивки получены!"),
            parse_mode="Markdown")

    # ── Калории сегодня ──
    elif text == "🍽️ Калории сегодня":
        status = build_kcal_status(cid)
        suggest = suggest_meal_for_remaining(cid)
        msg = status
        if suggest:
            msg += f"\n\n💡 *Что поесть:*\n{suggest}"
        bot.send_message(cid, msg, parse_mode="Markdown")

    # ── Фаза тренировок ──
    elif text == "📅 Фаза тренировок":
        phase = get_training_phase(cid)
        bot.send_message(cid,
            f"🏋️ *Текущая фаза:* {phase['name']}\n\n"
            f"🎯 *Цель:* {phase['focus']}\n"
            f"📊 *Подходы × повторения:* {phase['reps']}\n"
            f"⚡ *Интенсивность:* {phase['intensity']}\n"
            f"⏱️ *Отдых:* {phase['rest']}\n\n"
            f"💡 {phase['tip']}",
            parse_mode="Markdown")

    # ── ИИ-советник ──
    elif text == "🤖 Совет на день":
        advice = build_ai_advice(cid)
        bot.send_message(cid, advice, parse_mode="Markdown")

    # ── Макронутриенты ──
    elif text == "📊 Макронутриенты":
        bot.send_message(cid, build_macros_today(cid), parse_mode="Markdown")

    # ── Давление: запись ──
    elif text == "🩺 Давление/пульс":
        bot.send_message(cid, build_pressure_history_text(cid), parse_mode="Markdown",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("➕ Записать", callback_data="pressure_add")))

    # ── Лекарства ──
    elif text == "💊 Лекарства":
        msg = build_medications_today(cid)
        meds = get_medications(cid)
        kb2 = types.InlineKeyboardMarkup(row_width=2)
        for mid, name, dose, tpd in meds:
            taken = get_medications_taken_today(cid).get(mid, 0)
            if taken < tpd:
                kb2.add(types.InlineKeyboardButton(f"✅ {name}", callback_data=f"med_take:{mid}"))
        kb2.add(types.InlineKeyboardButton("➕ Добавить лекарство", callback_data="med_add"))
        bot.send_message(cid, msg, parse_mode="Markdown", reply_markup=kb2)

    # ── Экспорт CSV ──
    elif text in ("📤 Экспорт CSV", "📤 Экспорт данных"):
        csv_data = export_all_data_csv(cid)
        fname = f"/tmp/export_{cid}.csv"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(csv_data)
        with open(fname, "rb") as f:
            bot.send_document(cid, f, caption="📊 Все твои данные в CSV",
                              visible_file_name=f"health_data_{now_samara().strftime('%Y%m%d')}.csv")

    # ── Месячный отчёт ──
    elif text == "📋 Отчёт за месяц":
        report = export_monthly_report_text(cid)
        bot.send_message(cid, report, parse_mode="Markdown")

    # ── ГИ продукта ──
    elif text == "🍎 ГИ продукта":
        set_state(cid, "waiting_gi_query")
        bot.send_message(cid,
            "🍎 *Гликемический индекс*\n\nВведи название продукта:",
            parse_mode="Markdown", reply_markup=cancel_menu())

    # ── Недельный отчёт ──
    elif text == "📊 Отчёт за неделю":
        bot.send_message(cid, build_weekly_report(cid), parse_mode="Markdown")

    # ── Корреляции ──
    elif text == "🔬 Корреляции":
        bot.send_message(cid, build_correlations_report(cid), parse_mode="Markdown")

    # ── Обхваты ──
    elif text == "📏 Обхваты":
        summary = build_measurements_summary(cid)
        kb2 = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("➕ Внести обхваты", callback_data="measure_add"))
        bot.send_message(cid, summary, parse_mode="Markdown", reply_markup=kb2)

    # ── Инфографика прогресса ──
    elif text == "📈 Инфографика":
        bot.send_message(cid, build_progress_infographic(cid), parse_mode="Markdown")

    # ── Прогноз по неделям ──
    elif text == "📅 Прогноз по неделям":
        bot.send_message(cid, build_weekly_forecast(cid), parse_mode="Markdown")

    # ── Меню на неделю ──
    elif text == "🗓️ Меню на неделю":
        bot.send_message(cid, build_week_menu(cid), parse_mode="Markdown")

    # ── Список покупок ──
    elif text == "🛒 Список покупок":
        bot.send_message(cid, build_shopping_list_from_menu(), parse_mode="Markdown")

    # ── Избранные блюда ──
    elif text == "⭐ Избранные блюда":
        bot.send_message(cid, build_favorites_menu(cid), parse_mode="Markdown")

    # ── Напоминания ──
    elif text == "⏰ Напоминания":
        rows = get_user_reminders(cid)
        kb_rem = types.InlineKeyboardMarkup()
        kb_rem.add(types.InlineKeyboardButton("➕ Добавить напоминание", callback_data="reminder_add"))
        for rid, rtxt, rh, rm in rows:
            kb_rem.add(types.InlineKeyboardButton(
                f"🗑 {rh:02d}:{rm:02d} {rtxt}", callback_data=f"reminder_del:{rid}"))
        msg = build_reminders_list(cid)
        # Плато-проверка
        plateau_days = detect_plateau(cid)
        if plateau_days:
            msg += f"\n\n⚠️ *Обнаружено плато ({plateau_days} записей)*\nНажми кнопку для советов:"
            kb_rem.add(types.InlineKeyboardButton("🚨 Советы по выходу из плато", callback_data="plateau_tips"))
        bot.send_message(cid, msg, parse_mode="Markdown", reply_markup=kb_rem)

    # ── Супер-сеты ──
    elif text == "💪 Супер-сеты":
        kb_ss = types.InlineKeyboardMarkup()
        for name in SUPERSETS:
            kb_ss.add(types.InlineKeyboardButton(name, callback_data=f"superset:{name}"))
        bot.send_message(cid, "💪 *Выбери группу мышц:*", parse_mode="Markdown", reply_markup=kb_ss)

    # ── Виртуальный тренер ──
    elif text == "🤖 Тренер":
        bot.send_message(cid, build_trainer_message(cid), parse_mode="Markdown")

    # ── Цитата дня ──
    elif text == "💬 Цитата дня":
        bot.send_message(cid, get_quote_of_day(), parse_mode="Markdown")

    # ── Сводка за день ──
    elif text == "📋 Сводка за день":
        bot.send_message(cid, build_today_summary(cid), parse_mode="Markdown")

    # ── Баланс калорий ──
    elif text == "⚖️ Баланс калорий":
        bot.send_message(cid, build_calorie_balance(cid), parse_mode="Markdown")

    # ── Восстановление мышц ──
    elif text == "💪 Восстановление":
        bot.send_message(cid, build_muscle_recovery(cid), parse_mode="Markdown")

    # ── Шаблоны еды ──
    elif text == "📋 Шаблоны еды":
        templates = get_meal_templates(cid)
        kb_tpl = types.InlineKeyboardMarkup()
        for name, items in templates:
            total = sum(c for _, c in items)
            kb_tpl.add(
                types.InlineKeyboardButton(f"▶️ {name} ({total}ккал)", callback_data=f"tpl_apply:{name}"),
                types.InlineKeyboardButton("🗑", callback_data=f"tpl_del:{name}")
            )
        kb_tpl.add(types.InlineKeyboardButton("➕ Создать шаблон из дневника", callback_data="tpl_create"))
        bot.send_message(cid, build_templates_menu(cid), parse_mode="Markdown", reply_markup=kb_tpl)

    # ── Кардио таймер ──
    elif text == "🏃 Кардио таймер":
        # Проверяем есть ли активная сессия
        conn = sqlite3.connect("weight_tracker.db")
        active = conn.execute(
            "SELECT id, start_time FROM cardio_sessions WHERE user_id=? AND end_time IS NULL",
            (cid,)).fetchone()
        conn.close()
        kb_cardio = types.InlineKeyboardMarkup()
        if active:
            start_str = active[1]
            start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
            elapsed = round((now_samara() - start_dt).total_seconds() / 60)
            kb_cardio.add(types.InlineKeyboardButton("⏹ Остановить", callback_data="cardio_stop"))
            bot.send_message(cid,
                f"🏃 *Кардио идёт!* ⏱ {elapsed} мин.\n\nНажми Остановить когда закончишь.",
                parse_mode="Markdown", reply_markup=kb_cardio)
        else:
            kb_cardio.add(types.InlineKeyboardButton("▶️ Начать кардио", callback_data="cardio_start"))
            bot.send_message(cid,
                "🏃 *Кардио таймер*\n\nНажми кнопку когда начнёшь тренировку.\n"
                "Бот автоматически посчитает время и примерные ккал.",
                parse_mode="Markdown", reply_markup=kb_cardio)

    # ── Карточка прогресса ──
    elif text == "📸 Карточка прогресса":
        bot.send_message(cid, build_stories_card(cid), parse_mode="Markdown")

    # ── Партнёр ──
    elif text == "👫 Партнёр":
        partner_id = get_partner(cid)
        kb_pair = types.InlineKeyboardMarkup()
        if partner_id:
            kb_pair.add(types.InlineKeyboardButton("🔄 Обновить сравнение", callback_data="partner_refresh"))
            kb_pair.add(types.InlineKeyboardButton("❌ Отвязать партнёра", callback_data="partner_unlink"))
        else:
            kb_pair.add(types.InlineKeyboardButton("🔗 Подключить партнёра", callback_data="partner_link"))
        bot.send_message(cid, build_partner_comparison(cid), parse_mode="Markdown", reply_markup=kb_pair)

    # ── XP и уровень ──
    elif text == "⚡ Мой уровень XP":
        bot.send_message(cid, build_xp_card(cid), parse_mode="Markdown")

    # ── Челленджи ──
    elif text == "🏆 Челленджи":
        kb_ch = types.InlineKeyboardMarkup()
        for ch in WEEKLY_CHALLENGES:
            kb_ch.add(types.InlineKeyboardButton(ch["name"] + f" (+{ch['xp']} XP)",
                callback_data=f"challenge_start:{ch['id']}"))
        bot.send_message(cid, build_challenges_menu(cid), parse_mode="Markdown", reply_markup=kb_ch)

    # ── Домашние тренировки — переключатель ──
    elif text == "🏠 Домашние тренировки":
        profile = get_profile(cid)
        current = int(profile.get("home_workouts") or 0) if profile else 0
        kb_hw = types.InlineKeyboardMarkup()
        kb_hw.add(
            types.InlineKeyboardButton("🏋️ Только зал" + (" ✅" if current == 0 else ""),
                callback_data="hw_mode:0"),
            types.InlineKeyboardButton("🏠+🏋️ Зал + дома" + (" ✅" if current == 1 else ""),
                callback_data="hw_mode:1"),
        )
        kb_hw.add(
            types.InlineKeyboardButton("🏠 Только дома" + (" ✅" if current == 2 else ""),
                callback_data="hw_mode:2"),
        )
        modes = {0: "🏋️ Только зал", 1: "🏠+🏋️ Зал + домашние", 2: "🏠 Только домашние"}
        bot.send_message(cid,
            f"🏠 *Режим тренировок*\n\n"
            f"Сейчас: *{modes[current]}*\n\n"
            "• *Только зал* — стандартные программы А/Б/В\n"
            "• *Зал + дома* — зал по расписанию + домашние в дни отдыха\n"
            "• *Только дома* — всё расписание из домашних тренировок, зал не нужен",
            parse_mode="Markdown", reply_markup=kb_hw)

    # ── Расписание
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

    # ── Фрукты — список ──
    elif text == "🍓 Фрукты":
        fruit_list = FOOD_GROUPS.get("фрукты", [])
        bot.send_message(cid,
            "🍓 *ФРУКТЫ В РАЦИОНЕ*\n\n"
            "Выбери фрукт — получишь карточку с ГИ, лучшим временем и пользой для похудения:",
            parse_mode="Markdown", reply_markup=foods_keyboard(fruit_list))

    # ── Спортпит — список ──
    elif text == "💪 Спортпит":
        sportpit_list = FOOD_GROUPS.get("спортпит", [])
        bot.send_message(cid,
            "💪 *СПОРТИВНОЕ ПИТАНИЕ*\n\n"
            "Выбери продукт — получишь карточку с составом, временем приёма и советами:",
            parse_mode="Markdown", reply_markup=foods_keyboard(sportpit_list))

    # ── Карточка продукта при нажатии из списка ──
    elif text in ALL_CARD_PRODUCTS:
        card_text = build_product_card(text, get_profile(cid))
        bot.send_message(cid, card_text, parse_mode="Markdown", reply_markup=main_menu(cid))

    # Профиль
    elif text=="👤 Мой профиль":
        profile=get_profile(cid)
        if not profile:
            bot.send_message(cid,"Профиль не настроен. Нажми *⚙️ Изменить профиль*",parse_mode="Markdown"); return
        plan=get_user_plan(cid, profile); wd=get_weights(cid)
        curr_w=wd[-1][0] if wd else profile["current_weight"]
        loss=round(profile["current_weight"]-curr_w,1)
        fatigue=int(profile.get("fatigue") or 0)
        fat_label={0:"—",1:"😊 Отлично",2:"✅ Хорошо",3:"🟡 Умеренная",
                   4:"🔴 Высокая",5:"😵 Очень высокая"}.get(fatigue,"—")
        water=get_water_today(cid)
        active_conditions = get_user_conditions(profile)
        if active_conditions:
            cond_labels = ", ".join(HEALTH_CONDITIONS[c]["label"] for c in active_conditions)
            health_line = f"\n🏥 Ограничения: *{cond_labels}*"
        else:
            health_line = "\n🏥 Ограничения: *нет*"
        source_note = ""
        if plan.get("bmr_source") == "InBody":
            source_note = "\n📋 _Калораж и белок рассчитаны по данным InBody (точнее формулы)_"
        bot.send_message(cid,
            f"👤 *МОЙ ПРОФИЛЬ*\n\n"
            f"⚖️ Стартовый: *{profile['current_weight']} кг* | Текущий: *{curr_w} кг* (−{loss} кг)\n"
            f"🎯 Цель: *{profile['target_weight']} кг*\n"
            f"📏 Рост: *{profile['height']} см* | 🎂 Возраст: *{profile['age']} лет*\n\n"
            f"🏋️ Зал: *{profile['gym_days']} дней/нед* — {auto_workout_label(profile)}\n"
            f"📅 Срок: *{profile['deadline_weeks']} нед*\n\n"
            f"🔥 Калории: *{plan['calories']} ккал/день*\n"
            f"💪 Белок: *{plan['protein']}г/день*\n"
            f"📈 Темп: *~{plan['weekly_loss']} кг/нед*"
            f"{source_note}\n\n"
            f"😴 Усталость: *{fat_label}*\n"
            f"🏥 Здоровье: *{'🤒 Болезнь' if profile.get('is_sick') else '✅ Здоров'}*"
            f"{health_line}\n"
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

    # ── Мои ограничения по здоровью ──
    # ── Таймер отдыха ──
    elif text == "⏱️ Таймер отдыха":
        m2 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for label in REST_TIMERS:
            m2.add(types.KeyboardButton(f"⏱️ {label}"))
        m2.add(types.KeyboardButton("❌ Отмена"))
        bot.send_message(cid,
            "⏱️ *ТАЙМЕР ОТДЫХА МЕЖДУ ПОДХОДАМИ*\n\nВыбери время отдыха:",
            parse_mode="Markdown", reply_markup=m2)

    elif text.startswith("⏱️ ") and text[2:].strip() in REST_TIMERS:
        label = text[2:].strip()
        seconds = REST_TIMERS[label]
        start_time = now_samara().strftime("%H:%M:%S")
        bot.send_message(cid,
            f"⏱️ Отдыхай *{label}*... Отправлю сигнал когда время выйдет! 🔔",
            parse_mode="Markdown", reply_markup=main_menu(cid))
        t = threading.Thread(target=rest_timer_worker, args=(cid, seconds, start_time), daemon=True)
        t.start()

    # ── Достижения ──
    elif text == "🏅 Мои достижения":
        # Сначала проверяем новые достижения
        new_ach = check_and_unlock(cid)
        if new_ach:
            new_text = "\n".join(f"{ACHIEVEMENTS[k]['emoji']} *{ACHIEVEMENTS[k]['name']}* разблокировано!" for k in new_ach)
            bot.send_message(cid, f"🎉 *Новые достижения!*\n\n{new_text}", parse_mode="Markdown")
        ach_text = build_achievements_text(cid)
        if not ach_text:
            bot.send_message(cid,
                "🏅 *Достижений пока нет.*\n\nВноси данные каждый день — "
                "первое достижение придёт уже сегодня!",
                parse_mode="Markdown")
        else:
            bot.send_message(cid, ach_text, parse_mode="Markdown")

    # ── Режим сушки ──

    elif text == "🏆 Режим сушки":
        profile = get_profile(cid)
        if not profile:
            bot.send_message(cid, "Сначала настрой профиль."); return
        drying_on = int(profile.get("drying_mode") or 0)
        if drying_on:
            plan  = calc_drying_plan(profile, get_last_inbody_dict(cid))
            start = profile.get("drying_start") or "—"
            weeks = int(profile.get("drying_weeks") or 0)
            m2    = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            m2.add(types.KeyboardButton("🍽️ Рацион сушки сегодня"),
                   types.KeyboardButton("📅 Рацион сушки завтра"))
            m2.add(types.KeyboardButton("❌ Выключить сушку"),
                   types.KeyboardButton("❌ Отмена"))
            bot.send_message(cid,
                f"🏆 *РЕЖИМ СУШКИ АКТИВЕН*\n\n"
                f"📅 Начало: *{start}*\n"
                f"⏱️ Срок: *{weeks} нед.*\n\n"
                f"🎯 Калории: *{plan['calories']} ккал/день*\n"
                f"💪 Белок: *{plan['protein']}г* | "
                f"🍚 Углеводы: *{plan['carbs']}г* | "
                f"🥑 Жиры: *{plan['fat']}г*\n\n"
                "⚠️ *Правила сушки:*\n"
                "• Убираем крупы, хлеб, фрукты (кроме ягод)\n"
                "• Белок каждые 3-4 часа\n"
                "• Вода минимум 3.5л в день\n"
                "• Кардио каждый день 30-45 мин\n"
                "• Соль минимум — задерживает воду",
                parse_mode="Markdown", reply_markup=m2)
        else:
            m2 = types.ReplyKeyboardMarkup(resize_keyboard=True)
            m2.add(types.KeyboardButton("✅ Пройти опрос для сушки"))
            m2.add(types.KeyboardButton("❌ Отмена"))
            bot.send_message(cid,
                "🏆 *РЕЖИМ СУШКИ*\n\n"
                "Сушка — специальный режим для снижения % жира при сохранении мышц.\n\n"
                "⚠️ При % жира выше 25% лучше сначала похудеть в обычном режиме.\n\n"
                "Бот проведёт умный опрос (5 вопросов) и подберёт:\n"
                "• Тип сушки (мягкая/стандартная/агрессивная)\n"
                "• Срок и дефицит калорий\n"
                "• Рацион с 3 вариантами каждого приёма пищи\n\n"
                "💡 *Помни:* перед сушкой проконсультируйся с врачом.",
                parse_mode="Markdown", reply_markup=m2)

    elif text == "✅ Пройти опрос для сушки":
        set_state(cid, "drying_q1")
        bot.send_message(cid, DRYING_SURVEY[0][1], parse_mode="Markdown",
                         reply_markup=cancel_menu())

    elif text in ("🍽️ Рацион сушки сегодня", "📅 Рацион сушки завтра"):
        profile = get_profile(cid)
        if not profile or not int(profile.get("drying_mode") or 0):
            bot.send_message(cid, "Режим сушки не активен. Нажми «🏆 Режим сушки»."); return
        for_tomorrow = (text == "📅 Рацион сушки завтра")
        ration, cal = build_drying_ration(cid, for_tomorrow=for_tomorrow)
        bot.send_message(cid, ration, parse_mode="Markdown", reply_markup=main_menu(cid))

    elif text == "❌ Выключить сушку":
        save_profile(cid, drying_mode=0, drying_weeks=0, drying_start="")
        bot.send_message(cid,
            "✅ *Режим сушки выключен.*\n\n"
            "Рацион вернулся к стандартному плану похудения.\n"
            "Отличная работа — сушка требует большой дисциплины! 💪",
            parse_mode="Markdown", reply_markup=main_menu(cid))

    elif text == "🏥 Мои ограничения":
        profile = get_profile(cid)
        if not profile:
            bot.send_message(cid, "Сначала настрой профиль."); return
        active = get_user_conditions(profile)
        if active:
            labels = "\n".join(f"• {HEALTH_CONDITIONS[c]['label']}" for c in active)
            current_text = f"✅ *Активные ограничения:*\n{labels}"
        else:
            current_text = "✅ *Ограничений нет* — рацион и тренировки без фильтров."
        set_state(cid, "edit_health")
        bot.send_message(cid,
            f"🏥 *МОИ ОГРАНИЧЕНИЯ ПО ЗДОРОВЬЮ*\n\n{current_text}\n\n"
            "Бот автоматически исключает опасные продукты из рациона/рецептов "
            "и упражнения из тренировок.\n\n"
            "Введи цифры через запятую чтобы изменить (например: `1,3`) или `0` чтобы убрать все:\n\n"
            "1 — 🩸 Сахарный диабет\n"
            "2 — 🌾 Аллергия на глютен\n"
            "3 — 🥛 Непереносимость лактозы\n"
            "4 — 🥜 Аллергия на орехи\n"
            "5 — 💔 Высокое давление/сердечные\n"
            "6 — 🦴 Проблемы с суставами/связками",
            parse_mode="Markdown", reply_markup=cancel_menu())

    # ── Обхват талии ──
    elif text == "📏 Обхват талии":
        last = get_last_waist(cid)
        hint = f"\n\nПоследний замер: *{last[0]} см* ({last[1][:10]})" if last else ""
        set_state(cid, "waiting_waist")
        bot.send_message(cid,
            f"📏 *ОБХВАТ ТАЛИИ*\n\nИзмерь сантиметровой лентой на уровне пупка, "
            f"утром натощак, без втягивания живота.{hint}\n\n"
            f"Введи значение в см (например: *95*):",
            parse_mode="Markdown", reply_markup=cancel_menu())

    # ── Загрузить InBody PDF ──
    elif text == "📋 Загрузить InBody":
        if PDF_SUPPORT:
            set_state(cid, "waiting_inbody_pdf")
            bot.send_message(cid,
                "📋 *ЗАГРУЗКА ОТЧЁТА INBODY*\n\n"
                "Пришли PDF-файл отчёта с тренажёра InBody (через приложение DDX Fitness).\n\n"
                "Бот автоматически распознает:\n"
                "• Вес, мышечную массу, % жира\n"
                "• Воду, белок, кости в организме\n"
                "• Висцеральный жир, ИМТ\n"
                "• Обмен веществ и суточную норму калорий\n\n"
                "Просто прикрепи файл как документ 📎\n\n"
                "_Не получается? Нажми «✏️ Ввести вручную» ниже._",
                parse_mode="Markdown", reply_markup=inbody_choice_menu())
        else:
            bot.send_message(cid,
                "⚠️ *Автоматическое чтение PDF сейчас недоступно* на этом сервере.\n\n"
                "Но можно ввести результаты InBody вручную — нажми кнопку ниже.",
                parse_mode="Markdown", reply_markup=inbody_choice_menu())

    elif text == "✏️ Ввести вручную":
        set_state(cid, "inbody_manual_weight")
        bot.send_message(cid,
            "✏️ *РУЧНОЙ ВВОД INBODY*\n\n"
            "Введи данные по очереди — как они указаны в отчёте.\n\n"
            "1️⃣ Введи *вес* в кг (например: `108.4`):",
            parse_mode="Markdown", reply_markup=cancel_menu())

    # ── История InBody ──
    elif text == "📊 История InBody":
        history_text = build_inbody_history_text(cid)
        if not history_text:
            bot.send_message(cid,
                "📊 *История замеров InBody пуста.*\n\n"
                "Загрузи PDF-отчёт кнопкой *«📋 Загрузить InBody»*.",
                parse_mode="Markdown"); return
        last = get_last_inbody(cid)
        last_detail = ""
        if last:
            w, m, f, fm, water, prot, bone, visc, bmi, lean, bmr, tdee, opt, rdate, date = last
            last_detail = (
                f"\n\n📋 *Последний замер ({rdate or date[:10]}):*\n"
                f"⚖️ Вес: *{w} кг* | 💪 Мышцы: *{m} кг* | 🔥 Жир: *{f}%*\n"
            )
            if visc: last_detail += f"🎯 Висцеральный жир: *{visc}*\n"
            if bmi:  last_detail += f"📐 ИМТ: *{bmi}*\n"
        bot.send_message(cid,
            f"📊 *ИСТОРИЯ INBODY*\n{'─'*20}\n\n{history_text}{last_detail}",
            parse_mode="Markdown")

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
                wake_mins += 24 * 60
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

    # ── Разминка ──
    elif text == "🔥 Разминка":
        bot.send_message(cid, WARMUP, parse_mode="Markdown")

    # ── Заминка ──
    elif text == "🧘 Заминка":
        bot.send_message(cid, COOLDOWN, parse_mode="Markdown")

    # ── Расслабляющая ванна ──
    elif text == "🛁 Расслабляющая ванна":
        profile  = get_profile(cid)
        is_sick  = profile.get("is_sick") if profile else False
        hour     = now_samara().hour
        conds    = get_user_conditions(profile) if profile else []

        # Предупреждения по здоровью
        health_warn = ""
        if "давление" in conds:
            health_warn = ("\n\n⚠️ *Высокое давление:* горячие ванны (>38°C) противопоказаны! "
                           "Используй только тёплую воду 36-37°C и не более 10 мин.")
        elif "астма" in conds:
            health_warn = ("\n\n⚠️ *Астма:* избегай добавления эфирных масел эвкалипта и мяты "
                           "в закрытом помещении — могут спровоцировать спазм.")
        if is_sick:
            health_warn += "\n\n🤒 При болезни с температурой горячие ванны запрещены!"

        timing = ""
        if 20 <= hour or hour < 2:
            timing = "✅ Отличное время — вечерняя ванна расслабит мышцы и улучшит сон."
        elif hour < 12:
            timing = "🌅 Утренняя ванна тонизирует. Лучше чередовать тёплую и прохладную воду."
        else:
            timing = "🌞 Дневная ванна поможет снять усталость после тренировки."

        bot.send_message(cid,
            f"🛁 *ВАННЫ ДЛЯ ВОССТАНОВЛЕНИЯ И ПОХУДЕНИЯ*\n{'─'*26}\n\n"
            f"📍 Сейчас: {timing}{health_warn}\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "💪 *ВОССТАНОВИТЕЛЬНЫЕ ВАННЫ*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "🧂 *Ванна с морской солью*\n"
            "Снимает крепатуру и воспаление в мышцах после силовых.\n"
            "• Температура: *37-38°C*\n"
            "• Время: *15-20 мин*\n"
            "• Состав: 300-500г морской соли (без красителей)\n"
            "• Эффект: магний из соли проникает через кожу → расслабляет мышцы\n\n"

            "🌿 *Ванна с эфирными маслами*\n"
            "Снимает нервное напряжение, улучшает сон.\n"
            "• Температура: *36-37°C*\n"
            "• Время: *20 мин*\n"
            "• Состав: 5-7 капель масла лаванды + 1 ст.л. молока или мёда (эмульгатор)\n"
            "• Лучшее время: за 1-1.5 часа до сна\n\n"

            "🧪 *Ванна с содой и солью*\n"
            "Снимает отёки, мышечную усталость, выводит молочную кислоту.\n"
            "• Температура: *38°C*\n"
            "• Время: *20 мин*\n"
            "• Состав: 200г пищевой соды + 200г морской соли\n"
            "• После: ополоснись прохладной водой и отдохни 30 мин\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔥 *ВАННЫ ДЛЯ ПОХУДЕНИЯ*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "🌿 *Горчичная ванна*\n"
            "Разгоняет метаболизм, усиливает потоотделение и лимфодренаж.\n"
            "• Температура: *39-40°C*\n"
            "• Время: *10-15 мин* (не дольше!)\n"
            "• Состав: 4-6 ст.л. сухой горчицы, разведи в стакане тёплой воды и добавь в ванну\n"
            "• Эффект: +200-300 мл пота за сеанс, ускорение кровообращения\n"
            "• После: тепло укройся на 30-40 мин\n"
            "• ⚠️ Не чаще 2-3 раз в неделю. При жжении — сразу смыть!\n\n"

            "🍵 *Ванна с имбирём*\n"
            "Термогенный эффект — тело продолжает «гореть» ещё 1-2 часа после.\n"
            "• Температура: *39°C*\n"
            "• Время: *15-20 мин*\n"
            "• Состав: 3-4 ст.л. молотого имбиря (или отвар из 100г свежего) + щепотка корицы\n"
            "• Эффект: усиливает жиросжигание за счёт повышения температуры тела\n"
            "• Лучшее время: после тренировки\n\n"

            "🧂 *Ванна с морской солью и эфирными маслами цитрусовых*\n"
            "Лимфодренаж, борьба с целлюлитом, вывод лишней жидкости.\n"
            "• Температура: *38-39°C*\n"
            "• Время: *20 мин*\n"
            "• Состав: 500г морской соли + 5 капель масла грейпфрута + 3 капли апельсина\n"
            "• Усилить эффект: массаж проблемных зон жёсткой мочалкой ДО ванны\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📋 *ОБЩИЕ ПРАВИЛА*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• Принимай ванну не раньше *чем через 1 час после еды*\n"
            "• Выпей *250-300мл воды* до ванны и после — потери жидкости восполнить!\n"
            "• Не принимай горячую ванну *непосредственно перед сном* (за 1.5-2 часа — норм)\n"
            "• При головокружении — *сразу выходи* из ванны\n"
            "• Максимальная частота горячих ванн — *3 раза в неделю*\n\n"
            "💡 Ванны дополняют дефицит калорий и тренировки, но сами по себе жир не жгут — "
            "это вспомогательный инструмент для восстановления и снятия стресса.",
            parse_mode="Markdown")

    # ── Прогноз цели ──
    # ── Прогноз цели ──
    elif text == "🎯 Прогноз цели":
        profile = get_profile(cid)
        if not profile:
            bot.send_message(cid, "Сначала настрой профиль."); return
        wd = get_weights(cid)
        if len(wd) < 2:
            bot.send_message(cid, "Нужно минимум 2 взвешивания для прогноза.\n\nВноси вес регулярно — хотя бы раз в 3-4 дня."); return
        goal_date, weeks_left = calc_goal_date(cid)
        target = profile.get("target_weight") or 92
        curr_w = wd[-1][0]
        a = analyze_progress(wd)
        rate = a["rate"] if a else 0
        if not goal_date:
            if curr_w <= target:
                bot.send_message(cid, f"🎉 *Цель достигнута!*\n\nТекущий вес *{curr_w} кг* ≤ цели *{target} кг*.\nПоддерживающий режим активен.", parse_mode="Markdown")
            else:
                bot.send_message(cid, "📊 Недостаточно данных для прогноза.\nПродолжай вносить вес регулярно.", parse_mode="Markdown")
            return
        user_deadline = profile.get("deadline_weeks") or 12
        verdict = "✅ Укладываешься в срок!" if weeks_left <= user_deadline else f"⚠️ Чуть дольше чем планировал ({user_deadline} нед.)."
        bot.send_message(cid,
            f"🎯 *ПРОГНОЗ ДОСТИЖЕНИЯ ЦЕЛИ*\n{'─'*24}\n\n"
            f"⚖️ Сейчас: *{curr_w} кг*\n"
            f"🏁 Цель: *{target} кг*\n"
            f"📉 Осталось: *{round(curr_w-target,1)} кг*\n\n"
            f"📈 Темп: *{abs(rate)} кг/нед*\n"
            f"📅 Прогнозируемая дата: *{goal_date}*\n"
            f"⏱️ Осталось: *~{weeks_left} нед.*\n\n"
            f"{verdict}\n\n"
            "💡 Прогноз пересчитывается после каждого взвешивания.",
            parse_mode="Markdown")

    # ── Серия дней ──
    elif text == "🔥 Серия дней":
        current, best = get_streak(cid)
        if current == 0:
            bot.send_message(cid,
                "🔥 *СЕРИЯ ДНЕЙ*\n\nСерия ещё не начата.\n\n"
                "Вноси данные каждый день (вес, шаги или воду) — бот считает серию автоматически.",
                parse_mode="Markdown"); return
        medal = "🥇" if current >= 30 else ("🥈" if current >= 14 else ("🥉" if current >= 7 else "🔥"))
        record = " 🏆 Новый рекорд!" if current == best and current > 1 else ""
        bot.send_message(cid,
            f"🔥 *СЕРИЯ ДНЕЙ*\n{'─'*20}\n\n"
            f"{medal} Текущая серия: *{current} дней подряд*{record}\n"
            f"🏆 Лучшая серия: *{best} дней*\n\n"
            "💡 Серия считается если ты вносил данные каждый день.\n"
            "Пропуск одного дня — серия обнуляется!",
            parse_mode="Markdown")

    # ── Список покупок ──
    elif text == "🛒 Список покупок":
        shopping = build_shopping_list(cid)
        if not shopping:
            bot.send_message(cid, "Сначала настрой профиль."); return
        bot.send_message(cid, shopping, parse_mode="Markdown")

    # ── Самочувствие ──
    elif text == "😊 Самочувствие":
        set_state(cid, "wellbeing_mood")
        m2 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
        m2.add(*[types.KeyboardButton(str(i)) for i in range(1,6)])
        m2.add(types.KeyboardButton("❌ Отмена"))
        bot.send_message(cid,
            "😊 *ТРЕКЕР САМОЧУВСТВИЯ*\n\n"
            "Оцени *настроение* сегодня:\n\n"
            "1 — Ужасное 😞\n2 — Плохое 😕\n3 — Нормальное 😐\n"
            "4 — Хорошее 😊\n5 — Отличное 🌟",
            parse_mode="Markdown", reply_markup=m2)

    # ── Журнал весов ──
    elif text == "🏋️ Журнал весов":
        exercises = get_all_exercises(cid)
        if not exercises:
            set_state(cid, "log_exercise_name")
            bot.send_message(cid,
                "🏋️ *ЖУРНАЛ ВЕСОВ*\n\nИстория пуста.\nВведи название упражнения (например: *Жим гантелей*):",
                parse_mode="Markdown", reply_markup=cancel_menu())
        else:
            m2 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            for ex in exercises: m2.add(types.KeyboardButton(f"📊 {ex}"))
            m2.add(types.KeyboardButton("➕ Добавить упражнение"))
            m2.add(types.KeyboardButton("❌ Отмена"))
            bot.send_message(cid, "🏋️ *ЖУРНАЛ ВЕСОВ*\n\nВыбери упражнение:",
                parse_mode="Markdown", reply_markup=m2)

    elif text == "➕ Добавить упражнение":
        set_state(cid, "log_exercise_name")
        bot.send_message(cid, "Введи название упражнения (например: *Жим гантелей*):",
                         parse_mode="Markdown", reply_markup=cancel_menu())

    elif text.startswith("📊 ") and state == "idle":
        exercise = text[2:]
        if exercise in get_all_exercises(cid):
            history = get_exercise_history(cid, exercise)
            lines_ex = [f"• {d[:10]}: *{w}кг* × {r} повт. × {s} подх." for w,r,s,d in history]
            progress = ""
            if len(history) >= 2:
                diff = round(history[-1][0] - history[-2][0], 1)
                if diff > 0:   progress = f"\n📈 Прогресс: *+{diff} кг* к прошлой тренировке! 💪"
                elif diff < 0: progress = f"\n📉 На {abs(diff)} кг меньше чем прошлый раз."
                else:          progress = "\n➡️ Вес такой же — попробуй добавить повторение."
            set_state(cid, "log_exercise_name_known", extra=exercise)
            m2 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            m2.add(types.KeyboardButton("✏️ Записать новый подход"))
            m2.add(types.KeyboardButton("❌ Отмена"))
            bot.send_message(cid,
                f"🏋️ *{exercise}*\n{'─'*20}\n\n"
                + ("\n".join(lines_ex) if lines_ex else "История пуста") +
                f"{progress}\n\nЗаписать результат?",
                parse_mode="Markdown", reply_markup=m2)

    elif text == "✏️ Записать новый подход" and extra:
        set_state(cid, "log_exercise_weight", extra=extra)
        bot.send_message(cid,
            f"*{extra}*\n\nВведи через пробел: *вес повторения подходы*\n"
            "Например: *20 12 4*",
            parse_mode="Markdown", reply_markup=cancel_menu())

    # ── Дневник питания ──
    elif text == "📓 Дневник питания":
        rows        = get_food_today(cid)
        total_kcal  = get_kcal_today(cid)
        profile     = get_profile(cid)
        target_kcal = get_user_plan(cid, profile)["calories"] if profile else 2000
        remain      = target_kcal - total_kcal
        if not rows:
            msg = "📓 *ДНЕВНИК ПИТАНИЯ*\n\nСегодня пусто. Начни записывать что ешь!"
        else:
            meal_groups = {}
            for meal, product, grams, kcal in rows:
                if meal not in meal_groups: meal_groups[meal] = []
                meal_groups[meal].append(f"  • {product} {grams}г = {round(kcal)} ккал")
            lines_d = []
            for meal, items in meal_groups.items():
                lines_d.append(f"*{meal}:*")
                lines_d.extend(items)
            bar_f  = min(int(total_kcal / target_kcal * 10), 10) if target_kcal > 0 else 0
            bar    = "🟩" * bar_f + "⬜" * (10 - bar_f)
            status = "✅ Норма!" if abs(remain)<100 else (f"⬇️ Ещё {remain} ккал" if remain>0 else f"⚠️ Превышение на {abs(remain)} ккал")
            msg    = (f"📓 *ДНЕВНИК ПИТАНИЯ*\n{'─'*24}\n\n" +
                      "\n".join(lines_d) +
                      f"\n\n{bar}\n🔥 Итого: *{total_kcal}* / *{target_kcal} ккал*\n{status}")
        m2 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        m2.add(types.KeyboardButton("➕ Записать приём пищи"),
               types.KeyboardButton("❌ Закрыть дневник"))
        bot.send_message(cid, msg, parse_mode="Markdown", reply_markup=m2)

    elif text == "➕ Записать приём пищи":
        set_state(cid, "diary_choose_meal")
        m2 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for meal in ["🍳 Завтрак","🍗 Обед","🍎 Полдник","🌙 Ужин","🍵 Перекус"]:
            m2.add(types.KeyboardButton(meal))
        m2.add(types.KeyboardButton("❌ Отмена"))
        bot.send_message(cid, "Выбери приём пищи:", reply_markup=m2)

    elif text == "❌ Закрыть дневник":
        bot.send_message(cid, "Дневник закрыт.", reply_markup=main_menu(cid))

    # ── Калькулятор ──
    elif text == "🧮 Калькулятор ккал":
        set_state(cid, "calc_product")
        sample = ", ".join(list(KCAL_PER_100G.keys())[:15])
        bot.send_message(cid,
            "🧮 *КАЛЬКУЛЯТОР КАЛОРИЙ*\n\n"
            "Введи название продукта и граммы через пробел:\n\n"
            "Например: *куриная грудка 150*\nИли: *гречка 80*\n\n"
            f"Продукты в базе: {sample} и др.",
            parse_mode="Markdown", reply_markup=cancel_menu())

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

    # ── Тренировка дома ──
    elif text == "🏠 Тренировка дома":
        profile = get_profile(cid)
        if not profile:
            bot.send_message(cid,"Сначала настрой профиль.",reply_markup=main_menu(cid)); return
        if profile.get("is_sick"):
            bot.send_message(cid,"🤒 При болезни тренировки не рекомендуются.",reply_markup=main_menu(cid)); return
        weekday  = now_samara().weekday()
        gym_days = profile.get("gym_days") or 3
        schedule = get_week_schedule(profile, gym_days)
        wkey     = schedule.get(weekday)
        # Определяем какая домашняя тренировка
        if wkey and wkey.startswith("Д"):
            name, exercises = WORKOUTS.get(wkey, WORKOUTS["ДА"])
            fatigue = int(profile.get("fatigue") or 0)
            adj_key, fnote = adjust_workout_for_fatigue(wkey, fatigue)
            # Для домашних тренировок при высокой усталости — лёгкий вариант дома
            if adj_key == "К": adj_key = "ДК"
            name, exercises = WORKOUTS.get(adj_key, WORKOUTS["ДА"])
            msg = (f"🏠 *ДОМАШНЯЯ ТРЕНИРОВКА СЕГОДНЯ*\n*{name}*\n\n"
                   f"{fnote}\n\n🏋️ *Упражнения:*\n{exercises}\n\n"
                   f"💡 Нужно: коврик, стул или диван.\n"
                   f"После нажми *«✅ Тренировка завершена»*.")
        else:
            # Сегодня не домашний день по расписанию — предлагаем на выбор
            m2 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            m2.add(types.KeyboardButton("🏠 ДА — Грудь+Кор"),
                   types.KeyboardButton("🏠 ДБ — Ноги+Спина"),
                   types.KeyboardButton("🏠 ДВ — Всё тело"),
                   types.KeyboardButton("🏠 ДК — Кардио дома"),
                   types.KeyboardButton("❌ Отмена"))
            bot.send_message(cid,
                "🏠 *Сегодня не запланирована домашняя тренировка.*\n\n"
                "Но если хочешь потренироваться дома — выбери комплекс:",
                parse_mode="Markdown", reply_markup=m2)
            return
        bot.send_message(cid, msg, parse_mode="Markdown")

    elif text in ("🏠 ДА — Грудь+Кор","🏠 ДБ — Ноги+Спина","🏠 ДВ — Всё тело","🏠 ДК — Кардио дома"):
        key_map = {"🏠 ДА — Грудь+Кор":"ДА","🏠 ДБ — Ноги+Спина":"ДБ",
                   "🏠 ДВ — Всё тело":"ДВ","🏠 ДК — Кардио дома":"ДК"}
        wkey = key_map[text]
        name, exercises = WORKOUTS.get(wkey, WORKOUTS["ДА"])
        bot.send_message(cid,
            f"🏠 *ДОМАШНЯЯ ТРЕНИРОВКА*\n*{name}*\n\n"
            f"🏋️ *Упражнения:*\n{exercises}\n\n"
            f"💡 Нужно: коврик, стул или диван.\n"
            f"После нажми *«✅ Тренировка завершена»*.",
            parse_mode="Markdown", reply_markup=main_menu(cid))

    # ── Рецепты блюд ──
    elif text == "🍝 Рецепты блюд":
        dishes = list(RECIPES.keys())
        m2 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for d in dishes: m2.add(types.KeyboardButton(f"📖 {d}"))
        m2.add(types.KeyboardButton("❌ Отмена"))
        bot.send_message(cid,
            "🍝 *РЕЦЕПТЫ БЛЮД*\n\nВыбери блюдо — получишь пошаговый рецепт с калорийностью:",
            parse_mode="Markdown", reply_markup=m2)

    elif text.startswith("📖 ") and text[2:] in RECIPES:
        dish = text[2:]
        card = build_recipe_card(dish, get_profile(cid))
        kb_inline = types.InlineKeyboardMarkup()
        kb_inline.add(
            types.InlineKeyboardButton("➕ Добавить в дневник питания", callback_data=f"add_to_diary:{dish}"),
            types.InlineKeyboardButton("🍽️ Открыть рацион", callback_data="open_ration"),
        )
        bot.send_message(cid, card, parse_mode="Markdown", reply_markup=kb_inline)
        bot.send_message(cid, "⬆️ Что сделать с этим блюдом?", reply_markup=main_menu(cid))

    # ── Дневник питания ──
    elif text == "📊 Дневник питания":
        today = now_samara().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS food_diary (uid INTEGER, date TEXT, food TEXT, grams INTEGER, kcal INTEGER)")
        c.execute("SELECT food, grams, kcal FROM food_diary WHERE uid=? AND date=? ORDER BY rowid", (cid, today))
        rows = c.fetchall()
        conn.close()
        if not rows:
            # Показываем рацион как план + предложение добавить
            ration, cal = build_ration(cid)
            ration_kb = ration_recipe_inline(ration)
            bot.send_message(cid,
                "📊 *ДНЕВНИК ПИТАНИЯ*\n\nСегодня ещё ничего не записано.\n\n"
                "📋 _Открой рецепт любого блюда и нажми «➕ Добавить в дневник»_\n"
                "или выбери из рациона ниже:",
                parse_mode="Markdown")
            bot.send_message(cid,
                f"🍽️ *Рацион на сегодня:*\n{ration}",
                parse_mode="Markdown",
                reply_markup=ration_kb if ration_kb else main_menu(cid))
            if ration_kb:
                bot.send_message(cid, "⬆️ Нажми на блюдо для рецепта и добавления:", reply_markup=main_menu(cid))
        else:
            total_kcal = sum(r[2] for r in rows)
            profile = get_profile(cid)
            day_norm = profile.get("ration_kcal", 0) if profile else 0
            if not day_norm and profile:
                plan = get_user_plan(cid, profile)
                day_norm = plan.get("calories", 2000)
            remain = day_norm - total_kcal if day_norm else 0
            lines = "\n".join(f"• {r[0]} — {r[1]}г / {r[2]} ккал" for r in rows)
            remain_str = f"\n\n🎯 Осталось: *{remain} ккал* из *{day_norm}*" if day_norm else ""
            bar_filled = min(10, round(total_kcal / day_norm * 10)) if day_norm else 0
            bar = "🟩" * bar_filled + "⬜" * (10 - bar_filled)
            bot.send_message(cid,
                f"📊 *ДНЕВНИК ПИТАНИЯ — СЕГОДНЯ*\n\n"
                f"{lines}\n\n"
                f"─────────────\n"
                f"🔥 Итого: *{total_kcal} ккал*{remain_str}\n"
                f"{bar}",
                parse_mode="Markdown", reply_markup=main_menu(cid))

    # ── Умный выбор блюда ──
    elif text == "🍴 Выбрать блюдо":
        set_state(cid, "smart_food_category")
        bot.send_message(cid,
            "🍴 *УМНЫЙ ВЫБОР БЛЮДА*\n\nВыбери категорию — я сам рассчитаю порцию под твой калораж:",
            parse_mode="Markdown", reply_markup=build_smart_food_menu())

    # ── Вода в мл ──
    elif text == "💧 Вода (мл)":
        kb_water = types.InlineKeyboardMarkup(row_width=3)
        kb_water.add(
            types.InlineKeyboardButton("200 мл", callback_data="water_ml:200"),
            types.InlineKeyboardButton("300 мл", callback_data="water_ml:300"),
            types.InlineKeyboardButton("500 мл", callback_data="water_ml:500"),
            types.InlineKeyboardButton("750 мл", callback_data="water_ml:750"),
            types.InlineKeyboardButton("1000 мл", callback_data="water_ml:1000"),
            types.InlineKeyboardButton("✏️ Своё", callback_data="water_ml:custom"),
        )
        bot.send_message(cid, build_water_ml_status(cid) + "\n\nДобавить:", parse_mode="Markdown", reply_markup=kb_water)

    # ── Штрихкод ──
    elif text == "📦 Штрихкод":
        set_state(cid, "waiting_barcode")
        bot.send_message(cid, "📦 *Поиск по штрихкоду*\n\nВведи штрихкод с упаковки (цифры):\nНапример: `4607099494049`",
                         parse_mode="Markdown", reply_markup=cancel_menu())

    # ── Стресс-дневник ──
    elif text == "🧠 Стресс":
        rows = get_stress_history(cid, 7)
        kb_stress = types.InlineKeyboardMarkup(row_width=5)
        kb_stress.add(*[types.InlineKeyboardButton(str(i), callback_data=f"stress_log:{i}") for i in range(1, 11)])
        report = build_stress_report(cid)
        bot.send_message(cid, report + "\n\nОцени уровень стресса сегодня (1=спокойно, 10=максимум):",
                         parse_mode="Markdown", reply_markup=kb_stress)

    # ── Цикл ──
    elif text == "🩸 Цикл":
        result = get_cycle_phase(cid)
        kb_cycle = types.InlineKeyboardMarkup()
        kb_cycle.add(types.InlineKeyboardButton("🩸 Начало цикла сегодня", callback_data="cycle_start"))
        if result:
            day, phase, text_phase = result
            bot.send_message(cid, f"📅 День цикла: *{day}*\n\n{text_phase}", parse_mode="Markdown", reply_markup=kb_cycle)
        else:
            bot.send_message(cid, "🩸 *Менструальный цикл*\n\nОтметь начало цикла для персональных рекомендаций по тренировкам и питанию.",
                             parse_mode="Markdown", reply_markup=kb_cycle)

    # ── HRV / Пульс покоя ──
    elif text == "💓 HRV / Пульс":
        bot.send_message(cid, build_hrv_report(cid) + "\n\nВведи данные: /hrv 65 55\n(HRV пульс_покоя)", parse_mode="Markdown")

    # ── Фото-прогресс ──
    elif text == "📷 Фото-прогресс":
        bot.send_message(cid, build_body_photos_menu(cid) + "\n\nОтправь фото с подписью *#прогресс*",
                         parse_mode="Markdown")

    # ── Рекорды 1RM ──
    elif text == "🏆 Рекорды (1RM)":
        bot.send_message(cid, build_1rm_report(cid), parse_mode="Markdown")

    # ── 8-недельная программа ──
    elif text == "📅 Программа на 8 нед":
        bot.send_message(cid, build_8week_program(cid), parse_mode="Markdown")

    # ── ИИ-анализ недели ──
    elif text == "🤖 ИИ-анализ недели":
        bot.send_message(cid, "⏳ Анализирую данные недели...", parse_mode="Markdown")
        result = build_ai_week_analysis(cid)
        bot.send_message(cid, result, parse_mode="Markdown")

    # ── Прогноз «что будет если» ──
    elif text == "🔮 Прогноз «Что если»":
        kb_scenario = types.InlineKeyboardMarkup(row_width=1)
        kb_scenario.add(
            types.InlineKeyboardButton("❌ Пропущу 3 тренировки", callback_data="scenario:пропущу 3 тренировки"),
            types.InlineKeyboardButton("🍕 Съем лишние 500 ккал/день", callback_data="scenario:съем лишние 500 ккал"),
            types.InlineKeyboardButton("✅ Буду тренироваться каждый день", callback_data="scenario:буду тренироваться каждый день"),
        )
        bot.send_message(cid, "🔮 *Прогноз «Что будет если...»*\n\nВыбери сценарий:",
                         parse_mode="Markdown", reply_markup=kb_scenario)

    # ── Импорт Apple Health / Google Fit ──
    elif text == "📥 Импорт Health/Fit":
        bot.send_message(cid,
            "📥 *Импорт данных*\n\n"
            "Отправь CSV-файл из Apple Health или Google Fit.\n\n"
            "*Apple Health:* Здоровье → Профиль → Экспорт данных\n"
            "*Google Fit:* takeout.google.com → Google Fit\n\n"
            "Бот импортирует шаги и вес автоматически.",
            parse_mode="Markdown")
        set_state(cid, "waiting_health_import")

    # ── Мини-игра: угадай калорийность ──
    elif text == "🎮 Угадай калории":
        msg, kb_quiz = build_kcal_quiz_message(cid)
        bot.send_message(cid, msg, parse_mode="Markdown", reply_markup=kb_quiz)

    # ── Интервальное голодание ──
    elif text == "⏳ Интервальное голодание":
        msg, kb_if = build_fasting_status(cid)
        bot.send_message(cid, msg, parse_mode="Markdown", reply_markup=kb_if)

    # ── Сравнение дней КБЖУ ──
    elif text == "📊 День vs вчера":
        bot.send_message(cid, build_compare_days_kcal(cid), parse_mode="Markdown")

    # ── Алкоголь-трекер ──
    elif text == "🍺 Алкоголь-трекер":
        msg, kb_alc = build_alcohol_menu(cid)
        bot.send_message(cid, msg, parse_mode="Markdown", reply_markup=kb_alc)

    # ── Избранные блюда ──
    elif text == "⭐ Избранные блюда":
        result = build_favorites_menu(cid)
        if isinstance(result, tuple):
            txt, kb_fav = result
            bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=kb_fav)
        else:
            bot.send_message(cid, result)

    # ── ГИ продукта ──
    elif text == "🍎 ГИ продукта":
        bot.send_message(cid, "Введи название продукта для проверки ГИ:")
        set_state(cid, "waiting_gi_product")

    # ── Журнал упражнений ──
    elif text == "📒 Журнал упражнений":
        bot.send_message(cid, "Введи название упражнения для просмотра истории:\n\n_(например: жим лёжа, приседания, тяга)_",
                         parse_mode="Markdown")
        set_state(cid, "waiting_exercise_history")

    # ── Стрик активности ──
    elif text == "🔥 Стрик активности":
        bot.send_message(cid, build_activity_streak(cid), parse_mode="Markdown")

    # ── Разминка по мышцам ──
    elif text == "🤸 Разминка по мышцам":
        msg, kb_warmup = build_warmup_menu()
        bot.send_message(cid, msg, parse_mode="Markdown", reply_markup=kb_warmup)

    # ── Пульсовые зоны ──
    elif text == "❤️ Пульсовые зоны":
        result = build_hr_zones(cid)
        if isinstance(result, tuple):
            msg, kb_hr = result
            bot.send_message(cid, msg, parse_mode="Markdown", reply_markup=kb_hr)
        else:
            bot.send_message(cid, result, parse_mode="Markdown")

    # ── Помощь / команды ──
    elif text == "❓ Помощь / команды":
        kb_help = types.InlineKeyboardMarkup(row_width=2)
        kb_help.add(
            types.InlineKeyboardButton("🍽️ Питание", callback_data="help_section:food"),
            types.InlineKeyboardButton("🏋️ Тренировки", callback_data="help_section:workout"),
            types.InlineKeyboardButton("📊 Тело", callback_data="help_section:body"),
            types.InlineKeyboardButton("📈 Аналитика", callback_data="help_section:analytics"),
            types.InlineKeyboardButton("😴 Здоровье", callback_data="help_section:health"),
            types.InlineKeyboardButton("⚡ Команды", callback_data="help_section:commands"),
        )
        bot.send_message(cid, build_help_message(), parse_mode="Markdown", reply_markup=kb_help)

    # ── Счётчик привычек ──
    elif text == "✔️ Привычки":
        kb_habits = build_habits_keyboard(cid)
        done = get_habits_today(cid)
        bot.send_message(cid,
            f"✔️ *Трекер привычек — сегодня*\n\nВыполнено: *{len(done)}/{len(DEFAULT_HABITS)}*\n\nНажми чтобы отметить:",
            parse_mode="Markdown", reply_markup=kb_habits)

    # ── Заметки ──
    elif text == "📝 Заметки":
        result = build_notes_menu(cid)
        if isinstance(result, tuple):
            txt, kb_notes = result
            bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=kb_notes)
        else:
            bot.send_message(cid, result, parse_mode="Markdown")

    # ── Норма воды ──
    elif text == "💧 Норма воды":
        bot.send_message(cid, build_water_norm(cid), parse_mode="Markdown")

    # ── Норма белка ──
    elif text == "💪 Норма белка":
        bot.send_message(cid, build_protein_calc(cid), parse_mode="Markdown")

    # ── Личные рекорды ──
    elif text == "🏆 Личные рекорды":
        bot.send_message(cid, build_personal_records(cid), parse_mode="Markdown")

    else:
        # Умный fallback: пробуем распознать "продукт граммы" (напр. "гречка 200")
        parts = text.strip().rsplit(" ", 1)
        if len(parts) == 2:
            try:
                grams = float(parts[1].replace(",", "."))
                product = parts[0].lower().strip()
                if 0 < grams < 5000 and product:
                    kcal_p = KCAL_PER_100G.get(product)
                    if not kcal_p:
                        matches = [k for k in KCAL_PER_100G if product in k or k in product]
                        if matches:
                            product = matches[0]
                            kcal_p = KCAL_PER_100G[product]
                    if kcal_p:
                        kcal = round(kcal_p * grams / 100)
                        is_fav = product in get_favorite_dishes(cid)
                        kb_calc = types.InlineKeyboardMarkup()
                        kb_calc.add(
                            types.InlineKeyboardButton("✅ Записать", callback_data=f"add_to_diary:{product}:{int(grams)}"),
                            types.InlineKeyboardButton("❌ Нет", callback_data="close")
                        )
                        if not is_fav:
                            kb_calc.add(types.InlineKeyboardButton(
                                "⭐ В избранное", callback_data=f"fav_add:{product}"))
                        bot.send_message(cid,
                            f"🧮 *{product.capitalize()}* {grams}г = *{kcal} ккал*\n\n"
                            f"Записать в дневник питания?",
                            parse_mode="Markdown", reply_markup=kb_calc)
                        return
            except Exception:
                pass
        bot.send_message(cid,
            "Используй кнопки меню ниже 👇\n\n"
            "💡 *Быстрые команды:*\n"
            "`/w 105.7` — записать вес\n"
            "`/s 8500` — записать шаги\n"
            "`/water 3` — записать воду\n\n"
            "Или просто напиши продукт с граммами:\n"
            "`гречка 200`",
            parse_mode="Markdown", reply_markup=main_menu(cid))

if __name__ == '__main__':
    init_db()
    # Запуск фонового потока напоминаний
    t=threading.Thread(target=reminder_worker,daemon=True)
    t.start()
    print("Бот v7 запущен! Самара UTC+4 | Напоминания | Полуфабрикаты | Читмил | График | Экспорт")
    bot.infinity_polling()
