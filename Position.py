from typing import List


class Order:

    def __init__(self, type: str, api_order: dict) -> None:
        self.type = type
        self.specs = api_order

class Position:
    def __init__(self, api_position: dict, stop_losses: List[Order], take_profits: List[Order], is_triggered: bool) -> None:
        self.is_triggered = is_triggered
        self.stop_losses = stop_losses
        self.take_profits = take_profits # there can be more than 1 TP
        self.specs = api_position

    def update_specs(self, new_position_specs: dict) -> None:
        self.specs = new_position_specs

    def triggered_successfully(self) -> None:
        self.is_triggered = True
