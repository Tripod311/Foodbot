import sqlite3
import json
from shared import Bot, SINGLE_PAGE_SIZE, create_page_markup
import scenario
import nutrients


def setup():
    conn = sqlite3.connect("users.sql")
    conn.execute("CREATE TABLE IF NOT EXISTS users (chat_id BIGINT PRIMARY_KEY, last_list TEXT, exclusions TEXT)")
    conn.commit()
    conn.close()


def get_exclusions(chat_id):
    conn = sqlite3.connect("users.sql")
    cur = conn.execute("SELECT exclusions FROM users WHERE chat_id=?", [chat_id])
    row = cur.fetchone()
    if row is None:
        return []
    else:
        try:
            ex = json.loads(row[0])
            return ex
        except Exception as e:
            return []


def set_exclusions(chat_id, ex):
    str_data = json.dumps(ex)
    conn = sqlite3.connect("users.sql")
    cur = conn.execute("SELECT COUNT(*) FROM users WHERE chat_id=?", [chat_id])
    if cur.fetchone()[0] > 0:
        cur.close()
        conn.execute("UPDATE users SET exclusions=? WHERE chat_id=?", [str_data, chat_id])
    else:
        cur.close()
        conn.execute("INSERT INTO users (chat_id, exclusions) VALUES (?, ?)", [chat_id, str_data])
    conn.commit()
    conn.close()


def get_list(chat_id):
    conn = sqlite3.connect("users.sql")
    cur = conn.execute("SELECT last_list FROM users WHERE chat_id=?", [chat_id])
    row = cur.fetchone()
    if row is None:
        return None
    else:
        try:
            ex = json.loads(row[0])
            return ex
        except Exception as e:
            return None


def set_list(chat_id, ll):
    str_data = json.dumps(ll)
    conn = sqlite3.connect("users.sql")
    cur = conn.execute("SELECT COUNT(*) FROM users WHERE chat_id=?", [chat_id])
    if cur.fetchone()[0] > 0:
        cur.close()
        conn.execute("UPDATE users SET last_list=? WHERE chat_id=?", [str_data, chat_id])
    else:
        cur.close()
        conn.execute("INSERT INTO users (chat_id, last_list) VALUES (?, ?)", [chat_id, str_data])
    conn.commit()
    conn.close()


# BOT INTERACTIONS
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
        set_exclusions(state["chat_id"], state["exclusions"])
        Bot.edit_message_text(
            text="Я все запомнил...",
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
    offset = state["offset"]
    items = state["products"]
    exclusions = state["exclusions"]
    markup = create_page_markup(
        items,
        offset,
        [{"text": "Закончить", "callback_data": "Закончить"}],
        lambda product: product if product not in exclusions else "❌" + product
    )
    Bot.edit_message_reply_markup(
        chat_id=state["chat_id"],
        message_id=state["message_id"],
        reply_markup=markup
    )


@Bot.message_handler(commands=["my_products"])
def my_products(message):
    chat_id = message.chat.id
    scenario.reset_scenario(chat_id)
    products = nutrients.get_product_list()
    exclusions = get_exclusions(chat_id)
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
