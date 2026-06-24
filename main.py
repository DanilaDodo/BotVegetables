import asyncio
from vkbottle.bot import Bot, MessageEvent
from vkbottle import BaseStateGroup, GroupEventType, GroupTypes
from vkbottle import Keyboard, KeyboardButtonColor, Text, Callback
from vkbottle.dispatch.rules.base import PayloadContainsRule
import json
from config import TOKEN, ADMIN

bot = Bot(token=TOKEN)
adm = ADMIN


class SuperStates(BaseStateGroup):
    START_STATE = 'S'
    ORDERING = 'O'
    CREATE = "C"
    DELETE = "D"

def read_pizzeria():
    with open('adress.json', 'r', encoding='utf8') as f:
        piz = json.load(f)
    return list(piz.values())

def write_pizzeria(pizzeria):
    out = {}
    for index, adress in enumerate(pizzeria):
        out[index] = adress
    with open('adress.json', 'w', encoding='utf8') as f:
        json.dump(out, f, ensure_ascii=False, indent=4)


def read_order():
    with open('orders.json', 'r', encoding='utf8') as f:
        ord = json.load(f)
    return ord


def write_order(ord):
    with open('orders.json', 'w', encoding='utf8') as f:
        json.dump(ord, f, ensure_ascii=False, indent=4)


def order_text(cart):
    return '\n'.join([f'{key} - {value} кг' for key, value in cart.items()])


with open('vegetables.json', 'r', encoding='utf8') as f:
    veg = json.load(f)


async def data_for_order(event):
    state = dict(await bot.state_dispenser.get(event.object.peer_id))
    payload = state['payload']
    payload.pop('page', None)
    payload.pop('current_product', None)
    payload['user_id'] = event.object.user_id
    payload['status'] = 'pending'
    return payload

async def set_page(user_id, action):
    state = dict(await bot.state_dispenser.get(user_id))
    payload = state['payload']
    payload['page'] += action
    await bot.state_dispenser.set(user_id,
                                  SuperStates.ORDERING,
                                  **payload)
    return payload['page']


def build_keyboard(page):
    pizzerias = Keyboard(inline=True)
    start = page * 5
    end = start + 5
    for adress in read_pizzeria()[start:end]:
        pizzerias.add(
            Callback(adress, payload={'cmd': 'ordering',
                                      'pizzeria': adress}),
            color=KeyboardButtonColor.POSITIVE
        )
        pizzerias.row()
    pizzerias.add(Callback('⏪', payload={'cmd': 'choice_of_pizzeria', 'action': -1}),
                  color=KeyboardButtonColor.PRIMARY) \
        if page else None
    pizzerias.add(Callback('⏩', payload={'cmd': 'choice_of_pizzeria', 'action': 1}),
                  color=KeyboardButtonColor.PRIMARY) \
        if end < len(read_pizzeria()) else None
    return pizzerias.get_json()


def build_vegetable_keyboard():
    vegetables = Keyboard(inline=True)
    for index, vegetable in enumerate(veg, 1):
        vegetables.add(
            Callback(vegetable, payload={'cmd': 'choice_of_vegetable', 'vegetable': vegetable}),
            color=KeyboardButtonColor.POSITIVE
        )
        if not index % 2:
            vegetables.row()
    return vegetables.get_json()


def build_approve_keyboard(order_id):
    approve = Keyboard(inline=True)
    approve.add(
        Callback("✅ Принять", payload={'cmd': 'approve_order', 'order_id': order_id}),
        color=KeyboardButtonColor.POSITIVE
    )
    approve.add(
        Callback("❌ Отклонить", payload={'cmd': 'decline_order', 'order_id': order_id}),
        color=KeyboardButtonColor.NEGATIVE
    )
    return approve


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


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT,
                  MessageEvent,
                  PayloadContainsRule({'cmd': 'choice_of_pizzeria'}))
async def pagination(event):
    await render_pizzeria_menu(event.object.peer_id,
                               event.object.payload['action'],
                               event)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT,
                  MessageEvent,
                  PayloadContainsRule({'cmd': 'choice_of_vegetable'}))
async def quantity(event):
    state = dict(await bot.state_dispenser.get(event.object.peer_id))
    payload = state['payload']
    payload['current_product'] = event.object.payload['vegetable']
    await bot.state_dispenser.set(event.object.peer_id,
                                  SuperStates.ORDERING,
                                  **payload)
    await replace_message(event, 'Введите количество в килограммах, например - 10, 5.5, 0.1', None)


async def send_vegetables(peer_id):
    keyboard = build_vegetable_keyboard()
    await bot.api.messages.send(peer_id=peer_id,
                                random_id=0,
                                message='Выберите товар',
                                keyboard=keyboard)


async def send_to_adm(order_id, payload):
    keyboard = build_approve_keyboard(order_id)
    cart = order_text(payload['cart'])
    for user_id in adm:
        await bot.api.messages.send(peer_id=user_id,
                                    random_id=0,
                                    message=f'''Новый заказ для {payload["pizzeria"]}\n
{cart}''',
                                    keyboard=keyboard)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT,
                  MessageEvent,
                  PayloadContainsRule({'cmd': 'send_order'}))
