def limit1(x, low, high):
  return min(high, max(low, x))

def limit2(x, low, high):
  if low > high: (low, high) = (high, low)
  return min(high, max(low, x))

for x, l, h in itertools.product(range(3), range(3), range(3)):
  print 'x:', x, '  low:', l, '  high:', h, '  limit1:', limit1(x,l,h), '  limit2:', limit2(x,l,h)


'''

x: 0   low: 0   high: 0   limit1: 0   limit2: 0
x: 0   low: 0   high: 1   limit1: 0   limit2: 0
x: 0   low: 0   high: 2   limit1: 0   limit2: 0
x: 0   low: 1   high: 0   limit1: 0   limit2: 0
x: 0   low: 1   high: 1   limit1: 1   limit2: 1
x: 0   low: 1   high: 2   limit1: 1   limit2: 1
x: 0   low: 2   high: 0   limit1: 0   limit2: 0
x: 0   low: 2   high: 1   limit1: 1   limit2: 1
x: 0   low: 2   high: 2   limit1: 2   limit2: 2
x: 1   low: 0   high: 0   limit1: 0   limit2: 0
x: 1   low: 0   high: 1   limit1: 1   limit2: 1
x: 1   low: 0   high: 2   limit1: 1   limit2: 1
x: 1   low: 1   high: 0   limit1: 0   limit2: 1
x: 1   low: 1   high: 1   limit1: 1   limit2: 1
x: 1   low: 1   high: 2   limit1: 1   limit2: 1
x: 1   low: 2   high: 0   limit1: 0   limit2: 1
x: 1   low: 2   high: 1   limit1: 1   limit2: 1
x: 1   low: 2   high: 2   limit1: 2   limit2: 2
x: 2   low: 0   high: 0   limit1: 0   limit2: 0
x: 2   low: 0   high: 1   limit1: 1   limit2: 1
x: 2   low: 0   high: 2   limit1: 2   limit2: 2
x: 2   low: 1   high: 0   limit1: 0   limit2: 1
x: 2   low: 1   high: 1   limit1: 1   limit2: 1
x: 2   low: 1   high: 2   limit1: 2   limit2: 2
x: 2   low: 2   high: 0   limit1: 0   limit2: 2
x: 2   low: 2   high: 1   limit1: 1   limit2: 2
x: 2   low: 2   high: 2   limit1: 2   limit2: 2


'''