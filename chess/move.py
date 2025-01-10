class Move:
    def __init__(self, piece, startSq, endSq, isCapture=False, isCastle=False):
        self.piece = piece
        self.startSq = startSq
        self.endSq = endSq
        self.isCapture = isCapture
        self.isCastle = isCastle
