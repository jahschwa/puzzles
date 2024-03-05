#!/usr/bin/env python3

from functools import cache


def main():

  for n in range(-10, 11):
    assert recursive(n) == iterative(n)
  print('OK!')


@cache
def recursive(n):

  if n < 3:
    return n
  return recursive(n - 1) + 2 * recursive(n - 2) + 3 * recursive(n - 3)


def iterative(n):

  if n < 3:
    return n

  results = [0, 1, 2]
  while (l := len(results)) < n + 1:
    results.append(results[l - 1] + 2 * results[l - 2] + 3 * results[l - 3])
  return results[n]


if __name__ == '__main__':
  main()
