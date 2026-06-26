from loader import bot
from states import SuperStates
from keyboards import build_vegetable_keyboard


async def is_none(event):
    state = await bot.state_dispenser.get(event.object.peer_id)
    await event.ctx_api.messages.send_message_event_answer(
        event_id=event.object.event_id,
        user_id=event.object.user_id,
        peer_id=event.object.peer_id
    )
    if state is None:
        await bot.api.messages.send(
            peer_id=event.object.peer_id,
            random_id=0,
            message="Этот заказ уже устарел. Начните новый заказ."
        )
    return state

async def set_page(user_id, action):
    state = dict(await bot.state_dispenser.get(user_id))
    payload = state['payload']
    payload['page'] += action
    await bot.state_dispenser.set(user_id,
                                  SuperStates.ORDERING,
                                  **payload)
    return payload['page']


async def check_replaced(order, pizzeria):
    for ord in order:
        if order[ord]['pizzeria'] == pizzeria and order[ord]['status'] != 'history':
            order[ord]['status'] = 'replaced'
    return order


async def send_vegetables(peer_id):
    keyboard = build_vegetable_keyboard()
    await bot.api.messages.send(peer_id=peer_id,
                                random_id=0,
                                message='Выберите товар',
                                keyboard=keyboard)


async def replace_message(event, text, keyboard):
    await event.ctx_api.messages.delete(peer_id=event.object.peer_id,
                                        cmids=event.object.conversation_message_id,
                                        delete_for_all=True)
    await bot.api.messages.send(peer_id=event.object.peer_id,
                                message=text,
                                random_id=0,
                                keyboard=keyboard)