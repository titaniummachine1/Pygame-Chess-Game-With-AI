# chess/AI/ChessEngine.py
import time, asyncio
import math
from chess.game import GameState
from chess.movegen import generate_all_moves, Move

#
# Simple piece-square table (PST) example. 
# You can paste your own from PeSTO or any other source as needed.
#
PIECE_SQUARE_TABLES = {
    # We'll store PST for White in index [sq],
    # and for Black in index [63 - sq] if symmetrical, 
    # or you can store separate. For brevity, a small one:
    'P': [  0,  0,  0,  0,  0,  0,  0,  0,
            5, 10, 10,-20,-20, 10, 10,  5,
            5, -5,-10,  0,  0,-10, -5,  5,
            0,  0,  0, 20, 20,  0,  0,  0,
            5,  5, 10,25,25, 10,  5,  5,
           10, 10, 20,30,30, 20, 10, 10,
           50, 50, 50,50,50, 50, 50, 50,
            0,  0,  0,  0,  0,  0,  0,  0 ],  # white pawn

    'N': [-50,-40,-30,-30,-30,-30,-40,-50,
          -40,-20,  0,  0,  0,  0,-20,-40,
          -30,  0, 10, 15, 15, 10,  0,-30,
          -30,  5, 15, 20, 20, 15,  5,-30,
          -30,  0, 15, 20, 20, 15,  0,-30,
          -30,  5, 10, 15, 15, 10,  5,-30,
          -40,-20,  0,  5,  5,  0,-20,-40,
          -50,-40,-30,-30,-30,-30,-40,-50 ],  # white knight

    'B': [-20,-10,-10,-10,-10,-10,-10,-20,
          -10,  0,  0,  0,  0,  0,  0,-10,
          -10,  0,  5, 10, 10,  5,  0,-10,
          -10,  5,  5, 10, 10,  5,  5,-10,
          -10,  0, 10, 10, 10, 10,  0,-10,
          -10, 10, 10, 10, 10, 10, 10,-10,
          -10,  5,  0,  0,  0,  0,  5,-10,
          -20,-10,-10,-10,-10,-10,-10,-20 ],  # white bishop

    'R': [  0,  0,  0,  5,  5,  0,  0,  0,
            0, -5, -5, -5, -5, -5, -5,  0,
            0, -5, -5, -5, -5, -5, -5,  0,
            5,  0,  0,  0,  0,  0,  0,  5,
            5,  0,  0,  0,  0,  0,  0,  5,
            5,  0,  0,  0,  0,  0,  0,  5,
            5,  0,  0,  0,  0,  0,  0,  5,
            0,  0,  0,  5,  5,  0,  0,  0 ],  # white rook

    'Q': [-20,-10,-10, -5, -5,-10,-10,-20,
          -10,  0,  0,  0,  0,  0,  0,-10,
          -10,  0,  5,  5,  5,  5,  0,-10,
           -5,  0,  5,  5,  5,  5,  0, -5,
            0,  0,  5,  5,  5,  5,  0, -5,
          -10,  5,  5,  5,  5,  5,  0,-10,
          -10,  0,  5,  0,  0,  0,  0,-10,
          -20,-10,-10, -5, -5,-10,-10,-20 ],  # white queen

    'K': [-30,-40,-40,-50,-50,-40,-40,-30,
          -30,-40,-40,-50,-50,-40,-40,-30,
          -30,-40,-40,-50,-50,-40,-40,-30,
          -30,-40,-40,-50,-50,-40,-40,-30,
          -20,-30,-30,-40,-40,-30,-30,-20,
          -10,-20,-20,-20,-20,-20,-20,-10,
           20, 20,  0,  0,  0,  0, 20, 20,
           20, 30, 10,  0,  0, 10, 30, 20 ],  # white king
}

def _mirror_index(sq):
    """ Mirror index for black piece-square usage (flip rank). """
    return 63 - sq

