from storage import read_clients, write_clients
from loader import bot, adm
from datetime import datetime
from zoneinfo import ZoneInfo

@bot.loop_wrapper.interval(minutes=1)
async def reminders_scheduler():
    now = datetime.now(ZoneInfo("Europe/Moscow"))

    if now.weekday() in (0, 3) and now.hour == 12 and now.minute == 0:
        await send_reminders()

async def send_reminders():
    clients = read_clients()
    user_for_remove = []
    for i in clients['users']:
        try:
            await bot.api.messages.send(peer_id=i,
                                        message='Не забудьте отправить новый заказ!',
                                        random_id=0)
        except Exception:
            for j in adm:
                await bot.api.messages.send(peer_id=j,
                                            message=f'Не удалось отправить напоминание [id{i}|пользователю].\n'
                                                    f'Пользователь удален из рассылки.',
                                            random_id=0)
            user_for_remove.append(i)
    for i in user_for_remove:
        clients['users'].remove(i)
    write_clients(clients)