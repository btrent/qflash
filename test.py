import datetime
import re
from time import sleep

class Test:
    app = None
    cards = []

    def __init__(self, app, **kwargs):
        self.app = app
        self.load_data()

    def run_all(self):
        return True

    def load_data(self):
        self.cards.append(Card("test 1", "answer 1"))
        self.cards.append(Card("test 2<br>row 2", "answer 2"))
        self.cards.append(Card("test 3", "answer 3"))
        self.cards.append(Card("test 4", "answer 4"))
        self.cards.append(Card("test 5", "answer 5"))

        #TODO self.cards[2].valid_date = datetime.datetime.now() + 10 days

class Card:
    front = ""
    back = ""
    valid_date = None

    def __init__(self, f, b, **kwargs):
        front = f
        back = b
        valid_date = datetime.datetime.now()
