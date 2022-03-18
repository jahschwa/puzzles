#!/usr/bin/env python
#
# [TODO] fix cages>grid.size in _kk_config_gen()
# [TODO] make rows/cols Cage objects (also add Cage.unique)

from itertools import permutations,combinations
from functools import reduce

def main():
  g = Grid(9).make_sudoku()
  print(g)
  print('')

  g = Grid(3).make_kenken_from_ascii("""
    112
    332
    455
    ---
    1:2- 2:4+ 3:2/ 4:3= 5:3/
  """)
  print(g)
  print('')

  g = Grid(9).make_kenken_from_ascii("""
    123455667
    123445577
    11884997A
    BB8899CAA
    DBEE9FGAH
    DDEIIFGGH
    JDKILFGGH
    JJKMLNGOH
    JPKMLNOOQ
    ---
    1:64* 2:15* 3:5- 4:392* 5:378* 6:10+ 7:540* 8:54* 9:2400* A:672*
    B:144* C:5= D:1260* E:168* F:48* G:448* H:540* I:15+ J:378* K:30*
    L:12+ M:1- N:3/ O:168* P:2= Q:1=
  """)
  print(g)

###############################################################################
# Grid class
#
# - a Grid contains a 2d array of Cells that each belong to one Cage
# - it has creation methods for Sudoku and Kenken
# - and can solve them, with optional logging
###############################################################################

