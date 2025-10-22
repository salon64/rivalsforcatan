from abc import ABC, abstractmethod
import random

class PlayerStrategy(ABC):
    @abstractmethod
    def make_decision(self, decision_type, payload, player):
        pass

class HumanInputStrategy(PlayerStrategy):
    def make_decision(self, decision_type, payload):
        if decision_type == "ready_check":
            return True

        if decision_type == "list":
            return self._handle_list_choice(payload)
        elif decision_type == "quantity":
            return self._handle_quantity_choice(payload)
        else:
            raise ValueError(f"Unknown decision_type: {decision_type}")
    
    def _handle_list_choice(self, payload):
        """
        payload = {
            "message": "Choose a card:",
            "options": ["Card A", "Card B", "Card C"]
        }
        """
        print(payload["message"])
        for i, option in enumerate(payload["options"]):
            print(f"{i}: {option}")

        while True:
            try:
                choice = int(input("Enter choice index: "))
                if 0 <= choice < len(payload["options"]):
                    return choice
            except ValueError:
                pass
            print(f"Invalid choice: {choice}, try again.")

    def _handle_quantity_choice(self, payload):
        """
        payload = {
            "message": "How many units?",
            "min": 0,
            "max": 10
        }
        """
        print(payload["message"])
        while True:
            try:
                value = int(input(f"Enter a number ({payload['min']} - {payload['max']}): "))
                if payload["min"] <= value <= payload["max"]:
                    return value
            except ValueError:
                pass
            print(f"Invalid input: {value}, try again.")




class RandomAIStrategy(PlayerStrategy):
    def make_decision(self, decision_type, payload, player):
        if decision_type == "choose_resources":
            return random.choice(payload["options"])
        return "end_turn"
