from cctbx import sgtbx
from cctbx.sgtbx.direct_space_asu import cut_plane
from scitbx import matrix
import sys

class direct_space_asu:

  def __init__(self, hall_symbol, facets=[]):
    self.hall_symbol = hall_symbol
    self.facets = facets[:]

  def __copy__(self):
    return direct_space_asu(
      hall_symbol=self.hall_symbol,
      facets=self.facets)

  def __and__(self, obj):
    self.facets.append(obj)
    return self

  def show_summary(self, f=None):
    if (f == None): f = sys.stdout
    print >> f, "Hall symbol:", self.hall_symbol
    print >> f, "Number of facets:", len(self.facets)
    return self

  def show_comprehensive_summary(self, f=None):
    if (f == None): f = sys.stdout
    self.show_summary(f)
    for facet in self.facets:
      print "    &", facet
    return self

  def is_inside(self, point, volume_only=00000):
    if (volume_only):
      for facet in self.facets:
        if (facet.evaluate(point) < 0): return 00000
    else:
      for facet in self.facets:
        if (not facet.is_inside(point)): return 00000
    return 0001

  def in_which_facets(self, point):
    result = []
    for facet in self.facets:
      if (facet.evaluate(point) == 0):
        result.append(facet)
    return result

  def volume_only(self):
    result = direct_space_asu(self.hall_symbol)
    for facet in self.facets:
      result.facets.append(facet.strip())
    return result

  def volume_vertices(self):
    from cctbx.sgtbx.direct_space_asu import facet_analysis
    return facet_analysis.volume_vertices(self)

  def _box_corner(self, volume_vertices, min_or_max):
    if (volume_vertices is None):
      volume_vertices = self.volume_vertices()
    if (len(volume_vertices) == 0):
      return None
    result = list(volume_vertices[0])
    for vertex in volume_vertices[1:]:
      for i in xrange(3):
        result[i] = min_or_max(result[i], vertex[i])
    return result

  def box_min(self, volume_vertices=None):
    return self._box_corner(volume_vertices, min)

  def box_max(self, volume_vertices=None):
    return self._box_corner(volume_vertices, max)

  def add_plane(self, normal_direction, point=None):
    if (point is None):
      point = self.box_min()
    self.facets.append(cut_plane.cut(
      n=normal_direction,
      c=-(matrix.col(normal_direction).dot(matrix.col(point)))))

  def add_planes(self, normal_directions, point=None, both_directions=00000):
    if (point is None):
      point = self.box_min()
    for normal_direction in normal_directions:
      self.add_plane(normal_direction=normal_direction, point=point)
      if (both_directions):
        self.facets.append(-self.facets[-1])

  def change_basis(self, cb_op):
    if (not isinstance(cb_op, sgtbx.change_of_basis_op)):
      cb_op = sgtbx.change_of_basis_op(cb_op)
    cb_hall_symbol = None
    if (self.hall_symbol is not None):
      space_group_info = sgtbx.space_group_info("Hall: " + self.hall_symbol)
      cb_space_group_info = space_group_info.change_basis(cb_op)
      cb_hall_symbol = cb_space_group_info.type().hall_symbol()
    cb_asu = direct_space_asu(cb_hall_symbol)
    for facet in self.facets:
      cb_asu.facets.append(facet.change_basis(cb_op))
    return cb_asu

  def define_metric(self, unit_cell):
    import cctbx.crystal.direct_space_asu
    return cctbx.crystal.direct_space_asu.direct_space_asu(
      asu=self, unit_cell=unit_cell)

  def add_buffer(self, unit_cell, thickness=None, relative_thickness=None):
    return self.define_metric(unit_cell).add_buffer(
      thickness=thickness,
      relative_thickness=relative_thickness)
