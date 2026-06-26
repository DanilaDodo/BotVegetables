from loader import bot
from services.order import set_page, replace_message
from services.prepare_data import order_text
from keyboards import build_keyboard, build_send_order_keyboard


async def render_pizzeria_menu(user_id, action=0, event=None):
    page = await set_page(user_id, action)
    keyboard = build_keyboard(page)
    text = 'Выберите пиццерию'
    if event:
        await replace_message(event, text, keyboard)
    else:
        await bot.api.messages.send(peer_id=user_id,
                                    random_id=0,
                                    message=text,
                                    keyboard=keyboard)


async def render_cart(payload, event=None, peer_id=None):
    keyboard = build_send_order_keyboard(payload)
    text = f'Заказ для {payload["pizzeria"]}:\n\n'
    text += order_text(payload['cart'])
    if event:
        await replace_message(event, text, keyboard)
    else:
        await bot.api.messages.send(peer_id=peer_id,
                                    message=text,
                                    keyboard=keyboard,
                                    random_id=0)