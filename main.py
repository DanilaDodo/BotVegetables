import asyncio
from vkbottle.bot import Bot, MessageEvent
from vkbottle import BaseStateGroup, GroupEventType, GroupTypes
from vkbottle import Keyboard, KeyboardButtonColor, Text, Callback
from vkbottle.dispatch.rules.base import PayloadContainsRule
import json

bot = Bot(token=TOKEN)


class SuperStates(BaseStateGroup):
    START_STATE = 'S'
    ORDERING = 'O'


with open('adress.json', 'r', encoding='utf8') as f:
    piz = json.load(f)

with open('vegetables.json', 'r', encoding='utf8') as f:
    veg = json.load(f)


async def set_page(user_id, action):
    state = dict(await bot.state_dispenser.get(user_id))
    page = state['payload']['page'] + action
    await bot.state_dispenser.set(user_id,
                                  SuperStates.ORDERING,
                                  pizzeria=None,
                                  current_product=None,
                                  cart={i: 0 for i in veg},
                                  page=page)
    return page


def build_keyboard(page):
    pizzerias = Keyboard(inline=True)
    start = page * 5
    end = start + 5
    for adress in piz[start:end]:
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
        if end < len(piz) else None
    return pizzerias.get_json()


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
                  PayloadContainsRule({'cmd': 'ordering'}))
async def send_cart(event):
    state = dict(await bot.state_dispenser.get(event.object.peer_id))
    payload = state['payload']
    payload['pizzeria'] = event.object.payload['pizzeria']
    await bot.state_dispenser.set(event.object.peer_id,
                                  SuperStates.ORDERING,
                                  **payload)
    keyboard = (Keyboard(inline=True)
                .add(Text('Отправить заказ'), color=KeyboardButtonColor.SECONDARY))
    text = f'Заказ для {event.object.payload["pizzeria"]}:\n\n'
    text += '\n'.join([f'{key} - {value} кг' for key, value in payload['cart'].items()])
    await replace_message(event, text, keyboard)


async def replace_message(event, text, keyboard):
    await event.ctx_api.messages.delete(peer_id=event.object.peer_id,
                                        cmids=event.object.conversation_message_id,
                                        delete_for_all=True)
    await bot.api.messages.send(peer_id=event.object.peer_id,
                                message=text,
                                random_id=0,
                                keyboard=keyboard)


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
