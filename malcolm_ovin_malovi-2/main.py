# main.py
from game.core import Game
from game.phases.phases import InitialPhase
from game.players.player import Player
from game.players.strategies import HumanInputStrategy
from game.logger import Logger
from game.events.events import ExampleChoiceEvent
from game.events.events import SetUpCardsEvent
from game.modifiers_examples import ExampleAddOptionModifier

def main():
    game = Game(initial_phase=InitialPhase())

    p1 = Player("red", HumanInputStrategy(), 0)
    p2 = Player("blue", HumanInputStrategy(), 0)
    game.add_player(p1)
    game.add_player(p2)

    # register example modifier so it can decorate decision payloads
    game.modifier_engine.register(ExampleAddOptionModifier())

    # set red player (first player) as current
    game.current_player = p1

    # enqueue the interactive demo event
    # set up cards first
    game.enqueue_event(SetUpCardsEvent())
    game.enqueue_event(ExampleChoiceEvent())

    game.add_observer(Logger())

    # run until interrupted
    game.run_until()

if __name__ == "__main__":
    main()
