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
    Supports capturing the king via en passant after castling.
    """

    def __init__(self, white_drawback=None, black_drawback=None):
        self._initialize_bitboards()
        self._initialize_flags()
        self._initialize_drawbacks(white_drawback, black_drawback)
        self.halfmove_clock = 0
        self.repetition_history = {}
        self.game_over = False  # Ensure game_over attribute is initialized

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
        self.pawnGhostSquares = 0  # For pawn en passant
        self.kingGhostSquares = 0  # For king en passant
        self.move_history = []

        self.whiteKingMoved    = False
        self.whiteRookAMoved   = False  # a1
        self.whiteRookHMoved   = False  # h1
        self.blackKingMoved    = False
        self.blackRookAMoved   = False  # a8
        self.blackRookHMoved   = False  # h8

        self.en_passant_target = None  # Square index for en passant
        self.game_over = False         # Flag to indicate if the game has ended

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
        self.game_over = False  # Reset game_over flag

        # White pawns on row=6
        for col in range(8):
            sq = coords_to_square(6, col)
            self.whitePawns = set_bit(self.whitePawns, sq)

        # White rooks, knights, bishops, queen, king on row=7
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

        # Black rooks, knights, bishops, queen, king on row=0
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
        if self.game_over:
            print("Game is already over. No more moves can be made.")
            return

        # 1. Save snapshot for undo
        old_pos = self._snapshot()
        self.move_history.append((move, old_pos))

        # 2. Clear own ghost squares at the start of the move
        self.kingGhostSquares = 0

        # 3. Check if the move.endSq is in opponent's ghost squares
        if test_bit(self.kingGhostSquares, move.endSq):
            # Capture the opponent's king
            if self.whiteToMove:
                self.blackKing = clear_bit(self.blackKing, move.endSq)
                print("White captures Black King via King En Passant!")
            else:
                self.whiteKing = clear_bit(self.whiteKing, move.endSq)
                print("Black captures White King via King En Passant!")
            # Set game over flag
            self.game_over = True
            # Toggle side to move (optional, since game is over)
            self.whiteToMove = not self.whiteToMove
            return  # Exit after capturing the king

        # 4. Handle captures
        if move.isCapture:
            if move.piece in ['wP','bP'] and move.endSq == self.en_passant_target:
                # En passant capture for pawns
                capture_sq = move.endSq + (8 if move.piece == 'wP' else -8)
                remove_piece_at_square(capture_sq, self._opposite_side(), self)
                print(f"En Passant Capture at square {capture_sq}.")
            elif test_bit(self.kingGhostSquares, move.endSq):
                # Capture via King En Passant
                remove_piece_at_square(move.endSq, self._opposite_side(), self)
                print(f"King captured at square {move.endSq} via King En Passant.")
            else:
                # Regular capture
                remove_piece_at_square(move.endSq, self._opposite_side(), self)
                print(f"Captured piece at square {move.endSq}.")

            # Reset halfmove clock after a capture
            self.halfmove_clock = 0
        else:
            # Increment halfmove clock if no capture or pawn move
            self.halfmove_clock += 1

        # 5. Move the piece
        move_piece_on_board(move.piece, move.startSq, move.endSq, self)
        print(f"Moved {move.piece} from {move.startSq} to {move.endSq}.")

        # 6. Update movement flags if necessary
        self._update_move_flags(move)

        # 7. Handle castling
        if move.isCastle:
            path = self._king_castle_path(move.startSq, move.endSq)
            # Set ghost squares for King En Passant
            for sq in path:
                self.kingGhostSquares = set_bit(self.kingGhostSquares, sq)
            self.kingGhostSquares = set_bit(self.kingGhostSquares, move.startSq)
            self.kingGhostSquares = set_bit(self.kingGhostSquares, move.endSq)
            self._move_rook_for_castle(move)
            print("Castling move handled.")

        # 8. Handle en passant target
        if move.piece in ['wP', 'bP'] and abs(move.startSq - move.endSq) == 16:
            direction = -8 if move.piece == 'wP' else 8
            self.en_passant_target = move.endSq + direction
            self.pawnGhostSquares = set_bit(self.pawnGhostSquares, self.en_passant_target)
            print(f"En Passant target set at square {self.en_passant_target}.")
        else:
            self.en_passant_target = None

        # 9. Toggle side to move
        self.whiteToMove = not self.whiteToMove
        print(f"Turn toggled. White to move: {self.whiteToMove}")

        # 10. Clear opponent's ghost squares if it's their turn now
        self.kingGhostSquares = 0

        # 11. Check if the king of the player opposite to the one who moved is missing
        if (not self.whiteToMove and self.whiteKing == 0) or (self.whiteToMove and self.blackKing == 0):
            self.game_over = True
            if not self.whiteToMove:
                print("Black wins! White king is missing.")
            else:
                print("White wins! Black king is missing.")
            return

        # 12. Update repetition history and check for draw conditions
        self._update_repetition_history()
        if self._is_threefold_repetition():
            print("Threefold repetition detected. Game is a draw.")
            self._end_game()

        # 13. Check for 50-move rule
        if self.halfmove_clock >= 50:
            print("50-move rule reached. Game is a draw.")
            self._end_game()

        # 14. Check for loss condition (no legal moves)
        if not self._has_legal_moves():
            print("Player loses due to no legal moves.")
            self._end_game()

    def unmake_move(self, move: Move):
        """Undo the last move."""
        if not self.move_history:
            print("No moves to unmake.")
            return
        lastMove, old_state = self.move_history.pop()
        if lastMove != move:
            print("The move to unmake does not match the last move made.")
            return
        self._restore_snapshot(old_state)
        print(f"Move {move} has been undone.")

    def prune_moves(self, moves):
        """Prune moves based on the current player's drawback."""
        if self.whiteToMove and self.white_drawback:
            pruned = self.white_drawback.prune_moves_func(self, moves)
            print(f"Pruned moves for White: {len(moves)} -> {len(pruned)}")
            return pruned
        elif not self.whiteToMove and self.black_drawback:
            pruned = self.black_drawback.prune_moves_func(self, moves)
            print(f"Pruned moves for Black: {len(moves)} -> {len(pruned)}")
            return pruned
        print("No pruning applied to moves.")
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
            self.whiteKingGhostSquares,
            self.blackKingGhostSquares,
            self.whiteKingMoved, self.whiteRookAMoved, self.whiteRookHMoved,
            self.blackKingMoved, self.blackRookAMoved, self.blackRookHMoved,
            self.en_passant_target,
            self.halfmove_clock,
            self.repetition_history.copy(),
            self.game_over  # Added game_over here
        )

    def _restore_snapshot(self, snap):
        """Restore the game state from a snapshot."""
        (
            self.whitePawns, self.whiteKnights, self.whiteBishops, self.whiteRooks,
            self.whiteQueen, self.whiteKing,
            self.blackPawns, self.blackKnights, self.blackBishops, self.blackRooks,
            self.blackQueen, self.blackKing,
            self.whiteToMove,
            self.pawnGhostSquares,
            self.whiteKingGhostSquares,
            self.blackKingGhostSquares,
            self.whiteKingMoved, self.whiteRookAMoved, self.whiteRookHMoved,
            self.blackKingMoved, self.blackRookAMoved, self.blackRookHMoved,
            self.en_passant_target,
            self.halfmove_clock,
            self.repetition_history,
            self.game_over  # Added game_over here
        ) = snap

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
            path.pop()  # Exclude the final square
        return path

    def _move_rook_for_castle(self, move: Move):
        """Move the rook when castling."""
        start_row, start_col = square_to_coords(move.startSq)
        end_row, end_col = square_to_coords(move.endSq)

        if move.piece == WHITE_KING:
            if (start_row, start_col) == (7, 4) and (end_row, end_col) == (7, 6):
                # Kingside castling for White: Move rook from h1 to f1
                oldSq = coords_to_square(7, 7)  # h1
                newSq = coords_to_square(7, 5)  # f1
                if test_bit(self.whiteRooks, oldSq):
                    self.whiteRooks = clear_bit(self.whiteRooks, oldSq)
                    self.whiteRooks = set_bit(self.whiteRooks, newSq)
                    print(f"White Rook moved from {oldSq} to {newSq}.")
                self.whiteRookHMoved = True
            elif (start_row, start_col) == (7, 4) and (end_row, end_col) == (7, 2):
                # Queenside castling for White: Move rook from a1 to d1
                oldSq = coords_to_square(7, 0)  # a1
                newSq = coords_to_square(7, 3)  # d1
                if test_bit(self.whiteRooks, oldSq):
                    self.whiteRooks = clear_bit(self.whiteRooks, oldSq)
                    self.whiteRooks = set_bit(self.whiteRooks, newSq)
                    print(f"White Rook moved from {oldSq} to {newSq}.")
                self.whiteRookAMoved = True

        elif move.piece == BLACK_KING:
            if (start_row, start_col) == (0, 4) and (end_row, end_col) == (0, 6):
                # Kingside castling for Black: Move rook from h8 to f8
                oldSq = coords_to_square(0, 7)  # h8
                newSq = coords_to_square(0, 5)  # f8
                if test_bit(self.blackRooks, oldSq):
                    self.blackRooks = clear_bit(self.blackRooks, oldSq)
                    self.blackRooks = set_bit(self.blackRooks, newSq)
                    print(f"Black Rook moved from {oldSq} to {newSq}.")
                self.blackRookHMoved = True
            elif (start_row, start_col) == (0, 4) and (end_row, end_col) == (0, 2):
                # Queenside castling for Black: Move rook from a8 to d8
                oldSq = coords_to_square(0, 0)  # a8
                newSq = coords_to_square(0, 3)  # d8
                if test_bit(self.blackRooks, oldSq):
                    self.blackRooks = clear_bit(self.blackRooks, oldSq)
                    self.blackRooks = set_bit(self.blackRooks, newSq)
                    print(f"Black Rook moved from {oldSq} to {newSq}.")
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
        return len(all_moves) > 0

    def _end_game(self):
        """End the game."""
        self.game_over = True
        if not self.whiteToMove:
            print("White wins!")
        else:
            print("Black wins!")
        # Implement additional game over logic here (e.g., display message, reset game, etc.)

def path_bitboard(path: list) -> int:
    """Convert a list of squares into a bitboard."""
    bitboard = 0
    for square in path:
        bitboard = set_bit(bitboard, square)
    return bitboard
