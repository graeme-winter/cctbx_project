from __future__ import division

from future import standard_library
standard_library.install_aliases()
from builtins import object
from libtbx.scheduling import result

try:
  import pickle as pickle
except ImportError:
  import pickle


class Server(object):
  """
  Communication server
  """

  def __init__(self, instream, outstream, environment):

    self.instream = instream
    self.outstream = outstream
    self.environment = environment
    self.active = True


  def serve(self):

    while self.active:
      command = pickle.load( self.instream )

      try:
        response = command( server = self )

      except Exception as e:
        pickle.dump( result.Error( exception = e ), self.outstream, 0 )

      else:
        pickle.dump( result.Success( value = response ), self.outstream, 0 )

      self.outstream.flush()


class Command(object):
  """
  Command that operates on the environment
  """

  def __call__(self, server):

    return self.process( environment = server.environment )


def ShutDown(server):

  server.environment.shutdown()
  server.active = False
  return True


class Client(object):
  """
  Communication client
  """

  def __init__(self, instream, outstream):

    self.instream = instream
    self.outstream = outstream


  def send(self, command):

    pickle.dump( command, self.outstream, 0 )
    self.outstream.flush()
    return pickle.load( self.instream )


  def close(self):

    return self.send( command = ShutDown )

