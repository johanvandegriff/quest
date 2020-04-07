def range2(start, stop=None, step=1):
  if stop is None:
    stop = start
    start = 0
  return xrange(start, stop, step)


def range(start, stop=None, step=1):
  if stop is None:
    stop = start
    start = 0
  else:
    stop = int(stop)
  start = int(start)
  step = int(step)
  while start < stop:
    yield start
    start += step