class ChessAI:
    def __init__(self, max_depth=5, time_limit=5, piece_values=None):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.piece_values = piece_values or {
            'P': 100, 'N': 280, 'B': 320, 'R': 479, 'Q': 929, 'K': 60000
        }
        self.start_time = None
        self.best_move_so_far = None

    async def find_best_move(self, game_state: GameState):
        """
        Asynchronously search for the best move using iterative deepening + alpha-beta.
        We'll do alpha-beta from depth=1..max_depth or until time limit is reached.
        After each iteration, update self.best_move_so_far, then yield control.
        """
        self.start_time = time.time()
        root_maximizing = game_state.whiteToMove
        self.best_move_so_far = None

        # Generate all moves (the root move list)
        root_moves = generate_all_moves(game_state)
        if not root_moves:
            return None

        # --- Move ordering at root: put captures first ---
        root_moves = self._sort_moves(game_state, root_moves)

        alpha = float('-inf')
        beta = float('inf')

        for depth in range(1, self.max_depth + 1):
            best_score = float('-inf') if root_maximizing else float('inf')
            best_move = None

            # Debug: see if we're going deeper
            # print(f"Depth {depth} searching... (time={time.time()-self.start_time:.2f}s)")

            for move in root_moves:
                game_state.make_move(move)

                score = await self.minimax(game_state, depth - 1,
                                           alpha, beta,
                                           not root_maximizing)
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

                # Time check
                if self.time_limit and (time.time() - self.start_time) > self.time_limit:
                    break

                # Alpha-beta prune at root (rare but possible)
                if alpha >= beta:
                    break

            # If we found a best move => store it
            if best_move:
                self.best_move_so_far = best_move
                # Debug: see final best score at this depth
                # print(f"Depth {depth} complete. Best: {best_move} Score={best_score}")

            # Check if time's up
            if self.time_limit and (time.time() - self.start_time) > self.time_limit:
                break

            # yield so Pygame loop can remain responsive
            await asyncio.sleep(0)

        return self.best_move_so_far

    async def minimax(self, game_state: GameState, depth: int,
                      alpha: float, beta: float, maximizing: bool):
        """Asynchronous alpha-beta with a simple move-ordering by capture vs. non-capture."""
        # Time check
        if self.time_limit and (time.time() - self.start_time) > self.time_limit:
            return self.evaluate_board(game_state)

        if depth == 0:
            return self.evaluate_board(game_state)

        moves = generate_all_moves(game_state)
        if not moves:
            # No moves => e.g. checkmate/stalemate => evaluate
            return self.evaluate_board(game_state)

        # Sort moves for better alpha-beta performance
        moves = self._sort_moves(game_state, moves)

        if maximizing:
            value = float('-inf')
            for move in moves:
                game_state.make_move(move)
                score = await self.minimax(game_state, depth - 1, alpha, beta, False)
                game_state.unmake_move(move)

                value = max(value, score)
                alpha = max(alpha, value)

                # yield control occasionally
                await asyncio.sleep(0)

                if alpha >= beta:
                    break
                if self.time_limit and (time.time() - self.start_time) > self.time_limit:
                    break
            return value
        else:
            value = float('inf')
            for move in moves:
                game_state.make_move(move)
                score = await self.minimax(game_state, depth - 1, alpha, beta, True)
                game_state.unmake_move(move)

                value = min(value, score)
                beta = min(beta, value)

                # yield control occasionally
                await asyncio.sleep(0)

                if alpha >= beta:
                    break
                if self.time_limit and (time.time() - self.start_time) > self.time_limit:
                    break
            return value

    def evaluate_board(self, game_state: GameState):
        """Material + piece-square table evaluation."""
        # Material
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
        # PST for White pieces
        white_ps_score = self._piece_square_score(game_state.whitePawns,   'P', True)
        white_ps_score += self._piece_square_score(game_state.whiteKnights,'N', True)
        white_ps_score += self._piece_square_score(game_state.whiteBishops,'B', True)
        white_ps_score += self._piece_square_score(game_state.whiteRooks,  'R', True)
        white_ps_score += self._piece_square_score(game_state.whiteQueen,  'Q', True)
        white_ps_score += self._piece_square_score(game_state.whiteKing,   'K', True)
        # PST for Black
        black_ps_score = self._piece_square_score(game_state.blackPawns,   'P', False)
        black_ps_score += self._piece_square_score(game_state.blackKnights,'N', False)
        black_ps_score += self._piece_square_score(game_state.blackBishops,'B', False)
        black_ps_score += self._piece_square_score(game_state.blackRooks,  'R', False)
        black_ps_score += self._piece_square_score(game_state.blackQueen,  'Q', False)
        black_ps_score += self._piece_square_score(game_state.blackKing,   'K', False)

        total_white = white_score + white_ps_score
        total_black = black_score + black_ps_score

        return total_white - total_black

    def _piece_square_score(self, bitboard: int, piece_char: str, is_white: bool) -> int:
        """Sum up the piece-square table contributions for all bits in 'bitboard'."""
        pst = PIECE_SQUARE_TABLES[piece_char]
        total = 0
        while bitboard:
            sq = (bitboard & -bitboard).bit_length() - 1
            # remove that bit
            bitboard &= bitboard - 1

            if is_white:
                # White piece => use PST index = sq
                total += pst[sq]
            else:
                # Black piece => we mirror the square for black PST
                total += pst[_mirror_index(sq)]
        return total

    def _sort_moves(self, game_state: GameState, moves):
        """
        Basic move ordering: put captures first.
        Could also do more advanced ordering if desired.
        """
        def move_sort_key(m: Move):
            # We can check if it's a capture by (after we make the move in a temp?)
            # or simpler: if 'isCapture' is set. True => put at front => sort by bool desc
            # Or do a small search of the piece captured for tie-break.
            return (not m.isCapture)  # so captures come first => False < True

        sorted_moves = sorted(moves, key=move_sort_key)
        return sorted_moves
