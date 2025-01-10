# chess/AI/ChessEngine.py
import time
import asyncio
from chess.game import GameState
from chess.movegen import generate_all_moves
from chess.bitboard import test_bit
from chess.AI.evaluation import PIECE_VALUES, MG_PIECE_SQUARE_TABLES, EG_PIECE_SQUARE_TABLES

class ChessAI:
    def __init__(self, max_depth=5, time_limit=30):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.current_depth = 0
        self.current_eval = 0
        self.start_time = None
        self.best_move_so_far = None

    async def find_best_move(self, game_state: GameState):
        self.start_time = time.time()
        root_maximizing = game_state.whiteToMove
        self.best_move_so_far = None

        root_moves = generate_all_moves(game_state)
        if not root_moves:
            self.current_depth = 0
            self.current_eval = self.evaluate_board(game_state)
            return None

        alpha = float('-inf')
        beta = float('inf')

        for depth in range(1, self.max_depth + 1):
            self.current_depth = depth
            best_score = float('-inf') if root_maximizing else float('inf')
            best_move = None

            for move in root_moves:
                game_state.make_move(move)
                score = await self.minimax(game_state, depth - 1, alpha, beta, not root_maximizing)
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

                if self.time_limit and (time.time() - self.start_time) > self.time_limit:
                    break

                if alpha >= beta:
                    break

            if best_move:
                self.best_move_so_far = best_move
                self.current_eval = int(best_score)

            if self.time_limit and (time.time() - self.start_time) > self.time_limit:
                break

            await asyncio.sleep(0)

        return self.best_move_so_far

    async def minimax(self, game_state: GameState, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        if self.time_limit and (time.time() - self.start_time) > self.time_limit:
            return self.evaluate_board(game_state)

        if depth == 0:
            return self.evaluate_board(game_state)

        moves = generate_all_moves(game_state)
        if not moves:
            return self.evaluate_board(game_state)

        if maximizing:
            best_value = float('-inf')
            for move in moves:
                game_state.make_move(move)
                value = await self.minimax(game_state, depth - 1, alpha, beta, False)
                game_state.unmake_move(move)

                best_value = max(best_value, value)
                alpha = max(alpha, best_value)

                await asyncio.sleep(0)

                if self.time_limit and (time.time() - self.start_time) > self.time_limit:
                    break
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

                await asyncio.sleep(0)

                if self.time_limit and (time.time() - self.start_time) > self.time_limit:
                    break
                if alpha >= beta:
                    break

            return best_value

    def evaluate_board(self, game_state: GameState) -> float:
        white_score = (
            PIECE_VALUES['P'] * bin(game_state.whitePawns).count('1') +
            PIECE_VALUES['N'] * bin(game_state.whiteKnights).count('1') +
            PIECE_VALUES['B'] * bin(game_state.whiteBishops).count('1') +
            PIECE_VALUES['R'] * bin(game_state.whiteRooks).count('1') +
            PIECE_VALUES['Q'] * bin(game_state.whiteQueen).count('1') +
            PIECE_VALUES['K'] * bin(game_state.whiteKing).count('1')
        )
        black_score = (
            PIECE_VALUES['P'] * bin(game_state.blackPawns).count('1') +
            PIECE_VALUES['N'] * bin(game_state.blackKnights).count('1') +
            PIECE_VALUES['B'] * bin(game_state.blackBishops).count('1') +
            PIECE_VALUES['R'] * bin(game_state.blackRooks).count('1') +
            PIECE_VALUES['Q'] * bin(game_state.blackQueen).count('1') +
            PIECE_VALUES['K'] * bin(game_state.blackKing).count('1')
        )

        white_positional_score = sum(
            MG_PIECE_SQUARE_TABLES['P'][sq] for sq in range(64) if test_bit(game_state.whitePawns, sq)
        ) + sum(
            MG_PIECE_SQUARE_TABLES['N'][sq] for sq in range(64) if test_bit(game_state.whiteKnights, sq)
        ) + sum(
            MG_PIECE_SQUARE_TABLES['B'][sq] for sq in range(64) if test_bit(game_state.whiteBishops, sq)
        ) + sum(
            MG_PIECE_SQUARE_TABLES['R'][sq] for sq in range(64) if test_bit(game_state.whiteRooks, sq)
        ) + sum(
            MG_PIECE_SQUARE_TABLES['Q'][sq] for sq in range(64) if test_bit(game_state.whiteQueen, sq)
        ) + sum(
            MG_PIECE_SQUARE_TABLES['K'][sq] for sq in range(64) if test_bit(game_state.whiteKing, sq)
        )

        black_positional_score = sum(
            MG_PIECE_SQUARE_TABLES['P'][63 - sq] for sq in range(64) if test_bit(game_state.blackPawns, sq)
        ) + sum(
            MG_PIECE_SQUARE_TABLES['N'][63 - sq] for sq in range(64) if test_bit(game_state.blackKnights, sq)
        ) + sum(
            MG_PIECE_SQUARE_TABLES['B'][63 - sq] for sq in range(64) if test_bit(game_state.blackBishops, sq)
        ) + sum(
            MG_PIECE_SQUARE_TABLES['R'][63 - sq] for sq in range(64) if test_bit(game_state.blackRooks, sq)
        ) + sum(
            MG_PIECE_SQUARE_TABLES['Q'][63 - sq] for sq in range(64) if test_bit(game_state.blackQueen, sq)
        ) + sum(
            MG_PIECE_SQUARE_TABLES['K'][63 - sq] for sq in range(64) if test_bit(game_state.blackKing, sq)
        )

        white_score += white_positional_score
        black_score += black_positional_score

        return float(white_score - black_score)
