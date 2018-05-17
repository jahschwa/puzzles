#!/usr/bin/env python

def main():
  g = Grid(9)
  g.make_sudoku()
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
  """)
  print(g)

class Grid:

  VALUES = [chr(x) for x in list(range(49,59))+list(range(65,91))]

  def __init__(self,size):

    self.size = size
    self.poss = Grid.VALUES[:size]

    self.rows = [
      [Cell(self,(r,c),self.poss) for c in range(0,size)]
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

    cage.finalize()
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

    unique = set(s.strip().replace('\n','').replace(' ',''))
    cages = {c:Cage(self) for c in unique}
    for (r,line) in enumerate(s.strip().split('\n')):
      line = line.strip()
      for (c,char) in enumerate(line):
        cages[char].add_cell(self.rows[r][c])

    for cage in cages.values():
      self.add_cage(cage)

  def set_value(self,row,col,val):

    self.cells[row][col].value = val
    for cells in (
        self.rows[row],
        self.cols[col],
        self.cells[(row,col)].cells.values()):
      self.elim(val,cells)

  def to_str(self,cages=True):

    pad = (self.size+3)//4

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
    if poss:
      self.poss = poss()
    else:
      self.poss = [[str(x) for x in range(self.grid.size)]]
    self.cells = {}

  def add_cell(self,cell):

    if cell.loc in self.cells:
      raise ValueError('duplicate cell %s' % cell.loc)
    self.cells[cell.loc] = cell

  def finalize(self):

    raise NotImplemented

  def __contains__(self,obj):

    if isinstance(obj,tuple):
      return obj in self.cells
    return obj in self.cells.values()

class Cell:

  def __init__(self,grid,loc,poss,cage=None):

    self.grid = grid
    self.loc = loc
    self.value = set(poss)
    self.cage = cage

  def __eq__(self,obj):

    return isinstance(obj,Cell) and self.loc==obj.loc

  def __hash__(self):

    return hash(self.loc)

  def __str__(self):

    pad = (self.grid.size+3)//4
    if isinstance(self.value,set):
      value = 0
      for (i,c) in enumerate(self.grid.poss):
        if c in self.value:
          value += 2**i
      return hex(value)[2:].zfill(pad)
    return ('%%%ss' % pad) % pad

if __name__=='__main__':
  main()
