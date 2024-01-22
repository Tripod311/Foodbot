from threading import Timer
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from shared import Bot
import scenario
import nutrients
import users

users.setup()

SINGLE_PAGE_SIZE = 6


def process_products_operation(state, cb):
    data = cb.data
    if data == "Вперед":
        state["offset"] = state["offset"] + SINGLE_PAGE_SIZE
        render_products_page(state)
    elif data == "Назад":
        state["offset"] = state["offset"] - SINGLE_PAGE_SIZE
        render_products_page(state)
    elif data == "Закончить":
        scenario.reset_scenario(state["chat_id"])
        users.set_exclusions(state["chat_id"], state["exclusions"])
        Bot.edit_message_text(
            text="Я все запомнил...",
            chat_id=state["chat_id"],
            message_id=state["message_id"]
        )
        Bot.edit_message_reply_markup(
            chat_id=state["chat_id"],
            message_id=state["message_id"],
            reply_markup=None
        )
    else:
        if data in state["exclusions"]:
            state["exclusions"].remove(data)
        else:
            state["exclusions"].append(data)
        render_products_page(state)


def render_products_page(state, cb=None):
    index = state["offset"]
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    if index > 0:
        markup.row(InlineKeyboardButton(text="Назад", callback_data="Назад"))
    b1 = None
    while index < len(state["products"]) and index < state["offset"] + SINGLE_PAGE_SIZE:
        product_name = state["products"][index]
        display = product_name
        if product_name in state["exclusions"]:
            display = display + "❌"
        if b1 is None:
            b1 = InlineKeyboardButton(text=display, callback_data=product_name)
        else:
            markup.add(b1, InlineKeyboardButton(text=display, callback_data=product_name))
            b1 = None
        index = index + 1
    if b1 is not None:
        markup.add(b1)
    if index + SINGLE_PAGE_SIZE < len(state["products"]):
        markup.row(InlineKeyboardButton(text="Вперед", callback_data="Вперед"))
    markup.row(InlineKeyboardButton(text="Закончить", callback_data="Закончить"))
    Bot.edit_message_reply_markup(
        chat_id=state["chat_id"],
        message_id=state["message_id"],
        reply_markup=markup
    )


def process_operation(state, cb):
    data = cb.data
    if state["proc"] == "exc":
        if data == "Вперед":
            state["offset"] = state["offset"] + SINGLE_PAGE_SIZE
            render_exclude_page(state)
        elif data == "Назад":
            state["offset"] = state["offset"] - SINGLE_PAGE_SIZE
            render_exclude_page(state)
        else:
            state["exclusions"].append(data)
            make_list(state)
    elif state["proc"] == "ret":
        if data == "Вперед":
            state["offset"] = state["offset"] + 4
            render_return_page(state)
        elif data == "Назад":
            state["offset"] = state["offset"] - 4
            render_return_page(state)
        else:
            state["exclusions"].remove(data)
            make_list(state)


def render_exclude_page(state, cb=None):
    index = state["offset"]
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    if index > 0:
        markup.row(InlineKeyboardButton(text="Назад", callback_data="Назад"))
    b1 = None
    while index < len(state["list"]) and index < state["offset"] + SINGLE_PAGE_SIZE:
        product_name = state["list"][index]
        if b1 is None:
            b1 = InlineKeyboardButton(text=product_name, callback_data=product_name)
        else:
            markup.add(b1, InlineKeyboardButton(text=product_name, callback_data=product_name))
            b1 = None
        index = index + 1
    if b1 is not None:
        markup.add(b1)
    if index + SINGLE_PAGE_SIZE < len(state["list"]):
        markup.row(InlineKeyboardButton(text="Вперед", callback_data="Вперед"))
    Bot.edit_message_reply_markup(
        chat_id=state["chat_id"],
        message_id=state["message_id"],
        reply_markup=markup
    )


def render_return_page(state, cb=None):
    index = state["offset"]
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    if index > 0:
        markup.row(InlineKeyboardButton(text="Назад", callback_data="Назад"))
    b1 = None
    while index < len(state["exclusions"]) and index < state["offset"] + SINGLE_PAGE_SIZE:
        product_name = state["exclusions"][index]
        if b1 is None:
            b1 = InlineKeyboardButton(text=product_name, callback_data=product_name)
        else:
            markup.add(b1, InlineKeyboardButton(text=product_name, callback_data=product_name))
            b1 = None
        index = index + 1
    if b1 is not None:
        markup.add(b1)
    if index + SINGLE_PAGE_SIZE < len(state["exclusions"]):
        markup.row(InlineKeyboardButton(text="Вперед", callback_data="Вперед"))
    Bot.edit_message_reply_markup(
        chat_id=state["chat_id"],
        message_id=state["message_id"],
        reply_markup=markup
    )


