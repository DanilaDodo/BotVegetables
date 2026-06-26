from vkbottle.bot import MessageEvent
from vkbottle import GroupEventType
from states import SuperStates
from storage import read_order, write_order, read_pizzeria, write_pizzeria, veg
from loader import bot, adm
from vkbottle.dispatch.rules.base import PayloadContainsRule


@bot.on.message(text=['создать точку', 'Создать точку'], peer_ids=adm)
async def create_pizzeria(message):
    await message.answer('Введите адрес точки для добавления')
    await bot.state_dispenser.set(message.peer_id,
                                  SuperStates.CREATE)


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


@bot.on.message(state=SuperStates.DELETE)
async def delete_handler(message):
    piz = read_pizzeria()
    if message.text in piz:
        piz.remove(message.text)
        write_pizzeria(piz)
        await message.answer(f'Пиццерия по адресу {message.text} успешно удалена')
        await bot.state_dispenser.delete(message.peer_id)
    else:
        await message.answer(f'Пиццерия по адресу {message.text} не найдена.\nОтправьте адрес заново')


@bot.on.message(fuzzy=['показать сводку'], peer_ids=adm)
async def show_stat(message):
    order = read_order()
    total = {i: 0 for i in veg}
    total_text = "ИТОГО:\n"
    text = ""
    for i in order:
        if order[i]['status'] == 'approve':
            text += order[i]['pizzeria'] + ':\n'
            for j in order[i]['cart']:
                text += j + ' - ' + str(order[i]['cart'][j]) + ' кг\n'
                total[j] += order[i]['cart'][j]
            text += '\n'
    if not text:
        text = 'Сводка пуста'
    await message.answer(text)
    for i in total:
        total_text += i + ' - ' + str(total[i]) + ' кг\n'
    await message.answer(total_text)


@bot.on.message(fuzzy=['очистить сводку'], peer_ids=adm)
async def clear_stat(message):
    order = read_order()
    for ord in order:
        order[ord]['status'] = 'history'
    write_order(order)
    await message.answer('Сводка очищена')


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT,
                  MessageEvent,
                  PayloadContainsRule({'cmd': 'approve'}))
async def send_answer(event):
    await event.ctx_api.messages.send_message_event_answer(
        event_id=event.object.event_id,
        user_id=event.object.user_id,
        peer_id=event.object.peer_id
    )
    payload = event.object.payload
    answer = 'принят' if payload['action'] == 'approve' else 'отклонен'
    ord = read_order()
    if str(payload['order_id']) not in ord or ord[str(payload['order_id'])]['status'] == 'pending':
        await bot.api.messages.send(peer_id=event.object.peer_id,
                                    message=f'Заказ для {ord[str(payload["order_id"])]["pizzeria"]} {answer}',
                                    random_id=0)
        try:
            await bot.api.messages.send(peer_id=ord[str(payload['order_id'])]['user_id'],
                                        message=f'Ваш заказ {answer}',
                                        random_id=0)
        except Exception:
            await bot.api.messages.send(peer_id=event.object.peer_id,
                                        message=f'Не удалось уведомить пользователя.\nЗаказ всё равно {answer}',
                                        random_id=0)
        ord[str(payload['order_id'])]['status'] = payload['action']
        write_order(ord)
    else:
        await bot.api.messages.send(peer_id=event.object.peer_id,
                                    message=f'Заказ больше не ожидает согласования.',
                                    random_id=0)