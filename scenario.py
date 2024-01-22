from threading import Timer
from shared import Bot
running_scenarios = {}


@Bot.callback_query_handler(func=lambda call: True)
def process_callback_data(cb):
    chat_id = cb.from_user.id
    if chat_id in running_scenarios:
        state = running_scenarios[chat_id]["state"]
        handles = running_scenarios[chat_id]["handles"]
        if cb.data is not None:
            if cb.data in handles:
                handles[cb.data](state, cb)
                refresh_timeout(chat_id)
            elif "default" in handles:
                handles["default"](state, cb)
                refresh_timeout(chat_id)


def refresh_timeout(chat_id):
    if chat_id in running_scenarios:
        running_scenarios[chat_id]["timeout"].cancel()
        t = Timer(running_scenarios[chat_id]["timeout_value"], reset_scenario, [chat_id])
        running_scenarios[chat_id]["timeout"] = t
        t.start()


def launch_scenario(chat_id, handles, state, timeout=300):
    if chat_id in running_scenarios:
        reset_scenario(chat_id)
    t = Timer(timeout, reset_scenario, [chat_id])
    running_scenarios[chat_id] = {
        "handles": handles,
        "state": state,
        "timeout": t,
        "timeout_value": timeout
    }
    t.start()


def reset_scenario(chat_id):
    if chat_id in running_scenarios:
        running_scenarios[chat_id]["timeout"].cancel()
        handles = running_scenarios[chat_id]["handles"]
        if "end" in handles:
            handles["end"](running_scenarios[chat_id]["state"])
        del running_scenarios[chat_id]