def exclude_product(state, cb=None):
    state["proc"] = "exc"
    state["offset"] = 0
    Bot.edit_message_text(
        text="Выбери продукт, который надо исключить из списка",
        chat_id=state["chat_id"],
        message_id=state["message_id"]
    )
    render_exclude_page(state)


def return_product(state, cb=None):
    state["proc"] = "ret"
    state["offset"] = 0
    Bot.edit_message_text(
        text="Выбери продукт, который надо вернуть в список",
        chat_id=state["chat_id"],
        message_id=state["message_id"]
    )
    render_return_page(state)


def make_list(state, cb=None):
    r_c = nutrients.generate_list(state["exclusions"], state["product_size"])
    state["list"] = r_c[0]
    text = "Список:\n" + ",\n".join(r_c[0])
    if len(r_c[1]) > 0:
        text = (text + "\n\nВ этом списке содержатся в сниженном количестве:\n" + ", ".join(r_c[1]) +
                "\nЭто можно компенсировать количеством продуктов с этими нутриентами")
    if len(r_c[2]) > 0:
        text = (text + "\n\nВ этом списке отсутствуют:\n" + ", ".join(r_c[1]) +
                "\nНеобходимо добавить продукты с этими нутриентами в рацион")
    Bot.edit_message_text(
        text=text,
        chat_id=state["chat_id"],
        message_id=state["message_id"]
    )
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    if len(state["list"]) > 0:
        markup.add(InlineKeyboardButton(text="Убрать продукт", callback_data="Убрать продукт"))
    if len(state["exclusions"]) > 0:
        markup.add(InlineKeyboardButton(text="Вернуть продукт", callback_data="Вернуть продукт"))
    markup.add(InlineKeyboardButton(text="Сохранить список", callback_data="Сохранить список"))
    Bot.edit_message_reply_markup(
        chat_id=state["chat_id"],
        message_id=state["message_id"],
        reply_markup=markup
    )


def generate_small_list(state, cb=None):
    state["product_size"] = 1
    make_list(state)


def generate_extended_list(state, cb=None):
    state["product_size"] = 3
    make_list(state)


def save_list(state, cb=None):
    scenario.reset_scenario(state["chat_id"])
    users.set_list(state["chat_id"], {"list": state["list"], "product_size": state["product_size"], "exclusions": state["exclusions"]})
    Bot.edit_message_text(
        text="Сохранил список:\n" + ",\n".join(state["list"]) + "\nМожно модифицировать его, отправить /modify",
        chat_id=state["chat_id"],
        message_id=state["message_id"]
    )


def notify_end(state):
    Bot.edit_message_reply_markup(
        chat_id=state["chat_id"],
        message_id=state["message_id"],
        reply_markup=None
    )
    Bot.send_message(chat_id=state["chat_id"], text="Больше не редактирую список")


@Bot.message_handler(commands=["generate"])
def generate_list(message):
    chat_id = message.chat.id
    scenario.reset_scenario(chat_id)
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton(text="Минимальный", callback_data="Минимальный"))
    markup.add(InlineKeyboardButton(text="Расширенный", callback_data="Расширенный"))
    msg = Bot.send_message(
        chat_id=chat_id,
        text="""Выбери тип списка:
Минимальный - меньше продуктов, где каждый будет содержать наибольшее количество нутриентов
Расширенный - больше продуктов, некоторые будут дублировать нутриенты""",
        reply_markup=markup
    )
    if msg is not None:
        scenario.launch_scenario(
            chat_id,
            {
                "end": notify_end,
                "Минимальный": generate_small_list,
                "Расширенный": generate_extended_list,
                "Сохранить список": save_list,
                "Убрать продукт": exclude_product,
                "Вернуть продукт": return_product,
                "default": process_operation
            },
            {
                "chat_id": chat_id,
                "message_id": msg.message_id,
                "product_size": 1,
                "exclusions": users.get_exclusions(chat_id),
                "list": [],
                "proc": None,
                "offset": 0
            }
        )


