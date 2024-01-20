from threading import Timer
from telebot import TeleBot
from telebot.util import quick_markup
import foods

EXCLUSIONS_TIMEOUT = 300
Bot = TeleBot("6706767395:AAGmMyXCQm7humtVcYAMafK_8p2MjHVhDuk")
Exclusions = {}


def create_exclusions(chat_id, product_limit):
    clear_exclusions(chat_id)
    t = Timer(EXCLUSIONS_TIMEOUT, clear_exclusions, [chat_id])
    Exclusions[chat_id] = {
        "product_limit": product_limit,
        "arr": [],
        "timer": t
    }
    t.start()


def add_exclusion(chat_id, product):
    Exclusions[chat_id]["timer"].cancel()
    t = Timer(EXCLUSIONS_TIMEOUT, clear_exclusions, [chat_id])
    Exclusions[chat_id]["arr"].append(product)
    Exclusions[chat_id]["timer"] = t
    t.start()


def clear_exclusions(chat_id):
    if chat_id in Exclusions:
        Exclusions[chat_id]["timer"].cancel()
        del Exclusions[chat_id]


def process_exclusion(msg):
    chat_id = msg.chat.id

    if chat_id not in Exclusions:
        return
    if msg.text.strip() == "/cancel":
        clear_exclusions(chat_id)
        Bot.send_message(
            chat_id=chat_id,
            text="Больше не делаю список"
        )
        return

    ex = msg.text.strip().lower()
    add_exclusion(chat_id, ex)
    arr = foods.only_first(Exclusions[chat_id]["arr"], Exclusions[chat_id]["product_limit"])
    complete = foods.check_completeness(arr)
    if len(complete) == 0:
        Bot.send_message(
            chat_id=chat_id,
            text="Список:\n" + ",\n".join(arr) + "\nНапиши название продукта, чтобы исключить его из списка, бот заменит его, либо /cancel, чтобы закончить формирование\nЕсли в течение 5 минут не будет сообщений, список исключенных продуктов будет сброшен"
        )
    else:
        Bot.send_message(
            chat_id=chat_id,
            text="Список:\n" + ",\n".join(arr) + "\nWARNING! В этом списке не хватает следующих элементов: " + ", ".join(complete) +
                 "\nНапиши название продукта, чтобы исключить его из списка, бот заменит его, либо /cancel, чтобы закончить формирование\nЕсли в течение 5 минут не будет сообщений, список исключенных продуктов будет сброшен"
        )
    Bot.register_next_step_handler_by_chat_id(chat_id=chat_id, callback=process_exclusion)


def handle_limit(msg):
    chat_id = msg.chat.id

    if msg.text.strip() == "/cancel":
        clear_exclusions(chat_id)
        Bot.send_message(
            chat_id=chat_id,
            text="Больше не делаю список"
        )
        return

    product_limit = 1
    try:
        product_limit = int(msg.text.strip())
        if product_limit < 0:
            raise ValueError("Неотрицательные")

        create_exclusions(chat_id, product_limit)
        arr = foods.only_first(Exclusions[chat_id]["arr"], Exclusions[chat_id]["product_limit"])
        Bot.send_message(
            chat_id=chat_id,
            text="Список:\n" + ",\n".join(arr) + "\nНапиши название продукта, чтобы исключить его из списка, бот заменит его, либо /cancel, чтобы закончить формирование\nЕсли в течение 5 минут не будет сообщений, список исключенных продуктов будет сброшен"
        )
        Bot.register_next_step_handler_by_chat_id(chat_id=chat_id, callback=process_exclusion)
    except Exception as e:
        Bot.send_message(
            chat_id=chat_id,
            text="Неверный ввод. Напиши /cancel, чтобы отменить"
        )
        Bot.register_next_step_handler_by_chat_id(chat_id=chat_id, callback=handle_limit)


