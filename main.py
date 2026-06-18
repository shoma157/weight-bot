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
        health_conditions TEXT DEFAULT "")''')
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
    # Миграция
    for col, dflt in [
        ("fatigue","0"), ("last_workout_date","''"), ("next_workout_override","''"),
        ("reminders_enabled","1"), ("cheatmeal_used","0"), ("cheatmeal_week","''"),
        ("is_driver","0"),
        ("home_workouts","0"),
        ("health_conditions","''"),
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
            "reminders_enabled","cheatmeal_used","cheatmeal_week","is_driver","home_workouts",
            "health_conditions"]
    d = dict(zip(keys, row))
    # Приводим типы
    for k in ("is_sick","fatigue","reminders_enabled","cheatmeal_used","is_driver","home_workouts"):
        d[k] = int(d[k]) if d[k] else 0
    d["health_conditions"] = d.get("health_conditions") or ""
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
    plan = calc_plan(profile)
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

    schedule = dict(s.get(gd, s.get(3, {})))

    # Если домашние тренировки включены — добавляем их в свободные дни
    if home_mode:
        home_rotation = ["ДА","ДБ","ДВ","ДК"]
        home_idx = 0
        for day in range(7):
            if day not in schedule:
                # Добавляем домашнюю тренировку через день (не каждый свободный день)
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
    text = (f"{tag} *ТРЕНИРОВКА СЕГОДНЯ{orig}*\n*{name}*\n\n"
            f"{fnote}\n\n🏋️ *Упражнения:*\n{exercises}"
            f"{health_note_block}\n\n"
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
#  РЕЦЕПТЫ НОВЫХ БЛЮД
# ─────────────────────────────────────────

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
}

def build_recipe_card(dish_name):
    """Строит карточку рецепта блюда"""
    r = RECIPES.get(dish_name)
    if not r:
        return None
    grams = DEFAULT_PORTIONS.get(dish_name, 200)
    return (
        f"{r['emoji']} *{dish_name.upper()}*\n{'─'*22}\n\n"
        f"⏱️ Время приготовления: *{r['time']}*\n"
        f"🔥 Калорийность порции: *{r['kcal_portion']}*\n\n"
        f"🛒 *Ингредиенты:*\n{r['ingredients']}\n\n"
        f"👨‍🍳 *Приготовление:*\n{r['steps']}\n\n"
        f"{r['tip']}"
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
    ("setup_home",     "🏠 Готов ли ты иногда тренироваться *дома* (без похода в зал)?\n\n"
                       "1 — Да, иногда хочу тренироваться дома\n"
                       "2 — Нет, только зал"),
    ("setup_driver",   "🚗 Ты водитель или работаешь в основном сидя?\n\n1 — Да (водитель, офис)\n2 — Нет, есть физическая активность на работе"),
    ("setup_health",   "🏥 Есть ли у тебя ограничения по здоровью? Бот будет автоматически исключать опасные продукты и упражнения.\n\n"
                       "Выбери цифры через запятую (например: `1,3`) или `0` если ограничений нет:\n\n"
                       "1 — 🩸 Сахарный диабет\n"
                       "2 — 🌾 Аллергия на глютен\n"
                       "3 — 🥛 Непереносимость лактозы\n"
                       "4 — 🥜 Аллергия на орехи\n"
                       "5 — 💔 Высокое давление/сердечные\n"
                       "6 — 🦴 Проблемы с суставами/связками\n"
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
            assert text in ("1","2"); save_profile(cid,home_workouts=1 if text=="1" else 0)
        elif state == "setup_driver":
            assert text in ("1","2"); save_profile(cid,is_driver=1 if text=="1" else 0)
        elif state == "setup_health":
            condition_map = {"1":"диабет","2":"аллергия_глютен","3":"аллергия_лактоза",
                             "4":"аллергия_орехи","5":"давление","6":"суставы"}
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
                 "setup_deadline":"Недели: 12","setup_home":"Введи 1 или 2","setup_driver":"Введи 1 или 2",
                 "setup_health":"Введи цифры через запятую (1,3) или 0"}
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
        types.KeyboardButton("🏥 Мои ограничения"),
        types.KeyboardButton("🏠 Тренировка дома"),
        types.KeyboardButton("🔥 Разминка"),
        types.KeyboardButton("🧘 Заминка"),
        types.KeyboardButton("🍝 Рецепты блюд"),
        types.KeyboardButton("📓 Дневник питания"),
        types.KeyboardButton("🧮 Калькулятор ккал"),
        types.KeyboardButton("🏋️ Журнал весов"),
        types.KeyboardButton("🛒 Список покупок"),
        types.KeyboardButton("😊 Самочувствие"),
        types.KeyboardButton("🎯 Прогноз цели"),
        types.KeyboardButton("🔥 Серия дней"),
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
            target_kcal = calc_plan(profile)["calories"] if profile else 2000
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
    if state == "edit_health":
        condition_map = {"1":"диабет","2":"аллергия_глютен","3":"аллергия_лактоза",
                         "4":"аллергия_орехи","5":"давление","6":"суставы"}
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
        plan=calc_plan(profile); wd=get_weights(cid)
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

    # ── Разминка ──
    elif text == "🔥 Разминка":
        bot.send_message(cid, WARMUP, parse_mode="Markdown")

    # ── Заминка ──
    elif text == "🧘 Заминка":
        bot.send_message(cid, COOLDOWN, parse_mode="Markdown")

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
        target_kcal = calc_plan(profile)["calories"] if profile else 2000
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
        card = build_recipe_card(dish)
        bot.send_message(cid, card, parse_mode="Markdown", reply_markup=main_menu(cid))

    else:
        bot.send_message(cid,"Используй кнопки меню.",reply_markup=main_menu(cid))

if __name__ == '__main__':
    init_db()
    # Запуск фонового потока напоминаний
    t=threading.Thread(target=reminder_worker,daemon=True)
    t.start()
    print("Бот v7 запущен! Самара UTC+4 | Напоминания | Полуфабрикаты | Читмил | График | Экспорт")
    bot.infinity_polling()
