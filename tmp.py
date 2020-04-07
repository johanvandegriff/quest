#!/usr/bin/python

def memoize(f):
  m = {}
  def h(*x):
    if x not in m:
      m[x] = f(*x)
      print m
    return m[x]
  h.__name__ = f.__name__
  return h

def plus1(f):
  def h(x):
    return x *2
  return h

def strings(f):
  def h(x):
    return str(x) + "hi"
  return h

@memoize
def fib2(a, b):
  if a == 0:
    return 0
  if a == 1:
    return 1
  return fib2(a-1, b) + fib2(a-2, b) + b

print fib2(4,5)
print fib2(2,2)
print fib2.__name__