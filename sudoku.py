import copy, sys, pdb

'''
How we're going to do this...
The puzzle class already works as everything except the golden thread thing,
so the plan is to create an Application frame, which handles input and
output, and a button that causes it to digest all of the values input in
the grid, then solve, somehow, then output the result into the same grid.

Construction steps
------------------
 - Create application frame
 -

Final run configuration
-----------------------
 - open with grid
 - input values manually
 - why aren't I doing this with angular or vue and adding it to my site?

'''

# checks whether a set of numbers contains any repeats
def anyRepeats(a):
	found = {}
	for n in a:
		if n in found:
			return True
		found[n] = True
	return False

# class that holds coordinates and a value
class Move:
	def __init__(self, row, col, val):
		self.row = row
		self.col = col
		self.val = val
	def __str__(self):
		return '{} at [{}, {}]'.format(self.val, self.row, self.col)

class OptionList:
	def __init__(self, row, col, val_list):
		self.row = row
		self.col = col
		self.val_list = copy.deepcopy(val_list)

	def __str__(self):
		return '{} are options at [{}, {}]'.format(str(self.val_list), self.row, self.col)

	def howMany(self):
		return len(self.val_list)

# class to handle the logic of a puzzle
class Puzzle:
	# <tried> is a set of already-tried hashes
	def __init__(self, str_rep, tried=None):
		if tried:
			self.tried = tried
		else:
			self.tried = []
		self.steps = []
		self.recur_depth = 0	# recursion level
		self.rows = []
		chars = str_rep.split(' ')
		for row_ind in range(9):
			cur_row = []
			for col_ind in range(9):
				char = chars[row_ind*9 + col_ind]
				if(char == '*'):
					val = 0
				else:
					val = int(char)
				cur_row.append(val)
			self.rows.append(cur_row)
	
	def __str__(self):
		to_ret = ''
		for r in range(len(self.rows)):
			for c in range(len(self.rows[r])):
				to_ret += str(self.getAt(r, c)) + ' '
				if c % 3 == 2 and c != 8:
					to_ret += '| '
			to_ret += '\n'
			if r % 3 == 2 and r != 8:
				to_ret += '------+-------+-------\n'
		return to_ret

	# ROW IS I, COL IS J

	# returns val at i,j
	def getAt(self, i, j):
		return self.rows[i][j]

	def setAt(self, i, j, val):
		self.rows[i][j] = val

	def zeros(self):
		total = 0
		for r in self.rows:
			for c in r:
				if c == 0:
					total += 1
		return total

	# each iteration: for each spot, check via box, check via row, check via col. if none work, YA FUCKED BOI

	# returns a list of values in box containing point i,j
	def getBox(self, i, j):
		if i < 3:
			box_row = 0
		elif i < 6:
			box_row = 1
		else:
			box_row = 2
		if j < 3:
			box_col = 0
		elif j < 6:
			box_col = 1
		else:
			box_col = 2
		start_row = 3 * box_row
		start_col = 3 * box_col
		to_ret = []
		for m in range(3):
			r = start_row + m
			for n in range(3):
				c = start_col + n
				v = self.getAt(r, c)
				if v:
					to_ret.append(v)
		return to_ret

	# returns a list of values in row containing point i,j
	def getRow(self, i, j):
		to_ret = []
		for n in range(9):
			v = self.getAt(i, n)
			if v:
				to_ret.append(v)
		return to_ret

	# returns a list of values in col containing point i,j
	def getCol(self, i, j):
		to_ret = []
		for n in range(9):
			v = self.getAt(n, j)
			if v:
				to_ret.append(v)
		return to_ret

	def solveStep(self):
		
		guarantees = []
		legalMoves = []
		r = 0
		c = 0

		# ------------------------------------------------------------------------------------------------------------------------------- #
		# first we find guaranteed correct moves
		for r in range(9):
			for c in range(9):
				if self.getAt(r, c) == 0:
					couldBe = []
					box = self.getBox(r, c)
					row = self.getRow(r, c)
					col = self.getCol(r, c)
					opts = range(1,10)
					for o in opts:
						if o not in box and o not in row and o not in col:
							couldBe.append(o)
					if len(couldBe) == 1:
						guarantees.append(Move(r, c, couldBe[0]))
					else:
						legalMoves.append(OptionList(r, c, couldBe))
		
		for box_row in range(3):
			for box_col in range(3):
				for tester in range(1,10):
					nTrues = 0
					for i in range(3):
						r = box_row * 3 + i
						for j in range(3):
							c = box_col * 3 + j
							if self.getAt(r, c) == 0 and tester not in self.getRow(r, c) and tester not in self.getCol(r, c) and tester not in self.getBox(r, c):
								to_place = [r,c]
								nTrues += 1
					if nTrues == 1:
						guarantees.append(Move(to_place[0], to_place[1], tester))

		# we return at the end of this if, so we don't need any elif- or else-s after
		if len(guarantees):
			for move in guarantees:
				# we can set these in the current puzzle, because we know they're right
				self.setAt(move.row, move.col, move.val)
			# recursion, but from the next step from the current puzzle - no need to make a new one
			return self.solveStep()

		# ----------------------------------------------------------------------------------------------------------------------------------- #
		# if we can't find any guarantees, we have to search for moves that aren't illegal, in order of how many different options per square there are
		# this is where we try the golden thread idea
		if len(legalMoves):
			legalMoves.sort(key=lambda x: x.howMany())
			for l in legalMoves:
				for val in l.val_list:
					newPuz = copy.deepcopy(self)
					# tie in necessary ish
					newPuz.tried = self.tried
					# newPuz.steps = copy.deepcopy(self.steps).append('{} in [{}, {}]'.format(val, l.row, l.col))
					newPuz.recur_depth += 1
					# print newPuz
					# print '{} boxes filled, {} levels deep'.format(self.fullBoxes(), self.recur_depth)
					newPuz.setAt(l.row, l.col, val)
					# don't bother if we've already tried that setup
					if str(newPuz) not in self.tried:
						# newPuz.printSteps()
						if newPuz.solveStep():
							return newPuz()
					else:
						print 'hey, we saved a pass with the hash thing!'

		# if there are no legal moves at all, we're screwed, and the puzzle doesn't work, and we want to put that in the hash of <tried> before we get rid of it.
		# <tried> is passed by reference, so it's cool if we don't copy it or anything. And we can just use the string of it because it's unique and consistent
		self.tried.append(hash(str(self)))
		print len(self.tried)
		return False

		# for a given row, figure out spots-that-seven-can-go-in
		# '' column ''
		# '' box ''

	def printSteps(self):
		output = ''
		print self.steps
		for step in self.steps:
			output.append(step+', ')

	def fullBoxes(self):
		count = 0
		for i in range(9):
			for j in range(9):
				if self.getAt(i,j):
					count += 1
		return count

	# checks if all boxes are full
	def isFull(self):
		return self.fullBoxes()==81

	# checks whether a particular square of the puzzle is valid
	# r is row, c is col
	def squareIsValid(self, r, c):
		if anyRepeats(self.getBox(r, c)):
			return False
		if anyRepeats(self.getRow(r, c)):
			return False
		if anyRepeats(self.getCol(r, c)):
			return False
		return True


	# checks whether the whole puzzle is valid
	def puzzleIsValid(self):
		for i in range(9):
			for j in range(9):
				if not self.squareIsValid(i, j):
					return False
		return True

	# finds coordinates [row, col] of next open space
	# returns False if puzzle is full
	def findNextOpenSpace(self):
		for i in range(9):
			for j in range(9):
				if self.getAt(i,j) == 0:
					return [i,j]
		return False

	# this operates each time on the next open square of the puzzle
	# when it is forced to backtrack, it should clear whatever it had there, putting a zero back, unless the puzzle is full and correct
	def solveMe(self):
		if self.isFull():
			if self.puzzleIsValid():
				return True
			return False
		r, c = self.findNextOpenSpace()
		for i in range(1,10):
			self.setAt(r, c, i)
			if self.squareIsValid(r, c):
				if self.solveMe():
					return True
		self.setAt(r, c, 0)

		# answer = self.solveStep()
		# if answer:
			# print(answer)
