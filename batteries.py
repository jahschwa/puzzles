#!/usr/bin/env python3
#
# You have 8 batteries, only 4 of which work. They are otherwise
# indistinguishable. Your flashlight takes 2 batteries. It only turns on at all
# if both batteries work. Inserting 2 batteries at a time is therefore your only
# way to test them. How many times must you insert different batteries to
# guarantee the flashlight turns on?


from argparse import ArgumentParser
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from math import inf
from statistics import mean, median, mode, stdev
from string import ascii_uppercase


CUSTOM_NAME = 'CUSTOM'

SOLUTIONS = {

  'dumb_brute_force': [
    'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH',
    'BA', 'BC', 'BD', 'BE', 'BF', 'BG', 'BH',
    'CA', 'CB', 'CD', 'CE', 'CF', 'CG', 'CH',
    'DA', 'DB', 'DC', 'DE', 'DF', 'DG', 'DH',
    'EA', 'EB', 'EC', 'ED', 'EF', 'EG', 'EH',
    'FA', 'FB', 'FC', 'FD', 'FE', 'FG', 'FH',
    'GA', 'GB', 'GC', 'GD', 'GE', 'GF', 'GH',
  ],

  'no_dupes_brute_force': [
    'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH',
    'BC', 'BD', 'BE', 'BF', 'BG', 'BH',
    'CD', 'CE', 'CF', 'CG', 'CH',
    'DE', 'DF', 'DG', 'DH',
    'EF', 'EG', 'EH',
    'FG', 'FH',
    'GH',
  ],

  'andrew_drop_two_fails': [
    'AB', 'CD', 'BC', 'AD', 'AC', 'BD', 'EF',
  ],

  'andrew_drop_two_works': [
    'AB', 'AC', 'AD', 'AE', 'AF',  # 6 batteries have at least 2 good
    'BC', 'BD', 'BE', 'BF',        # so we can just try every combo in the 6
    'CD', 'CE', 'CF',
    'DE', 'DF',
    'EF',
  ],

  'half_two_good': [
    'AB', 'CD', 'EF', 'GH',  # each pair now has exactly 1 good
    'AC', 'AD', 'BC', 'BD',  # so 2 pairs have 2 good; brute force them
  ],

  'half_eliminate': [
    'AB', 'AC', 'AD', 'BC', 'BD', 'CD',  # these 4 now have either 0 or 1 good
    'EF', 'GH',                          # the others have either 3 or 4 good
  ],

  'by_threes': [
    'AB', 'AC', 'BC',  # these 3 now have 0 or 1 good
    'DE', 'EF', 'DF',  # both groups of 3 have exactly 1 good
    'GH',              # the last 2 must both be good
  ],
}


def main(detail=False, solution=None, name=CUSTOM_NAME, verbose=False):

  if solution:
    SOLUTIONS[name] = solution

  max_name_len = len(max(SOLUTIONS, key=len))
  print(max_name_len * ' ' + ' | ' + Solution.HEADER)
  print(
    max_name_len * '-'
    + '-+-'
    + '-+-'.join(width * '-' for width in Solution.COLUMNS.values())
  )

  name_fmt = f'{{:<{max_name_len}}} | '
  for (name, algorithm) in SOLUTIONS.items():
    print(name_fmt.format(name), end='')
    solution = Solution(name, algorithm)
    solution.analyze()
    solution.explain(
      header=False,
      measure_names=False,
      detail=detail,
      verbose=verbose,
    )


@dataclass
class Battery:
  name: str
  good: bool = False

  def __bool__(self):

    return self.good


@dataclass
class Pair:
  batt1: Battery
  batt2: Battery

  def __post_init__(self):

    self.name = ''.join(sorted([self.batt1.name, self.batt2.name]))

  def __bool__(self):

    return bool(self.batt1 and self.batt2)


class Solution:

  COLUMNS = {
    'Worst': 5,
    'Mean': 5,
    'Stdev': 5,
    'Median': 6,
    'Mode': 4,
  }
  HEADER = ' | '.join(
    '{{:>{}}}'.format(width).format(col)
    for (col, width) in COLUMNS.items()
  )

  def __init__(self, name, test_order, batteries=8, good=4):

    self.name = name
    self.batteries = {c: Battery(c) for c in ascii_uppercase[:batteries]}
    self.good = good
    self.test_order = []
    for pair in test_order:
      self.test_order.append(
        Pair(self.batteries[pair[0]], self.batteries[pair[1]])
      )
    self.results = {}

  def analyze(self):

    if not self.results:

      last = None
      for good in combinations(self.batteries.values(), self.good):
        trial_name = ''.join(batt.name for batt in good)

        if last:
          for batt in last:
            batt.good = False
        for batt in good:
          batt.good = True

        for (i, pair) in enumerate(self.test_order):
          if pair:
            self.results[trial_name] = i + 1
            break
        else:
          self.results[trial_name] = inf

        last = good

    return self.results

  def explain(
    self,
    header=True,
    measure_names=True,
    failed=True,
    detail=False,
    verbose=False,
  ):

    if not self.results:
      self.analyze()

    if header:
      print(f'===== {self.name} =====')
    if measure_names:
      print(self.HEADER + ' = ', end='')

    vals = self.results.values()
    try:
      sd = stdev(vals)
    except OverflowError:
      sd = inf

    print(
        f'{max(vals):5.0f} | {mean(vals):5.2f} | {sd:5.2f}'
      f' | {median(vals):6.1f} | {mode(vals):4.0f}'
    )

    if failed:
      failed = []
      for (name, tests) in self.results.items():
        if tests is inf:
          failed.append(name)
      if failed:
        print(f'    FAILED {len(failed)}: ' + ', '.join(sorted(failed)))

    if detail:
      counts = Counter()
      for count in self.results.values():
        counts[count] += 1
      print(
        '    FREQ: {}'.format(
          ', '.join(
            f'{tests}={count}' for (tests, count) in sorted(counts.items())
          )
        )
      )

    if verbose:
      print('    ALL RESULTS:')
      for (name, tests) in sorted(self.results.items()):
        print(f'        {name}={tests}')


def parse_solution(s):

  pairs = []
  for pair in s.split(','):
    if len(pair := pair.strip()) != 2:
      raise ValueError(f'pair "{pair}" is not 2 characters')
    pairs.append(pair)

  return pairs


def get_args():

  ap = ArgumentParser()
  add = ap.add_argument

  add(
    '-d', '--detail', action='store_true',
    help='show detailed stats about test counts',
  )
  add(
    '-s', '--solution', type=parse_solution,
    help='analyze a solution (e.g. "AB,AC,...")',
  )
  add(
    '-S', '--name', default=CUSTOM_NAME,
    help='name to use when displaying --solution (default: CUSTOM)',
  )
  add(
    '-v', '--verbose', action='store_true',
    help='show all individual test counts',
  )

  args = ap.parse_args()
  if args.verbose:
    args.detail = True

  return args


if __name__ == '__main__':
  main(**vars(get_args()))
