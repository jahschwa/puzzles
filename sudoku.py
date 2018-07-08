#!/usr/bin/env python

from itertools import permutations,combinations
from functools import reduce

CHARS = [chr(x) for x in list(range(49,59))+list(range(65,91))]

def main():
  g = Grid(9)
  g.make_sudoku()
  print(g)
  print('')

  g = Grid(3)
  g.make_kenken_from_ascii("""
    112
    332
    455
    ---
    1:2- 2:4+ 3:2/ 4:3= 5:3/
  """)
  print(g)
  print('')

  g = Grid(9)
  g.make_kenken_from_ascii("""
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

class Grid:

  CHARS = CHARS

  def __init__(self,size):

    self.size = size
    self.chars = Grid.CHARS[:size]

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

  def add_cage(self,cage):

    for loc in cage.cells:
      if loc in self.cage_index:
        raise ValueError('overlap in cell %s' % loc)

    self.cages.append(cage)
    for cell in cage.cells.values():
      self.cage_index[cell.loc] = cage

  def make_sudoku(self):

    step = self.size**0.5
    if int(step)!=step:
      raise ValueError('invalid size for sudoku')
    step = int(step)

    for row in range(0,step):
      for col in range(0,step):
        cage = Cage(self)
        for r in range(0,step):
          for c in range(0,step):
            cage.add_cell(self.rows[step*row+r][step*col+c])
        self.add_cage(cage)

  def make_kenken_from_ascii(self,s):

    (grid,ops) = s.split('---')

    unique = set(grid.strip().replace('\n','').replace(' ',''))
    cages = {char:Cage(self) for char in unique}
    for (r,line) in enumerate(grid.strip().split('\n')):
      line = line.strip()
      for (c,char) in enumerate(line):
        cages[char].add_cell(self.rows[r][c])

    for line in ops.strip().split('\n'):
      for op in line.strip().split(' '):
        (char,op) = op.strip().split(':')
        i = 0
        while op[i].isnumeric():
          i += 1
        (num,op) = (op[:i],op[i:])
        cages[char].set_poss(Poss.kenken(op,int(num)))

    for cage in cages.values():
      self.add_cage(cage)

  def set_value(self,row,col,val):

    cell = self.rows[row][col]
    cell.value = val
    for cells in (
        self.rows[row],
        self.cols[col],
        self.cells[(row,col)].cells.values()):
      self.elim(val,cells,cell)

  def elim(self,val,cells,skip):

    if not isinstance(skip,list):
      skip = [skip]

    for cell in cells:
      if cell not in skip and cell.elim(val):
        self.update_queue.add(cell)

  def to_str(self,cages=True):

    pad = max((self.size+3)//4,3)

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

    for r in range(self.size):
      s += '│'
      for c in range(self.size):
        cage = self.cage_index[(r,c)]
        s += str(self.rows[r][c])
        if c<self.size-1 and (r,c+1) in cage:
          s += ' '
        else:
          s += '│'
      s += '\n'
      for c in range(self.size):
        cage = self.cage_index[(r,c)]
        if r<self.size-1 and (r+1,c) in cage:
          if c==0:
            s += '│'
          s += ' '*pad
          if c==self.size-1:
            s += '│'
        else:
          if c==0:
            s += '└' if r==self.size-1 else '├'
          s += '─'*pad
          if c==self.size-1:
            s += '┘' if r==self.size-1 else '┤'
        if c<self.size-1:
          if r==self.size-1:
            if (r,c+1) in cage:
              s += '─'
            else:
              s += '┴'
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

  def __str__(self):
    return self.to_str()

class Cage:

  def __init__(self,grid,poss=None):

    self.grid = grid
    self.set_poss(poss)
    self.cells = {}
    self.rows = {}
    self.cols = {}

  def set_poss(self,poss):

    if poss:
      self.poss = poss(self)
    else:
      self.poss = [[x for x in range(1,self.grid.size+1)]]
    # [TODO]

  def add_cell(self,cell):

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

  def get_dims(self):

    row = lambda x:x[0]
    col = lambda x:x[1]
    return (
      max(self.cells,key=row)[0]-min(self.cells,key=row)[0]+1,
      max(self.cells,key=col)[1]-min(self.cells,key=col)[1]+1,
      len(self.cells)
    )

  def copy(self):

    new = Cage(self.grid)
    for loc in self.cells:
      new.add_cell(Cell(self.grid,loc))
    return new

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

  def __contains__(self,obj):

    if isinstance(obj,tuple):
      return obj in self.cells
    return obj in self.cells.values()

class Cell:

  def __init__(self,grid,loc,poss=None,cage=None):

    self.grid = grid
    self.loc = loc
    self.poss = set(poss or self.grid.chars)
    self.value = list(self.poss)[0] if len(self.poss)==1 else None
    self.cage = cage

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

  def __eq__(self,obj):

    return isinstance(obj,Cell) and self.loc==obj.loc

  def __hash__(self):

    return hash(self.loc)

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

class Poss:

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

  @staticmethod
  def _kk_config(cage):

    (rows,cols,cells) = cage.get_dims()
    max_count = min(rows,cols)
    vals = list(range(cells))
    poss = [vals[:]]
    Poss._kk_config_gen(cage,max_count,vals,1,poss)
    return [Poss._kk_count(p) for p in poss]

  @staticmethod
  def _kk_config_gen(cage,max_count,vals,index,poss):

    vals = [x if i<index else x-1 for (i,x) in enumerate(vals)]
    counts = {i:vals.count(i) for i in set(vals)}
    for (x,c) in counts.items():
      if c>max_count or (x>0 and c>counts[x-1]):
        return
    if index+2<len(vals):
      Poss._kk_config_gen(cage,max_count,vals,index+2,poss)
    if Poss._kk_config_is_valid(cage,vals):
      poss.append(vals[:])
    if index+1<len(vals):
      Poss._kk_config_gen(cage,max_count,vals,index+1,poss)

  @staticmethod
  def _kk_config_is_valid(cage,vals):

    cage = cage.copy()
    cells = list(cage.cells.values())
    for perm in set(permutations(vals,len(vals))):
      for (cell,val) in zip(cells,perm):
        cell.value = val
      if not cage.has_conflict():
        return True
    return False

  @staticmethod
  def _kk_count(vals):

    counts = [vals.count(i) for i in set(vals)]
    return {i:counts.count(i) for i in set(counts)}

  @staticmethod
  def _kk_valid(cage,poss):

    valid = Poss._kk_config(cage)
    return [p for p in poss if Poss._kk_count(p) in valid]

  @staticmethod
  def _kk_add_mutate(poss,index=None,vals=None):

    index = index if index is not None else len(poss[0])-1
    vals = vals[:] if vals else poss[-1][:]
    if index==0:
      return

    Poss._kk_add_mutate(poss,index-1,vals)

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
    if vals[0]<=vals[1]:
      poss.append(vals)
      Poss._kk_add_mutate(poss,index,vals)

  @staticmethod
  def _kk_mult_mutate(poss,cage,num,factors=None,index=0,vals=None):

    (size,_max) = (len(cage.cells),cage.grid.size)
    factors = factors or [f for f in range(2,_max+1) if num%f==0]
    vals = vals or [1]*size

    if index==size-1 and num<=_max:
      vals[-1] = num
      v = sorted(vals)
      if v not in poss:
        poss.append(v)
    elif index<size-1:
      for f in factors:
        if num%f==0:
          vals[index] = f
          Poss._kk_mult_mutate(poss,cage,num//f,factors,index+1,vals)

  @staticmethod
  def _kk_add(cage,num):

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

  @staticmethod
  def _kk_sub(cage,num):

    return [[x,x+num] for x in range(1,cage.grid.size-num+1)]

  @staticmethod
  def _kk_mult(cage,num):

    factors = [x for x in range(1,cage.grid.size+1) if num%x==0]
    prod = lambda l: reduce(lambda a,b: a*b,l,1)
    poss = []
    Poss._kk_mult_mutate(poss,cage,num)
    return poss

  @staticmethod
  def _kk_div(cage,num):

    return [[x,x*num] for x in range(1,cage.grid.size//num+1)]

  @staticmethod
  def _kk_eq(cage,num):

    return [[num]]

if __name__=='__main__':
  main()