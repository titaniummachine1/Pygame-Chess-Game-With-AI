class Drawback:
    def __init__(self, name, description, prune_moves_func):
        self.name = name
        self.description = description
        self.prune_moves_func = prune_moves_func

def no_knights(game_state, moves):
    """Prune moves that involve knights."""
    return [move for move in moves if 'N' not in move.piece]

def no_castling(game_state, moves):
    """Prune castling moves."""
    return [move for move in moves if not move.isCastle]

# Add more drawbacks as needed
DRAWBACKS = {
    'no_knights': Drawback('No Knights', 'You cannot move knights.', no_knights),
    'no_castling': Drawback('No Castling', 'You cannot castle.', no_castling),
    # Add more drawbacks here
}
