from vkbottle import BaseStateGroup


class SuperStates(BaseStateGroup):
    START_STATE = 'S'
    CHOICE_OF_PIZZERIA = 'COP'
    ORDERING = 'O'
    ENTER_QUANTITY = 'EQ'
    CREATE = 'C'
    DELETE = 'D'