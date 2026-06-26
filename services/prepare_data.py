from services.order import is_none

def prepare_json(ord):
    while len(ord) >= 500:
        key_to_remove = list(ord.keys())[0]
        ord.pop(key_to_remove)
    return ord


def order_text(cart):
    return '\n'.join([f'{key} - {value} кг' for key, value in cart.items()])


async def data_vegetable(event):
    payload = await is_none(event)
    if payload is not None:
        payload = dict(payload)
        payload = payload['payload']
        payload['current_product'] = event.object.payload['vegetable']
    return payload


async def data_pizzeria(event):
    payload = await is_none(event)
    if payload is not None:
        payload = dict(payload)
        payload = payload['payload']
        payload['pizzeria'] = event.object.payload['pizzeria']
    return payload


async def data_for_order(event):
    payload = await is_none(event)
    if payload is not None:
        payload = dict(payload)
        payload = payload['payload']
        payload.pop('page', None)
        payload.pop('current_product', None)
        payload['user_id'] = event.object.user_id
        payload['status'] = 'pending'
    return payload