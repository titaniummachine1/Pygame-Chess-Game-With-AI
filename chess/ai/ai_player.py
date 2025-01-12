import random
from chess.movegen import generate_all_moves
from chess.move import Move

PIECE_VALUES = {
    'wP': 1, 'wN': 3, 'wB': 3, 'wR': 5, 'wQ': 9, 'wK': 0,
    'bP': 1, 'bN': 3, 'bB': 3, 'bR': 5, 'bQ': 9, 'bK': 0
}

class AIPlayer:
    def __init__(self, game_state, depth=4):
        self.game_state = game_state
        self.depth = depth

    def select_move(self):
        """
        Select a move for the AI player using the minimax algorithm.
        """
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
        if depth == 0:
            return self.evaluate_board()

        all_moves = generate_all_moves(self.game_state)
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

    def evaluate_board(self):
        """
        Evaluate the board based on material count.
        """
        white_material = (
            bin(self.game_state.whitePawns).count('1') * PIECE_VALUES['wP'] +
            bin(self.game_state.whiteKnights).count('1') * PIECE_VALUES['wN'] +
            bin(self.game_state.whiteBishops).count('1') * PIECE_VALUES['wB'] +
            bin(self.game_state.whiteRooks).count('1') * PIECE_VALUES['wR'] +
            bin(self.game_state.whiteQueen).count('1') * PIECE_VALUES['wQ']
        )
        black_material = (
            bin(self.game_state.blackPawns).count('1') * PIECE_VALUES['bP'] +
            bin(self.game_state.blackKnights).count('1') * PIECE_VALUES['bN'] +
            bin(self.game_state.blackBishops).count('1') * PIECE_VALUES['bB'] +
            bin(self.game_state.blackRooks).count('1') * PIECE_VALUES['bR'] +
            bin(self.game_state.blackQueen).count('1') * PIECE_VALUES['bQ']
        )
        return white_material - black_material
