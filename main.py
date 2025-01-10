import pygame
import sys
import asyncio
import copy

from chess.game import GameState
from chess.movegen import generate_all_moves
from chess.move import Move
from chess.bitboard import coords_to_square, square_to_coords, test_bit
from chess.pieces import ALL_PIECES
from chess.AI.ChessEngine import ChessAI  # your async-based engine

pygame.init()

WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS
FPS = 30

WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Chess with AI Suggestions')

IMAGES = {}

def loadImages():
    """Load piece images into IMAGES{}."""
    for piece in ALL_PIECES:
        path = f"images/{piece}.png"
        img = pygame.image.load(path)
        IMAGES[piece] = pygame.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))

def drawBoard(win):
    """Draw an 8x8 board with two colors."""
    colors = [pygame.Color("burlywood"), pygame.Color("burlywood4")]
    for row in range(ROWS):
        for col in range(COLS):
            color = colors[(row + col) % 2]
            rect = pygame.Rect(col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(win, color, rect)

def drawPieces(win, state: GameState):
    """Draw all the pieces from bitboards."""
    def drawBitboard(bb, piece_code):
        for sq in range(64):
            if test_bit(bb, sq):
                r, c = square_to_coords(sq)
                img = IMAGES[piece_code]
                win.blit(img, (c*SQUARE_SIZE, r*SQUARE_SIZE))

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

async def main():
    clock = pygame.time.Clock()
    loadImages()

    # Create our real GameState used by the UI
    gameState = GameState()
    gameState.init_standard_position()

    # Create the AI object
    ai = ChessAI(max_depth=18, time_limit=30)

    # We'll keep a reference to the ongoing Task
    engine_task = None
    # And a place to store the bestMove from the engine
    bestMove = None

    selectedSquare = None
    movesForSelected = []

    running = True
    while running:
        dt = clock.tick(FPS)

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                col = x // SQUARE_SIZE
                row = y // SQUARE_SIZE
                sq = coords_to_square(row, col)

                if selectedSquare is None:
                    # We are picking the piece
                    all_moves = generate_all_moves(gameState)
                    movesForSelected = [m for m in all_moves if m.startSq == sq]
                    if movesForSelected:
                        selectedSquare = (row, col)
                    else:
                        selectedSquare = None
                else:
                    # We have a selected square -> see if we can make a move
                    chosenMove = None
                    for mv in movesForSelected:
                        if mv.endSq == sq:
                            chosenMove = mv
                            break

                    if chosenMove:
                        # Actually do the move in the real game
                        gameState.make_move(chosenMove)

                        # Now it's the other color's turn, so let's start a new AI search
                        # because we always want suggestions for the side to move.
                        if engine_task and not engine_task.done():
                            engine_task.cancel()

                        # Create a copy to avoid messing real board
                        copy_state = copy.deepcopy(gameState)
                        engine_task = asyncio.create_task(ai.find_best_move(copy_state))
                        bestMove = None
                    # Clear selection
                    selectedSquare = None
                    movesForSelected = []

        # Check if the AI task finished or is partially done
        if engine_task:
            if engine_task.done():
                # Done => get final best move
                try:
                    bestMove = engine_task.result()
                except asyncio.CancelledError:
                    bestMove = None
                engine_task = None
            else:
                # Not done => we can read partial best
                partial_best = ai.best_move_so_far
                if partial_best:
                    bestMove = partial_best

        # Draw
        drawBoard(WIN)
        drawPieces(WIN, gameState)

        # Highlight user selection
        if selectedSquare:
            srow, scol = selectedSquare
            highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight.fill((255, 255, 0, 100))
            WIN.blit(highlight, (scol*SQUARE_SIZE, srow*SQUARE_SIZE))

            for mv in movesForSelected:
                r, c = square_to_coords(mv.endSq)
                surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                surf.fill((0, 255, 0, 100))
                WIN.blit(surf, (c*SQUARE_SIZE, r*SQUARE_SIZE))

        # If we have a suggested best move, highlight it
        # (We do not auto-play it!)
        if bestMove:
            sr, sc = square_to_coords(bestMove.startSq)
            er, ec = square_to_coords(bestMove.endSq)
            suggestSurf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            suggestSurf.fill((0, 0, 255, 80))  # some translucent blue
            WIN.blit(suggestSurf, (sc*SQUARE_SIZE, sr*SQUARE_SIZE))
            WIN.blit(suggestSurf, (ec*SQUARE_SIZE, er*SQUARE_SIZE))

        pygame.display.flip()

        # yield to allow the AI search to proceed
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())