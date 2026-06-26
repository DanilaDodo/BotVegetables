from keyboards import build_approve_keyboard
from loader import bot, adm
from services.prepare_data import order_text


async def send_to_adm(order_id, payload):
    keyboard = build_approve_keyboard(order_id)
    cart = order_text(payload['cart'])
    for user_id in adm:
        await bot.api.messages.send(peer_id=user_id,
                                    random_id=0,
                                    message=f'''Новый заказ для {payload["pizzeria"]}
[id{payload["user_id"]}|Связаться]
{cart}''',
                                    keyboard=keyboard)