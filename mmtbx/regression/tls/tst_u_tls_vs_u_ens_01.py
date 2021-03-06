from __future__ import division
from mmtbx.tls import tools
import math
import time

pdb_str_1 = """
CRYST1   10.000   10.000   10.000  90.00  90.00  90.00 P1
ATOM      1  CA  THR A   6       0.000   0.000   0.000  1.00  0.00           C
ATOM      1  CA  THR B   6       3.000   0.000   0.000  1.00  0.00           C
"""

pdb_str_2 = """
CRYST1   10.000   10.000   10.000  90.00  90.00  90.00 P1
ATOM      1  CA  THR A   6       0.000   0.000   0.000  1.00  0.00           C
ATOM      1  CA  THR B   6       0.000   3.000   0.000  1.00  0.00           C
"""

pdb_str_3 = """
CRYST1   10.000   10.000   10.000  90.00  90.00  90.00 P1
ATOM      1  CA  THR A   6       0.000   0.000   0.000  1.00  0.00           C
ATOM      1  CA  THR B   6       0.000   0.000   3.000  1.00  0.00           C
"""

pdb_str_4 = """
CRYST1   10.000   10.000   10.000  90.00  90.00  90.00 P1
ATOM      1  CA  THR A   6       0.000   0.000   0.000  1.00  0.00           C
ATOM      1  CA  THR B   6       1.000   2.000   3.000  1.00  0.00           C
"""

def exercise_01():
  sqrt = math.sqrt
  ls = []
  ls.append( [(sqrt(2)/2, sqrt(2)/2, 0), (-sqrt(2)/2, sqrt(2)/2, 0), (0,0,1)] )
  ls.append( [(1,0,0), (0, sqrt(2)/2, sqrt(2)/2), (0, -sqrt(2)/2, sqrt(2)/2)] )
  ls.append( [(sqrt(3)/2, 1/2, 0), (-1/2, sqrt(3)/2, 0), (0,0,1)] )
  ls.append( [(1,0,0), (0, sqrt(3)/2, 1/2), (0, -1/2, sqrt(3)/2)] )
  for pdb_str in [pdb_str_1, pdb_str_2, pdb_str_3, pdb_str_4]:
    for ls_ in ls:
      lx,ly,lz = ls_
      print lx,ly,lz
      tools.u_tls_vs_u_ens(pdb_str=pdb_str,
          dx=0.05,dy=0.06,dz=0.07,
          sx=0.5, sy=0.4, sz=0.3,
          lx=lx, ly=ly, lz=lz)

if (__name__ == "__main__"):
  t0 = time.time()
  exercise_01()
  print "Time: %6.4f"%(time.time()-t0)
  print "OK"
