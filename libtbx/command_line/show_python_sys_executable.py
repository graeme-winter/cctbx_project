from __future__ import division
from __future__ import print_function
import sys, os

def run(args):
  assert len(args) == 0
  print(os.path.normpath(sys.executable))

if (__name__ == "__main__"):
  run(args=sys.argv[1:])
