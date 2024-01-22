from shared import Bot, SINGLE_PAGE_SIZE, create_page_markup, create_markup
import scenario
import nutrients
import users


def process_operation(state, cb):
    data = cb.data
    if data == "Отмена":
        make_list(state)
        return
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
    offset = state["offset"]
    items = state["list"]
    markup = create_page_markup(
        items,
        offset,
        [{"text": "Отмена", "callback_data": "Отмена"}]
    )
    Bot.edit_message_reply_markup(
        chat_id=state["chat_id"],
        message_id=state["message_id"],
        reply_markup=markup
    )


def render_return_page(state, cb=None):
    offset = state["offset"]
    items = state["exclusions"]
    markup = create_page_markup(
        items,
        offset,
        [{"text": "Отмена", "callback_data": "Отмена"}]
    )
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
    m_rows = []
    m_struct = {"row_width": 2}
    row = []
    if len(state["list"]) > 0:
        row.append({"text": "Убрать продукт", "callback_data": "Убрать продукт"})
    if len(state["exclusions"]) > 0:
        row.append({"text": "Вернуть продукт", "callback_data": "Вернуть продукт"})
    m_rows.append(row)
    m_rows.append([{"text": "Сохранить список", "callback_data": "Сохранить список"}])
    m_struct["rows"] = m_rows
    markup = create_markup(m_struct)
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
        message_id=state["message_id"],
        reply_markup=None
    )


def notify_end(state):
    Bot.send_message(chat_id=state["chat_id"], text="Больше не редактирую список")


@Bot.message_handler(commands=["generate"])
def generate_list(message):
    chat_id = message.chat.id
    scenario.reset_scenario(chat_id)
    markup = create_markup({
        "row_width": 1,
        "rows": [
            [{"text": "Минимальный", "callback_data": "Минимальный"}],
            [{"text": "Расширенный", "callback_data": "Расширенный"}]
        ]
    })
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
        m_rows = []
        m_struct = {"row_width": 2}
        row = []
        if len(state["list"]) > 0:
            row.append({"text": "Убрать продукт", "callback_data": "Убрать продукт"})
        if len(state["exclusions"]) > 0:
            row.append({"text": "Вернуть продукт", "callback_data": "Вернуть продукт"})
        m_rows.append(row)
        m_rows.append([{"text": "Сохранить список", "callback_data": "Сохранить список"}])
        m_struct["rows"] = m_rows
        markup = create_markup(m_struct)
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
