from gym import Env
from gym.spaces import Discrete, Box
import numpy as np
import random
from hearts.player import Player
from hearts import facts, utils
from itertools import repeat, chain
from ql.encoder import *


OTHER_SEAT = [facts.SEATS.EAST, facts.SEATS.WEST, facts.SEATS.SOUTH]

class HeartsEnv(Env):
    def __init__(self, player, others, direction=facts.DIRECTION.LEFT):
        self.player = player
        self.others = others
        self.players = {player} | set(others)
        self.player_seats = {p.seat.value: p for p in self.players}

        self.action_space = Discrete(13)
        self.observation_space = Box(0, 13, shape=(2, 52))
        self.state = np.zeros((16, 52))

        self.lead = None
        self.direction = direction
        self.broken_hearts = False
        self.is_first = True
        self.gives = dict()
        self.played_cards = {}
        self.turns = []
        self.num_invalid = 0
        self.total_invalid = 0

        self.seat_value = player.seat.value
        self.seat_adj = facts.SEATS.NORTH.value - player.seat.value

        self._turns_iter = None

        if self.direction != facts.DIRECTION.KEEP:
            self.to_give = 3
        else:
            self.to_give = 0
        self.num_turns = 0

        self.start()

    def start(self, verbose=False):
        self._deal_cards()
        if verbose:
            print(f'{self.direction.name}:')

        for g in OTHER_SEAT:
            s = facts.SEATS((g.value + self.direction.value) % 4)
            cards = self.player_seats[s.value].select_give(s)
            self.gives[self.player_seats[g.value]] = (s, cards)

    def _resolve_gives(self, verbose=False):
        for g, (r, cards) in self.gives.items():
            if verbose:
                print(f'\t{g.seat.name} -> {r.name}: {sorted(cards)}')
        self._turns_iter = self._turn(next((p for p in self.players if facts.TWO_OF_CLUBS in p.hand)))

    def step(self, action):
        if self.to_give > 0:
            (self.state, reward, done, info), valid = self._give_step(action)
            if valid:
                self.num_invalid = 0
                self.to_give -= 1
                if self.to_give == 0:
                    self._resolve_gives()
                    next(self._turns_iter)
                self.state = obs_round_encoder(self.player, self)
                return self.state, reward, done, info
        else:
            (self.state, reward, done, info), valid = self._turn_step(action)
            if valid:
                self.num_invalid = 0
                self.num_turns += 1
                self.is_first = False

                sp = next(self._turns_iter)
                self._turns_iter = self._turn(sp)

                if self.num_turns == 13:
                    reward = self.score()
                    done = True
                    print()
                    print(f'Score: {reward}, Fails: {self.total_invalid}')
                    print(', '.join(f'{p.seat.name}: {p.score}' for p in self.players))
                else:
                    next(self._turns_iter)

                self.state = obs_round_encoder(self.player, self)
                return self.state, reward, done, info
            self.num_invalid += 1
            self.total_invalid += 1
            if self.num_invalid > 15:
                done = True
                reward = -(200 + 100 * len(self.player.hand))
                print()
                print(f'Failed to Finish, with {len(self.player.hand)} cards: {sorted(self.player.hand)}')
                valid_actions = [self.player.starting_hand.index(c)
                                for c in sorted(self.player.can_play(self.lead, self.broken_hearts, self.is_first))]
                print(f'Action: {action}, valid actions: {valid_actions}')
            return self.state, reward, done, info

    def _deal_cards(self, verbose: bool = False) -> None:
        d = utils.shuffle_deck()
        for i, p in enumerate(self.players):
            i *= 13
            hand = set(d[i:i + 13])
            p.start_round(hand)

            if verbose:
                print(f'{p.seat.name}: {sorted(hand)}')

    def _give_step(self, action):
        c = self.player.starting_hand[action]
        if c in self.player.hand:
            if self.player in self.gives:
                self.gives[self.player][1].add(c)
            else:
                seat = facts.SEATS(self.direction.value % 4)
                self.gives[self.player] = (seat, {c})
            return (self.state, 0, False, {}), True
        else:
            return (self.state, -10, False, {}), False

    def _turn_step(self, action):
        c = self.player.starting_hand[action]
        if c in self.player.can_play(self.lead, self.broken_hearts, self.is_first):

            # print(f'NORTH, Played: {sorted(self.played_cards.values())}\n'
            #       f'\tHand: {sorted(self.player.hand)}\n'
            #       f'\tValid: {sorted(self.player.can_play(self.lead, self.broken_hearts, self.is_first))}\n'
            #       f'\t\t-> {c}')

            self.player.play(c)
            self.played_cards[self.player] = c
            return (self.state, 0, False, {}), True
        else:
            return (self.state, -10, False, {}), False

    def _turn(self, starting_player: 'Player', verbose: bool = False):
        self.lead = None
        self.played_cards = {}
        self.turns.append(self.played_cards)
        lead_seat = starting_player.seat
        if starting_player == self.player:
            yield
            self.lead = self.played_cards[starting_player].suit
        else:
            card = starting_player.select_play(None, self.broken_hearts, self.is_first)
            self.lead = card.suit

            if verbose:
                print(f'{starting_player.seat.name}, Starting\n'
                      f'\tHand: {sorted(starting_player.hand)}\n'
                      f'\tValid: {sorted(starting_player.can_play(None, self.broken_hearts, self.is_first))}\n'
                      f'\t\t-> {card}')

            starting_player.play(card)
            self.played_cards = {starting_player: card}
        self.is_first = False

        for i in range(1, 4):
            seat = facts.SEATS((i + lead_seat.value) % 4)

            player = self.player_seats[seat.value]
            if player == self.player:
                yield
            else:
                card = player.select_play(self.lead, self.broken_hearts, self.is_first)
                if verbose:
                    print(f'{seat.name}, Played: {sorted(self.played_cards.values())}\n'
                          f'\tHand: {sorted(player.hand)}\n'
                          f'\tValid: {sorted(player.can_play(self.lead, self.broken_hearts, self.is_first))}\n'
                          f'\t\t-> {card}')

                player.play(card)
                self.played_cards.update({player: card})

        if not self.broken_hearts:
            self.broken_hearts = any(c.face == facts.SUIT.HEARTS for c in self.played_cards.values())

        starting_player = max(self.players, key=lambda p: utils.score_card(self.lead, self.played_cards[p]))
        starting_player.win(set(self.played_cards.values()))

        if verbose:
            print(f'Won: {starting_player.seat.name} '
                  f'-> {self.played_cards[starting_player]}, {sorted(self.played_cards.values())}')
        yield starting_player

    def score(self):
        if self.player.score == 26:
            return 100
        other_scores = [p.score for p in self.others]
        if 26 in other_scores:
            return 4
        else:
            return 20 + sum(other_scores) - self.player.score

    def render(self):
        pass

    def reset(self):
        for p in (self.player, *self.others):
            p.end_round()
        self.__init__(self.player, self.others)

        self.state = obs_round_encoder(self.player, self)
        return self.state