@Bot.callback_query_handler(func=lambda call: True)
def handle_limit_human(msg):
    chat_id = msg.message.chat.id

    product_limit = 1
    if msg.data == "Минимальный":
        product_limit = 1
    elif msg.data == "Расширенный":
        product_limit = 3
    create_exclusions(chat_id, product_limit)
    arr = foods.only_first(Exclusions[chat_id]["arr"], Exclusions[chat_id]["product_limit"])
    Bot.send_message(
        chat_id=chat_id,
        text="Список:\n" + ",\n".join(
            arr) + "\nНапиши название продукта, чтобы исключить его из списка, бот заменит его, либо /cancel, чтобы закончить формирование\nЕсли в течение 5 минут не будет сообщений, список исключенных продуктов будет сброшен"
    )
    Bot.register_next_step_handler_by_chat_id(chat_id=chat_id, callback=process_exclusion)


@Bot.message_handler(commands=["generate"])
def generate_list(message):
    chat_id = message.chat.id
    Bot.send_message(
        chat_id=chat_id,
        text="""Выбери тип списка:
Минимальный - меньше продуктов, где каждый будет содержать наибольшее количество нутриентов
Расширенный - больше продуктов, некоторые будут дублировать нутриенты
Напиши /cancel, чтобы отменить генерацию""",
        reply_markup=quick_markup({
            "Минимальный": {"callback_data": "Минимальный"},
            "Расширенный": {"callback_data": "Расширенный"}
        })
    )
    # Bot.register_next_step_handler_by_chat_id(chat_id=chat_id, callback=handle_limit_human)


@Bot.message_handler(commands=["minimal"])
def generate_minimal(message):
    clear_exclusions(message.chat.id)
    arr = foods.find_minimal()
    Bot.send_message(
        chat_id=message.chat.id,
        text="Минимальный список продуктов, содержащий все нутриенты (не обязательно в нужном количестве):\n" + ",\n".join(arr)
    )


@Bot.message_handler(commands=["nutrient_list"])
def nutrient_list(message):
    clear_exclusions(message.chat.id)
    arr = foods.get_nutrient_list()
    Bot.send_message(
        chat_id=message.chat.id,
        text="Список нутриентов:\n" + ",\n".join(arr)
    )


@Bot.message_handler(commands=["product_list"])
def product_list(message):
    clear_exclusions(message.chat.id)
    arr = foods.get_product_list()
    Bot.send_message(
        chat_id=message.chat.id,
        text="Список продуктов:\n" + ",\n".join(arr)
    )


@Bot.message_handler(commands=["get_nutrient"])
def get_nutrient(message):
    clear_exclusions(message.chat.id)

    def process_nutrient(msg):
        nutrient_name = msg.text.strip().lower()
        arr = foods.get_product_for_nutrient(nutrient_name)
        if len(arr) == 0:
            Bot.send_message(
                chat_id=message.chat.id,
                text="Неправильный ввод. Нутриент не найден"
            )
        else:
            Bot.send_message(
                chat_id=message.chat.id,
                text="Продукты, содержащие " + nutrient_name + ":\n" + ",\n".join(arr)
            )

    Bot.send_message(
        chat_id=message.chat.id,
        text="Напиши название нутриента"
    )
    Bot.register_next_step_handler_by_chat_id(chat_id=message.chat.id, callback=process_nutrient)


@Bot.message_handler(commands=["get_product"])
def get_product(message):
    clear_exclusions(message.chat.id)

    def process_product(msg):
        product_name = msg.text.strip().lower()
        arr = foods.get_nutrient_in_product(product_name)
        if len(arr) == 0:
            Bot.send_message(
                chat_id=message.chat.id,
                text="Продукт не найден"
            )
        else:
            Bot.send_message(
                chat_id=message.chat.id,
                text=product_name + " содержит:\n" + ",\n".join(arr)
            )

    Bot.send_message(
        chat_id=message.chat.id,
        text="Напиши название нутриента"
    )
    Bot.register_next_step_handler_by_chat_id(chat_id=message.chat.id, callback=process_product)


@Bot.message_handler(commands=["help"])
def get_help(message):
    Bot.send_message(
        chat_id=message.chat.id,
        text="""/nutrient_list - чтобы посмотреть список всех нутриентов
/product_list - чтобы посмотреть список всех продуктов
/get_nutrient - чтобы посмотреть в каких продуктах содержится нутриент
/get_product - чтобы посмотреть что содержится в продукте
/minimal - оставил прикола ради. Минимальный список продуктов, который закрывает все нутриенты (но не обязательно в нужном количестве!)
/generate - составить список продуктов. Напиши и следуй инструкциям"""
    )


Bot.infinity_polling()