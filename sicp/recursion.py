#!/usr/bin/env python3
#
# $ ./recursion.py -m -30 -M 30
#
#   recursive_caching       :  0.000045776367188 sec
#   iterative_dict          :  0.000144243240356 sec
#   iterative               :  0.000149965286255 sec
#   iterative_deque         :  0.000154018402100 sec
#   iterative_deque_caching :  0.000386714935303 sec
#   recursive               : 11.924983739852905 sec
#
# $ ./recursion.py -m -400 -M 400
#
#   recursive_caching       : 0.0004036426544189453 sec
#   iterative               : 0.025094270706176758 sec
#   iterative_deque         : 0.025687694549560547 sec
#   iterative_dict          : 0.027811527252197266 sec
#   iterative_deque_caching : 0.04084444046020508 sec


from argparse import ArgumentParser
from collections import deque
from functools import cache
from time import time


def main(all, min, max):

  times = {
    func: 0
    for (func, skip) in SKIP_WHEN.items()
    if all or skip is None or max <= skip
  }

  for n in range(min, max + 1):
    results = {}
    for func in times:
      (result, sec) = timeit(func, n)
      if results:
        assert result == next(iter(results.values()))
      results[func] = result
      times[func] += sec

  for (func, sec) in sorted(times.items(), key=lambda x: x[1]):
    print(f'{func.__name__} : {sec} sec')


def timeit(func, *args, **kwargs):

  start = time()
  result = func(*args, **kwargs)
  return (result, time() - start)


def recursive(n):

  if n < 3:
    return n
  return recursive(n - 1) + 2 * recursive(n - 2) + 3 * recursive(n - 3)


@cache
def recursive_caching(n):

  if n < 3:
    return n
  return (
    recursive_caching(n - 1)
    + 2 * recursive_caching(n - 2)
    + 3 * recursive_caching(n - 3)
  )


def iterative(n):

  if n < 3:
    return n

  results = [0, 1, 2]
  while (l := len(results)) < n + 1:
    results.append(results[l - 1] + 2 * results[l - 2] + 3 * results[l - 3])
  return results[n]


def iterative_deque(n):

  if n < 3:
    return n

  results = deque([0, 1, 2])
  while (l := len(results)) < n + 1:
    results.append(results[l - 1] + 2 * results[l - 2] + 3 * results[l - 3])
  return results[n]


def iterative_deque_caching(n):

  if n < 3:
    return n

  results = deque([0, 1, 2])

  @cache
  def get(idx):
    return results[idx]

  while (l := len(results)) < n + 1:
    results.append(get(l - 1) + 2 * get(l - 2) + 3 * get(l - 3))
  return results[n]


def iterative_dict(n):

  if n < 3:
    return n

  results = {0: 0, 1: 1, 2: 2}
  while (l := len(results)) < n + 1:
    results[l] = results[l - 1] + 2 * results[l - 2] + 3 * results[l - 3]
  return results[n]


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


SKIP_WHEN = {
  iterative: None,
  iterative_deque: None,
  iterative_deque_caching: None,
  iterative_dict: None,
  recursive: 30,
  recursive_caching: None,
}


if __name__ == '__main__':
  main(**vars(get_args()))
