#!/usr/bin/env python3
#
# $ ./recursion.py -m -30 -M 30
#
#   iterative_no_collection :  0.000078439712524 sec
#   iterative_deque_maxlen  :  0.000138521194458 sec
#   iterative_dict          :  0.000154495239258 sec
#   iterative_list          :  0.000159025192261 sec
#   iterative_deque         :  0.000166177749634 sec
#   recursive_caching       :  0.000228643417358 sec
#   iterative_deque_caching :  0.000428438186646 sec
#   recursive               : 12.660402536392212 sec
#
# $ ./recursion.py -m -400 -M 400
#
#   iterative_no_collection : 0.01356840133666992 sec
#   iterative_deque_maxlen  : 0.01883316040039063 sec
#   iterative_list          : 0.02612996101379395 sec
#   iterative_deque         : 0.02642154693603516 sec
#   iterative_dict          : 0.02887105941772461 sec
#   recursive_caching       : 0.03300261497497559 sec
#   iterative_deque_caching : 0.04248166084289551 sec


from argparse import ArgumentParser
from collections import deque
from functools import cache
from math import inf
from time import time


def main(all, min, max):

  times = {
    func: 0
    for (name, func) in globals().items()
    if (
      callable(func)
      and name.startswith('_')
      and not name.startswith('__')
      and (all or max <= getattr(func, 'skip_after', inf))
    )
  }

  for n in range(min, max + 1):
    results = {}
    for func in times:
      try:
        func.cache_clear()
      except AttributeError:
        pass
      (result, sec) = timeit(func, n)
      if results and result != (expected := next(iter(results.values()))):
        done = [f.__name__ for (f, sec) in times.items() if sec > 0]
        assert False, '\n'.join((
          '',
          f'  observed: f({n}) = {result} from {func.__name__}',
          f'  expected: f({n}) = {expected} from {", ".join(sorted(done))}',
        ))
      results[func] = result
      times[func] += sec

  for (func, sec) in sorted(times.items(), key=lambda x: x[1]):
    print(f'{func.__name__.strip("_")} : {sec} sec')


def skip_after(limit):
  def decorator(func):
    func.skip_after = limit
    return func
  return decorator


def timeit(func, *args, **kwargs):

  start = time()
  result = func(*args, **kwargs)
  return (result, time() - start)


@skip_after(30)
def _recursive(n):

  if n < 3:
    return n
  return _recursive(n - 1) + 2 * _recursive(n - 2) + 3 * _recursive(n - 3)


@cache
def _recursive_caching(n):

  if n < 3:
    return n
  return (
    _recursive_caching(n - 1)
    + 2 * _recursive_caching(n - 2)
    + 3 * _recursive_caching(n - 3)
  )


def _iterative_list(n):

  if n < 3:
    return n

  results = [0, 1, 2]
  while (l := len(results)) < n + 1:
    results.append(results[l - 1] + 2 * results[l - 2] + 3 * results[l - 3])
  return results[n]


def _iterative_deque(n):

  if n < 3:
    return n

  results = deque([0, 1, 2])
  while (l := len(results)) < n + 1:
    results.append(results[l - 1] + 2 * results[l - 2] + 3 * results[l - 3])
  return results[n]


def _iterative_deque_maxlen(n):

  if n < 3:
    return n

  results = deque([0, 1, 2], maxlen=3)
  for _ in range(n - 2):
    results.append(results[2] + 2 * results[1] + 3 * results[0])

  return results[2]


def _iterative_deque_caching(n):

  if n < 3:
    return n

  results = deque([0, 1, 2])

  @cache
  def get(idx):
    return results[idx]

  while (l := len(results)) < n + 1:
    results.append(get(l - 1) + 2 * get(l - 2) + 3 * get(l - 3))
  return results[n]


def _iterative_dict(n):

  if n < 3:
    return n

  results = {0: 0, 1: 1, 2: 2}
  while (l := len(results)) < n + 1:
    results[l] = results[l - 1] + 2 * results[l - 2] + 3 * results[l - 3]
  return results[n]


def _iterative_no_collection(n):

  if n < 3:
    return n

  (a, b, c) = (0, 1, 2)
  for _ in range(n - 2):
    (a, b, c) = (b, c, c + 2 * b + 3 * a)
  return c


def get_args():

  ap = ArgumentParser()
  add = ap.add_argument

  add(
    '-a', '--all', action='store_true',
    help='do not skip functions that are expected to take a long time',
  )
  add(
    '-m', '--min', type=int, default=-30,
    help='minimum value',
  )
  add(
    '-M', '--max', type=int, default=30,
    help='maximum value',
  )

  args = ap.parse_args()
  if args.max < args.min:
    ap.error('--max must be greater than --min')

  return args


if __name__ == '__main__':
  main(**vars(get_args()))