class Grid:

  # 1-9 + A-Z + 0
  CHARS = [chr(x) for x in list(range(49,58))+list(range(65,91))]+['0']

  # @param size (int) number of rows/cols in the grid
  def __init__(self,size):

    self.size = size
    self.chars = Grid.CHARS[:size]

    # populate the Grid with Cell objects and re-index for cols
    self.rows = [
      [Cell(self,(r,c)) for c in range(0,size)]
      for r in range(0,size)
    ]
    self.cols = [
      [self.rows[r][c] for r in range(0,size)]
      for c in range(0,size)
    ]

    self.cages = []
    self.cage_index = {}

    self.update_queue = set()

  # @param cage (Cage) a new Cage to validate and add to this Grid
  # @raise ValueError if this Cage overlaps any others or has disjoint cells
  def add_cage(self,cage):

    for loc in cage.cells:
      if loc not in self:
        raise ValueError('cage cell %s not in Grid' % loc)
      if loc in self.cage_index:
        raise ValueError('overlap in cell %s' % loc)

    self.cages.append(cage)
    for cell in cage.cells.values():
      self.cage_index[cell.loc] = cage

    # check for disjoint cells
    cells = cage.cells.values()
    if len(cells)>1:
      for cell in cells:
        (r,c) = cell.loc
        disjoint = True
        for neighbor in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
          if neighbor in self.cage_index:
            other = self.cage_index[neighbor]
            if other is not None and other is cage:
              disjoint = False
              break
        if disjoint:
          raise ValueError('cage is disjoint: %s' %
              [c.loc for c in cage.cells.values()])

  # set this Grid up as a Sudoku
  # @raise ValueError if this Grid's size is invalid for a Sudoku
  def make_sudoku(self):

    # Sudoku grids must be square numbers (e.g. 9x9, 16x16)
    step = self.size**0.5
    if int(step)!=step:
      raise ValueError('invalid size for sudoku')
    step = int(step)

    # Sudoku grids contain a number of cages equal to the Grid size
    # arranged in a sqrt(size) by sqrt(size) grid
    # where each Cage contains a number of Cells equal the Grid size
    # e.g. a 9x9 Sudoku has 9 Cages, each with 9 Cells, in a 3x3 Grid
    for row in range(0,step):
      for col in range(0,step):
        cage = Cage(self)
        for r in range(0,step):
          for c in range(0,step):
            cage.add_cell(self.rows[step*row+r][step*col+c])
        self.add_cage(cage)

    return self

  # set this Grid up as a Kenken
  # Kenkens can be of any size, and their cages can be of any size/shape
  # each Cage has a restricting math rule, with an operator in [=+-*/] and a
  # number, e.g. "*24" means the cells in the cage have a product of 24
  # @param s (str) the string to parse, see example in docstring
  # @raise ValueError if the string is not a valid KenKen
  def make_kenken_from_ascii(self,s):
    """
    Sample input:

      123455667
      123445577
      11884997A
      BB8899CAA
      DBEE9FGAH
      DDEIIFGGH
      JDKILFGGH
      JJKMLNGOH
      JPKMLNOOQ
      ---
      1:64* 2:15* 3:5- 4:392* 5:378* 6:10+ 7:540* 8:54* 9:2400* A:672*
      B:144* C:5= D:1260* E:168* F:48* G:448* H:540* I:15+ J:378* K:30*
      L:12+ M:1- N:3/ O:168* P:2= Q:1=
    """

    (grid,ops) = s.split('---')
    grid = grid.strip().rstrip('-').strip()
    ops = ops.strip().lstrip('-').strip()
    unique = set(grid.replace('\n','').replace(' ',''))
    cages = {char:Cage(self) for char in unique}

    # add this Grid's Cell objects to our new Cages
    for (r,line) in enumerate(grid.strip().split('\n')):
      line = line.strip()
      for (c,char) in enumerate(line):
        try:
          cages[char].add_cell(self.rows[r][c])
        except IndexError:
          raise ValueError('invalid cell (%s,%s) in line "%s" @ "%s"'
              % (r,c,line,char))

    # parse the operations and assign the possibilty gen func
    observed = []
    for line in ops.strip().split('\n'):
      for op in line.strip().split(' '):
        try:
          (char,o) = op.strip().split(':')
          if char not in cages:
            raise ValueError('identifier "%s" not found in grid' % char)
          i = 0
          while o[i].isnumeric():
            i += 1
          (num,o) = (o[:i],o[i:])
          cages[char].set_poss(Poss.kenken(o,int(num)))
          observed.append(char)
        except Exception as e:
          raise ValueError('(parsing "%s") %s' % (op,e.args[0]))

    if len(observed)!=len(cages):
      raise ValueError('operator not defined for [%s]'
          % ','.join(sorted([x for x in cages if x not in observed])))

    for cage in cages.values():
      self.add_cage(cage)

    if len(self.cage_index)!=self.size**2:
      raise ValueError('some Cells do not belong to a Cage')

    return self

  # set a cell value and eliminate possibilities
  # @param row (int)
  # @param col (int)
  # @param val (str)
  def set_value(self,row,col,val):

    cell = self.rows[row][col]
    cell.value = val
    for cells in (
        self.rows[row],
        self.cols[col],
        self.cage_index[(row,col)].cells.values()):
      self.elim(val,cells,cell)

  # eliminate a value from a group of cells
  # @param val (str)
  # @param cells (list of Cell) cells to eliminate value from
  # @param skip (Cell or list of Cell) cells to skip
  def elim(self,val,cells,skip):

    if not isinstance(skip,list):
      skip = [skip]

    for cell in cells:
      if cell not in skip and cell.elim(val):
        self.update_queue.add(cell)

  # print this grid with nice-looking table-drawing characters
  # @param cages (bool) [True] whether to draw lines
  # @return (str)
  def to_str(self,cages=True):

    pad = max((self.size+3)//4,3)

    # draw the top border of the table
    s = '┌'
    for c in range(self.size):
      s += '─'*pad
      if c==self.size-1:
        s += '┐'
      elif (0,c+1) in self.cage_index[(0,c)]:
        s += '─'
      else:
        s += '┬'
    s += '\n'

    # draw each row
    for r in range(self.size):

      # the row itself containing the Cell values
      s += '│'
      for c in range(self.size):
        cage = self.cage_index[(r,c)]
        s += str(self.rows[r][c])
        if c<self.size-1 and (r,c+1) in cage:
          s += ' '
        else:
          s += '│'

      # the lines or spaces separating this row from the next
      s += '\n'
      for c in range(self.size):
        cage = self.cage_index[(r,c)]

        # cage spans across rows
        if r<self.size-1 and (r+1,c) in cage:
          if c==0:
            s += '│'
          s += ' '*pad
          if c==self.size-1:
            s += '│'

        # cage does not span across rows
        else:
          if c==0:
            s += '└' if r==self.size-1 else '├'
          s += '─'*pad
          if c==self.size-1:
            s += '┘' if r==self.size-1 else '┤'

        # vertex where 4 cells touch has significantly more possibilities
        if c<self.size-1:
          if r==self.size-1:
            if (r,c+1) in cage:
              s += '─'
            else:
              s += '┴'

          # we first retrieve each cage toucing this vertex (nw,ne,sw,se)
          # then choose the correct table character based on which are equal
          else:
            nw = self.cage_index[(r,c)]
            ne = self.cage_index[(r,c+1)]
            sw = self.cage_index[(r+1,c)]
            se = self.cage_index[(r+1,c+1)]
            s += {
              0 : ' ',
              3 : '└',  6 : '┌',  9 : '┘',  12: '┐',
              5 : '│',  10: '─',
              7 : '├',  11: '┴',  13: '┤',  14: '┬',
              15: '┼'
            }[
              (nw is not ne) +
              2*(ne is not se) +
              4*(se is not sw) +
              8*(sw is not nw)
            ]
      s += '\n'

    return s

  # override string magic method
  # @return (str)
  def __str__(self):
    return self.to_str()

  # @param (2-tuple)
  #   #0 (int) row
  #   #1 (int) col
  def __contains__(self,x):

    if isinstance(x,tuple):
      if len(x)!=2:
        raise ValueError('tuple must be length 2')
      (row,col) = x
      if not isinstance(row,int) or not isinstance(col,int):
        raise ValueError('tuple must contain int')
      return row>=0 and row<self.size and col>=0 and col<self.size
    else:
      raise TypeError('argument must be 2-tuple (row,col)')

###############################################################################
# Cage class
#
# - contains specific Cells and tracks valid Cell combinations
###############################################################################

class Cage:

  # @param grid (Grid)
  # @param poss (func) [None] function that returns possibilities
  #   given this Cage object
  def __init__(self,grid,poss=None):

    self.grid = grid
    self.set_poss(poss)
    self.cells = {}
    self.rows = {}
    self.cols = {}

  # @param poss (func or None)
  def set_poss(self,poss):

    if poss:
      self.poss = poss(self)
    else:
      self.poss = [[x for x in range(1,self.grid.size+1)]]
    # [TODO]

  # @param cell (Cell) the cell to add to this cage
  # @raise ValueError if the cell is already in this cage
  def add_cell(self,cell):

    if cell.loc not in self.grid:
      raise ValueError('invalid cell %s' % (cell.loc,))
    if cell.loc in self.cells:
      raise ValueError('duplicate cell %s' % (cell.loc,))
    self.cells[cell.loc] = cell
    (r,c) = cell.loc
    if r in self.rows:
      self.rows[r].append(cell)
    else:
      self.rows[r] = [cell]
    if c in self.cols:
      self.cols[c].append(cell)
    else:
      self.cols[c] = [cell]
    cell.cage = self

  # get the dimensions that define this cage
  # @return (3-tuple)
  #   #0 (int) row span i.e. height
  #   #1 (int) col span i.e. width
  #   #2 (int) number of cells in this cage
  def get_dims(self):

    row = lambda x:x[0]
    col = lambda x:x[1]
    return (
      max(self.cells,key=row)[0]-min(self.cells,key=row)[0]+1,
      max(self.cells,key=col)[1]-min(self.cells,key=col)[1]+1,
      len(self.cells)
    )

  # @return (Cage) a deep copy of this Cage
  def copy(self):

    new = Cage(self.grid)
    for loc in self.cells:
      new.add_cell(Cell(self.grid,loc))
    return new

  # @return (bool or None) whether this Cage contains diplicates in rows/cols
  #   True if we find a duplicate
  #   None if there are no duplicates but some Cells are undetermined
  #   False if there are no duplicates and all Cells are determined
  def has_conflict(self):

    result = False
    for lines in (self.rows,self.cols):
      for line in lines.values():
        if len(line)>1:
          line = [cell.value for cell in line if cell.value is not None]
          if len(line)!=len(set(line)):
            return True
          if None in line:
            result = None
    return result

  def elim(self):

    raise NotImplementedError

  # override magic contains method to act on Cells or tuples
  # @param obj (Cell or 2-tuple) if tuple:
  #   #0 (int) row
  #   #1 (int) col
  def __contains__(self,obj):

    if isinstance(obj,tuple):
      return obj in self.cells
    return obj in self.cells.values()

###############################################################################
# Cell class
#
# - has a (row,col) location
# - tracks which character in self.grid.chars it can be
# - self.value is None if multiple possibilities, or a character if determined
# - displays as self.value if determined, otherwise as one-hot encoded hex
#   e.g. [1,2,3,4,5,6,7,8,9] = 1ff; [1,2] = 3; [3,7,8] = c4; [6] = 20
###############################################################################

class Cell:

  # @param grid (Grid)
  # @param loc (2-tuple)
  #   #0 (int) row
  #   #1 (int) col
  # @param poss (list of int or None) [self.grid.chars]
  # @param cage (Cage) [None]
  def __init__(self,grid,loc,poss=None,cage=None):

    self.grid = grid
    self.loc = loc
    self.poss = set(poss or self.grid.chars)
    self.value = list(self.poss)[0] if len(self.poss)==1 else None
    self.cage = cage

  # @param val (str) the value to eliminate from this cell
  # @return (bool) whether a value was eliminated
  # @raise RuntimeError if this cell has zero possible values
  def elim(self,val):

    if val in self.poss:
      self.poss.remove(val)
      if len(self.poss)==0:
        raise RuntimeError('cell at %s has no values' % self.loc)
      elif len(self.poss)==1:
        self.value = list(self.poss)[0]
        return True
      self.cage.elim()
    return False

  # @override to compare our row+col
  # @param obj (object)
  def __eq__(self,obj):

    return isinstance(obj,Cell) and self.loc==obj.loc

  # @override to use (row,col)
  def __hash__(self):

    return hash(self.loc)

  # @override to display value or possibilities if there's more than one
  #   the possibilities get one-hot encoded then converted to hex
  #   e.g. [3,7,8] --> hex(2**2+2**6+2**7) = 0xc4
  def __str__(self):

    pad = max((self.grid.size+3)//4,3)

    if self.value:
      s = self.grid.chars[self.value-1]
      return ('%%-%ss' % pad) % (('%%%ss' % pad//2) % s)

    value = 0
    for (i,c) in enumerate(self.grid.chars):
      if c in self.poss:
        value += 2**i
    return hex(value)[2:].zfill(pad)

###############################################################################
# Poss class
#
# - everything is @staticmethod so this is really just a grouping mechanism
###############################################################################

class Poss:

  # return a function to generate possibilities for the given kenken cage
  # @param op (str) one of [=+-*/]
  # @param num (int) the result of the operation
  # @return (func) a function to call on the cage to return possibilities
  #   @param cage (Cage)
  #   @return (list of (list of int))
  @staticmethod
  def kenken(op,num):
    return lambda cage: Poss._kk_valid(cage,
      getattr(Poss, '_kk_'+{
        '+' : 'add',
        '-' : 'sub',
        '*' : 'mult',
        '/' : 'div',
        '=' : 'eq'
      }[op])(cage,num)
    )

  # find valid configurations (i.e. this cage can have 2 duplicate values)
  #   e.g. a 3-cell cage in a straight line must be unique = {1:3}
  #     a 4-cell cage in a square can have dupes = {1:4}; {1:2},{2:1}; {2:2}
  # @param cage (Cage) the cage to analyze
  # @return (list of dict) of {repetitions of a value : allowed occurences}
  #   e.g. {1:3} we need 3 numbers, no number may appear more than once
  #     {1:4}; {1:2},{2:1}; {2:2} we need 4, up to 2 numbers may appear twice
  @staticmethod
  def _kk_config(cage):

    (rows,cols,cells) = cage.get_dims()
    max_count = min(rows,cols)
    vals = list(range(cells))
    poss = [vals[:]]
    Poss._kk_config_gen(cage,max_count,vals,1,poss)
    return [Poss._kk_count(p) for p in poss]

  # recursively do the work for finding valid configurations
  # @param cage (Cage)
  # @param max_count (int) the most times a single value can appear
  # @param vals (list of int) the current set of values we're testing
  # @param index (int) the current index in vals we're manipulating
  # @param poss (list of (list of int))
  @staticmethod
  def _kk_config_gen(cage,max_count,vals,index,poss):

    # we move from all unique e.g. 12345 to repetitions e.g. 11123
    vals = [x if i<index else x-1 for (i,x) in enumerate(vals)]
    counts = {i:vals.count(i) for i in set(vals)}
    for (x,c) in counts.items():
      if c>max_count or (x>0 and c>counts[x-1]):
        return

    # mutate 11234 --> 11223
    if index+2<len(vals):
      Poss._kk_config_gen(cage,max_count,vals,index+2,poss)

    # test for validity and record
    if Poss._kk_config_is_valid(cage,vals):
      poss.append(vals[:])

    # mutate 11234 --> 11123
    if index+1<len(vals):
      Poss._kk_config_gen(cage,max_count,vals,index+1,poss)

  # construct a Cage and test if the config is possible via guess & check
  # @param cage (Cage) the cage to use as template
  # @param vals (list of int) the values to test
  # @return (bool) whether the values can be placed in the cage
  @staticmethod
  def _kk_config_is_valid(cage,vals):

    # copy the cage and get a static order for its cells so we can permute
    cage = cage.copy()
    cells = list(cage.cells.values())

    # permute the values we were provided into the cage and test
    for perm in set(permutations(vals,len(vals))):
      for (cell,val) in zip(cells,perm):
        cell.value = val
      if not cage.has_conflict():
        return True
    return False

  # convert a value list into a config dict
  # @param (list of int)
  # @return (dict) of {repetitions of a value : allowed occurences}
  #   e.g. [1,2,3]-->{1:3}; [1,1,2,2]-->{2:2}; [1,2,2,3,3]-->{1:1,2:2}
  @staticmethod
  def _kk_count(vals):

    # this gets us counts of each value e.g. [1,2,2,3,3]-->[1,2,2]
    counts = [vals.count(i) for i in set(vals)]

    # this gets us counts of each count e.g. [1,2,2]-->{1:1,2:2}
    return {i:counts.count(i) for i in set(counts)}

  # check if the given possibility is valid for this cage
  # @param cage (Cage)
  # @param poss (list of (list of int))
  # @return (list of (list of int))
  @staticmethod
  def _kk_valid(cage,poss):

    # generate a list of all valid configs
    valid = Poss._kk_config(cage)

    # check if each possibility is in the valid list
    return [p for p in poss if Poss._kk_count(p) in valid]

  # generate all possibilities for a sum cage
  # @param poss (list of (list of int)) the list of possibilities
  # @param index (int) [cage.size-1] the index we're currently mutating
  # @param vals (list of int) the current possibility we're mutating
  @staticmethod
  def _kk_add_mutate(poss,index=None,vals=None):

    # we start at the end of vals, e.g. 129-->138-->147-->156
    index = index if index is not None else len(poss[0])-1
    vals = vals[:] if vals else poss[-1][:]
    if index==0:
      return

    # mutate 156-->246
    Poss._kk_add_mutate(poss,index-1,vals)

    # normalize to be monotonically non-decreasing
    vals[index] -= 1
    vals[index-1] += 1
    while not all(x<=y for (x,y) in zip(vals[1:],vals[2:])):
      i = len(vals)-1
      while i>1:
        if vals[i-1]>vals[i]:
          diff = vals[i-1]-vals[i]
          vals[i-1] -= diff
          vals[i-2] += diff
        i -= 1

    # if we were able to normalize, record and mutate
    if vals[0]<=vals[1]:
      poss.append(vals)

      # mutate 156-->165 (will get normalized to 255)
      Poss._kk_add_mutate(poss,index,vals)

  # generate all possibilities for a product cage
  # @param poss (list of (list of int)) the list of possibilities
  # @param cage (Cage)
  # @param num (int) the desired product divided by the product of vals
  #   e.g. 42 [1,1,1] --> 6 [7,1,1] --> 1 [7,6,1]
  # @param factors (list of int) [None] valid factors for the final product
  # @param index (int) [0] the index we're currently manipulating
  # @param vals (list of int) [1 repeated cage.size times] active mutation
  @staticmethod
  def _kk_mult_mutate(poss,cage,num,factors=None,index=0,vals=None):

    (size,_max) = (len(cage.cells),cage.grid.size)
    factors = factors or [f for f in range(2,_max+1) if num%f==0]
    vals = vals or [1]*size

    # we've assigned all cells but one, check and record
    if index==size-1 and num<=_max:
      vals[-1] = num
      v = sorted(vals)
      if v not in poss:
        poss.append(v)

    # otherwise mutate by populating the current index with each factor
    elif index<size-1:
      for f in factors:
        if num%f==0:
          vals[index] = f

          # update num and move to the next index
          Poss._kk_mult_mutate(poss,cage,num//f,factors,index+1,vals)

  # get a list of possible addends
  # @param cage (Cage)
  # @param num (int) the target sum
  # @return (list of (list of int)) all possibilities
  @staticmethod
  def _kk_add(cage,num):

    # we start with a single possibility, with as many ones in front and as
    # high numbers as possible to the right, e.g. 20-->299, 15-->159, 10-->118
    poss = []
    temp = [1 for x in range(len(cage.cells))]
    _max = min(num-len(cage.cells)+1, cage.grid.size)
    temp[-1] = _max
    i = len(temp)-2
    while sum(temp)<num:
      temp[i] = min(num-sum(temp)+1,_max)
      i -= 1

    poss = [temp]
    Poss._kk_add_mutate(poss)
    return poss

  # get a list of possible subtrahends/minuends
  # @param cage (Cage)
  # @param num (int) target difference
  # @return (list of (list of int)) all possibilities
  @staticmethod
  def _kk_sub(cage,num):

    return [[x,x+num] for x in range(1,cage.grid.size-num+1)]

  # get a list of possible multiplicands
  # @param cage (Cage)
  # @param num (int) target product
  # @return (list of (list of int)) all possibilities
  @staticmethod
  def _kk_mult(cage,num):

    factors = [x for x in range(1,cage.grid.size+1) if num%x==0]
    poss = []
    Poss._kk_mult_mutate(poss,cage,num)
    return poss

  # get a list of possible dividends/divisors
  # @param cage (Cage)
  # @param num (int) target quotient
  # @return (list of (list of int)) all possibilities
  @staticmethod
  def _kk_div(cage,num):

    return [[x,x*num] for x in range(1,cage.grid.size//num+1)]

  # the equal (=) operator in a kenken is an identity, e.g. a freebie
  # @param cage (Cage)
  # @param num (int)
  # @return (list of (list of int)) the input num inside a double list
  @staticmethod
  def _kk_eq(cage,num):

    return [[num]]

###############################################################################
# CLI entry point into main()
###############################################################################

if __name__=='__main__':
  main()