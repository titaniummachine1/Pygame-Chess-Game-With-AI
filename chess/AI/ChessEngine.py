# chess/AI/ChessEngine.py
import time
import asyncio
from chess.game import GameState
from chess.movegen import generate_all_moves


class ChessAI:
    def __init__(self, max_depth=5, time_limit=5, piece_values=None):
        """
        :param max_depth: Maximum search depth in plies
        :param time_limit: Time limit for iterative deepening, in seconds
        :param piece_values: dict mapping piece letters to numerical values
        """
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.piece_values = piece_values or {
            'P': 100, 'N': 280, 'B': 320, 'R': 479, 'Q': 929, 'K': 60000
        }

        # We’ll keep track of the current search depth and evaluation
        # so the GUI can display them in real time.
        self.current_depth = 0      # which depth we are currently searching
        self.current_eval = 0       # best evaluation at root (White perspective)

        self.start_time = None
        self.best_move_so_far = None

    async def find_best_move(self, game_state: GameState):
        """
        Entry point for iterative deepening search. We'll iteratively
        deepen from depth=1..max_depth or until the time limit is reached.
        After each iteration, we store the best move in `self.best_move_so_far`
        and store the best eval in `self.current_eval`.
        """
        self.start_time = time.time()
        root_maximizing = game_state.whiteToMove
        self.best_move_so_far = None

        # Gather all possible moves from the root position
        root_moves = generate_all_moves(game_state)
        if not root_moves:
            # No moves => immediate terminal position
            self.current_depth = 0
            self.current_eval = self.evaluate_board(game_state)
            return None

        alpha = float('-inf')
        beta = float('inf')

        # Iterative deepening loop
        for depth in range(1, self.max_depth + 1):
            # Let the GUI see how "deep" we've gone
            self.current_depth = depth

            best_score = float('-inf') if root_maximizing else float('inf')
            best_move = None

            # Search each move at this depth
            for move in root_moves:
                game_state.make_move(move)
                score = await self.minimax(
                    game_state,
                    depth - 1,
                    alpha,
                    beta,
                    maximizing=not root_maximizing
                )
                game_state.unmake_move(move)

                # Root node logic to pick best/worst move
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

                # Check time limit
                if self.time_limit and (time.time() - self.start_time) > self.time_limit:
                    break

                # Alpha-beta cutoff
                if alpha >= beta:
                    break

            # If we got a best_move from this iteration, record it
            if best_move:
                self.best_move_so_far = best_move
                # From White’s perspective, 'best_score' is the evaluation.
                # If you prefer always from current side's perspective,
                # you can adjust sign if black is to move, etc.
                self.current_eval = int(best_score)

            # Also time-limit check at the end of iteration
            if self.time_limit and (time.time() - self.start_time) > self.time_limit:
                break

            # Give control back to event loop => prevents freezing
            await asyncio.sleep(0)

        # Return the best move from the deepest iteration we completed
        return self.best_move_so_far

    async def minimax(
        self,
        game_state: GameState,
        depth: int,
        alpha: float,
        beta: float,
        maximizing: bool
    ) -> float:
        """
        Alpha-beta search, asynchronous so we can `await asyncio.sleep(0)` 
        occasionally to keep the GUI responsive.
        """
        # Time check
        if self.time_limit and (time.time() - self.start_time) > self.time_limit:
            # Return an immediate evaluation if time is up
            return self.evaluate_board(game_state)

        # If we’re at depth=0, evaluate
        if depth == 0:
            return self.evaluate_board(game_state)

        moves = generate_all_moves(game_state)
        if not moves:
            # No moves => likely checkmate or stalemate
            return self.evaluate_board(game_state)

        if maximizing:
            best_value = float('-inf')
            for move in moves:
                game_state.make_move(move)
                value = await self.minimax(game_state, depth - 1, alpha, beta, False)
                game_state.unmake_move(move)

                best_value = max(best_value, value)
                alpha = max(alpha, best_value)

                # yield periodically
                await asyncio.sleep(0)

                # Check time limit
                if self.time_limit and (time.time() - self.start_time) > self.time_limit:
                    break
                # alpha-beta cutoff
                if alpha >= beta:
                    break

            return best_value
        else:
            best_value = float('inf')
            for move in moves:
                game_state.make_move(move)
                value = await self.minimax(game_state, depth - 1, alpha, beta, True)
                game_state.unmake_move(move)

                best_value = min(best_value, value)
                beta = min(beta, best_value)

                # yield periodically
                await asyncio.sleep(0)

                # Time check
                if self.time_limit and (time.time() - self.start_time) > self.time_limit:
                    break
                # alpha-beta cutoff
                if alpha >= beta:
                    break

            return best_value

    def evaluate_board(self, game_state: GameState) -> float:
        """
        Very basic material-only evaluation, from White's perspective:
         +  if White is leading in material
         -  if Black is leading
        Returns an integer or float. We'll just do integer “centipawns”.
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
        # Positive if White is better, negative if Black is better
        return float(white_score - black_score)
