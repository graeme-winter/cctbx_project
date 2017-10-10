from __future__ import division
from __future__ import print_function
from builtins import range
import os

#for integration pickles:
allowable_basename_endings = ["_00000.pickle",
                              ".pickle",
                              "_refined_experiments.json",
                              "_experiments.json"
                             ]
def is_odd_numbered(file_name):
  for allowable in allowable_basename_endings:
    if (file_name.endswith(allowable)):
      try:
        return int(os.path.basename(file_name).split(allowable)[0][-1])%2==1
      except ValueError:
        file_name = os.path.basename(file_name).split(allowable)[0]
        break
  #can not find standard filename extension, instead find the last digit:
  for idx in range(1,len(file_name)+1):
    if file_name[-idx].isdigit():
      return int(file_name[-idx])%2==1
  raise ValueError
if __name__=="__main__":
  print(is_odd_numbered("int_fake_19989.img"))
