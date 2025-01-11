# game_state.py

from .bitboard import (
    test_bit, set_bit, clear_bit, coords_to_square, square_to_coords
)
from .pieces import *
from .move import Move
from .drawbacks import DRAWBACKS

class GameState:
    """
    Holds piece bitboards, manages moves, castling, en passant, etc.
    """

    def __init__(self, white_drawback=None, black_drawback=None):
        # Piece bitboards
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

        # White to move = True, else Black
        self.whiteToMove = True

        # Ghost squares for en passant and castling
        self.pawnGhostSquares = 0
        self.kingGhostSquares = 0

        # Move history for undo
        self.move_history = []

        # Flags for castling
        self.whiteKingMoved    = False
        self.whiteRookAMoved   = False
        self.whiteRookHMoved   = False
        self.blackKingMoved    = False
        self.blackRookAMoved   = False
        self.blackRookHMoved   = False

        # Drawbacks
        self.white_drawback = DRAWBACKS.get(white_drawback)
        self.black_drawback = DRAWBACKS.get(black_drawback)

        # En passant target square (None if no en passant)
        self.en_passant_target = None

    def init_standard_position(self):
        # Clears all and sets standard chess start
        self.whitePawns = self.whiteKnights = self.whiteBishops = 0
        self.whiteRooks = self.whiteQueen = self.whiteKing = 0
        self.blackPawns = self.blackKnights = self.blackBishops = 0
        self.blackRooks = self.blackQueen = self.blackKing = 0

        self.whiteToMove = True
        self.pawnGhostSquares = 0
        self.kingGhostSquares = 0
        self.move_history.clear()

        self.whiteKingMoved   = False
        self.whiteRookAMoved  = False
        self.whiteRookHMoved  = False
        self.blackKingMoved   = False
        self.blackRookAMoved  = False
        self.blackRookHMoved  = False

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
        return (self.whitePawns | self.whiteKnights | self.whiteBishops |
                self.whiteRooks | self.whiteQueen | self.whiteKing)

    def get_black_occupancy(self) -> int:
        return (self.blackPawns | self.blackKnights | self.blackBishops |
                self.blackRooks | self.blackQueen | self.blackKing)

    def get_occupancy(self) -> int:
        return self.get_white_occupancy() | self.get_black_occupancy()

    def make_move(self, move: Move):
        # Save old snapshot for undo
        old_pos = self._snapshot()
        self.move_history.append((move, old_pos))

        # Clear ghost squares at the start of the turn
        self.pawnGhostSquares = 0
        self.kingGhostSquares = 0

        # If capture => remove the piece from 'endSq' or do en passant removal
        if move.isCapture:
            if move.piece in ['wP','bP'] and move.endSq == self.en_passant_target:
                # en passant capture
                capture_sq = move.endSq + (8 if move.piece == 'wP' else -8)
                self._remove_piece_at_square(capture_sq, self._opposite_side())
            else:
                # normal capture
                self._remove_piece_at_square(move.endSq, self._opposite_side())

        # Actually move the piece
        self._move_piece_on_board(move.piece, move.startSq, move.endSq)
        self._update_move_flags(move)

        # Handle castling => record ghost squares + move the rook
        if move.isCastle:
            path = self._king_castle_path(move.startSq, move.endSq)
            for sq in path:
                self.kingGhostSquares = set_bit(self.kingGhostSquares, sq)
            self._move_rook_for_castle(move)

        # If a pawn moved 2 squares, set en_passant_target behind it
        if move.piece in ['wP','bP'] and abs(move.startSq - move.endSq) == 16:
            direction = -8 if move.piece == 'wP' else 8
            self.en_passant_target = move.endSq + direction
            self.pawnGhostSquares = set_bit(self.pawnGhostSquares, self.en_passant_target)
        else:
            self.en_passant_target = None

        # Switch side
        self.whiteToMove = not self.whiteToMove

    def unmake_move(self, move: Move):
        if not self.move_history:
            return
        lastMove, old_state = self.move_history.pop()
        if lastMove != move:
            return
        self._restore_snapshot(old_state)

    def _snapshot(self):
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
            self.en_passant_target
        )

    def _restore_snapshot(self, snap):
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
          self.en_passant_target
        ) = snap

        self.kingGhostSquares = king_ghost_list

    def _opposite_side(self) -> bool:
        return not self.whiteToMove

    def _remove_piece_at_square(self, sq: int, side_is_white: bool):
        # remove whichever piece is at sq for that side
        if side_is_white:
            if test_bit(self.whitePawns, sq):
                self.whitePawns = clear_bit(self.whitePawns, sq)
            elif test_bit(self.whiteKnights, sq):
                self.whiteKnights = clear_bit(self.whiteKnights, sq)
            elif test_bit(self.whiteBishops, sq):
                self.whiteBishops = clear_bit(self.whiteBishops, sq)
            elif test_bit(self.whiteRooks, sq):
                self.whiteRooks = clear_bit(self.whiteRooks, sq)
            elif test_bit(self.whiteQueen, sq):
                self.whiteQueen = clear_bit(self.whiteQueen, sq)
            elif test_bit(self.whiteKing, sq):
                self.whiteKing = clear_bit(self.whiteKing, sq)
        else:
            if test_bit(self.blackPawns, sq):
                self.blackPawns = clear_bit(self.blackPawns, sq)
            elif test_bit(self.blackKnights, sq):
                self.blackKnights = clear_bit(self.blackKnights, sq)
            elif test_bit(self.blackBishops, sq):
                self.blackBishops = clear_bit(self.blackBishops, sq)
            elif test_bit(self.blackRooks, sq):
                self.blackRooks = clear_bit(self.blackRooks, sq)
            elif test_bit(self.blackQueen, sq):
                self.blackQueen = clear_bit(self.blackQueen, sq)
            elif test_bit(self.blackKing, sq):
                self.blackKing = clear_bit(self.blackKing, sq)

    def _move_piece_on_board(self, piece: str, startSq: int, endSq: int):
        # Clear bit at startSq, set bit at endSq
        if piece == WHITE_PAWN:
            self.whitePawns = clear_bit(self.whitePawns, startSq)
            self.whitePawns = set_bit(self.whitePawns, endSq)
        elif piece == WHITE_KNIGHT:
            self.whiteKnights = clear_bit(self.whiteKnights, startSq)
            self.whiteKnights = set_bit(self.whiteKnights, endSq)
        elif piece == WHITE_BISHOP:
            self.whiteBishops = clear_bit(self.whiteBishops, startSq)
            self.whiteBishops = set_bit(self.whiteBishops, endSq)
        elif piece == WHITE_ROOK:
            self.whiteRooks = clear_bit(self.whiteRooks, startSq)
            self.whiteRooks = set_bit(self.whiteRooks, endSq)
        elif piece == WHITE_QUEEN:
            self.whiteQueen = clear_bit(self.whiteQueen, startSq)
            self.whiteQueen = set_bit(self.whiteQueen, endSq)
        elif piece == WHITE_KING:
            self.whiteKing = clear_bit(self.whiteKing, startSq)
            self.whiteKing = set_bit(self.whiteKing, endSq)
        elif piece == BLACK_PAWN:
            self.blackPawns = clear_bit(self.blackPawns, startSq)
            self.blackPawns = set_bit(self.blackPawns, endSq)
        elif piece == BLACK_KNIGHT:
            self.blackKnights = clear_bit(self.blackKnights, startSq)
            self.blackKnights = set_bit(self.blackKnights, endSq)
        elif piece == BLACK_BISHOP:
            self.blackBishops = clear_bit(self.blackBishops, startSq)
            self.blackBishops = set_bit(self.blackBishops, endSq)
        elif piece == BLACK_ROOK:
            self.blackRooks = clear_bit(self.blackRooks, startSq)
            self.blackRooks = set_bit(self.blackRooks, endSq)
        elif piece == BLACK_QUEEN:
            self.blackQueen = clear_bit(self.blackQueen, startSq)
            self.blackQueen = set_bit(self.blackQueen, endSq)
        elif piece == BLACK_KING:
            self.blackKing = clear_bit(self.blackKing, startSq)
            self.blackKing = set_bit(self.blackKing, endSq)

    def _king_castle_path(self, startSq: int, endSq: int) -> list:
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

    def prune_moves(self, moves):
        """
        Prune moves based on the current player's drawback.
        """
        if self.whiteToMove and self.white_drawback:
            return self.white_drawback.prune_moves_func(self, moves)
        elif not self.whiteToMove and self.black_drawback:
            return self.black_drawback.prune_moves_func(self, moves)
        return moves
