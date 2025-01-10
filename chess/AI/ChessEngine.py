import time
import asyncio
import logging
from chess.game import GameState
from chess.movegen import generate_all_moves
from chess.bitboard import test_bit
from chess.AI.evaluation import PIECE_VALUES, MG_PIECE_SQUARE_TABLES

CHECKMATE_SCORE = 99999  # Large score magnitude to indicate a forced win or loss

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ChessAI:
    def __init__(self, max_depth=5, time_limit=30):
        self.max_depth = max_depth
        self.time_limit = time_limit

        # For UI display:
        self.current_depth = 0
        self.current_eval  = 0

        self.start_time = None
        self.best_move_so_far = None

    async def find_best_move(self, game_state: GameState):
        """
        Iterative deepening search up to max_depth or until time is up.
        If no moves exist, that's an immediate loss for side to move.
        """
        self.start_time = time.time()
        root_maximizing = game_state.whiteToMove
        self.best_move_so_far = None

        # Generate all root moves
        root_moves = generate_all_moves(game_state)
        if not root_moves:
            # No moves => side to move loses right away
            self.current_depth = 0
            self.current_eval  = self._no_moves_score(game_state)
            return None

        # Sort moves so captures come first
        root_moves = self._order_moves(game_state, root_moves)

        alpha = float('-inf')
        beta  = float('inf')

        for depth in range(1, self.max_depth + 1):
            self.current_depth = depth
            best_score = float('-inf') if root_maximizing else float('inf')
            best_move  = None

            for move in root_moves:
                game_state.make_move(move)
                score = await self.minimax(game_state, depth - 1, alpha, beta, not root_maximizing)
                game_state.unmake_move(move)

                if root_maximizing:
                    if score > best_score:
                        best_score = score
                        best_move  = move
                    alpha = max(alpha, best_score)
                else:
                    if score < best_score:
                        best_score = score
                        best_move  = move
                    beta = min(beta, best_score)

                # Check time
                if self.time_limit and (time.time() - self.start_time) > self.time_limit:
                    break

                # Do not prune at the root level
                # if alpha >= beta:
                #     break

            # If found a best move at this depth, save partial result
            if best_move:
                self.best_move_so_far = best_move
                self.current_eval     = int(best_score)

            # Time up?
            if self.time_limit and (time.time() - self.start_time) > self.time_limit:
                break

            # yield so UI can update
            await asyncio.sleep(0)

        return self.best_move_so_far

    async def minimax(self, game_state: GameState, depth: int,
                      alpha: float, beta: float, maximizing: bool) -> float:
        """
        Alpha-beta search, with 'no moves => lose' and 'king missing => lose'.
        """
        # Time check
        if self.time_limit and (time.time() - self.start_time) > self.time_limit:
            return self.evaluate_board(game_state)

        # Check if the side to move has lost its king
        side_white = game_state.whiteToMove
        if self._king_is_gone(game_state, side_white):
            # if your king is gone at the start of your turn => you lost
            return -CHECKMATE_SCORE if side_white else +CHECKMATE_SCORE

        if depth == 0:
            return self.evaluate_board(game_state)

        moves = generate_all_moves(game_state)
        if not moves:
            # No moves => side to move instantly loses
            return self._no_moves_score(game_state)

        # Basic move ordering: captures first
        moves = self._order_moves(game_state, moves)

        if maximizing:
            best_value = float('-inf')
            for move in moves:
                game_state.make_move(move)
                value = await self.minimax(game_state, depth - 1, alpha, beta, False)
                game_state.unmake_move(move)

                if value > best_value:
                    best_value = value
                alpha = max(alpha, best_value)

                # occasional yield
                await asyncio.sleep(0)

                # Debug logging
                logging.debug(f"Depth: {depth}, Move: {str(move)}, Alpha: {alpha}, Beta: {beta}, Value: {value}")

                if alpha >= beta:
                    break

            return best_value

        else:
            best_value = float('inf')
            for move in moves:
                game_state.make_move(move)
                value = await self.minimax(game_state, depth - 1, alpha, beta, True)
                game_state.unmake_move(move)

                if value < best_value:
                    best_value = value
                beta = min(beta, best_value)

                await asyncio.sleep(0)

                # Debug logging
                logging.debug(f"Depth: {depth}, Move: {str(move)}, Alpha: {alpha}, Beta: {beta}, Value: {value}")

                if alpha >= beta:
                    break

            return best_value

    def evaluate_board(self, game_state: GameState) -> float:
        """
        Simple material + piece-square table evaluation.
        """
        # Basic material
        w_score = (
            PIECE_VALUES['P'] * bin(game_state.whitePawns).count('1') +
            PIECE_VALUES['N'] * bin(game_state.whiteKnights).count('1') +
            PIECE_VALUES['B'] * bin(game_state.whiteBishops).count('1') +
            PIECE_VALUES['R'] * bin(game_state.whiteRooks).count('1') +
            PIECE_VALUES['Q'] * bin(game_state.whiteQueen).count('1') +
            PIECE_VALUES['K'] * bin(game_state.whiteKing).count('1')
        )
        b_score = (
            PIECE_VALUES['P'] * bin(game_state.blackPawns).count('1') +
            PIECE_VALUES['N'] * bin(game_state.blackKnights).count('1') +
            PIECE_VALUES['B'] * bin(game_state.blackBishops).count('1') +
            PIECE_VALUES['R'] * bin(game_state.blackRooks).count('1') +
            PIECE_VALUES['Q'] * bin(game_state.blackQueen).count('1') +
            PIECE_VALUES['K'] * bin(game_state.blackKing).count('1')
        )

        # White piece-square table
        w_psq = 0
        for sq in range(64):
            if test_bit(game_state.whitePawns, sq):
                w_psq += MG_PIECE_SQUARE_TABLES['P'][sq]
            if test_bit(game_state.whiteKnights, sq):
                w_psq += MG_PIECE_SQUARE_TABLES['N'][sq]
            if test_bit(game_state.whiteBishops, sq):
                w_psq += MG_PIECE_SQUARE_TABLES['B'][sq]
            if test_bit(game_state.whiteRooks, sq):
                w_psq += MG_PIECE_SQUARE_TABLES['R'][sq]
            if test_bit(game_state.whiteQueen, sq):
                w_psq += MG_PIECE_SQUARE_TABLES['Q'][sq]
            if test_bit(game_state.whiteKing, sq):
                w_psq += MG_PIECE_SQUARE_TABLES['K'][sq]

        # Black piece-square table (flip sq => 63 - sq)
        b_psq = 0
        for sq in range(64):
            flipped = 63 - sq
            if test_bit(game_state.blackPawns, sq):
                b_psq += MG_PIECE_SQUARE_TABLES['P'][flipped]
            if test_bit(game_state.blackKnights, sq):
                b_psq += MG_PIECE_SQUARE_TABLES['N'][flipped]
            if test_bit(game_state.blackBishops, sq):
                b_psq += MG_PIECE_SQUARE_TABLES['B'][flipped]
            if test_bit(game_state.blackRooks, sq):
                b_psq += MG_PIECE_SQUARE_TABLES['R'][flipped]
            if test_bit(game_state.blackQueen, sq):
                b_psq += MG_PIECE_SQUARE_TABLES['Q'][flipped]
            if test_bit(game_state.blackKing, sq):
                b_psq += MG_PIECE_SQUARE_TABLES['K'][flipped]

        w_score += w_psq
        b_score += b_psq
        return float(w_score - b_score)

    def _king_is_gone(self, game_state: GameState, side_white: bool) -> bool:
        """Return True if side's king bitboard is empty."""
        if side_white:
            return (game_state.whiteKing == 0)
        else:
            return (game_state.blackKing == 0)

    def _no_moves_score(self, game_state: GameState) -> float:
        """
        If no moves => side to move loses instantly.
        Return a big negative if white to move, big positive if black to move.
        """
        # White is maximizing => if White has no moves => White lost => large negative
        # Black is minimizing => if Black has no moves => that’s good for White => large positive
        return -CHECKMATE_SCORE if game_state.whiteToMove else +CHECKMATE_SCORE

    def _order_moves(self, game_state: GameState, moves):
        """Sort moves using MVV-LVA heuristic and prioritize attacks on the king, captures, threats of capture, and piece movements before pawn movements."""
        piece_values = {
            'K': 1000, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1,
            'k': 1000, 'q': 9, 'r': 5, 'b': 3, 'n': 3, 'p': 1
        }

        def move_score(move):
            score = 0
            if move.isCapture:
                victim_value = piece_values.get(move.captured_piece, 0)
                attacker_value = piece_values.get(move.piece, 0)
                score += 10 * victim_value - attacker_value
            if move.isCastle:
                score += 100
            if move.piece in ['K', 'k']:
                score += 1000
            elif move.piece in ['Q', 'q']:
                score += 900
            elif move.piece in ['R', 'r']:
                score += 500
            elif move.piece in ['B', 'b', 'N', 'n']:
                score += 300
            elif move.piece in ['P', 'p']:
                score += 100
            return score

        return sorted(moves, key=move_score, reverse=True)
