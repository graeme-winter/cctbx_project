from __future__ import division
from __future__ import print_function
def run():
  try: import numpy
  except ImportError: print("None")
  else: print(numpy.__version__)

if (__name__ == "__main__"):
  run()
