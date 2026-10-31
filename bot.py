import json
import telebot
from telebot import types, custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from config import TOKEN

bot = telebot.TeleBot(TOKEN, state_storage=StateMemoryStorage())

MENYU = {
    "pitsa": ("Pitsa", 45000),
    "burger": ("Burger", 30000),
    "lavash": ("Lavash", 25000),
    "choy": ("Choy", 5000),
}
class Buyurtma(StatesGroup):
    taom = State()
    soni = State()
    tasdiq = State()

FAYL = "buyurtmalar.json"

def yukla():
    try:
        with open(FAYL, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
def saqla(data):
    with open(FAYL, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
def asosiy_menyu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("Buyurtma berish", "Mening buyurtmam")
    m.row("Menyu", "Yordam")
    return m
def taom_tugmalari():
    m = types.InlineKeyboardMarkup(row_width=2)
    for kod, (nom, narx) in MENYU.items():
        m.add(types.InlineKeyboardButton(f"{nom} — {narx} so'm", callback_data=f"taom_{kod}"))
    return m
def tasdiq_tugmalari():
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("Ha", callback_data="ha"),
          types.InlineKeyboardButton("Yo'q", callback_data="yoq"))
    return m
def royxat_matni(royxat):
    matn = "Sizning buyurtmalaringiz:\n"
    for i, v in enumerate(royxat, 1):
        matn += f"{i}. {v}\n"
    return matn + "\nBekor qilish — raqamni bosing"
def bekor_tugmalari(royxat):
    m = types.InlineKeyboardMarkup(row_width=5)
    for i in range(len(royxat)):
        m.add(types.InlineKeyboardButton(f"{i + 1}", callback_data=f"bekor_{i}"))
    return m
@bot.message_handler(commands=["cancel"])
def cancel(message):
    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(message.chat.id, "Bekor qilindi.", reply_markup=asosiy_menyu())
@bot.message_handler(commands=["start"])
def start(message):
    bot.delete_state(message.from_user.id, message.chat.id)
    ism = message.from_user.first_name
    bot.send_message(message.chat.id,
                     f"Salom, <b>{ism}</b>! Ustudy kafega xush kelibsiz.\nPastdagi tugmalardan tanlang ",
                     parse_mode="HTML", reply_markup=asosiy_menyu())
@bot.message_handler(commands=["help"])
def yordam(message):
    bot.send_message(message.chat.id,
                     "Yordam:\nBuyurtma berish — taom tanlang\nMening buyurtmam — buyurtmalaringiz\n/cancel — bekor qilish")
@bot.message_handler(commands=["menyu"])
def menyu(message):
    matn = "Menyu:\n"
    for nom, narx in MENYU.values():
        matn += f"{nom} — {narx} so'm\n"
    bot.send_message(message.chat.id, matn)
@bot.message_handler(func=lambda m: m.text == "Yordam")
def yordam_tugma(message):
    yordam(message)
@bot.message_handler(func=lambda m: m.text == "Menyu")
def menyu_tugma(message):
    menyu(message)
@bot.message_handler(commands=["buyurtma"])
def buyurtma(message):
    bot.set_state(message.from_user.id, Buyurtma.taom, message.chat.id)
    bot.send_message(message.chat.id, "Nima buyurasiz? (/cancel — bekor qilish)",
                     reply_markup=taom_tugmalari())
@bot.message_handler(func=lambda m: m.text == "Buyurtma berish")
def buyurtma_tugma(message):
    buyurtma(message)
@bot.callback_query_handler(func=lambda c: c.data.startswith("taom_"), state=Buyurtma.taom)
def taom_tanlandi(call):
    kod = call.data.split("_")[1]
    nom, narx = MENYU[kod]
    bot.answer_callback_query(call.id)
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data["taom"] = nom
        data["narx"] = narx
    bot.set_state(call.from_user.id, Buyurtma.soni, call.message.chat.id)
    bot.edit_message_text(f"Tanlandi: {nom}\n\nNechta?(1-10)", call.message.chat.id, call.message.message_id)
@bot.message_handler(state=Buyurtma.taom)
def taom_matn(message):
    bot.send_message(message.chat.id, "Tugmalardan birini bosing (yoki /cancel)")
@bot.message_handler(state=Buyurtma.soni)
def soni_qabul(message):
    if not message.text.isdigit() or not 1 <= int(message.text) <= 10:
        bot.send_message(message.chat.id, "1 dan 10 gacha son kiriting.")
        return
    soni = int(message.text)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["soni"] = soni
        data["jami"] = data["narx"] * soni
        matn = f"{data['taom']} * {soni} = {data['jami']} so'm"
    bot.set_state(message.from_user.id,Buyurtma.tasdiq,message.chat.id)
    bot.send_message(message.chat.id,f"{matn}\nTasdiqlaysizmi?",reply_markup=tasdiq_tugmalari())
@bot.callback_query_handler(func=lambda c: c.data in ("ha", "yoq"), state=Buyurtma.tasdiq)
def tasdiq(call):
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        matn = f"{data['taom']} * {data['soni']} = {data['jami']} so'm"
    bot.delete_state(call.from_user.id,call.message.chat.id)
    if call.data == "ha":
        data = yukla()
        data.setdefault(str(call.message.chat.id), []).append(matn)
        saqla(data)
        bot.answer_callback_query(call.id, "Qabul qilindi")
        bot.edit_message_text(f"Buyurtma qabul qilindi:\n{matn}\n 15 daqiqada tayyor!",
                              call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id)
        bot.edit_message_text("Buyurtma bekor qilindi.",
                              call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "Yana nimadir kerakmi? ", reply_markup=asosiy_menyu())
@bot.message_handler(state=Buyurtma.tasdiq)
def tasdiq_matn(message):
    bot.send_message(message.chat.id, "Ha yoki Yo'q tugmasini bosing")
@bot.message_handler(commands=["mening"])
def mening(message):
    royxat = yukla().get(str(message.chat.id), [])
    if not royxat:
        bot.send_message(message.chat.id, "Hali buyurtma yo'q. Buyurtma berish tugmasini bosing.")
        return
    bot.send_message(message.chat.id, royxat_matni(royxat), reply_markup=bekor_tugmalari(royxat))
@bot.message_handler(func=lambda m: m.text == "Mening buyurtmam")
def mening_tugma(message):
    mening(message)
@bot.callback_query_handler(func=lambda c: c.data.startswith("bekor_"))
def bekor(call):
    i = int(call.data.split("_")[1])
    data = yukla()
    royxat = data.get(str(call.message.chat.id), [])
    if i >= len(royxat):
        bot.answer_callback_query(call.id, "Bu buyurtma topilmadi. Ro'yxatni qayta oching.")
        return
    ochirilgan = royxat.pop(i)
    saqla(data)
    bot.answer_callback_query(call.id, f"Bekor qilindi: {ochirilgan}")
    if royxat:
        bot.edit_message_text(royxat_matni(royxat), call.message.chat.id, call.message.message_id,
                              reply_markup=bekor_tugmalari(royxat))
    else:
        bot.edit_message_text("Buyurtma qolmadi.", call.message.chat.id, call.message.message_id)
@bot.callback_query_handler(func=lambda c: True)
def eski_tugma(call):
    bot.answer_callback_query(call.id, "Bu tugma eskirgan. Buyurtma berishdan boshlang.")
@bot.message_handler(func=lambda m: True)
def tushunmadim(message):
    bot.send_message(message.chat.id, "Tushunmadim. Pastdagi tugmalardan foydalaning.")

bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling()