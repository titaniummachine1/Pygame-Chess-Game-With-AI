# game_state.py

from .bitboard import (
    test_bit, set_bit, clear_bit, coords_to_square, square_to_coords, in_bounds
)
from .pieces import *
from .move import Move
from .drawbacks import DRAWBACKS
from .helpers.bitboard_helpers import move_piece_on_board, remove_piece_at_square
from .movegen import generate_all_moves
from .helpers.check_detection import is_square_attacked, get_attackers

class GameState:
    """
    Holds piece bitboards, manages moves, castling, en passant, etc.
    """

    def __init__(self, white_drawback=None, black_drawback=None):
        self._initialize_bitboards()
        self._initialize_flags()
        self._initialize_drawbacks(white_drawback, black_drawback)
        self.halfmove_clock = 0
        self.repetition_history = {}

    def _initialize_bitboards(self):
        """Initialize piece bitboards."""
        self.whitePawns   = 0
        self.whiteKnights = 0
        self.whiteBishops = 0
        self.whiteRooks   = 0
        self.whiteQueen   = 0
        self.whiteKing    = 0

        self.blackPawns   = 0
        self.blackKnights = 0
        self.blackBishops = 0
        self.blackRooks   = 0
        self.blackQueen   = 0
        self.blackKing    = 0

    def _initialize_flags(self):
        """Initialize flags and other state variables."""
        self.whiteToMove = True
        self.pawnGhostSquares = 0
        self.kingGhostSquares = 0
        self.move_history = []

        self.whiteKingMoved    = False
        self.whiteRookAMoved   = False
        self.whiteRookHMoved   = False
        self.blackKingMoved    = False
        self.blackRookAMoved   = False
        self.blackRookHMoved   = False

        self.en_passant_target = None

    def _initialize_drawbacks(self, white_drawback, black_drawback):
        """Initialize drawbacks for both players."""
        self.white_drawback = DRAWBACKS.get(white_drawback)
        self.black_drawback = DRAWBACKS.get(black_drawback)

    def init_standard_position(self):
        """Set up the board with the standard chess starting position."""
        self._initialize_bitboards()
        self._initialize_flags()
        self.halfmove_clock = 0
        self.repetition_history = {}

        # White pawns on row=6
        for col in range(8):
            sq = coords_to_square(6, col)
            self.whitePawns = set_bit(self.whitePawns, sq)

        # White rooks etc. on row=7
        self.whiteRooks = set_bit(self.whiteRooks, coords_to_square(7, 0))
        self.whiteRooks = set_bit(self.whiteRooks, coords_to_square(7, 7))
        self.whiteKnights = set_bit(self.whiteKnights, coords_to_square(7, 1))
        self.whiteKnights = set_bit(self.whiteKnights, coords_to_square(7, 6))
        self.whiteBishops = set_bit(self.whiteBishops, coords_to_square(7, 2))
        self.whiteBishops = set_bit(self.whiteBishops, coords_to_square(7, 5))
        self.whiteQueen = set_bit(self.whiteQueen, coords_to_square(7, 3))
        self.whiteKing = set_bit(self.whiteKing, coords_to_square(7, 4))

        # Black pawns on row=1
        for col in range(8):
            sq = coords_to_square(1, col)
            self.blackPawns = set_bit(self.blackPawns, sq)

        # Black rooks etc. on row=0
        self.blackRooks = set_bit(self.blackRooks, coords_to_square(0, 0))
        self.blackRooks = set_bit(self.blackRooks, coords_to_square(0, 7))
        self.blackKnights = set_bit(self.blackKnights, coords_to_square(0, 1))
        self.blackKnights = set_bit(self.blackKnights, coords_to_square(0, 6))
        self.blackBishops = set_bit(self.blackBishops, coords_to_square(0, 2))
        self.blackBishops = set_bit(self.blackBishops, coords_to_square(0, 5))
        self.blackQueen = set_bit(self.blackQueen, coords_to_square(0, 3))
        self.blackKing = set_bit(self.blackKing, coords_to_square(0, 4))

    def get_white_occupancy(self) -> int:
        """Return bitboard of all white pieces."""
        return (self.whitePawns | self.whiteKnights | self.whiteBishops |
                self.whiteRooks | self.whiteQueen | self.whiteKing)

    def get_black_occupancy(self) -> int:
        """Return bitboard of all black pieces."""
        return (self.blackPawns | self.blackKnights | self.blackBishops |
                self.blackRooks | self.blackQueen | self.blackKing)

    def get_occupancy(self) -> int:
        """Return bitboard of all pieces."""
        return self.get_white_occupancy() | self.get_black_occupancy()

    def make_move(self, move: Move):
        """Make a move on the board."""
        old_pos = self._snapshot()
        self.move_history.append((move, old_pos))

        if self.whiteToMove:
            self.pawnGhostSquares = 0
            self.kingGhostSquares = 0

        if move.isCapture or move.piece in ['wP', 'bP']:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        if move.isCapture:
            if move.piece in ['wP','bP'] and move.endSq == self.en_passant_target:
                capture_sq = move.endSq + (8 if move.piece == 'wP' else -8)
                remove_piece_at_square(capture_sq, self._opposite_side(), self)
            elif test_bit(self.kingGhostSquares, move.endSq):
                remove_piece_at_square(move.endSq, self._opposite_side(), self)
            else:
                remove_piece_at_square(move.endSq, self._opposite_side(), self)

        move_piece_on_board(move.piece, move.startSq, move.endSq, self)
        self._update_move_flags(move)

        if move.isCastle:
            path = self._king_castle_path(move.startSq, move.endSq)
            for sq in path:
                self.kingGhostSquares = set_bit(self.kingGhostSquares, sq)
            self.kingGhostSquares = set_bit(self.kingGhostSquares, move.startSq)
            self._move_rook_for_castle(move)

        if move.piece in ['wP','bP'] and abs(move.startSq - move.endSq) == 16:
            direction = -8 if move.piece == 'wP' else 8
            self.en_passant_target = move.endSq + direction
            self.pawnGhostSquares = set_bit(self.pawnGhostSquares, self.en_passant_target)
        else:
            self.en_passant_target = None

        self.whiteToMove = not self.whiteToMove

        if not self.whiteToMove:
            self.pawnGhostSquares = 0
            self.kingGhostSquares = 0

        # Check for threefold repetition
        self._update_repetition_history()
        if self._is_threefold_repetition():
            print("Threefold repetition detected. Game is a draw.")
            self._end_game()

        # Check for 50-move rule
        if self.halfmove_clock >= 50:
            print("50-move rule reached. Game is a draw.")
            self._end_game()

        # Check for win condition
        if not self._has_legal_moves():
            print("Player loses due to no legal moves.")
            self._end_game()

    def unmake_move(self, move: Move):
        """Undo the last move."""
        if not self.move_history:
            return
        lastMove, old_state = self.move_history.pop()
        if lastMove != move:
            return
        self._restore_snapshot(old_state)

    def prune_moves(self, moves):
        """Prune moves based on the current player's drawback."""
        if self.whiteToMove and self.white_drawback:
            return self.white_drawback.prune_moves_func(self, moves)
        elif not self.whiteToMove and self.black_drawback:
            return self.black_drawback.prune_moves_func(self, moves)
        return moves

    def _snapshot(self):
        """Take a snapshot of the current game state."""
        return (
            self.whitePawns, self.whiteKnights, self.whiteBishops, self.whiteRooks,
            self.whiteQueen, self.whiteKing,
            self.blackPawns, self.blackKnights, self.blackBishops, self.blackRooks,
            self.blackQueen, self.blackKing,
            self.whiteToMove,
            self.pawnGhostSquares,
            self.kingGhostSquares,
            list(self.kingGhostSquares),
            self.whiteKingMoved, self.whiteRookAMoved, self.whiteRookHMoved,
            self.blackKingMoved, self.blackRookAMoved, self.blackRookHMoved,
            self.en_passant_target,
            self.halfmove_clock,
            self.repetition_history.copy()
        )

    def _restore_snapshot(self, snap):
        """Restore the game state from a snapshot."""
        ( self.whitePawns, self.whiteKnights, self.whiteBishops, self.whiteRooks,
          self.whiteQueen, self.whiteKing,
          self.blackPawns, self.blackKnights, self.blackBishops, self.blackRooks,
          self.blackQueen, self.blackKing,
          self.whiteToMove,
          self.pawnGhostSquares,
          self.kingGhostSquares,
          king_ghost_list,
          self.whiteKingMoved, self.whiteRookAMoved, self.whiteRookHMoved,
          self.blackKingMoved, self.blackRookAMoved, self.blackRookHMoved,
          self.en_passant_target,
          self.halfmove_clock,
          self.repetition_history
        ) = snap

        self.kingGhostSquares = king_ghost_list

    def _opposite_side(self) -> bool:
        """Return the opposite side to move."""
        return not self.whiteToMove

    def _king_castle_path(self, startSq: int, endSq: int) -> list:
        """Return the path of squares the king moves through when castling."""
        path = []
        step = 1 if endSq > startSq else -1
        current = startSq
        while current != endSq:
            path.append(current)
            current += step
        if path:
            path.pop()
        return path

    def _move_rook_for_castle(self, move: Move):
        """Move the rook when castling."""
        start_row, start_col = square_to_coords(move.startSq)
        end_row, end_col = square_to_coords(move.endSq)

        if move.piece == WHITE_KING:
            if (start_row, start_col) == (7, 4) and (end_row, end_col) == (7, 6):
                oldSq = coords_to_square(7, 7)  # h1
                newSq = coords_to_square(7, 5)  # f1
                if test_bit(self.whiteRooks, oldSq):
                    self.whiteRooks = clear_bit(self.whiteRooks, oldSq)
                    self.whiteRooks = set_bit(self.whiteRooks, newSq)
                self.whiteRookHMoved = True
            elif (start_row, start_col) == (7, 4) and (end_row, end_col) == (7, 2):
                oldSq = coords_to_square(7, 0)  # a1
                newSq = coords_to_square(7, 3)  # d1
                if test_bit(self.whiteRooks, oldSq):
                    self.whiteRooks = clear_bit(self.whiteRooks, oldSq)
                    self.whiteRooks = set_bit(self.whiteRooks, newSq)
                self.whiteRookAMoved = True

        elif move.piece == BLACK_KING:
            if (start_row, start_col) == (0, 4) and (end_row, end_col) == (0, 6):
                oldSq = coords_to_square(0, 7)  # h8
                newSq = coords_to_square(0, 5)  # f8
                if test_bit(self.blackRooks, oldSq):
                    self.blackRooks = clear_bit(self.blackRooks, oldSq)
                    self.blackRooks = set_bit(self.blackRooks, newSq)
                self.blackRookHMoved = True
            elif (start_row, start_col) == (0, 4) and (end_row, end_col) == (0, 2):
                oldSq = coords_to_square(0, 0)  # a8
                newSq = coords_to_square(0, 3)  # d8
                if test_bit(self.blackRooks, oldSq):
                    self.blackRooks = clear_bit(self.blackRooks, oldSq)
                    self.blackRooks = set_bit(self.blackRooks, newSq)
                self.blackRookAMoved = True

    def _update_move_flags(self, move: Move):
        """Update flags based on the move made."""
        piece = move.piece
        if piece == WHITE_KING:
            self.whiteKingMoved = True
        elif piece == BLACK_KING:
            self.blackKingMoved = True
        elif piece == WHITE_ROOK:
            if move.startSq == coords_to_square(7, 0):
                self.whiteRookAMoved = True
            elif move.startSq == coords_to_square(7, 7):
                self.whiteRookHMoved = True
        elif piece == BLACK_ROOK:
            if move.startSq == coords_to_square(0, 0):
                self.blackRookAMoved = True
            elif move.startSq == coords_to_square(0, 7):
                self.blackRookHMoved = True

    def _update_repetition_history(self):
        """Update the repetition history for threefold repetition detection."""
        board_state = (
            self.whitePawns, self.whiteKnights, self.whiteBishops, self.whiteRooks,
            self.whiteQueen, self.whiteKing,
            self.blackPawns, self.blackKnights, self.blackBishops, self.blackRooks,
            self.blackQueen, self.blackKing,
            self.whiteToMove
        )
        if board_state in self.repetition_history:
            self.repetition_history[board_state] += 1
        else:
            self.repetition_history[board_state] = 1

    def _is_threefold_repetition(self) -> bool:
        """Check if the current board state has occurred three times."""
        board_state = (
            self.whitePawns, self.whiteKnights, self.whiteBishops, self.whiteRooks,
            self.whiteQueen, self.whiteKing,
            self.blackPawns, self.blackKnights, self.blackBishops, self.blackRooks,
            self.blackQueen, self.blackKing,
            self.whiteToMove
        )
        return self.repetition_history.get(board_state, 0) >= 3

    def _has_legal_moves(self) -> bool:
        """Check if the current player has any legal moves."""
        all_moves = generate_all_moves(self)
        for move in all_moves:
            self.make_move(move)
            if not self._is_in_check():
                self.unmake_move(move)
                return True
            self.unmake_move(move)
        return False

    def _is_in_check(self) -> bool:
        """Check if the current player's king is in check."""
        king_sq = self._get_king_square(self.whiteToMove)
        return is_square_attacked(king_sq, not self.whiteToMove, self)

    def _get_king_square(self, white: bool) -> int:
        """Get the square of the king for the specified side."""
        king_bitboard = self.whiteKing if white else self.blackKing
        for sq in range(64):
            if test_bit(king_bitboard, sq):
                return sq
        return -1

    def _end_game(self):
        """End the game."""
        print("Game over.")
        # Implement game over logic here (e.g., display message, reset game, etc.)