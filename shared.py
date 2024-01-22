from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
Bot = TeleBot("6706767395:AAGmMyXCQm7humtVcYAMafK_8p2MjHVhDuk")
SINGLE_PAGE_SIZE = 6


def create_markup(struct):
    markup = InlineKeyboardMarkup()
    markup.row_width = struct.get("row_width")
    for row in struct["rows"]:
        line = []
        for button in row:
            line.append(InlineKeyboardButton(
                text=button.get("text"),
                callback_data=button.get("callback_data")
            ))
        markup.row(*line)
    return markup


def create_page_markup(items, offset, additional_actions=None, view_func=None):
    markup_struct = {"row_width": 2}
    rows = []
    if offset > 0:
        rows.append([{"text": "Назад", "callback_data": "Назад"}])
    index = offset
    row = []
    while index < len(items) and index < offset + SINGLE_PAGE_SIZE:
        item = items[index]
        display = item
        if view_func is not None:
            display = view_func(display)
        row.append({"text": display, "callback_data": item})
        if len(row) == 2:
            rows.append(row)
            row = []
        index = index + 1
    if len(row) == 1:
        rows.append(row)
    if index < len(items):
        rows.append([{"text": "Вперед", "callback_data": "Вперед"}])
    if additional_actions is not None:
        for action in additional_actions:
            rows.append([
                {"text": action["text"], "callback_data": action["callback_data"]}
            ])
    markup_struct["rows"] = rows
    return create_markup(markup_struct)
