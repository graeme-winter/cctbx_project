from __future__ import division
from __future__ import absolute_import
from . import gcd
from boost.rational import lcm
import sys

def run(args):
  gcd.run(args=args, func=lcm)

if (__name__ == "__main__"):
  run(sys.argv[1:])