episodes = 1
init_player = Player(facts.SEATS.NORTH)
others = [Player(s) for s in OTHER_SEAT]
env = HeartsEnv(init_player, others)
# for episode in range(1, episodes + 1):
#     done = False
#     score = 0
#
#     while not done:
#         # env.render()
#         action = env.action_space.sample()
#         n_state, reward, done, info = env.step(action)
#         print(n_state)
#         score += reward
#         if score < -1000:
#             break
#     env.reset()
#     print('Episode:{} Score:{}'.format(episode, score))


from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.optimizers import Adam
from rl.agents import DQNAgent
from rl.policy import BoltzmannQPolicy
from rl.memory import SequentialMemory

states = env.observation_space.shape
actions = env.action_space.n


def build_model(states, actions):
    model = Sequential()
    model.add(Flatten(input_shape=(1, *states)))
    model.add(Dense(256, activation='relu'))
    model.add(Dense(256, activation='relu'))
    model.add(Dense(256, activation='relu'))
    model.add(Dense(256, activation='relu'))
    model.add(Dense(actions, activation='linear'))
    return model


def build_agent(model, actions):
    policy = BoltzmannQPolicy()
    memory = SequentialMemory(limit=50000, window_length=1)
    dqn = DQNAgent(model=model, memory=memory, policy=policy,
                  nb_actions=actions, nb_steps_warmup=10000, target_model_update=1e-2)
    return dqn


model = build_model(states, actions)
model.summary()

dqn = build_agent(model, actions)
dqn.compile(Adam(lr=1e-3), metrics=['mae'])
dqn.fit(env, nb_steps=500000000, visualize=False, verbose=1)
