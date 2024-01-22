from telebot.types import InputFile
from shared import Bot, create_page_markup, SINGLE_PAGE_SIZE
import scenario
import nutrients


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


def process_op(state, cb):
    data = cb.data
    if data == "Вперед":
        state["offset"] = state["offset"] + SINGLE_PAGE_SIZE
        Bot.edit_message_reply_markup(
            chat_id=state["chat_id"],
            message_id=state["message_id"],
            reply_markup=create_page_markup(state["list"], state["offset"])
        )
    elif data == "Назад":
        state["offset"] = state["offset"] - SINGLE_PAGE_SIZE
        Bot.edit_message_reply_markup(
            chat_id=state["chat_id"],
            message_id=state["message_id"],
            reply_markup=create_page_markup(state["list"], state["offset"])
        )
    else:
        if state["proc"] == "nut":
            n_prod = nutrients.get_products_for_nutrient(data)
            Bot.edit_message_text(
                chat_id=state["chat_id"],
                message_id=state["message_id"],
                text=f"{data} содержится в следующих продуктах (указан % от суточной нормы):\n" + ",\n".join(n_prod)
            )
            scenario.reset_scenario(state["chat_id"])
        else:
            p_nut = nutrients.get_nutrients_in_product(data)
            Bot.edit_message_text(
                chat_id=state["chat_id"],
                message_id=state["message_id"],
                text=f"{data} содержит в себе следующие нутриенты:\n" + ",\n".join(p_nut)
            )
            scenario.reset_scenario(state["chat_id"])


@Bot.message_handler(commands=["get_nutrient"])
def get_nutrient(message):
    scenario.reset_scenario(message.chat.id)
    n_list = nutrients.get_nutrient_list()
    msg = Bot.send_message(
        chat_id=message.chat.id,
        text="Выбери нутриент",
        reply_markup=create_page_markup(
            n_list,
            0
        )
    )
    if msg is not None:
        scenario.launch_scenario(
            message.chat.id,
            {
                "default": process_op
            },
            {
                "chat_id": message.chat.id,
                "message_id": msg.message_id,
                "proc": "nut",
                "list": n_list,
                "offset": 0
            }
        )


@Bot.message_handler(commands=["get_product"])
def get_product(message):
    scenario.reset_scenario(message.chat.id)
    p_list = nutrients.get_product_list()
    msg = Bot.send_message(
        chat_id=message.chat.id,
        text="Выбери продукт",
        reply_markup=create_page_markup(
            p_list,
            0
        )
    )
    if msg is not None:
        scenario.launch_scenario(
            message.chat.id,
            {
                "default": process_op
            },
            {
                "chat_id": message.chat.id,
                "message_id": msg.message_id,
                "proc": "prod",
                "list": p_list,
                "offset": 0
            }
        )


def process_rating_selection(state, cb):
    data = cb.data
    if data == "Вперед":
        state["offset"] = state["offset"] + SINGLE_PAGE_SIZE
        Bot.edit_message_reply_markup(
            chat_id=state["chat_id"],
            message_id=state["message_id"],
            reply_markup=create_page_markup(
                state["list"],
                state["offset"],
                [{"text": "Рассчитать", "callback_data": "Рассчитать"}],
                lambda product: product if product not in state["selection"] else "✅" + product
            )
        )
    elif data == "Назад":
        state["offset"] = state["offset"] - SINGLE_PAGE_SIZE
        Bot.edit_message_reply_markup(
            chat_id=state["chat_id"],
            message_id=state["message_id"],
            reply_markup=create_page_markup(
                state["list"],
                state["offset"],
                [{"text": "Рассчитать", "callback_data": "Рассчитать"}],
                lambda product: product if product not in state["selection"] else "✅" + product
            )
        )
    elif data == "Рассчитать":
        if len(state["selection"]) == 0:
            Bot.edit_message_text(
                chat_id=state["chat_id"],
                message_id=state["message_id"],
                text="Не выбран ни один продукт, ничего не делаю"
            )
        else:
            ratings = nutrients.get_product_ratings(state["selection"])
            r_t = []
            for entry in ratings:
                r_t.append(entry[0] + " - {:.2f}".format(entry[1]))
            Bot.edit_message_text(
                chat_id=state["chat_id"],
                message_id=state["message_id"],
                text="Результат:\n" + "\n".join(r_t)
            )
        scenario.reset_scenario(state["chat_id"])
    else:
        if data in state["selection"]:
            state["selection"].remove(data)
        else:
            state["selection"].append(data)
        Bot.edit_message_reply_markup(
            chat_id=state["chat_id"],
            message_id=state["message_id"],
            reply_markup=create_page_markup(
                state["list"],
                state["offset"],
                [{"text": "Рассчитать", "callback_data": "Рассчитать"}],
                lambda product: product if product not in state["selection"] else product + "✅"
            )
        )


@Bot.message_handler(commands=["get_rating"])
def get_product_ratings(message):
    scenario.reset_scenario(message.chat.id)
    p_list = nutrients.get_product_list()
    msg = Bot.send_message(
        chat_id=message.chat.id,
        text="Выбери продукты в рейтинг",
        reply_markup=create_page_markup(
            p_list,
            0,
            [{"text": "Рассчитать", "callback_data": "Рассчитать"}]
        )
    )
    if msg is not None:
        scenario.launch_scenario(
            message.chat.id,
            {
                "default": process_rating_selection
            },
            {
                "chat_id": message.chat.id,
                "message_id": msg.message_id,
                "list": p_list,
                "selection": [],
                "offset": 0
            }
        )


@Bot.message_handler(commands=["get_csv"])
def get_csv(message):
    Bot.send_document(
        chat_id=message.chat.id,
        document=InputFile("foodTable.csv")
    )
