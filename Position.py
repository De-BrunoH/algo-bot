from typing import Dict, List

class Order:

    def __init__(self, api_order: dict) -> None:
        self.specs = api_order


class Position:

    def __init__(self, api_position: dict, stop_losses: List[Order], take_profits: List[Order], is_triggered: bool) -> None:
        self.is_triggered = is_triggered
        self.stop_loss = stop_losses
        self.take_profit = take_profits # there can be more than 1 TP
        self.specs = api_position
