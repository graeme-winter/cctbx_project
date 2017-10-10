from __future__ import division
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from cctbx.web import cgi_utils
import pydoc
import cgi
from io import StringIO
import sys

def interpret_form_data(form):
  inp = cgi_utils.inp_from_form(form,
     (("query", ""),))
  return inp

def run(server_info, inp, status):
  print("<pre>")
  sys.argv = ["libtbx.help"] + inp.query.split()
  s = StringIO()
  sys.stdout = s
  pydoc.cli()
  sys.stdout = sys.__stdout__
  s = s.getvalue()
  sys.stdout.write(cgi.escape(s))
  print("</pre>")
