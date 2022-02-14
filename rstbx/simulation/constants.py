from __future__ import absolute_import, division, print_function

electron_radius = 2.818e-15  # classical electron radius in meters

plank_constant = 6.62606896e-34  # Joule-seconds

speed_of_light = 299792458.0e0  # meters/second

Joules_per_eV = 1.602176487e-19

# conversion factor from inverse meters to eV:
eV_per_inv_meter = speed_of_light * plank_constant * 1.0 / (Joules_per_eV)
