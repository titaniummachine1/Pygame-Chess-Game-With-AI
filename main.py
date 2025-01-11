# main.py
import pygame
import sys

from chess.game import GameState
from chess.movegen import generate_all_moves
from chess.move import Move
from chess.bitboard import coords_to_square, square_to_coords, test_bit
from chess.pieces import ALL_PIECES
from chess.ai.ai_player import AIPlayer

pygame.init()

WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS
FPS = 24

WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Custom Chess Variant')

# Global dictionary for piece images
IMAGES = {}

def loadImages():
    """
    Load piece images from the 'images/' folder for each piece in ALL_PIECES.
    For example: 'images/wP.png', 'images/bK.png', etc.
    """
    for piece in ALL_PIECES:
        path = f"images/{piece}.png"
        img = pygame.image.load(path)
        IMAGES[piece] = pygame.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))

def drawBoard(win):
    """
    Draw the 8x8 board in a burlywood color pattern.
    """
    colors = [pygame.Color("burlywood"), pygame.Color("burlywood4")]
    for row in range(ROWS):
        for col in range(COLS):
            color = colors[(row + col) % 2]
            rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(win, color, rect)

def drawPieces(win, state: GameState):
    """
    Draw the pieces on the board according to the bitboards in 'state'.
    """
    def drawBitboard(bitboard, piece_code):
        for sq in range(64):
            if test_bit(bitboard, sq):
                r, c = square_to_coords(sq)
                pieceImg = IMAGES[piece_code]
                win.blit(pieceImg, (c * SQUARE_SIZE, r * SQUARE_SIZE))

    # White pieces
    drawBitboard(state.whitePawns,   'wP')
    drawBitboard(state.whiteKnights, 'wN')
    drawBitboard(state.whiteBishops, 'wB')
    drawBitboard(state.whiteRooks,   'wR')
    drawBitboard(state.whiteQueens,  'wQ')
    drawBitboard(state.whiteKing,    'wK')

    # Black pieces
    drawBitboard(state.blackPawns,   'bP')
    drawBitboard(state.blackKnights, 'bN')
    drawBitboard(state.blackBishops, 'bB')
    drawBitboard(state.blackRooks,   'bR')
    drawBitboard(state.blackQueens,  'bQ')
    drawBitboard(state.blackKing,    'bK')

def main():
    clock = pygame.time.Clock()
    loadImages()

    # Create and init GameState
    gameState = GameState()
    gameState.init_standard_position()

    # Initialize AI player
    ai_player = AIPlayer(gameState)

    selectedSquare = None      # (row, col) for the piece the user selected
    movesForSelected = []      # possible moves from that square

    run = True
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                col = x // SQUARE_SIZE
                row = y // SQUARE_SIZE
                sq = coords_to_square(row, col)

                if selectedSquare is None:
                    # We are picking the piece to move
                    allMoves = generate_all_moves(gameState)
                    # Filter moves that start from 'sq'
                    movesForSelected = [m for m in allMoves if m.startSq == sq]
                    if movesForSelected:
                        selectedSquare = (row, col)
                    else:
                        selectedSquare = None
                else:
                    # We have a piece selected => see if we can move to new sq
                    chosenMove = None
                    for m in movesForSelected:
                        if m.endSq == sq:
                            chosenMove = m
                            break
                    if chosenMove:
                        # Make the move
                        gameState.make_move(chosenMove)

                        # AI makes a move
                        ai_move = ai_player.select_move()
                        if ai_move:
                            gameState.make_move(ai_move)

                        # Clear the selection
                        selectedSquare = None
                        movesForSelected = []
                    else:
                        # Check if the new square selects another piece of the same color
                        piece_color = 'w' if gameState.whiteToMove else 'b'
                        piece_at_sq = None
                        piece_bitboards = {
                            'wP': gameState.whitePawns,
                            'wN': gameState.whiteKnights,
                            'wB': gameState.whiteBishops,
                            'wR': gameState.whiteRooks,
                            'wQ': gameState.whiteQueens,
                            'wK': gameState.whiteKing,
                            'bP': gameState.blackPawns,
                            'bN': gameState.blackKnights,
                            'bB': gameState.blackBishops,
                            'bR': gameState.blackRooks,
                            'bQ': gameState.blackQueens,
                            'bK': gameState.blackKing,
                        }
                        for piece, bitboard in piece_bitboards.items():
                            if piece.startswith(piece_color) and test_bit(bitboard, sq):
                                piece_at_sq = piece
                                break
                        if piece_at_sq:
                            # Switch selection to the new piece
                            allMoves = generate_all_moves(gameState)
                            movesForSelected = [m for m in allMoves if m.startSq == sq]
                            selectedSquare = (row, col)
                        else:
                            # Clear the selection
                            selectedSquare = None
                            movesForSelected = []

        # Draw the board + pieces
        drawBoard(WIN)
        drawPieces(WIN, gameState)

        # Highlight selected square & its possible moves
        if selectedSquare is not None:
            srow, scol = selectedSquare
            highlightSurface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlightSurface.fill((255, 255, 0, 100))
            WIN.blit(highlightSurface, (scol * SQUARE_SIZE, srow * SQUARE_SIZE))

            # highlight each valid move's end square
            for mv in movesForSelected:
                r, c = square_to_coords(mv.endSq)
                moveSurface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                moveSurface.fill((0, 255, 0, 100))
                WIN.blit(moveSurface, (c * SQUARE_SIZE, r * SQUARE_SIZE))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()