'''

while there is an open square left:
	find next open square
	for i in range(1,10):
		set open square to i
		if puzzle is valid:
			recurse()



'''


puz_str = '6 * * 2 9 * * * * * * * 3 * * 7 * * * * 7 * 4 * * 9 * 2 6 * * * 3 * * * 1 * 5 * * * 4 * 2 * * * 6 * * * 3 8 * 7 * * 6 * 3 * * * * 4 * * 2 * * * * * * * 3 9 * * 5'
easy_puz = '* 4 * 2 8 * * * * 6 3 * 5 * 4 9 2 * 1 9 * * * 6 * * * * * 5 4 9 * * 8 * * * 6 * 7 * 4 * * * 1 * * 6 2 3 * * * * * 3 * * * 4 8 * 7 3 9 * 8 * 1 6 * * * * 2 1 * 3 *'
med_puz = '* 7 * * 1 2 4 * * 9 1 * * * 6 * * * * 6 * 9 * * * 1 7 2 8 7 * * * * * 5 * * * * * * * * * 5 * * * * * 1 4 2 6 3 * * * 1 * 8 * * * * 8 * * * 9 6 * * 4 3 6 * * 2 *'
hard_puz = '* 4 * * * 7 3 * * * * * * 3 * * 5 * * * 7 * 4 * * * 8 * * 6 * * 4 * * 2 * * 8 9 2 3 6 * * 2 * * 7 * * 1 * * 7 * * * 6 * 9 * * * 2 * * 1 * * * * * * 5 8 * * * 6 *'
hard_puz_2 = '1 * * * * 7 * 9 * * 3 * * 2 * * * 8 * * 9 6 * * 5 * * * * 5 3 * * 9 * * * 1 * * 8 * * * 2 6 * * * * 4 * * * 3 * * * * * * 1 * * 4 * * * * * * 7 * * 7 * * * 3 * *'
hard_puz_3 = '* * * 2 * * * 6 3 3 * * * * 5 4 * 1 * * 1 * * 3 9 8 * * * * * * * * 9 * * * * 5 3 8 * * * * 3 * * * * * * * * 2 6 3 * * 5 * * 5 * 3 7 * * * * 8 4 7 * * * 1 * * *'
hard_puz_3_ans = '8 5 4 2 1 9 7 6 3 3 9 7 8 6 5 4 2 1 2 6 1 4 7 3 9 8 5 7 8 5 1 2 6 3 9 4 6 4 9 5 3 8 1 7 2 1 3 2 9 4 7 8 5 6 9 2 6 3 8 4 5 1 7 5 1 3 7 9 2 6 4 8 4 7 8 6 5 1 2 3 9'

'''
blank = ''
for i in range(80):
	blank = blank + '* '
blank = blank + '*'
bpuz = Puzzle(blank)

print str(bpuz)
bpuz.solveMe()
print str(bpuz)
sys.exit(0)
'''

puzzle = Puzzle(hard_puz_3)
puzzle_ans = Puzzle(hard_puz_3_ans)

print str(puzzle)

# start_zeros = puzzle.zeros()
puzzle.solveMe()
# end_zeros = puzzle.zeros()

print str(puzzle)

if str(puzzle) == str(puzzle_ans):
	print '\npuzzle was solved correctly!'




