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


with open('data/vegetables.json', 'r', encoding='utf8') as f:
    veg = json.load(f)