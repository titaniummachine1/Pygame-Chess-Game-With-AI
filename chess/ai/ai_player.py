import random
from chess.movegen import generate_all_moves
from chess.move import Move

class AIPlayer:
    def __init__(self, game_state):
        self.game_state = game_state

    def select_move(self):
        """
        Select a move for the AI player.
        Currently, it selects a random move from the list of all possible moves.
        """
        all_moves = generate_all_moves(self.game_state)
        if not all_moves:
            return None
        return random.choice(all_moves)