@Bot.message_handler(commands=["modify"])
def modify(message):
    chat_id = message.chat.id
    scenario.reset_scenario(chat_id)
    ll = users.get_list(chat_id)
    if ll is None:
        Bot.send_message(
            chat_id=chat_id,
            text="Нет сохраненного списка. Сначала создай его с помощью /generate"
        )
    else:
        state = {
            "chat_id": chat_id,
            "product_size": ll["product_size"],
            "exclusions": ll["exclusions"],
            "list": ll["list"],
            "proc": None,
            "offset": 0
        }
        markup = InlineKeyboardMarkup()
        markup.row_width = 2
        if len(state["list"]) > 0:
            markup.add(InlineKeyboardButton(text="Убрать продукт", callback_data="Убрать продукт"))
        if len(state["exclusions"]) > 0:
            markup.add(InlineKeyboardButton(text="Вернуть продукт", callback_data="Вернуть продукт"))
        markup.add(InlineKeyboardButton(text="Сохранить список", callback_data="Сохранить список"))
        msg = Bot.send_message(
            chat_id=chat_id,
            text="Список:\n" + ",\n".join(ll["list"]),
            reply_markup=markup
        )
        if msg is not None:
            state["message_id"] = msg.message_id,
            scenario.launch_scenario(
                chat_id,
                {
                    "end": notify_end,
                    "Сохранить список": save_list,
                    "Убрать продукт": exclude_product,
                    "Вернуть продукт": return_product,
                    "default": process_operation
                },
                state
            )


@Bot.message_handler(commands=["my_products"])
def my_products(message):
    chat_id = message.chat.id
    scenario.reset_scenario(chat_id)
    products = nutrients.get_product_list()
    exclusions = users.get_exclusions(chat_id)
    msg = Bot.send_message(
        chat_id=chat_id,
        text="Ща все будет"
    )
    if msg is not None:
        state = {
            "chat_id": chat_id,
            "message_id": msg.message_id,
            "products": products,
            "exclusions": exclusions,
            "offset": 0
        }
        scenario.launch_scenario(
            chat_id,
            {
                "default": process_products_operation
            },
            state
        )
        render_products_page(state)


@Bot.message_handler(commands=["minimal"])
def generate_minimal(message):
    scenario.reset_scenario(message.chat.id)
    arr = nutrients.find_minimal()
    Bot.send_message(
        chat_id=message.chat.id,
        text="Минимальный список продуктов, содержащий все нутриенты (не обязательно в нужном количестве):\n" + ",\n".join(arr)
    )


@Bot.message_handler(commands=["nutrient_list"])
def nutrient_list(message):
    scenario.reset_scenario(message.chat.id)
    arr = nutrients.get_nutrient_list()
    Bot.send_message(
        chat_id=message.chat.id,
        text="Список нутриентов:\n" + ",\n".join(arr)
    )


@Bot.message_handler(commands=["product_list"])
def product_list(message):
    scenario.reset_scenario(message.chat.id)
    arr = nutrients.get_product_list()
    Bot.send_message(
        chat_id=message.chat.id,
        text="Список продуктов:\n" + ",\n".join(arr)
    )


@Bot.message_handler(commands=["get_nutrient"])
def get_nutrient(message):
    scenario.reset_scenario(message.chat.id)

    def process_nutrient(msg):
        nutrient_name = msg.text.strip().lower()
        arr = nutrients.get_products_for_nutrient(nutrient_name)
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
    scenario.reset_scenario(message.chat.id)

    def process_product(msg):
        product_name = msg.text.strip().lower()
        arr = nutrients.get_nutrients_in_product(product_name)
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
        text="Напиши название продукта"
    )
    Bot.register_next_step_handler_by_chat_id(chat_id=message.chat.id, callback=process_product)


@Bot.message_handler(commands=["help"])
def get_help(message):
    scenario.reset_scenario(message.chat.id)
    Bot.send_message(
        chat_id=message.chat.id,
        text="""/nutrient_list - чтобы посмотреть список всех нутриентов
/product_list - чтобы посмотреть список всех продуктов
/get_nutrient - чтобы посмотреть в каких продуктах содержится нутриент
/get_product - чтобы посмотреть что содержится в продукте
/minimal - оставил прикола ради. Минимальный список продуктов, который закрывает все нутриенты (но не обязательно в нужном количестве!)
/generate - составить список продуктов. Напиши и следуй инструкциям
/modify - редактировать сохраненный список
/my_products - редактировать свой список продуктов"""
    )


Bot.infinity_polling()
