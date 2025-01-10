# chess/AI/ChessEngine.py (example)
import time
from chess.game import GameState
from chess.movegen import generate_all_moves

class ChessAI:
    def __init__(self, depth=3, time_limit=None, piece_values=None):
        self.depth = depth
        self.time_limit = time_limit
        self.piece_values = piece_values or {
            'P': 100, 'N': 280, 'B': 320, 'R': 479, 'Q': 929, 'K': 60000
        }
        self.start_time = None

    def find_best_move(self, game_state: GameState):
        """
        Synchronous: Perform alpha-beta search up to self.depth. Return best move.
        """
        self.start_time = time.time()
        root_maximizing = game_state.whiteToMove

        best_score = float('-inf') if root_maximizing else float('inf')
        best_move = None

        moves = generate_all_moves(game_state)
        if not moves:
            return None

        alpha = float('-inf')
        beta = float('inf')

        for move in moves:
            game_state.make_move(move)
            score = self.minimax(game_state, self.depth - 1, alpha, beta, not root_maximizing)
            game_state.unmake_move(move)

            if root_maximizing:
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, best_score)
            else:
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, best_score)

            if self.time_limit and time.time() - self.start_time > self.time_limit:
                break
            if alpha >= beta:
                break

        return best_move

    def minimax(self, game_state: GameState, depth: int, alpha: float, beta: float, maximizing: bool):
        if depth == 0 or (self.time_limit and time.time() - self.start_time > self.time_limit):
            return self.evaluate_board(game_state)

        moves = generate_all_moves(game_state)
        if not moves:
            return self.evaluate_board(game_state)  # No moves => presumably a losing or drawn position

        if maximizing:
            value = float('-inf')
            for move in moves:
                game_state.make_move(move)
                value = max(value, self.minimax(game_state, depth - 1, alpha, beta, not maximizing))
                game_state.unmake_move(move)
                alpha = max(alpha, value)
                if alpha >= beta or (self.time_limit and time.time() - self.start_time > self.time_limit):
                    break
            return value
        else:
            value = float('inf')
            for move in moves:
                game_state.make_move(move)
                value = min(value, self.minimax(game_state, depth - 1, alpha, beta, not maximizing))
                game_state.unmake_move(move)
                beta = min(beta, value)
                if alpha >= beta or (self.time_limit and time.time() - self.start_time > self.time_limit):
                    break
            return value

    def evaluate_board(self, game_state: GameState):
        """
        Very basic material-based eval. 
        Extend with piece-square tables or PeSTO if desired.
        """
        white_score = (
            self.piece_values['P'] * bin(game_state.whitePawns).count('1') +
            self.piece_values['N'] * bin(game_state.whiteKnights).count('1') +
            self.piece_values['B'] * bin(game_state.whiteBishops).count('1') +
            self.piece_values['R'] * bin(game_state.whiteRooks).count('1') +
            self.piece_values['Q'] * bin(game_state.whiteQueen).count('1') +
            self.piece_values['K'] * bin(game_state.whiteKing).count('1')
        )
        black_score = (
            self.piece_values['P'] * bin(game_state.blackPawns).count('1') +
            self.piece_values['N'] * bin(game_state.blackKnights).count('1') +
            self.piece_values['B'] * bin(game_state.blackBishops).count('1') +
            self.piece_values['R'] * bin(game_state.blackRooks).count('1') +
            self.piece_values['Q'] * bin(game_state.blackQueen).count('1') +
            self.piece_values['K'] * bin(game_state.blackKing).count('1')
        )
        return white_score - black_score