from enum import Enum
from hearts.card import Card


class SUIT(Enum):
    CLUBS = 'C'
    SPADES = 'S'
    HEARTS = 'H'
    DIAMONDS = 'D'


class DIRECTION(Enum):
    LEFT = 1
    RIGHT = -1
    ACROSS = 2
    KEEP = 0


class FACE(Enum):
    ACE = 'A'
    TWO = '2'
    THREE = '3'
    FOUR = '4'
    FIVE = '5'
    SIX = '6'
    SEVEN = '7'
    EIGHT = '8'
    NINE = '9'
    TEN = '10'
    JACK = 'J'
    QUEEN = 'Q'
    KING = 'K'


class FACE_VALUES(Enum):
    ACE = 14
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13


class SEATS(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3


TWO_OF_CLUBS = Card(FACE.TWO, SUIT.CLUBS)
QUEEN_OF_SPADES = Card(FACE.QUEEN, SUIT.SPADES)
DECK = tuple(sorted(Card(f, s) for f in FACE for s in SUIT))
