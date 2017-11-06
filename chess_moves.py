#!/usr/bin/env python

import random

SQUARE = 'g7'
FILE = 'chess_moves.txt'

def main():
  print ''
  sample_moves(SQUARE)
  print ''
  all_moves()
  print ''

def all_moves():

  moves = set()
  pawn_moves = set()
  for x in range(0,8):
    for y in range(0,8):
      sq = Square(x,y)
      moves.update(Queen(sq).get_moves())
      moves.update(Knight(sq).get_moves())
      pawn_moves.update(Pawn(sq).get_moves())

  print 'Total Moves: %s + %s = %s' % (
      2*len(moves),2*len(pawn_moves),2*len(moves)+2*len(pawn_moves)
  )

  print ('Examples: '
      + ','.join([str(random.choice(list(moves))) for x in range(0,10)])
      +',...'
  )

  with open(FILE,'w') as f:
    f.write('\n'.join([str(x) for x in sorted(moves)])+'\n')
    f.write('\n'.join([str(x) for x in sorted(pawn_moves)])+'\n')

def sample_moves(sq):

  s = Square(sq)
  q = Queen(s).get_moves()
  k = Knight(s).get_moves()
  p = Pawn(s).get_moves()
  moves = q+k+p
  print '%s Moves: %s' % (s,len(moves))
  show_moves(s,moves)
  print 'Knight: '+','.join([str(x) for x in k])
  print 'Pawn: '+','.join([str(x) for x in p])

def show_moves(piece,moves):

  squares = [move.other(piece) for move in moves]
  s = '+-----------------+\n'
  for y in range(7,-1,-1):
    s += '| '
    for x in range(0,8):
      sq = Square(x,y)
      if sq==piece:
        s += 'o '
      elif sq in squares:
        s += 'x '
      else:
        s += '. '
    s += '|\n'
  s += '+-----------------+'
  print s

class Square(object):

  @staticmethod
  def valid(s):

    return s.x>=0 and s.x<8 and s.y>=0 and s.y<8

  @staticmethod
  def a1(x,y):

    return '%s%s' % ('abcdefgh'[x],y+1)

  @staticmethod
  def xy(a1):

    return ('abcdefg'.index(a1[0]),int(a1[1])-1)

  def __init__(self,*args):

    if len(args)==1:
      vals = Square.xy(args[0])
    else:
      vals = args
    (self.x,self.y) = vals

  def __eq__(self,other):

    return self.x==other.x and self.y==other.y

  def __str__(self):

    return Square.a1(self.x,self.y)

  __repr__ = __str__

class Move(object):

  @staticmethod
  def valid(move):

    return Square.valid(move.a) and Square.valid(move.b)

  def __init__(self,a,b,promote=None):

    self.a = a
    self.b = b
    self.p = promote

    if self.p and self.p not in 'rbnq':
      raise ValueError('invalid promotion "%s"' % self.p)

  def other(self,sq):

    if sq==self.a:
      return self.b
    elif sq==self.b:
      return self.a

  def __eq__(self,x):

    return self.p==x.p and (
        (self.a==x.a and self.b==x.b) or
        (self.a==x.b and self.b==x.a)
    )

  def __lt__(self,other):

    return str(self)<str(other)

  def __contains__(self,x):

    return x==self.a or x==self.b

  def __str__(self):

    return '%s%s%s' % (self.a,self.b,self.p if self.p else '')

  __repr__ = __str__

class Piece(object):

  def __init__(self,square):

    self.s = square
    self.x = square.x
    self.y = square.y

  def get_moves(self):

    return [Move(Square(self.x,self.y),s) for s in self.get_squares()]

  def get_squares(self):

    return [s for s in self.get() if Square.valid(s)]

  def get(self):

    raise NotImplementedError

class Queen(Piece):

  def get(self):

    moves = []
    for i in range(0,8):
      if i!=self.x:
        moves.append(Square(i,self.y))
        moves.append(Square(i,self.y-self.x+i))
        moves.append(Square(i,self.y+self.x-i))
      if i!=self.y:
        moves.append(Square(self.x,i))
    return moves

class Knight(Piece):

  MOVES = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]

  def get(self):

    moves = []
    for (x,y) in Knight.MOVES:
      moves.append(Square(self.x+x,self.y+y))
    return moves

class Pawn(Piece):

  def get(self):

    if self.y!=6:
      return []

    moves = []
    for i in range(self.x-1,self.x+2):
      moves.append(Square(i,7))
    return moves

  def get_moves(self):

    moves = []
    for sq in self.get_squares():
      for p in 'rnbq':
        me = Square(self.x,self.y)
        moves.append(Move(me,sq,p))
    return moves

if __name__=='__main__':
  main()
