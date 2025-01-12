from chess.movegen import generate_all_moves
from chess.ai.evaluation import evaluate_board

PIECE_VALUES = {
    'wP': 1, 'wN': 3, 'wB': 3, 'wR': 5, 'wQ': 9, 'wK': 1000,
    'bP': 1, 'bN': 3, 'bB': 3, 'bR': 5, 'bQ': 9, 'bK': 1000
}

class AIPlayer:
    def __init__(self, game_state, depth=3):
        self.game_state = game_state
        self.depth = depth

    def select_move(self):
        """
        Select a move for the AI player using the minimax algorithm.
        """
        if self.game_state.game_over:
            return None  # No moves possible when the game is over

        best_move = None
        best_value = float('-inf') if self.game_state.whiteToMove else float('inf')
        all_moves = generate_all_moves(self.game_state)

        for move in all_moves:
            self.game_state.make_move(move)
            board_value = self.minimax(self.depth - 1, not self.game_state.whiteToMove)
            self.game_state.unmake_move(move)

            if self.game_state.whiteToMove:
                if board_value > best_value:
                    best_value = board_value
                    best_move = move
            else:
                if board_value < best_value:
                    best_value = board_value
                    best_move = move

        return best_move

    def minimax(self, depth, is_maximizing):
        """
        Minimax algorithm to evaluate the board state.
        """
        if depth == 0 or self.game_state.game_over:
            return evaluate_board(self.game_state)

        all_moves = generate_all_moves(self.game_state)
        if not all_moves:
            return evaluate_board(self.game_state)  # Return evaluation if no moves left

        if is_maximizing:
            max_eval = float('-inf')
            for move in all_moves:
                self.game_state.make_move(move)
                eval = self.minimax(depth - 1, False)
                self.game_state.unmake_move(move)
                max_eval = max(max_eval, eval)
            return max_eval
        else:
            min_eval = float('inf')
            for move in all_moves:
                self.game_state.make_move(move)
                eval = self.minimax(depth - 1, True)
                self.game_state.unmake_move(move)
                min_eval = min(min_eval, eval)
            return min_eval
