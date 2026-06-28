import json


def read_pizzeria():
    with open('data/adress.json', 'r', encoding='utf8') as f:
        piz = json.load(f)
    return list(piz.values())


def write_pizzeria(pizzeria):
    out = {}
    for index, adress in enumerate(pizzeria):
        out[index] = adress
    with open('data/adress.json', 'w', encoding='utf8') as f:
        json.dump(out, f, ensure_ascii=False, indent=4)


def read_order():
    with open('data/orders.json', 'r', encoding='utf8') as f:
        ord = json.load(f)
    return ord


def write_order(ord):
    with open('data/orders.json', 'w', encoding='utf8') as f:
        json.dump(ord, f, ensure_ascii=False, indent=4)


def read_clients():
    with open('data/users.json', 'r', encoding='utf8') as f:
        clients = json.load(f)
    return clients


def write_clients(clients):
    with open('data/users.json', 'w', encoding='utf8') as f:
        json.dump(clients, f, ensure_ascii=False, indent=4)


def save_client(user_id):
    clients = read_clients()
    if user_id not in clients['users']:
        clients['users'].append(user_id)
        write_clients(clients)


with open('data/vegetables.json', 'r', encoding='utf8') as f:
    veg = json.load(f)