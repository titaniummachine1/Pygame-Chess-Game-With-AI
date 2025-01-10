class Move:
    def __init__(self, piece, startSq, endSq, isCapture=False, isCastle=False, captured_piece=None):
        self.piece = piece
        self.startSq = startSq
        self.endSq = endSq
        self.isCapture = isCapture
        self.isCastle = isCastle
        self.captured_piece = captured_piece

    def __str__(self):
        return f"{self.piece} from {self.startSq} to {self.endSq} {'capture' if self.isCapture else ''} {'castle' if self.isCastle else ''}"