async def send_order(event):
    await event.ctx_api.messages.send_message_event_answer(
        event_id=event.object.event_id,
        user_id=event.object.user_id,
        peer_id=event.object.peer_id
    )
    await event.ctx_api.messages.delete(peer_id=event.object.peer_id,
                                        cmids=event.object.conversation_message_id + 1,
                                        delete_for_all=True)
    payload = await data_for_order(event)
    ord = read_order()
    order_id = int(list(ord.keys())[-1]) + 1 if list(ord.keys()) else 0
    ord[order_id] = payload
    write_order(ord)
    await send_to_adm(order_id, payload)
    await bot.api.messages.send(peer_id=event.peer_id,
                                random_id=0,
                                message='Ваш заказ отправлен на согласование')




async def render_cart(payload, event=None, peer_id=None):
    keyboard = (Keyboard(inline=True)
                .add(Callback('Отправить заказ',
                              payload={'cmd': 'send_order', 'cart': list(payload['cart'].items())}),
                     color=KeyboardButtonColor.SECONDARY))
    text = f'Заказ для {payload["pizzeria"]}:\n\n'
    text += order_text(payload['cart'])
    if event:
        await replace_message(event, text, keyboard.get_json())
    else:
        await bot.api.messages.send(peer_id=peer_id,
                                    message=text,
                                    keyboard=keyboard.get_json(),
                                    random_id=0)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT,
                  MessageEvent,
                  PayloadContainsRule({'cmd': 'ordering'}))
async def send_cart(event):
    state = dict(await bot.state_dispenser.get(event.object.peer_id))
    payload = state['payload']
    payload['pizzeria'] = event.object.payload['pizzeria']
    await bot.state_dispenser.set(event.object.peer_id,
                                  SuperStates.ORDERING,
                                  **payload)
    await render_cart(payload, event)
    await send_vegetables(event.object.peer_id)


async def replace_message(event, text, keyboard):
    await event.ctx_api.messages.delete(peer_id=event.object.peer_id,
                                        cmids=event.object.conversation_message_id,
                                        delete_for_all=True)
    await bot.api.messages.send(peer_id=event.object.peer_id,
                                message=text,
                                random_id=0,
                                keyboard=keyboard)


@bot.on.message(regex=r"^\d+(?:[.,]\d+)?$", state=SuperStates.ORDERING)
async def quantity_handler(message):
    quant = round(float(message.text.replace(',', '.')), 1)
    state = dict(await bot.state_dispenser.get(message.peer_id))
    payload = state['payload']
    payload['cart'][payload['current_product']] = quant
    payload['current_product'] = None
    await bot.state_dispenser.set(message.peer_id,
                                  SuperStates.ORDERING,
                                  **payload)
    await render_cart(payload, peer_id=message.peer_id)
    await send_vegetables(message.peer_id)


@bot.on.message(state=SuperStates.DELETE)
async def create_handler(message):
    piz = read_pizzeria()
    if message.text in piz:
        piz.remove(message.text)
        write_pizzeria(piz)
        await message.answer(f'Пиццерия по адресу {message.text} успешно удалена')
        await bot.state_dispenser.delete(message.peer_id)
    else:
        await message.answer(f'Пиццерия по адресу {message.text} не найдена.\nОтправьте адрес заново')


@bot.on.message(state=SuperStates.CREATE)
async def create_handler(message):
    piz = read_pizzeria()
    piz.append(message.text)
    piz.sort()
    write_pizzeria(piz)
    await message.answer(f'Пиццерия по адресу {message.text} успешно добавлена')
    await bot.state_dispenser.delete(message.peer_id)


@bot.on.message(text=['удалить точку', 'Удалить точку'], peer_ids=adm)
async def delete_pizzeria(message):
    await message.answer('Введите адрес точки для удаления')
    await bot.state_dispenser.set(message.peer_id,
                                  SuperStates.DELETE)


@bot.on.message(text=['создать точку', 'Создать точку'], peer_ids=adm)
async def create_pizzeria(message):
    await message.answer('Введите адрес точки для добавления')
    await bot.state_dispenser.set(message.peer_id,
                                  SuperStates.CREATE)

@bot.on.message(fuzzy=['новый заказ'])
async def choice_of_pizzeria(message):
    await bot.state_dispenser.set(message.peer_id,
                                  SuperStates.ORDERING,
                                  pizzeria=None,
                                  current_product=None,
                                  cart={i: 0 for i in veg},
                                  page=0)
    await render_pizzeria_menu(message.peer_id)


@bot.on.message(fuzzy=['/start', 'начать'])
async def start_handler(message):
    await bot.state_dispenser.set(message.peer_id,
                                  SuperStates.START_STATE,
                                  page=None)
    await message.answer('Нажмите на кнопку ниже, чтоб сделать новый заказ',
                         keyboard=(Keyboard(inline=True)
                                   .add(Text('Новый заказ'), color=KeyboardButtonColor.POSITIVE)).get_json())

bot.run_forever()