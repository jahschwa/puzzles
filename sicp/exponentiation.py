#!/usr/bin/env python3
#
# Exercise 1.16: Design a procedure that evolves an iterative exponentiation
# process that uses successive squaring and uses a logarithmic number of steps,
# as does `fast-expt`.
#
# Hint: Using the observation that
#     `(b ^ (n/2)) ^ 2 == (b ^ 2) ^ (n/2)`
# keep, along with the exponent `n` and the base `b`, an additional state
# variable `a`, and define the state transformation in such a way that the
# product `a * b ^ n` is unchanged from state to state. At the beginning of the
# process `a` is taken to be 1, and the answer is given by the value of `a` at
# the end of the process. In general, the technique of defining an
# _invariant quantity_ that remains unchanged from state to state is a powerful
# way to think about the design of iterative algorithms.

from argparse import ArgumentParser


def main(base, debug, exponent):

  global DEBUG
  DEBUG = debug

  expected = base ** exponent
  observed = exp(base, exponent)

  print(f'Expected : {expected}')
  print(f'Observed : {observed}')


def exp(b, n):
  """
  even : b ^ n = (b ^ 2) ^ (n / 2)
  odd  : b ^ n = b * (b ^ 2) ^ ((n - 1) / 2)
  b ^ 5 = b * (b ^ 2) ^ 2
  b ^ 6 = (b ^ 2) ^ 3 = b ^ 2 * (b ^ 4)
  b ^ 7 = b * (b ^ 2) ^ 3 = b * b ^ 2 * (b ^ 4)
  b ^ 8 = (b ^ 2) ^ 4 = (b ^ 4) ^ 2
  b ^ 9 = b * (b ^ 2) ^ 4 = b * b ^ (b ^ 4) ^ 2
  """

  a = 1
  say(f'a={a}, b={b}, n={n}')
  while n > 1:
    if n % 2:
      a *= b
      n -= 1
    b *= b
    n //= 2
    say(f'a={a}, b={b}, n={n}')

  return a * b


def say(s):

  if DEBUG:
    print('### ' + s)


def get_args():

  ap = ArgumentParser()
  add = ap.add_argument

  add('base', type=int)
  add('exponent', type=int)

  add('-d', '--debug', action='store_true')

  return ap.parse_args()


DEBUG = False


if __name__ == '__main__':
  main(**vars(get_args()))
