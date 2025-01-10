import pygame
import sys
import asyncio
import copy
import time

from chess.game import GameState
from chess.movegen import generate_all_moves
from chess.move import Move
from chess.bitboard import coords_to_square, square_to_coords, test_bit
from chess.pieces import ALL_PIECES
from chess.AI.ChessEngine import ChessAI

pygame.init()

# Constants
TOP_PANEL_HEIGHT = 60
BOARD_SIZE = 800   # The board is 800x800
WINDOW_WIDTH = BOARD_SIZE
WINDOW_HEIGHT = BOARD_SIZE + TOP_PANEL_HEIGHT
ROWS, COLS = 8, 8
SQUARE_SIZE = BOARD_SIZE // COLS
FPS = 30
DEPTH_Setting = 18
time_limit_Setting = 30

WIN = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Chess with AI Analysis Overlay")

IMAGES = {}

def loadImages():
    """Load piece images from 'images/' folder for each piece in ALL_PIECES."""
    for piece in ALL_PIECES:
        path = f"images/{piece}.png"
        img = pygame.image.load(path)
        IMAGES[piece] = pygame.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))

def drawTopPanel(win, ai):
    """
    Draw the top panel to show AI analysis info (e.g. depth, eval).
    We'll assume AI has .current_depth and .current_eval attributes.
    """
    pygame.draw.rect(win, pygame.Color("gray20"), (0, 0, WINDOW_WIDTH, TOP_PANEL_HEIGHT))

    font = pygame.font.SysFont(None, 32)  # default font, size 32

    # Depth
    depth_str = f"Depth: {ai.current_depth}" if hasattr(ai, "current_depth") else "Depth: -"

    # Evaluation in pawns
    if hasattr(ai, "current_eval"):
        # convert centipawns -> pawns
        # e.g., 123 => 1.23
        eval_in_pawns = ai.current_eval / 100.0
        eval_str = f"Eval: {eval_in_pawns:+.2f}"
    else:
        eval_str = "Eval: --"

    # Optionally, if you have a nodes_searched or something:
    # nodes_str = f"Nodes: {ai.nodes_searched}" if hasattr(ai, "nodes_searched") else ""

    text_str = f"{depth_str}  |  {eval_str}"
    text_surface = font.render(text_str, True, pygame.Color("white"))
    WIN.blit(text_surface, (10, 10))

def drawBoard(win):
    """Draw the board at y-offset = TOP_PANEL_HEIGHT."""
    colors = [pygame.Color("burlywood"), pygame.Color("burlywood4")]
    for row in range(ROWS):
        for col in range(COLS):
            color = colors[(row + col) % 2]
            rect = pygame.Rect(
                col * SQUARE_SIZE,
                TOP_PANEL_HEIGHT + row * SQUARE_SIZE,
                SQUARE_SIZE,
                SQUARE_SIZE
            )
            pygame.draw.rect(win, color, rect)

def drawPieces(win, state: GameState):
    """
    Draw the pieces on the bitboards, offset by TOP_PANEL_HEIGHT for each square’s y.
    """
    def drawBitboard(bb, piece_code):
        for sq in range(64):
            if test_bit(bb, sq):
                r, c = square_to_coords(sq)
                x = c * SQUARE_SIZE
                y = TOP_PANEL_HEIGHT + (r * SQUARE_SIZE)  # shift down
                win.blit(IMAGES[piece_code], (x, y))

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

    # Create and init GameState
    gameState = GameState()
    gameState.init_standard_position()

    # Create AI with chosen depth/time limit
    ai = ChessAI(max_depth=DEPTH_Setting, time_limit=time_limit_Setting)
    engine_task = None
    bestMove = None

    selectedSquare = None
    movesForSelected = []

    running = True
    while running:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Board coordinates are offset by TOP_PANEL_HEIGHT
                mouseX, mouseY = pygame.mouse.get_pos()
                # If user clicks in top panel, ignore
                if mouseY < TOP_PANEL_HEIGHT:
                    continue
                col = mouseX // SQUARE_SIZE
                row = (mouseY - TOP_PANEL_HEIGHT) // SQUARE_SIZE
                sq = coords_to_square(row, col)

                if selectedSquare is None:
                    # pick piece
                    all_moves = generate_all_moves(gameState)
                    movesForSelected = [m for m in all_moves if m.startSq == sq]
                    if movesForSelected:
                        selectedSquare = (row, col)
                    else:
                        selectedSquare = None
                else:
                    # potential destination
                    chosenMove = None
                    for mv in movesForSelected:
                        if mv.endSq == sq:
                            chosenMove = mv
                            break
                    if chosenMove:
                        # Make the user’s move
                        gameState.make_move(chosenMove)
                        bestMove = None

                        # If an engine task was running, cancel it
                        if engine_task and not engine_task.done():
                            engine_task.cancel()

                        # Start new engine task with a copy of the current state
                        copyState = copy.deepcopy(gameState)
                        engine_task = asyncio.create_task(ai.find_best_move(copyState))

                    selectedSquare = None
                    movesForSelected = []

        # Check engine status => partial results
        if engine_task:
            if engine_task.done():
                try:
                    bestMove = engine_task.result()
                except asyncio.CancelledError:
                    bestMove = None
                engine_task = None
            else:
                # partial best from iterative deepening
                bestMove = ai.best_move_so_far

        # ---------- DRAWING ----------
        # 1) top panel (AI info)
        drawTopPanel(WIN, ai)

        # 2) board
        drawBoard(WIN)
        drawPieces(WIN, gameState)

        # highlight selected square
        if selectedSquare:
            srow, scol = selectedSquare
            rect = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            rect.fill((255, 255, 0, 100))
            WIN.blit(rect, (scol*SQUARE_SIZE, TOP_PANEL_HEIGHT + srow*SQUARE_SIZE))

            # highlight possible moves
            for mv in movesForSelected:
                r, c = square_to_coords(mv.endSq)
                rSurf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                rSurf.fill((0,255,0,100))
                WIN.blit(rSurf, (c*SQUARE_SIZE, TOP_PANEL_HEIGHT + r*SQUARE_SIZE))

        # highlight AI's best suggestion
        if bestMove:
            sr, sc = square_to_coords(bestMove.startSq)
            er, ec = square_to_coords(bestMove.endSq)
            surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            surf.fill((0,0,255,80))
            # highlight start
            WIN.blit(surf, (sc*SQUARE_SIZE, TOP_PANEL_HEIGHT + sr*SQUARE_SIZE))
            # highlight end
            WIN.blit(surf, (ec*SQUARE_SIZE, TOP_PANEL_HEIGHT + er*SQUARE_SIZE))

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())
