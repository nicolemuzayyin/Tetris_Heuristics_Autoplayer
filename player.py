from board import Direction, Rotation, Action
from random import Random

class Player:
    def choose_action(self, board):
        raise NotImplementedError

class TetrisPlayerAI(Player):
    gameOverPenalty = float('inf') #higher score --> worse placement
    tetrisBonus = float('-inf') #lower score --> better placement
    criticalClearBonus = -1000 

    def __init__(self, seed=None):
        self.random = Random(seed)

        #heuristics ––––––––––––
        self.gapWeight = 39.8 
        self.heightWeight = 2.8
        self.lineWeight = -35.1 
        self.bumpWeight = 3.5
        # ––––––––––––––––––––––

    def choose_action(self, board):
        if board.falling is None:
            return None

        try:
            currentGaps = self.calculateGaps(board)
            heights = self.getColumnHeights(board)
            maxHeight = max(heights) if heights else 0
            
            
            # step 1 –––––––––––– determine whether bomb is used ––––––––––––
            if board.bombs_remaining > 0:
                shouldBomb = False
                targetColumn = None
                columnGaps = self.calculateGapsPerColumn(board)
                maxColumnGaps = max(columnGaps) if columnGaps else 0
                
                #bomb if height of board exceeds 63% 
                if maxHeight > (board.height * 0.63):
                    shouldBomb = True
                    targetColumn = heights.index(maxHeight)  # bomb the tallest column
                elif currentGaps > 16: #bomb if there are more than 16 gaps 
                    shouldBomb = True
                    #place bomb where there are the most gaps
                    columnGaps = self.calculateGapsPerColumn(board)
                    targetColumn = columnGaps.index(max(columnGaps))
                #if there is a dangerous column with various gaps
                elif maxColumnGaps >= 8 and maxHeight > board.height * 0.5:
                    shouldBomb = True
                    targetColumn = columnGaps.index(max(columnGaps))
                
                if shouldBomb and targetColumn is not None:
                    testBoard = board.clone()
                    testMoves = []
                    
                    #calculate how many steps to the target column
                    currentX = testBoard.falling.left
                    steps = targetColumn - currentX
                    
                    #move block by certain number of steps
                    if steps != 0:
                        self.moveBlock(testBoard, testMoves, steps)
                    
                    testMoves.append(Action.Bomb)
                    return testMoves[0]
            # ––––––––––––––––––––––
            
            # step 2 –––––––––––– find best block placement ––––––––––––
            bestPlacementScore = float('inf')
            bestPlacementMoves = []
            bestPlacementBoard = None
            
            for rotationCount in range(4):
                for x in range(board.width):
                    testBoard = board.clone()
                    testMoves = []
                    
                    if testBoard.falling is None:
                        continue
                    
                    numBlocks = len(testBoard.cells) + len(testBoard.falling.cells)

                    for _ in range(rotationCount):
                        testMoves.append(Rotation.Clockwise)
                        testBoard.rotate(Rotation.Clockwise)
                    
                    currentX = testBoard.falling.left
                    steps = x - currentX
                    
                    if steps != 0:
                        self.moveBlock(testBoard, testMoves, steps)
                    
                    testMoves.append(Direction.Drop) 
                    testBoard.move(Direction.Drop)
                    
                    completedLines = (numBlocks - len(testBoard.cells)) / testBoard.width
                    score = self.evaluateBoard(testBoard, int(completedLines)) 
                    
                    if score < bestPlacementScore:
                        bestPlacementScore = score
                        bestPlacementMoves = testMoves.copy()
                        bestPlacementBoard = testBoard
            # ––––––––––––––––––––––
            
            # step 3 –––––––––––– compare discard vs placement score ––––––––––––
            if bestPlacementMoves and board.discards_remaining > 0:
                addedGaps = self.calculateGaps(bestPlacementBoard) - currentGaps
                
                # consider board state when deciding to discard –– allows for AI to decide if it is best option to discard current block
                if addedGaps >= 1:
                    # check if lines are being cleared
                    testBoard = board.clone()
                    testBoard.move(Direction.Drop)
                    numBlocks = len(board.cells) + len(board.falling.cells)
                    completedLines = (numBlocks - len(testBoard.cells)) / board.width
                    
                    # only discard if block does not clear 2+ lines
                    if completedLines < 2:
                        if board.discards_remaining > 1:
                            return Action.Discard
                        # only use last discard if adding 2+ gaps on board is dangerous
                        elif addedGaps >= 2 or maxHeight > board.height * 0.55:
                            return Action.Discard
            # ––––––––––––––––––––––
            
            if bestPlacementMoves:
                return bestPlacementMoves[0]
            
            return None
        
        except Exception as e:
            print(f"[ERROR in choose_action] {e}")
            return Direction.Drop
    
    def evaluateBoard(self, board, completedLines):
        heights = self.getColumnHeights(board) # get height of each column
        bumpiness = self.calculateBumpiness(heights) # calculate height differences between adjacent columns
        maxHeight = max(heights) if heights else 0 # find tallest column
        
        # return worst score if board is full (game over)
        if maxHeight == board.height:
            return self.gameOverPenalty
        
        gaps = self.calculateGaps(board) # count empty cells below blocks
        almostCompletedLines = self.countAlmostCompleteLines(board) # count lines with width-1 blocks
        
        # return best score for tetris (4 lines cleared)
        if completedLines == 4:
            return self.tetrisBonus
        # return best score for critical clears when board is 65%+ full and 3 lines cleared
        if board.height * 0.65 < maxHeight and completedLines == 3:
            return self.criticalClearBonus
        # return best score for critical clears when board is 70%+ full and 2 lines cleared
        if board.height * 0.7 < maxHeight and completedLines == 2:
            return self.criticalClearBonus
        # return best score for critical clears when board is 75%+ full and 1 line cleared
        if board.height * 0.75 < maxHeight and completedLines == 1:
            return self.criticalClearBonus
        
        # return best score for 3 line clear when gaps exist and no discards left
        if gaps > 1 and completedLines == 3 and board.discards_remaining == 0:
            return self.criticalClearBonus
        # return best score for 2 line clear when gaps exist and no discards left
        if gaps > 2 and completedLines == 2 and board.discards_remaining == 0:
            return self.criticalClearBonus
        # return best score for 1 line clear when gaps exist and no discards left
        if gaps > 3 and completedLines == 1 and board.discards_remaining == 0:
            return self.criticalClearBonus
        
        # calculate weighted score based on board state
        if maxHeight < board.height * 0.6: # normal scoring when board is less than 60% full
            score = (gaps * self.gapWeight +
                     maxHeight * self.heightWeight +
                     almostCompletedLines * self.lineWeight +
                     bumpiness * self.bumpWeight)
        else: # aggressive scoring when board is 60%+ full (prioritize clearing lines)
            score = (gaps * self.gapWeight * 20 +
                     maxHeight * self.heightWeight * 20 +
                     completedLines * self.lineWeight * 100 +
                     bumpiness * self.bumpWeight)
        
        return score
    
    def moveBlock(self, board, moves, steps):
        direction = Direction.Left if steps < 0 else Direction.Right # determine direction based on sign
        moves.extend([direction] * abs(steps))
        for _ in range(abs(steps)): # execute each move on the board
            board.move(direction)
    
    def getColumnHeights(self, board):
        heights = [] # store height of each column
        for x in range(board.width): # iterate through each column
            # find first block from top, calculate height from bottom
            height = next((board.height - y for y in range(board.height) 
                          if (x, y) in board.cells), 0)
            heights.append(height)
        return heights
    
    def calculateBumpiness(self, heights):
        # sum absolute differences between adjacent column heights
        return sum(abs(heights[i] - heights[i+1]) for i in range(len(heights) - 1))
    
    def calculateGaps(self, board):
        gaps = 0 # total number of gaps
        for x in range(board.width): # check each column
            foundBlock = False # block flag
            for y in range(board.height):
                if (x, y) in board.cells:
                    foundBlock = True
                elif foundBlock: # empty cell below a block means it is a gap
                    gaps += 1
        return gaps
    
    def calculateGapsPerColumn(self, board):
        columnGaps = [] # store gaps for each column
        for x in range(board.width): 
            gaps = 0 # gaps in column
            foundBlock = False #block flag
            for y in range(board.height): 
                if (x, y) in board.cells: 
                    foundBlock = True
                elif foundBlock: 
                    gaps += 1
            columnGaps.append(gaps)
        return columnGaps

    def countCompleteLines(self, board):
        # count lines that are completely filled
        return self.countLinesWithBlocks(board, board.width)

    def countAlmostCompleteLines(self, board):
        # count lines that are one block away from being complete
        return self.countLinesWithBlocks(board, board.width - 1)

    def countLinesWithBlocks(self, board, threshold):
        count = 0 # number of lines meeting threshold
        for y in range(board.height): 
            blocksInRow = sum(1 for x in range(board.width) if (x, y) in board.cells)
            if blocksInRow == threshold: # row meets threshold
                count += 1
        return count


SelectedPlayer = TetrisPlayerAI
