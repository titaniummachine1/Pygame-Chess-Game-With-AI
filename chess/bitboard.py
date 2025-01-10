# chess/bitboard.py
# Common bitboard utilities.

def set_bit(bitboard: int, sq: int) -> int:
    """Set the bit at 'sq' to 1."""
    return bitboard | (1 << sq)

def clear_bit(bitboard: int, sq: int) -> int:
    """Set the bit at 'sq' to 0."""
    return bitboard & ~(1 << sq)

def test_bit(bitboard: int, sq: int) -> bool:
    """Check if bit at 'sq' is 1."""
    return (bitboard & (1 << sq)) != 0

def coords_to_square(row: int, col: int) -> int:
    """
    Convert (row, col) to [0..63], with row=0..7 top to bottom,
    col=0..7 left to right.
    """
    return row * 8 + col

def square_to_coords(sq: int) -> tuple[int, int]:
    """
    Convert [0..63] -> (row, col).
    row = sq // 8, col = sq % 8
    """
    return (sq // 8, sq % 8)

def in_bounds(row: int, col: int) -> bool:
    """Check if 0 <= row,col < 8."""
    return 0 <= row < 8 and 0 <= col < 8