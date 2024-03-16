#!/usr/bin/env python3
#
# $ ./recursion.py -m -30 -M 30
#
#   iterative_no_collection :  0.000079687684774 sec
#   iterative_deque_maxlen  :  0.000142939388752 sec
#   iterative_dict          :  0.000156778842211 sec
#   iterative_list          :  0.000160545110703 sec
#   iterative_deque         :  0.000170182436705 sec
#   recursive_caching       :  0.000232491642237 sec
#   iterative_deque_caching :  0.000422552227974 sec
#   recursive               : 12.339210778474808 sec
#
# $ ./recursion.py -m -400 -M 400
#
#   iterative_no_collection : 0.01620534434914589 sec
#   iterative_deque_maxlen  : 0.02222696319222450 sec
#   iterative_list          : 0.03143409639596939 sec
#   iterative_deque         : 0.03188804164528847 sec
#   iterative_dict          : 0.03405065461993218 sec
#   recursive_caching       : 0.03834217041730881 sec
#   iterative_deque_caching : 0.04966166242957115 sec


from argparse import ArgumentParser
from collections import deque
from functools import cache
from math import inf
from time import perf_counter

from tqdm import tqdm


def main(all_, min_, max_, quiet):

  times = {
    func: 0
    for (name, func) in globals().items()
    if (
      callable(func)
      and name.startswith('_')
      and not name.startswith('__')
      and (all_ or max_ <= getattr(func, 'skip_after', inf))
    )
  }

  if not quiet:
    progress = tqdm(total=max_ - min_ + 1)

  for n in range(min_, max_ + 1):
    results = {}
    for func in times:
      try:
        func.cache_clear()
      except AttributeError:
        pass
      (result, sec) = time_it(func, n)
      if results and result != (expected := next(iter(results.values()))):
        done = [f.__name__ for (f, sec) in times.items() if sec > 0]
        assert False, '\n'.join((
          '',
          f'  observed: f({n}) = {result} from {func.__name__}',
          f'  expected: f({n}) = {expected} from {", ".join(sorted(done))}',
        ))
      results[func] = result
      times[func] += sec
    if not quiet:
      progress.update()

  progress.close()

  longest = max((func.__name__.strip("_") for func in times), key=len)
  fmt = '{:%ds} : {:.9f} sec' % len(longest)
  for (func, sec) in sorted(times.items(), key=lambda x: x[1]):
    print(fmt.format(func.__name__.strip("_"), sec))


def skip_after(limit):
  def decorator(func):
    func.skip_after = limit
    return func
  return decorator


def time_it(func, *args, **kwargs):

  start = perf_counter()
  result = func(*args, **kwargs)
  return (result, perf_counter() - start)


@skip_after(30)
def _recursive(n):

  if n < 3:
    return n
  return _recursive(n - 1) + 2 * _recursive(n - 2) + 3 * _recursive(n - 3)


@cache
@skip_after(499)
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
    '-a', '--all', action='store_true', dest='all_',
    help='do not skip functions that are expected to take a long time',
  )
  add(
    '-m', '--min', type=int, default=-30, dest='min_',
    help='minimum value',
  )
  add(
    '-M', '--max', type=int, default=30, dest='max_',
    help='maximum value',
  )
  add(
    '-q', '--quiet', action='store_true',
    help='hide progress bar',
  )

  args = ap.parse_args()
  if args.max_ < args.min_:
    ap.error('--max must be greater than --min')

  return args


if __name__ == '__main__':
  main(**vars(get_args()))
