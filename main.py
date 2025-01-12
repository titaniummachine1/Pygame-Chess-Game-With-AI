import pygame
import sys

from chess.game import GameState
from chess.movegen import generate_all_moves
from chess.move import Move
from chess.bitboard import coords_to_square, square_to_coords, test_bit, clear_bit, set_bit
from chess.pieces import ALL_PIECES
from chess.ai.ai_player import AIPlayer

pygame.init()

WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS
FPS = 12

# Adjust window size to accommodate the mode selection buttons
WINDOW_HEIGHT = HEIGHT + 150
BOARD_OFFSET_Y = 100

WIN = pygame.display.set_mode((WIDTH, WINDOW_HEIGHT))
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
        try:
            img = pygame.image.load(path)
            IMAGES[piece] = pygame.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))
        except pygame.error as e:
            print(f"Unable to load image for piece '{piece}' from path '{path}': {e}")

def drawBoard(win):
    """
    Draw the 8x8 board in a burlywood color pattern.
    """
    colors = [pygame.Color("burlywood"), pygame.Color("burlywood4")]
    for row in range(ROWS):
        for col in range(COLS):
            color = colors[(row + col) % 2]
            rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE + BOARD_OFFSET_Y, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(win, color, rect)

def drawPieces(win, state: GameState):
    """
    Draw the pieces on the board according to the bitboards in 'state'.
    """
    def drawBitboard(bitboard, piece_code):
        for sq in range(64):
            if test_bit(bitboard, sq):
                r, c = square_to_coords(sq)
                pieceImg = IMAGES.get(piece_code)
                if pieceImg:
                    win.blit(pieceImg, (c * SQUARE_SIZE, r * SQUARE_SIZE + BOARD_OFFSET_Y))
                else:
                    # If image is missing, draw a placeholder
                    pygame.draw.circle(win, (255, 0, 0), (c * SQUARE_SIZE + SQUARE_SIZE // 2, r * SQUARE_SIZE + BOARD_OFFSET_Y + SQUARE_SIZE // 2), SQUARE_SIZE // 2)

    # White pieces
    drawBitboard(state.whitePawns,   'wP')
    drawBitboard(state.whiteKnights, 'wN')
    drawBitboard(state.whiteBishops, 'wB')
    drawBitboard(state.whiteRooks,   'wR')
    drawBitboard(state.whiteQueen,   'wQ')
    drawBitboard(state.whiteKing,    'wK')

    # Black pieces
    drawBitboard(state.blackPawns,   'bP')
    drawBitboard(state.blackKnights, 'bN')
    drawBitboard(state.blackBishops, 'bB')
    drawBitboard(state.blackRooks,   'bR')
    drawBitboard(state.blackQueen,   'bQ')
    drawBitboard(state.blackKing,    'bK')

def drawHighlights(win, selectedSquare, movesForSelected, mode):
    """
    Highlight the selected square and possible moves.
    """
    if mode != 'Setup' and selectedSquare is not None:
        srow, scol = selectedSquare
        highlightSurface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        highlightSurface.fill((255, 255, 0, 100))
        win.blit(highlightSurface, (scol * SQUARE_SIZE, srow * SQUARE_SIZE + BOARD_OFFSET_Y))

    if mode != 'Setup' and movesForSelected:
        for mv in movesForSelected:
            r, c = square_to_coords(mv.endSq)
            if mv.isCapture:
                # Draw a transparent ring for capture moves
                ringSurface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                pygame.draw.circle(ringSurface, (0, 0, 0, 50), (SQUARE_SIZE // 2, SQUARE_SIZE // 2), SQUARE_SIZE // 2, 10)
                win.blit(ringSurface, (c * SQUARE_SIZE, r * SQUARE_SIZE + BOARD_OFFSET_Y))
            else:
                # Draw a transparent black circle for normal moves
                circleSurface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                pygame.draw.circle(circleSurface, (0, 0, 0, 50), (SQUARE_SIZE // 2, SQUARE_SIZE // 2), SQUARE_SIZE // 6)
                win.blit(circleSurface, (c * SQUARE_SIZE, r * SQUARE_SIZE + BOARD_OFFSET_Y))

# Button dimensions and positions
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
BUTTON_Y = 10
AI_BUTTON_X = WIDTH // 2 - 1.5 * BUTTON_WIDTH - 10
MANUAL_BUTTON_X = AI_BUTTON_X + BUTTON_WIDTH + 10
SETUP_BUTTON_X = MANUAL_BUTTON_X + BUTTON_WIDTH + 10

# Colors
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER_COLOR = (100, 149, 237)
BUTTON_TEXT_COLOR = (255, 255, 255)

# Fonts
pygame.font.init()
FONT = pygame.font.SysFont('Arial', 24)

def draw_button(win, x, y, width, height, text, is_hovered):
    color = BUTTON_HOVER_COLOR if is_hovered else BUTTON_COLOR
    pygame.draw.rect(win, color, (x, y, width, height))
    text_surface = FONT.render(text, True, BUTTON_TEXT_COLOR)
    text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
    win.blit(text_surface, text_rect)

def draw_info(win, depth, evaluation, positions):
    """
    Draw the current depth of search, evaluation, and the number of analyzed positions.
    """
    info_text = f"Depth: {depth}  Eval: {evaluation:.2f}  Positions: {positions}"
    text_surface = FONT.render(info_text, True, BUTTON_TEXT_COLOR)
    text_rect = text_surface.get_rect(center=(WIDTH // 2, BUTTON_Y + BUTTON_HEIGHT + 20))
    win.blit(text_surface, text_rect)

def main():
    clock = pygame.time.Clock()
    loadImages()

    # Create and init GameState
    gameState = GameState()
    gameState.init_standard_position()

    # Initialize AI player
    ai_player = AIPlayer(gameState)

    # Selection variables for AI and Manual modes
    selectedSquare = None      # (row, col) for the piece the user selected
    movesForSelected = []      # possible moves from that square

    # Selection variables for Setup Mode
    selectedSquareSetup = None # (row, col) for the piece selected in Setup Mode
    selectedPieceSetup = None  # 'wP', 'bQ', etc.

    mode = 'AI'  # Modes: 'AI', 'Manual', 'Setup'

    # Variables to track AI search info
    current_depth = 0
    current_evaluation = 0.0
    analyzed_positions = 0

    run = True
    while run:
        clock.tick(FPS)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        ai_button_hovered = AI_BUTTON_X <= mouse_x <= AI_BUTTON_X + BUTTON_WIDTH and BUTTON_Y <= mouse_y <= BUTTON_Y + BUTTON_HEIGHT
        manual_button_hovered = MANUAL_BUTTON_X <= mouse_x <= MANUAL_BUTTON_X + BUTTON_WIDTH and BUTTON_Y <= mouse_y <= BUTTON_Y + BUTTON_HEIGHT
        setup_button_hovered = SETUP_BUTTON_X <= mouse_x <= SETUP_BUTTON_X + BUTTON_WIDTH and BUTTON_Y <= mouse_y <= BUTTON_Y + BUTTON_HEIGHT

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if ai_button_hovered:
                    mode = 'AI'
                    # Clear Setup Mode selections when switching modes
                    selectedSquareSetup = None
                    selectedPieceSetup = None
                elif manual_button_hovered:
                    mode = 'Manual'
                    # Clear Setup Mode selections when switching modes
                    selectedSquareSetup = None
                    selectedPieceSetup = None
                elif setup_button_hovered:
                    mode = 'Setup'
                    # Clear other mode selections when switching to Setup Mode
                    selectedSquare = None
                    movesForSelected = []
                else:
                    x, y = pygame.mouse.get_pos()
                    col = x // SQUARE_SIZE
                    row = (y - BOARD_OFFSET_Y) // SQUARE_SIZE  # Adjust for the dropdown height

                    if not (0 <= row < 8 and 0 <= col < 8):
                        continue  # Clicked outside the board

                    sq = coords_to_square(row, col)

                    if mode == 'Setup':
                        if event.button == 3:  # Right-click to remove piece
                            # Remove any piece (white or black) at the clicked square
                            gameState._remove_piece_at_square(sq, True)
                            gameState._remove_piece_at_square(sq, False)
                            # Clear selection if the removed piece was selected
                            if selectedSquareSetup == (row, col):
                                selectedSquareSetup = None
                                selectedPieceSetup = None
                        elif event.button == 1:  # Left-click to select or move piece
                            if selectedPieceSetup is None:
                                # Select a piece to move
                                piece_at_sq = None
                                for piece, bitboard in {
                                    'wP': gameState.whitePawns,
                                    'wN': gameState.whiteKnights,
                                    'wB': gameState.whiteBishops,
                                    'wR': gameState.whiteRooks,
                                    'wQ': gameState.whiteQueen,
                                    'wK': gameState.whiteKing,
                                    'bP': gameState.blackPawns,
                                    'bN': gameState.blackKnights,
                                    'bB': gameState.blackBishops,
                                    'bR': gameState.blackRooks,
                                    'bQ': gameState.blackQueen,
                                    'bK': gameState.blackKing,
                                }.items():
                                    if test_bit(bitboard, sq):
                                        piece_at_sq = piece
                                        break
                                if piece_at_sq:
                                    selectedSquareSetup = (row, col)
                                    selectedPieceSetup = piece_at_sq
                            else:
                                # Move the selected piece to the new square
                                # Remove any piece at the destination
                                gameState._remove_piece_at_square(sq, True)
                                gameState._remove_piece_at_square(sq, False)
                                # Move the piece
                                gameState._remove_piece_at_square(coords_to_square(*selectedSquareSetup), True)
                                gameState._remove_piece_at_square(coords_to_square(*selectedSquareSetup), False)
                                gameState._move_piece_on_board(selectedPieceSetup, sq, sq)
                                # Clear selection after moving
                                selectedSquareSetup = None
                                selectedPieceSetup = None
                    else:
                        if selectedSquare is None:
                            # Selecting a piece to move
                            allMoves = generate_all_moves(gameState)
                            movesForSelected = [m for m in allMoves if m.startSq == sq]
                            if movesForSelected:
                                selectedSquare = (row, col)
                        else:
                            # Attempting to move the selected piece to the new square
                            chosenMove = next((m for m in movesForSelected if m.endSq == sq), None)
                            if chosenMove:
                                # Make the move
                                gameState.make_move(chosenMove)
                                # AI makes a move if in AI mode
                                if mode == 'AI':
                                    ai_move = ai_player.select_move()
                                    if ai_move:
                                        gameState.make_move(ai_move)
                                        # Update AI search info
                                        current_depth = ai_player.depth
                                        current_evaluation = ai_player.current_evaluation
                                        analyzed_positions = ai_player.analyzed_positions
                                # Clear selections after move
                                selectedSquare = None
                                movesForSelected = []
                            else:
                                # Check if the clicked square has another piece of the same color
                                piece_color = 'w' if gameState.whiteToMove else 'b'
                                piece_at_sq = None
                                for piece, bitboard in {
                                    'wP': gameState.whitePawns,
                                    'wN': gameState.whiteKnights,
                                    'wB': gameState.whiteBishops,
                                    'wR': gameState.whiteRooks,
                                    'wQ': gameState.whiteQueen,
                                    'wK': gameState.whiteKing,
                                    'bP': gameState.blackPawns,
                                    'bN': gameState.blackKnights,
                                    'bB': gameState.blackBishops,
                                    'bR': gameState.blackRooks,
                                    'bQ': gameState.blackQueen,
                                    'bK': gameState.blackKing,
                                }.items():
                                    if piece.startswith(piece_color) and test_bit(bitboard, sq):
                                        piece_at_sq = piece
                                        break
                                if piece_at_sq:
                                    # Switch selection to the new piece
                                    selectedSquare = (row, col)
                                    allMoves = generate_all_moves(gameState)
                                    movesForSelected = [m for m in allMoves if m.startSq == sq]
                                else:
                                    # Clear the selection if no valid move or same-color piece is clicked
                                    selectedSquare = None
                                    movesForSelected = []

        # Draw the board + pieces
        drawBoard(WIN)
        drawPieces(WIN, gameState)
        drawHighlights(WIN, selectedSquare, movesForSelected, mode)

        # Draw mode buttons
        draw_button(WIN, AI_BUTTON_X, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT, 'AI Mode', ai_button_hovered)
        draw_button(WIN, MANUAL_BUTTON_X, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT, 'Manual Mode', manual_button_hovered)
        draw_button(WIN, SETUP_BUTTON_X, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT, 'Setup Mode', setup_button_hovered)

        # Draw AI search info
        draw_info(WIN, current_depth, current_evaluation, analyzed_positions)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
