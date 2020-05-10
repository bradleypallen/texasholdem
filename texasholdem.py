#!/usr/bin/env python
# coding: utf-8

import random, re
from itertools import combinations, chain
from collections import Counter

SUITS = ['♣', '♦', '♥', '♠']

SUITS_ASCII = ['C', 'D', 'H', 'S']

SUITS_LONG = ['clubs', 'diamonds', 'hearts', 'spades']

CARD_RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

CARD_RANKS_LONG = ['two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'jack', 'queen', 'king', 'ace']

STATES = ['compulsory bets', 'pre-flop', 'flop', 'turn', 'river', 'showdown']

HAND_RANKS = ['high card',
              'pair',
              'two pair',
              'three of a kind',
              'straight',
              'flush',
              'full house',
              'four of a kind',
              'straight flush',
              'royal flush']

WIN_PROBABILITY_SAMPLE_SIZE = 10000

class Card:

    def __init__(self, rank, suit):
        if rank in range(13) and suit in range(4):
            self.__card_rank = rank
            self.__suit = suit
        elif rank not in range(13):
            raise ValueError(f'{rank} is not a valid card rank (an int in range(13))')
        else:
            raise ValueError(f'{suit} is not a valid card suit (an int in range(4))')

    def rank(self):
        return self.__card_rank

    def suit(self):
        return self.__suit

    @classmethod
    def from_string(cls, str):
        return cls(CARD_RANKS.index(str[:-1].upper()), SUITS_ASCII.index(str[-1].upper()))

    def __eq__(self, other):
        return self.rank() == other.rank()

    def __ne__(self, other):
        return self.rank() != other.rank()

    def __lt__(self, other):
        return self.rank() < other.rank()

    def __le__(self, other):
        return self.rank() <= other.rank()

    def __gt__(self, other):
        return self.rank() > other.rank()

    def __ge__(self, other):
        return self.rank() >= other.rank()

    def __repr__(self):
        return f"<Card {CARD_RANKS[self.rank()]}{SUITS[self.suit()]}>"

    def __str__(self):
        return f"{CARD_RANKS[self.rank()]}{SUITS[self.suit()]}"

class Player:

    def __init__(self, id, pocket=[]):
        if len(pocket) < 3 and all(isinstance(x, Card) for x in pocket):
            self.__id = id
            self.__pocket = pocket
        else:
            raise ValueError(f'{pocket} is not a list of at most two Cards')

    def id(self):
        return self.__id

    def pocket(self):
        return self.__pocket

    def reset_pocket(self):
        self.__pocket = []

    def add_pocket_card(self, card):
        if len(self.__pocket) == 2:
            raise ValueError(f'{self} pocket is full')
        elif isinstance(card, Card):
            self.__pocket.append(card)
        else:
            raise ValueError(f'{cards} is not a Card')

    def __repr__(self):
        return f"<Player id {self.id()}, pocket {self.pocket()}>"

    def __str__(self):
        return f"{self.id()}: {','.join([f'{card}' for card in self.pocket()])}"

class Hand:

    def __init__(self, cards):
        if len(cards) == 5 and all(isinstance(x, Card) for x in cards):
            self.__cards = sorted(cards, reverse=True)
            ranks = [card.rank() for card in self.cards()]
            suits = [card.suit() for card in self.cards()]
            rank_counts = Counter(ranks).most_common()
            suit_counts = Counter(suits).most_common()
            low_card = min(ranks)
            ranks_set = frozenset(ranks)
            if suit_counts[0][1] == 5 and ranks_set == frozenset([8, 9, 10, 11, 12]):
                self.__hand_rank = 9 # royal flush
            elif suit_counts[0][1] == 5 and ranks_set == frozenset(range(low_card, low_card + 5)):
                self.__hand_rank = 8 # straight flush
            elif rank_counts[0][1] == 4:
                self.__hand_rank = 7 # four of a kind, with one kicker
            elif rank_counts[0][1] == 3 and rank_counts[1][1] == 2:
                self.__hand_rank = 6 # full house
            elif suit_counts[0][1] == 5:
                self.__hand_rank = 5 # flush
            elif ranks_set == frozenset(range(low_card, low_card + 5)) or ranks_set == frozenset([0, 1, 2, 3, 12]):
                self.__hand_rank = 4 # straight
            elif rank_counts[0][1] == 3:
                self.__hand_rank = 3 # three of a kind, with two kickers
            elif rank_counts[0][1] == 2 and rank_counts[1][1] == 2:
                self.__hand_rank = 2 # two pair, with one kicker
            elif rank_counts[0][1] == 2:
                self.__hand_rank = 1 # pair, with three kickers
            else:
                self.__hand_rank = 0 # high card
        else:
            raise ValueError(f'{cards} is not a list containing 5 Cards')

    def cards(self):
        return self.__cards

    def rank(self):
        return self.__hand_rank

    def description(self):
        card_ranks = [ count[0] for count in Counter([card.rank() for card in self.cards()]).most_common() ]
        if self.rank() == 9: # royal flush
            return f"royal flush"
        elif self.rank() == 8: # straight flush
            return f"{CARD_RANKS_LONG[card_ranks[0]]} high straight flush"
        elif self.rank() == 7: # four of a kind
            return f"{CARD_RANKS_LONG[card_ranks[0]]}s four of a kind, {CARD_RANKS_LONG[card_ranks[1]]} kicker"
        elif self.rank() == 6: # full house
            return f"{CARD_RANKS_LONG[card_ranks[0]]} over {CARD_RANKS_LONG[card_ranks[1]]}"
        elif self.rank() == 5: # flush
            return f"{CARD_RANKS_LONG[card_ranks[0]]} high flush"
        elif self.rank() == 4 and self.cards()[0].rank() == 12 and self.cards()[1].rank() == 3: # ace low straight
            return f"5 high straight"
        elif self.rank() == 4: # straight
            return f"{CARD_RANKS_LONG[card_ranks[0]]} high straight"
        elif self.rank() == 3: # three of a kind
            return f"{CARD_RANKS_LONG[card_ranks[0]]} trip, {', '.join([CARD_RANKS_LONG[r] for r in card_ranks[1:]])} kickers"
        elif self.rank() == 2: # two pair
            return f"{CARD_RANKS_LONG[card_ranks[0]]} up, {CARD_RANKS_LONG[card_ranks[-1]]} kicker"
        elif self.rank() == 1: # pair
            return f"pair {CARD_RANKS_LONG[card_ranks[0]]}, {', '.join([CARD_RANKS_LONG[r] for r in card_ranks[1:]])} kickers"
        else: # high card
            return f"{CARD_RANKS_LONG[card_ranks[0]]} high"

    def value(self):
        card_ranks = [ count[0] for count in Counter([card.rank() for card in self.cards()]).most_common() ]
        if self.rank() == 4 and card_ranks[0] == 12 and card_ranks[1] == 3: # address ace low straight case
            card_ranks = card_ranks[1:] + [-1]
        return [ self.rank() ] + card_ranks

    @classmethod
    def from_string(cls, str):
        return cls([Card.from_string(card_str) for card_str in re.findall(r'\d{0,1}\w{1,2}', str) ])

    def __eq__(self, other):
        return self.value() == other.value()

    def __ne__(self, other):
        return self.value() != other.value()

    def __lt__(self, other):
        return self.value() < other.value()

    def __le__(self, other):
        return self.value() <= other.value()

    def __gt__(self, other):
        return self.value() > other.value()

    def __ge__(self, other):
        return self.value() >= other.value()

    def __repr__(self):
        return f"<Hand {self.cards()}>"

    def __str__(self):
        ranks = [card.rank() for card in self.cards()]
        rank_counts = Counter(ranks).most_common()
        if self.rank() == 9: # royal flush
            cards = sorted(self.cards(), key=lambda x: x.rank())
        elif self.rank() == 8: # straight flush
            cards = sorted(self.cards(), key=lambda x: x.rank())
        elif self.rank() == 7: # four of a kind
            cards = [card for card in self.cards() if card.rank() == rank_counts[0][0]]
            cards += [card for card in self.cards() if card.rank() == rank_counts[1][0]]
        elif self.rank() == 6: # full house
            cards = [card for card in self.cards() if card.rank() == rank_counts[0][0]]
            cards += [card for card in self.cards() if card.rank() == rank_counts[1][0]]
        elif self.rank() == 5: # flush
            cards = self.cards()
        elif self.rank() == 4 and self.cards()[0].rank() == 12 and self.cards()[1].rank() == 3: # ace low straight
            cards = self.cards()[1:] + self.cards()[:1]
        elif self.rank() == 4: # straight
            cards = self.cards()
        elif self.rank() == 3: # three of a kind
            cards = [card for card in self.cards() if card.rank() == rank_counts[0][0]]
            cards += [card for card in self.cards() if card.rank() != rank_counts[0][0]]
        elif self.rank() == 2: # two pair
            cards = [card for card in self.cards() if card.rank() == rank_counts[0][0]]
            cards += [card for card in self.cards() if card.rank() == rank_counts[1][0]]
            cards += [card for card in self.cards() if not card in cards]
        elif self.rank() == 1: # pair
            cards = [card for card in self.cards() if card.rank() == rank_counts[0][0]]
            cards += [card for card in self.cards() if card.rank() != rank_counts[0][0]]
        else: # high card
            cards = self.cards()
        return ','.join([f"{card}" for card in cards])

class Deck:

    def __init__(self):
        self.__cards = []
        for suit in range(len(SUITS)):
            for rank in range(len(CARD_RANKS)):
                self.__cards.append(Card(rank, suit))

    def cards(self):
        return self.__cards

    def shuffle(self):
        random.shuffle(self.__cards)

    def deal(self):
        card = self.__cards.pop()
        return card

    def __repr__(self):
        return f"<Deck of {len(self.cards())} cards>"

class Game:

    def __init__(self, players, board=[], deck=Deck()):
        if not (1 < len(players) < 23 and all(isinstance(x, Player) for x in players)):
            raise ValueError(f'{players} is not a list of between 1 and 23 Players')
        elif not all(isinstance(x, Card) for x in board):
            raise ValueError(f'{board} is not a list of Cards')
        elif len(board) > 5:
            raise ValueError(f'{board} has more than 5 Cards')
        elif not isinstance(deck, Deck):
            raise ValueError(f'{deck} is not a Deck')
        else:
            self.__players = players
            self.__board = board
            self.__deck = deck
            self.__state = 0
            self.__dealer = 0

    def players(self):
        return self.__players

    def deck(self):
        return self.__deck

    def state(self):
        return f"{STATES[self.__state]}"

    def dealer(self):
        return self.players()[self.__dealer]

    def board(self):
        return self.__board

    def compulsory_bets(self):
        self.__state = 0
        self.__deck = Deck()
        self.__deck.shuffle()
        for player in self.players():
            player.reset_pocket()
        self.__dealer = (self.__dealer + 1) % len(self.players())
        self.__board = []

    def pre_flop(self):
        self.__state += 1
        for i in range(2):
            for player in self.players():
                player.add_pocket_card(self.__deck.deal())

    def flop(self):
        self.__state += 1
        self.__deck.deal()
        for i in range(3):
            self.__board.append(self.__deck.deal())

    def turn(self):
        self.__state += 1
        self.__deck.deal()
        self.__board.append(self.__deck.deal())

    def river(self):
        self.__state += 1
        self.__deck.deal()
        self.__board.append(self.__deck.deal())

    def showdown(self):
        self.__state += 1

    def play_hand(self):
        self.compulsory_bets()
        self.pre_flop()
        self.flop()
        self.turn()
        self.river()
        self.showdown()

    def possible_boards(self):
        remaining_draws = 5 - len(self.board())
        pocket_cards = [ card for card in chain.from_iterable([player.pocket() for player in self.players()]) ]
        seen_cards = [ f'{card}' for card in self.board() + pocket_cards ] # ugly hack as we made cards equal if their rank is equal
        fresh_deck = Deck()
        unseen_cards = [card for card in fresh_deck.cards() if not f'{card}' in seen_cards]
        return [self.board() + list(draw) for draw in combinations(unseen_cards, remaining_draws)]

    def possible_hands(self, player, board):
        cards = player.pocket() + board
        return [Hand(list(combination)) for combination in combinations(cards, 5)]

    def best_possible_hand(self, player, board):
        return sorted(self.possible_hands(player, board), reverse=True)[0]

    def player_odds(self):
        boards = self.possible_boards()
        n_boards = len(boards)
        if n_boards > WIN_PROBABILITY_SAMPLE_SIZE:
            boards = random.sample(boards, WIN_PROBABILITY_SAMPLE_SIZE)
            n_boards = WIN_PROBABILITY_SAMPLE_SIZE
        results = [ sorted([ (i, self.best_possible_hand(player, board)) for i, player in enumerate(self.players()) ], key=lambda x: x[1], reverse=True) for board in boards ]
        winners = [ [ result[i][0] for i in range(len(result)) if result[i][1] == result[0][1] ] for result in results ]
        wins = Counter([ winner[0] for winner in winners if len(winner) == 1 ])
        ties = Counter(list(chain.from_iterable([ winner for winner in winners if len(winner) > 1 ])))
        return [ (player, float(wins[i])/float(n_boards), float(ties[i])/float(n_boards)) for i, player in enumerate(self.players()) ]

    def is_a_tie(self):
        current_odds = sorted(self.player_odds(), key=lambda x: x[1:], reverse=True)
        return len(self.board()) == 5 and current_odds[0][2] == 1.0

    def hand_summary(self):
        current_odds = sorted(self.player_odds(), key=lambda x: x[1:], reverse=True)
        for player_odds in current_odds:
            player = player_odds[0]
            win_probability = player_odds[1]
            tie_probability = player_odds[2]
            if len(self.board()) == 5:
                best_hand = self.best_possible_hand(player, self.board())
                best_hand_description = f" \u2192 {best_hand} ({best_hand.description()})"
                print(f'{str(player):<20} {win_probability:>7.2%} win {tie_probability:>7.2%} tie {str(best_hand):>18} ({best_hand.description()})')
            else:
                print(f'{str(player):<20} {win_probability:>7.2%} win {tie_probability:>7.2%} tie')

    def __repr__(self):
        return f"<Game {self.state()} {','.join([f'{card}' for card in self.board()])}>"

    def __str__(self):
        return f"{self.state()} {','.join([f'{card}' for card in self.board()])}"
