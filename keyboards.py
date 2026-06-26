from vkbottle import Keyboard, KeyboardButtonColor, Text, Callback
from storage import read_pizzeria, veg

def build_keyboard(page):
    pizzeria_list = read_pizzeria()
    pizzerias = Keyboard(inline=True)
    start = page * 5
    end = start + 5
    for adress in pizzeria_list[start:end]:
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
        if end < len(pizzeria_list) else None
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
        Callback("✅ Принять", payload={'cmd': 'approve', 'action': 'approve', 'order_id': order_id}),
        color=KeyboardButtonColor.POSITIVE
    )
    approve.add(
        Callback("❌ Отклонить", payload={'cmd': 'approve', 'action': 'decline', 'order_id': order_id}),
        color=KeyboardButtonColor.NEGATIVE
    )
    return approve


def build_send_order_keyboard(payload):
    keyboard = (Keyboard(inline=True)
                .add(Callback('Отправить заказ',
                              payload={'cmd': 'send_order', 'cart': list(payload['cart'].items())}),
                     color=KeyboardButtonColor.SECONDARY))
    return keyboard.get_json()


def build_start_keyboard():
    keyboard = (Keyboard(inline=True)
                .add(Text('Новый заказ'), color=KeyboardButtonColor.POSITIVE))
    return keyboard.get_json()
