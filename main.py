import pygame
import sys
from chess.game import GameState
from chess.movegen import generate_all_moves
from chess.move import Move
from chess.bitboard import coords_to_square, square_to_coords, test_bit
from chess.pieces import ALL_PIECES
from chess.AI.ChessEngine import ChessAI  # the synchronous AI from above

pygame.init()

WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS
FPS = 24
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Custom Chess Variant')

IMAGES = {}

def loadImages():
    for piece in ALL_PIECES:
        path = f"images/{piece}.png"
        img = pygame.image.load(path)
        IMAGES[piece] = pygame.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))

def drawBoard(win):
    colors = [pygame.Color("burlywood"), pygame.Color("burlywood4")]
    for row in range(ROWS):
        for col in range(COLS):
            color = colors[(row + col) % 2]
            rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(win, color, rect)

def drawPieces(win, state: GameState):
    def drawBitboard(bitboard, piece_code):
        for sq in range(64):
            if test_bit(bitboard, sq):
                r, c = square_to_coords(sq)
                pieceImg = IMAGES[piece_code]
                win.blit(pieceImg, (c * SQUARE_SIZE, r * SQUARE_SIZE))

    # White
    drawBitboard(state.whitePawns,   'wP')
    drawBitboard(state.whiteKnights, 'wN')
    drawBitboard(state.whiteBishops, 'wB')
    drawBitboard(state.whiteRooks,   'wR')
    drawBitboard(state.whiteQueen,   'wQ')
    drawBitboard(state.whiteKing,    'wK')

    # Black
    drawBitboard(state.blackPawns,   'bP')
    drawBitboard(state.blackKnights, 'bN')
    drawBitboard(state.blackBishops, 'bB')
    drawBitboard(state.blackRooks,   'bR')
    drawBitboard(state.blackQueen,   'bQ')
    drawBitboard(state.blackKing,    'bK')

def main():
    clock = pygame.time.Clock()
    loadImages()

    gameState = GameState()
    gameState.init_standard_position()

    ai = ChessAI(depth=7, time_limit=10)  # synchronous AI
    selectedSquare = None
    movesForSelected = []
    bestMove = None

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
                    # Pick a piece
                    allMoves = generate_all_moves(gameState)
                    movesForSelected = [m for m in allMoves if m.startSq == sq]
                    if movesForSelected:
                        selectedSquare = (row, col)
                    else:
                        selectedSquare = None
                else:
                    # Attempt move
                    chosenMove = None
                    for m in movesForSelected:
                        if m.endSq == sq:
                            chosenMove = m
                            break
                    if chosenMove:
                        gameState.make_move(chosenMove)
                        # Calculate best move (blocking, synchronous)
                        bestMove = ai.find_best_move(gameState)

                    selectedSquare = None
                    movesForSelected = []

        # Draw
        drawBoard(WIN)
        drawPieces(WIN, gameState)

        # highlight selected square
        if selectedSquare is not None:
            srow, scol = selectedSquare
            highlightSurface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlightSurface.fill((255, 255, 0, 100))
            WIN.blit(highlightSurface, (scol * SQUARE_SIZE, srow * SQUARE_SIZE))

            # highlight possible moves
            for mv in movesForSelected:
                r, c = square_to_coords(mv.endSq)
                moveSurface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                moveSurface.fill((0, 255, 0, 100))
                WIN.blit(moveSurface, (c * SQUARE_SIZE, r * SQUARE_SIZE))

        # highlight best move squares
        if bestMove:
            start_row, start_col = square_to_coords(bestMove.startSq)
            end_row, end_col = square_to_coords(bestMove.endSq)
            highlightSurface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlightSurface.fill((0, 0, 255, 100))
            WIN.blit(highlightSurface, (start_col * SQUARE_SIZE, start_row * SQUARE_SIZE))
            WIN.blit(highlightSurface, (end_col * SQUARE_SIZE, end_row * SQUARE_SIZE))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
