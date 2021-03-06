import ray

import numpy as np

# Test simple functionality

@ray.remote([int, int], [int, int])
def handle_int(a, b):
  return a + 1, b + 1

# Test aliasing

@ray.remote([], [np.ndarray])
def test_alias_f():
  return np.ones([3, 4, 5])

@ray.remote([], [np.ndarray])
def test_alias_g():
  return test_alias_f.remote()

@ray.remote([], [np.ndarray])
def test_alias_h():
  return test_alias_g.remote()

# Test timing

@ray.remote([], [])
def empty_function():
  pass

@ray.remote([], [int])
def trivial_function():
  return 1

# Test keyword arguments

@ray.remote([int, str], [str])
def keyword_fct1(a, b="hello"):
  return "{} {}".format(a, b)

@ray.remote([str, str], [str])
def keyword_fct2(a="hello", b="world"):
  return "{} {}".format(a, b)

@ray.remote([int, int, str, str], [str])
def keyword_fct3(a, b, c="hello", d="world"):
  return "{} {} {} {}".format(a, b, c, d)

# Test variable numbers of arguments

@ray.remote([int], [str])
def varargs_fct1(*a):
  return " ".join(map(str, a))

@ray.remote([int, int], [str])
def varargs_fct2(a, *b):
  return " ".join(map(str, b))

try:
  @ray.remote([int], [])
  def kwargs_throw_exception(**c):
    return ()
  kwargs_exception_thrown = False
except:
  kwargs_exception_thrown = True

try:
  @ray.remote([int, str, int], [str])
  def varargs_and_kwargs_throw_exception(a, b="hi", *c):
    return "{} {} {}".format(a, b, c)
  varargs_and_kwargs_exception_thrown = False
except:
  varargs_and_kwargs_exception_thrown = True

# test throwing an exception

@ray.remote([], [])
def throw_exception_fct1():
  raise Exception("Test function 1 intentionally failed.")

@ray.remote([], [int])
def throw_exception_fct2():
  raise Exception("Test function 2 intentionally failed.")

@ray.remote([float], [int, str, np.ndarray])
def throw_exception_fct3(x):
  raise Exception("Test function 3 intentionally failed.")

# test Python mode

@ray.remote([], [np.ndarray])
def python_mode_f():
  return np.array([0, 0])

@ray.remote([np.ndarray], [np.ndarray])
def python_mode_g(x):
  x[0] = 1
  return x

# test no return values

@ray.remote([], [])
def no_op():
  pass

@ray.remote([], [])
def no_op_fail():
  return 0

# test wrong return types

@ray.remote([], [int])
def test_return1():
  return 0.0

@ray.remote([], [int, float])
def test_return2():
  return 2.0, 3.0
