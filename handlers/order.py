from vkbottle.dispatch.rules.base import PayloadContainsRule
from storage import read_order, write_order, veg, save_client
from states import SuperStates
from loader import bot, adm
from keyboards import build_start_keyboard
from services.notifications import send_to_adm
from services.renders import render_pizzeria_menu, render_cart
from services.order import send_vegetables, check_replaced, replace_message
from services.prepare_data import data_pizzeria, data_vegetable, data_for_order, prepare_json
from vkbottle.bot import MessageEvent
from vkbottle import GroupEventType


@bot.on.message(fuzzy=['/start', 'начать'])
async def start_handler(message):
    save_client(message.peer_id)
    await bot.state_dispenser.set(message.peer_id,
                                  SuperStates.START_STATE,
                                  page=None)
    await message.answer('Нажмите на кнопку ниже, чтоб сделать новый заказ',
                         keyboard=build_start_keyboard())


@bot.on.message(fuzzy=['новый заказ'])
async def choice_of_pizzeria(message):
    save_client(message.peer_id)
    await bot.state_dispenser.set(message.peer_id,
                                  SuperStates.CHOICE_OF_PIZZERIA,
                                  pizzeria=None,
                                  current_product=None,
                                  cart={i: 0 for i in veg},
                                  page=0)
    await render_pizzeria_menu(message.peer_id)


@bot.on.message(regex=r"^\d+(?:[.,]\d+)?$", state=SuperStates.ENTER_QUANTITY)
async def quantity_handler(message):
    state = dict(await bot.state_dispenser.get(message.peer_id))
    payload = state['payload']
    quant = round(float(message.text.replace(',', '.')), 1)
    payload['cart'][payload['current_product']] = quant
    payload['current_product'] = None
    await bot.state_dispenser.set(message.peer_id,
                                  SuperStates.ORDERING,
                                  **payload)
    await render_cart(payload, peer_id=message.peer_id)
    await send_vegetables(message.peer_id)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT,
                  MessageEvent,
                  PayloadContainsRule({'cmd': 'ordering'}))
async def send_cart(event):
    payload = await data_pizzeria(event)
    if payload is not None:
        await bot.state_dispenser.set(event.object.peer_id,
                                      SuperStates.ORDERING,
                                      **payload)
        await render_cart(payload, event)
        await send_vegetables(event.object.peer_id)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT,
                  MessageEvent,
                  PayloadContainsRule({'cmd': 'send_order'}))
async def send_order(event):
    payload = await data_for_order(event)
    if payload is not None:
        await event.ctx_api.messages.delete(peer_id=event.object.peer_id,
                                            cmids=event.object.conversation_message_id + 1,
                                            delete_for_all=True)
        ord = read_order()
        ord = prepare_json(ord)
        ord = await check_replaced(ord, payload['pizzeria'])
        order_id = int(list(ord.keys())[-1]) + 1 if list(ord.keys()) else 0
        ord[order_id] = payload
        write_order(ord)
        await send_to_adm(order_id, payload)
        await bot.state_dispenser.delete(event.object.peer_id)
        try:
            await bot.api.messages.send(peer_id=payload['user_id'],
                                        message='Ваш заказ отправлен на согласование',
                                        random_id=0)
        except Exception:
            for i in adm:
                await bot.api.messages.send(peer_id=i,
                                            message=f'Не удалось уведомить пользователя о статусе согласования.',
                                            random_id=0)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT,
                  MessageEvent,
                  PayloadContainsRule({'cmd': 'choice_of_vegetable'}))
async def quantity(event):
    payload = await data_vegetable(event)
    if payload is not None:
        await bot.state_dispenser.set(event.object.peer_id,
                                      SuperStates.ENTER_QUANTITY,
                                      **payload)
        await replace_message(event, 'Введите количество в килограммах, например - 10, 5.5, 0.1', None)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT,
                  MessageEvent,
                  PayloadContainsRule({'cmd': 'choice_of_pizzeria'}))
async def pagination(event):
    await render_pizzeria_menu(event.object.peer_id,
                               event.object.payload['action'],
                               event)