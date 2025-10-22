# Import classes from same package (use relative imports)
from ..core import Game
from ..events.events import NumberChoiceEvent, ReadyCheckEvent
from game.interfaces.game_phase import GamePhase

class InitialPhase(GamePhase):
    """does nothing is just used to step to actual first phase"""
    def handle(self, game: Game):
        pass

    def next_phase(self):
        return PhaseOne()

class PhaseOne(GamePhase):
    def handle(self, game: Game):
        game.notify_observers(
                "phase one",
                {}
            )
        game.enqueue_event(ReadyCheckEvent())

    def next_phase(self):
        return PhaseTwo()

class PhaseTwo(GamePhase):
    def handle(self, game: Game):
        game.notify_observers(
                "phase two",
                {}
            )
        
        game.enqueue_event(NumberChoiceEvent())
    
    def next_phase(self):
        return PhaseOne()
