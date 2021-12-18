from hearts import facts
from hearts.card import Card
from typing import List, Set
import random


def shuffle_deck() -> List['Card']:
    d = list(facts.DECK)
    random.shuffle(d)
    return d


def str_to_card(s: str) -> Set['Card']:
    return {Card(facts.SUIT(cs[0]), facts.FACE(cs[1:])) for cs in s.split()}


def score_card(lead: 'Suit', card: 'Card') -> int:
    return facts.FACE_VALUES[card.face.name].value if card.suit == lead else 0
