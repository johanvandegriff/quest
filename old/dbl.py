#!/usr/bin/python
import itertools

def doublerange(xlen, ylen=0):
  if ylen == 0 and xlen.__class__ in [tuple, list]:
    return doublerange(xlen[0], xlen[1])
  return itertools.product(range(xlen), range(ylen))

def get23():
  return 2,3

for x, y in doublerange(2,3):
  print x, y

print
print get23()
print

for x, y in doublerange(get23()):
  print x, y
