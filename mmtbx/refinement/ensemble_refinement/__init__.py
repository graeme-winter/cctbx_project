from __future__ import division
import sys, os, time, math, random, cPickle, gzip
from cctbx.array_family import flex
from cctbx import adptbx
from iotbx.option_parser import iotbx_option_parser
from libtbx.utils import Sorry, user_plus_sys_time, multi_out, show_total_time
from iotbx import reflection_file_utils
from libtbx.str_utils import format_value
import libtbx.load_env
import iotbx
from mmtbx import utils
from iotbx import pdb
from cStringIO import StringIO
import mmtbx.model
from mmtbx.dynamics import ensemble_cd
import iotbx.phil
from libtbx import adopt_init_args
import mmtbx.solvent.ensemble_ordered_solvent as ensemble_ordered_solvent
from cctbx import miller
from mmtbx.refinement.ensemble_refinement import ensemble_utils
import scitbx.math
from cctbx import xray
from cctbx import geometry_restraints
import mmtbx.maps
master_params = iotbx.phil.parse("""\
ensemble_refinement {
  cartesian_dynamics {
    temperature = 300
      .type = float
    protein_thermostat = True
      .type = bool
      .help = Use protein atoms sthermostat
    number_of_steps = 10
      .type = int
    time_step = 0.0005
      .type = float
      .help = Time in ps
    initial_velocities_zero_fraction = 0
      .type = float
    n_print = 100
      .type = int
    verbose = -1
      .type = int
  }
  verbose = -1
    .type = int
  output_file_prefix = ensemble_refinement
    .type = str
  random_seed = 2679941
    .type = int
    .help = set random seed
  pdb_stored_per_block = 100
    .type = int
    .help = Number of structures stored during simulation
  equilibrium_n_tx = 10
    .type = int
  acquisition_block_n_tx = 2
    .type = int
  number_of_acquisition_periods = 10
    .type = int
    .help = Number of acquisition periods
  tx = None
    .type = float
    .help = relaxation time (ps)
  wxray = 1.0
    .type = float
    .help = multiplier for xray weighting
  wxray_coupled_tbath = True
    .type = bool
  wxray_coupled_tbath_offset = 2.5
    .type = float
  tls_group_selections = None
    .type = str
    .multiple = True
    .help = Uses TLS groups as defined here (TLS details in PDB header not used)
  ptls = 0.80
    .type = float
    .help = fraction of atoms to include in TLS fitting
  max_ptls_cycles = 10
    .type = int
  set_occupancies = True
    .type = bool
  target_name = *ml ls_wunit_k1_fixed ls_wunit_k1
    .type = choice
    .help = target function
  update_rescale_normalisation_factors_scale_kn = True
    .type = bool
    .help = scale <Ncalc> to starting Ncalc
  high_resolution = None
    .type = float
    .help = high res limit
  low_resolution = None
    .type = float
    .help = low res limit
  er_harmonic_restraints_selections = None
    .type = str
    .help = atom numbers for ta specific harmonic restraints e.g. (1231 1232 1233)
  er_harmonic_restraints_weight = 0.001
    .type = float
    .help = weight for ta specific harmonic function
  er_harmonic_restraints_slack = 1.0
    .type = float
    .help = slack distance for ta specific harmonic function
  output_running_kinetic_energy_in_occupancy_column = False
    .type = bool
    .help = Output PDB file contains running kinetic energy in place of occupancy
  electron_density_maps {
    apply_default_maps = True
      .type = bool
        map_coefficients
      .multiple = True
    {
      map_type = None
        .type = str
      format = *mtz phs
        .type = choice(multi=True)
      mtz_label_amplitudes = None
        .type = str
      mtz_label_phases = None
        .type = str
      kicked = False
        .type = bool
      fill_missing_f_obs = False
        .type = bool
      acentrics_scale = 2.0
        .type = float
      centrics_pre_scale = 1.0
        .type = float
      sharpening = False
        .type = bool
        .help = Apply B-factor sharpening
      sharpening_b_factor = None
        .type = float
      exclude_free_r_reflections = False
        .type = bool
      isotropize = True
        .type = bool
      resharp_after_isotropize = False
        .type = bool
      dev
        .expert_level=3
      {
        complete_set_up_to_d_min = False
          .type = bool
        aply_same_incompleteness_to_complete_set_at = randomly low high
          .type = choice(multi=False)
        }
      }
    }
  mask {
    use_asu_masks = True
    .type = bool
    solvent_radius = 1.11
      .type = float
    shrink_truncation_radius = 0.9
      .type = float
    grid_step_factor = 4.0
      .type = float
      .help = The grid step for the mask calculation is determined as \
              highest_resolution divided by grid_step_factor. This is considered \
              as suggested value and may be adjusted internally based on the \
              resolution.
    verbose = 1
      .type = int
      .expert_level=3
    mean_shift_for_mask_update = 0.1
      .type = float
      .help = Value of overall model shift in refinement to updates the mask.
      .expert_level=2
    ignore_zero_occupancy_atoms = True
      .type = bool
      .help = Include atoms with zero occupancy into mask calculation
    ignore_hydrogens = False
      .type = bool
      .help = Ignore H or D atoms in mask calculation
    n_radial_shells = 1
    .type = int
    .help = Number of shells in a radial shell bulk solvent model
    radial_shell_width = 1.5
      .type = float
      .help = Radial shell width TODO: default 2.5?
    }
  at_start_apply_back_trace_of_b_cart = False
    .type = bool
  ordered_solvent_update = True
    .type = bool
    .help = Ordered water molecules automatically updated every nth macro cycle
  ordered_solvent_update_cycle = 25
    .type = int
    .help = Number of macro-cycles / ordered solvent update
  ensemble_ordered_solvent {
    tolerance = 1.0
      .type = float
    ordered_solvent_map_to_model = True
      .type = bool
    reset_all = False
      .type = bool
      .help = Removes all water atoms prior to re-picking using mFobs-DFmodel and 2mFobs-DFmodel
    output_residue_name = HOH
      .type=str
      .input_size = 50
    output_chain_id = S
      .type=str
      .input_size = 50
    output_atom_name = O
      .type=str
      .input_size = 50
    scattering_type = O
      .type=str
      .help = Defines scattering factors for newly added waters
      .expert_level=2
      .input_size = 50
    primary_map_type = mFo-DFmodel
      .type=str
    primary_map_cutoff = 1.0
      .type=float
    secondary_map_type = 2mFo-DFmodel
      .type=str
    secondary_map_cutoff_keep = 3.0
      .type=float
    secondary_map_cutoff_find = 3.0
      .type=float
    h_bond_min_mac = 1.8
      .type = float
      .short_caption = H-bond minimum for solvent-model
      .expert_level = 1
    h_bond_min_sol = 1.8
      .type = float
      .short_caption = H-bond minimum for solvent-solvent
      .expert_level = 1
    h_bond_max = 3.2
      .type = float
      .short_caption = Maximum H-bond length
      .expert_level = 1
    new_solvent = *isotropic anisotropic
      .type = choice
      .help = Based on the choice, added solvent will have isotropic or \
              anisotropic b-factors
      .short_caption = New solvent ADP type
      .expert_level = 1
    b_iso_min = 0.0
      .type=float
      .help = Minimum B-factor value, waters with smaller value will be rejected
      .short_caption = Minimum B-factor
      .expert_level = 1
    b_iso_max = 100.0
      .type=float
      .help = Maximum B-factor value, waters with bigger value will be rejected
      .short_caption = Maximum B-factor
      .expert_level = 1
    anisotropy_min = 0.1
      .type = float
      .help = For solvent refined as anisotropic: remove is less than this value
      .short_caption = Minimum anisotropic B-factor
      .expert_level = 1
    b_iso = None
      .type=float
      .help = Initial B-factor value for newly added water
      .short_caption = Initial B-factor value
      .expert_level = 1
    refine_occupancies = False
      .type = bool
      .help = Refine solvent occupancies.
      .expert_level = 1
    occupancy_min = 0.1
      .type=float
      .help = Minimum occupancy value, waters with smaller value will be rejected
      .short_caption = Minimum occupancy
    occupancy_max = 1.0
      .type=float
      .help = Maximum occupancy value, waters with bigger value will be rejected
      .short_caption = Maximum occupancy
    occupancy = 1.0
      .type=float
      .help = Initial occupancy value for newly added water
      .short_caption = Initial occupancy value
    add_hydrogens = False
      .type = bool
      .help = Adds hydrogens to water molecules (except those on special positions)
    refilter = True
      .type = bool
    temperature = 300
      .type = float
      .help = Target temperature for random velocity assignment
    seed = 343534534
      .type = int
      .help = Fixes the random seed for velocity assignment
    preserved_solvent_minimum_distance = 7.0
      .type = float
    find_peaks {
      use_sigma_scaled_maps = True
        .type=bool
        .help = Default is sigma scaled map, map in absolute scale is used \
                otherwise.
      resolution_factor = 1./4.
        .type=float
      map_next_to_model
        .expert_level=2
      {
        min_model_peak_dist = 1.8
          .type=float
        max_model_peak_dist = 3.0
          .type=float
        min_peak_peak_dist = 1.8
          .type=float
        use_hydrogens = True
          .type = bool
      }
      max_number_of_peaks = None
        .type=int
        .expert_level=1
      peak_search
        .expert_level=1
      {
        peak_search_level = 1
          .type=int
        max_peaks = 0
          .type=int
          .short_caption=Maximum peaks
        interpolate = True
          .type=bool
        min_distance_sym_equiv = None
          .type=float
          .short_caption=Minimum distance between symmetry-equivalent atoms
        general_positions_only = False
          .type=bool
        min_cross_distance = 1.8
          .type=float
          .short_caption=Minimum cross distance
        min_cubicle_edge = 5
          .type=float
          .short_caption=Minimum edge length of cubicles used for \
            fast neighbor search
          .expert_level=2
      }
    }
  }
  refinement.geometry_restraints.edits
    {
    excessive_bond_distance_limit = 10
      .type = float
    bond
      .optional = True
      .multiple = True
      .short_caption = Bond
      .style = auto_align
    {
      action = *add delete change
        .type = choice
      atom_selection_1 = None
        .type = atom_selection
        .input_size = 400
      atom_selection_2 = None
        .type = atom_selection
        .input_size = 400
      symmetry_operation = None
        .help = "The bond is between atom_1 and symmetry_operation * atom_2,"
                " with atom_1 and atom_2 given in fractional coordinates."
                " Example: symmetry_operation = -x-1,-y,z"
        .type = str
      distance_ideal = None
        .type = float
      sigma = None
        .type = float
      slack = None
        .type = float
    }
    angle
      .optional = True
      .multiple = True
      .short_caption = Angle
      .style = auto_align
    {
      action = *add delete change
        .type = choice
      atom_selection_1 = None
        .type = atom_selection
        .input_size = 400
      atom_selection_2 = None
        .type = atom_selection
        .input_size = 400
      atom_selection_3 = None
        .type = atom_selection
        .input_size = 400
      angle_ideal = None
        .type = float
      sigma = None
        .type = float
    }
    planarity
      .optional = True
      .multiple = True
      .short_caption = Planarity
      .style = auto_align
    {
      action = *add delete change
        .type = choice
      atom_selection = None
        .type = atom_selection
        .multiple = True
        .input_size = 400
      sigma = None
        .type = float
    }
    scale_restraints
      .multiple = True
      .optional = True
      .help = Apply a scale factor to restraints for specific atom selections, \
        to tighten geometry without changing the overall scale of the geometry \
        target.
    {
      atom_selection = None
        .type = atom_selection
      scale = 1.0
        .type = float
      apply_to = *bond *angle *dihedral *chirality
        .type = choice(multi=True)
      }
    }
  }
""", process_includes=True)

class er_pickle(object):
  def __init__(self,
               pickle_object,
               pickle_filename):
    cPickle.dump(pickle_object, gzip.open(pickle_filename, 'wb'))

class ensemble_refinement_data(object):
  def __init__(self, f_calc_running                      = None,
                     f_calc_data_total                   = None,
                     f_calc_data_current                 = None,
                     f_mask_running                      = None,
                     f_mask_current                      = None,
                     f_mask_total                        = None,
                     total_SF_cntr                       = 0,
                     total_SF_cntr_mask                  = 0,
                     fix_scale_factor                    = None,
                     non_solvent_temp                    = None,
                     solvent_temp                        = None,
                     system_temp                         = None,
                     xray_structures                     = [],
                     pdb_hierarchys                      = [],
                     seed                                = None,
                     velocities                          = None,
                     ke_protein_running                  = None,
                     ke_pdb                              = [],
                     geo_grad_rms                        = None,
                     xray_grad_rms                       = None,
                     solvent_sel                         = None,
                     all_sel                             = None,
                     er_harmonic_restraints_info         = None,
                     er_harmonic_restraints_weight       = 0.001,
                     er_harmonic_restraints_slack        = 1.0
                     ):
    adopt_init_args(self, locals())

class er_tls_manager(object):
  def __init__(self, tls_selection_strings_no_sol       = None,
                     tls_selection_strings_no_sol_no_hd = None,
                     tls_selections_with_sol            = None,
                     tls_selections_no_sol              = None,
                     tls_selections_no_sol_no_hd        = None,
                     tls_operators                      = None):
    adopt_init_args(self, locals())

class run_ensemble_refinement(object):
  def __init__(self, fmodel,
                     model,
                     log,
                     mtz_dataset_original,
                     params):
    adopt_init_args(self, locals())
    self.params = params.extract().ensemble_refinement
    if self.params.electron_density_maps.apply_default_maps != False\
      or len(self.params.electron_density_maps.map_coefficients) == 0:
      maps_par = libtbx.env.find_in_repositories(
        relative_path="cctbx_project/mmtbx/refinement/ensemble_refinement/maps.params",
        test=os.path.isfile)
      maps_par_phil = iotbx.phil.parse(file_name=maps_par)
      working_params = mmtbx.refinement.ensemble_refinement.master_params.fetch(
                          sources = [params]+[maps_par_phil])
      self.params = working_params.extract().ensemble_refinement
      print >> self.log, """Will apply parameters for default map types."""
    if self.params.target_name == 'ml':
      self.fix_scale = False
    else:
      self.fix_scale = True
    if not self.params.wxray_coupled_tbath:
      self.params.wxray_coupled_tbath_offset = 0.0
    self.wxray = self.params.wxray
    self.params.ensemble_ordered_solvent.temperature = self.params.cartesian_dynamics.temperature
    self.ensemble_utils = ensemble_utils.manager(ensemble_obj = self)
    self.xray_gradient = None
    self.fc_running_ave = None
    self.macro_cycle = 1
    self.sf_model_ave = None
    self.fmodel_total_block_list = []
    self.reset_velocities = True
    self.cmremove = True
    self.cdp = self.params.cartesian_dynamics
    self.bsp = mmtbx.bulk_solvent.bulk_solvent_and_scaling.master_params.extract()
    self.bsp.target = self.params.target_name
    if self.params.tx == None:
      print >> log, "\nAutomatically set Tx (parameter not defined)"
      print >> log, "Tx          :  2(1/dmin)**2"
      self.params.tx = round(2.0 * ((1.0/self.fmodel.f_obs().d_min())**2),1)
      print >> log, 'Dmin        : ', self.fmodel.f_obs().d_min()
      print >> log, 'Set Tx      : ', self.params.tx
    self.n_mc_per_tx = self.params.tx / (self.cdp.time_step * self.cdp.number_of_steps)

    # Set simulation length
    utils.print_header("Simulation length:", out = self.log)
    print >> log, "Number of time steps per macro cycle    : ", self.cdp.number_of_steps
    print >> log, "Tx                                      : ", self.params.tx
    print >> log, "Number macro cycles per Tx period       : ", self.n_mc_per_tx
    self.equilibrium_macro_cycles = int(self.n_mc_per_tx * self.params.equilibrium_n_tx)
    self.acquisition_block_macro_cycles = int(self.n_mc_per_tx * self.params.acquisition_block_n_tx)
    self.total_macro_cycles = int(self.equilibrium_macro_cycles \
                            + (self.acquisition_block_macro_cycles * self.params.number_of_acquisition_periods))
    #
    print >> log, "\nEquilibration"
    print >> log, "    Number Tx periods    : ", self.params.equilibrium_n_tx
    print >> log, "    Number macro cycles  : ", self.equilibrium_macro_cycles
    print >> log, "    Time (ps)            : ", self.equilibrium_macro_cycles \
                                                  * self.cdp.number_of_steps * self.cdp.time_step
    #
    print >> log, "\nAcquisition block"
    print >> log, "    Number Tx periods    : ",  self.params.acquisition_block_n_tx
    print >> log, "    Number macro cycles  : ",  self.acquisition_block_macro_cycles
    print >> log, "    Time (ps)            : ",  self.acquisition_block_macro_cycles \
                                                  * self.cdp.number_of_steps\
                                                  * self.cdp.time_step
    #
    print >> log, "\nSimulation total"
    print >> log, "    Number Tx periods    : ", self.params.equilibrium_n_tx\
                                                + (self.params.number_of_acquisition_periods\
                                                   * self.params.acquisition_block_n_tx)
    print >> log, "    Number macro cycles  : ", self.total_macro_cycles
    self.total_time = self.total_macro_cycles\
                        * self.cdp.number_of_steps\
                        * self.cdp.time_step
    print >> log, "    Time (ps)            : ", self.total_time
    print >> log, "    Total = Equilibration + nAcquisition"
    # Store block
    self.block_store_cycle_cntr = 0
    self.block_store_cycle = \
        range(self.acquisition_block_macro_cycles + self.equilibrium_macro_cycles,
              self.acquisition_block_macro_cycles + self.total_macro_cycles,
              self.acquisition_block_macro_cycles
              )
    # Store pdb
    self.pdb_store_cycle = max(int(self.acquisition_block_macro_cycles \
                         / self.params.pdb_stored_per_block), 1)

    #Setup ensemble_refinement_data_object
    self.er_data = ensemble_refinement_data()
    #Setup fmodels for running average   = refinement target
    #                  total average     = final model
    #                  current model     = model at time point n
    self.fmodel_running = self.fmodel
    self.fmodel_total = None
    self.fmodel_current = None
    self.tls_manager = None
    self.er_data.seed = self.params.random_seed
    self.run_time_stats_dict = {}

    #Dummy miller array
    self.copy_ma = self.fmodel_running.f_masks()[0].array(data = self.fmodel_running.f_masks()[0].data()*0).deep_copy()
    #
    self.fmodel_running.xray_structure = self.model.xray_structure
    assert self.fmodel_running.xray_structure is self.model.xray_structure
    self.pdb_hierarchy = self.model.pdb_hierarchy

    #Atom selections
    self.atom_selections()

    #Harmonic restraints
    if self.params.er_harmonic_restraints_selections is not None:
      self.add_harmonic_restraints()

    self.model.show_geometry_statistics(message   = "Starting model",
                                        ignore_hd = True,
                                        out       = self.log)

    self.setup_bulk_solvent_and_scale()

    self.fmodel_running.info(
      free_reflections_per_bin = 100,
      max_number_of_bins       = 999).show_rfactors_targets_in_bins(out = self.log)

    if self.params.target_name == 'ml':
      #Must be called before reseting ADPs
      if self.params.update_rescale_normalisation_factors_scale_kn:
        utils.print_header("Calculate Ncalc and restrain to scale kn", out = self.log)
        self.fmodel_running.n_obs_n_calc(update_nobs_ncalc = True)
        n_obs  = self.fmodel_running.n_obs
        n_calc = self.fmodel_running.n_calc
        self.scale_n1_reference = self.scale_helper(target    = n_calc,
                                                    reference = n_obs
                                                    )
        self.scale_n1_target    = self.scale_n1_reference
        self.scale_n1_current   = self.scale_n1_reference
        self.update_normalisation_factors()
      else:
        utils.print_header("Calculate and fix scale of Ncalc", out = self.log)
        self.fmodel_running.n_obs_n_calc(update_nobs_ncalc = True)
        print >> self.log, "Fix Ncalc scale          : True"
        print >> self.log, "Sum current Ncalc        : {0:5.3f}".format(sum(self.fmodel_running.n_calc))
      print >> self.log, "|"+"-"*77+"|\n"

    #Set ADP model
    self.tls_manager = er_tls_manager()
    self.setup_tls_selections(tls_group_selection_strings = self.params.tls_group_selections)
    self.fit_tls(input_model = self.model)
    self.assign_solvent_tls_groups()

    #Set occupancies to 1.0
    if self.params.set_occupancies:
      utils.print_header("Set occupancies to 1.0", out = self.log)
      self.model.xray_structure.set_occupancies(
        value      = 1.0)
      self.model.show_occupancy_statistics(out = self.log)

    #Initiates running average SFs
    self.er_data.f_calc_running = self.fmodel_running.f_calc().data().deep_copy()
    #self.fc_running_ave = self.fmodel_running.f_calc()
    self.fc_running_ave = self.fmodel_running.f_calc().deep_copy()

    #Initial sigmaa array, required for ML target function
    #Set eobs and ecalc normalization factors in Fmodel, required for ML
    if self.params.target_name == 'ml':
      self.sigmaa_array = self.fmodel_running.sigmaa().sigmaa().data()
      self.best_r_free = self.fmodel_running.r_free()
      self.fmodel_running.set_sigmaa = self.sigmaa_array

############################## START Simulation ################################
    utils.print_header("Start simulation", out = self.log)
    while self.macro_cycle <= self.total_macro_cycles:
      self.time = self.cdp.time_step * self.cdp.number_of_steps * self.macro_cycle
      #XXX Debug
      if False and self.macro_cycle % 10==0:
        print >> self.log, "Sys temp  : ", self.er_data.system_temp
        print >> self.log, "Xray grad : ", self.er_data.xray_grad_rms
        print >> self.log, "Geo grad  : ", self.er_data.geo_grad_rms
        print >> self.log, "Wx        : ", self.wxray

      if self.fmodel_running.target_name == 'ml'\
          and self.macro_cycle%int(self.n_mc_per_tx)==0\
          and self.macro_cycle < self.equilibrium_macro_cycles:
        self.update_normalisation_factors()

      # Ordered Solvent Update
      if self.params.ordered_solvent_update \
          and (self.macro_cycle == 1\
          or self.macro_cycle%self.params.ordered_solvent_update_cycle == 0):
        self.ordered_solvent_update()

      xrs_previous = self.model.xray_structure.deep_copy_scatterers()
      assert self.fmodel_running.xray_structure is self.model.xray_structure

      cd_manager = ensemble_cd.cartesian_dynamics(
        structure                   = self.model.xray_structure,
        restraints_manager          = self.model.restraints_manager,
        temperature                 = self.cdp.temperature - self.params.wxray_coupled_tbath_offset,
        protein_thermostat          = self.cdp.protein_thermostat,
        n_steps                     = self.cdp.number_of_steps,
        n_print                     = self.cdp.n_print,
        time_step                   = self.cdp.time_step,
        initial_velocities_zero_fraction = self.cdp.initial_velocities_zero_fraction,
        fmodel                      = self.fmodel_running,
        xray_target_weight          = self.wxray,
        chem_target_weight          = 1.0,
        xray_structure_last_updated = None,
        shift_update                = 0.0,
        xray_gradient               = self.xray_gradient,
        reset_velocities            = self.reset_velocities,
        stop_cm_motion              = self.cmremove,
        update_f_calc               = False,
        er_data                     = self.er_data,
        verbose                     = self.cdp.verbose,
        log                         = self.log)

      self.reset_velocities = False
      self.cmremove = False

      #Calc rolling average KE energy
      self.kinetic_energy_running_average()
      #Show KE stats
      if self.params.verbose > 0 and self.macro_cycle % 500 == 0:
        self.ensemble_utils.kinetic_energy_stats()

      #Update Fmodel
      self.fmodel_running.update_xray_structure(
        xray_structure      = self.model.xray_structure,
        update_f_calc       = True,
        update_f_mask       = True,
        force_update_f_mask = True)

      #Save current Fmask
      self.er_data.f_mask_current = self.fmodel_running.f_masks()[0].data().deep_copy()

      #Save current Fcalc
      self.er_data.f_calc_data_current = self.fmodel_running.f_calc().data().deep_copy()

      #Total Fmask calculation
      if self.er_data.f_mask_total is None:
        self.er_data.f_mask_total = self.fmodel_running.f_masks()[0].data().deep_copy()
        self.er_data.total_SF_cntr_mask = 1
      else:
        self.er_data.f_mask_total += self.fmodel_running.f_masks()[0].data().deep_copy()
        self.er_data.total_SF_cntr_mask += 1

      #Total Fcalc calculation
      if self.er_data.f_calc_data_total is None:
        self.er_data.f_calc_data_total = self.fmodel_running.f_calc().data().deep_copy()
        self.er_data.total_SF_cntr = 1
      else:
        self.er_data.f_calc_data_total += self.fmodel_running.f_calc().data().deep_copy()
        self.er_data.total_SF_cntr += 1

      #Running average Fcalc calculation
      if self.params.tx > 0:
        self.a_prime = math.exp(-(self.cdp.time_step * self.cdp.number_of_steps)/self.params.tx)
      else:
        self.a_prime = 0

      self.er_data.f_calc_running \
        = (self.a_prime * self.er_data.f_calc_running) + ((1-self.a_prime) * self.fmodel_running.f_calc().data().deep_copy())
      self.fc_running_ave = self.fc_running_ave.array(data = self.er_data.f_calc_running)

      #Update running average Fmask
      if self.macro_cycle == 1:
        self.er_data.f_mask_running = self.fmodel_running.f_masks()[0].data().deep_copy()
      else:
        self.er_data.f_mask_running \
          = (self.a_prime * self.er_data.f_mask_running) + ((1-self.a_prime) * self.fmodel_running.f_masks()[0].data())
      running_f_mask_update = self.copy_ma.array(data = self.er_data.f_mask_running)


      #Update runnning average Fcalc and Fmask
      self.fmodel_running.update(f_calc = self.fc_running_ave,
                                 f_mask = running_f_mask_update)

      #Update total average Fcalc
      total_f_mask_update \
          = self.copy_ma.array(data = self.er_data.f_mask_total / self.er_data.total_SF_cntr_mask)


      if self.fmodel_total == None:
        self.fmodel_total = self.fmodel_running.deep_copy()
        self.fmodel_total.update(
          f_calc = self.copy_ma.array(data = self.er_data.f_calc_data_total / self.er_data.total_SF_cntr ),
          f_mask = total_f_mask_update)

        if(self.er_data.fix_scale_factor is not None):
          self.fmodel_total.set_scale_switch = self.er_data.fix_scale_factor
      else:
        self.fmodel_total.update(
          f_calc = self.copy_ma.array(data = self.er_data.f_calc_data_total / self.er_data.total_SF_cntr),
          f_mask = total_f_mask_update)

      #Update current time-step Fcalc
      current_f_mask_update = self.copy_ma.array(data = self.er_data.f_mask_current)

      if self.fmodel_current == None:
        self.fmodel_current = self.fmodel_running.deep_copy()
        self.fmodel_current.update(
          f_calc = self.copy_ma.array(data = self.er_data.f_calc_data_current),
          f_mask = current_f_mask_update)
        if(self.er_data.fix_scale_factor is not None):
          self.fmodel_current.set_scale_switch = self.er_data.fix_scale_factor
      else:
        self.fmodel_current.update(
          f_calc = self.copy_ma.array(data = self.er_data.f_calc_data_current),
          f_mask = current_f_mask_update)

      #ML params update
      if self.params.target_name == 'ml':
        if self.macro_cycle < self.equilibrium_macro_cycles:
          if self.fmodel_running.r_free() < (self.best_r_free - 0.005):
            self.update_sigmaa()

      # Wxray coupled to temperature bath
      if self.params.wxray_coupled_tbath:
        if self.macro_cycle < 5:
          self.wxray        = 2.5
        elif self.macro_cycle < self.equilibrium_macro_cycles:
          if self.params.tx == 0:
            a_prime_wx = 0
          else:
            wx_tx = min(self.time, self.params.tx)
            a_prime_wx = math.exp(-(self.cdp.time_step * self.cdp.number_of_steps)/wx_tx)
          wxray_t = self.wxray * max(0.01, self.cdp.temperature / self.er_data.non_solvent_temp)
          self.wxray = (a_prime_wx * self.wxray) + ((1-a_prime_wx) * wxray_t)

      #Store current structure, current KE
      if self.macro_cycle % self.pdb_store_cycle == 0 \
           and self.macro_cycle >= self.equilibrium_macro_cycles:
        self.er_data.xray_structures.append(self.model.xray_structure.deep_copy_scatterers())
        self.er_data.pdb_hierarchys.append(self.model.pdb_hierarchy().deep_copy())
        if self.er_data.ke_protein_running is None:
          self.er_data.ke_pdb.append(flex.double(self.model.xray_structure.sites_cart().size(), 0.0) )
        else:
          ke_expanded = flex.double(self.model.xray_structure.sites_cart().size(), 0.0)
          ke_expanded.set_selected(~self.model.solvent_selection(),
                                   self.er_data.ke_protein_running)
          self.er_data.ke_pdb.append(ke_expanded)

      #Current structural deviation vs starting structure and previous macro-cycle structure
      if xrs_previous.distances(other = self.model.xray_structure).min_max_mean().mean > 1.0:
        print >> self.log, "\n\nWARNING:"
        print >> self.log, "Macro cycle too long, max atomic deviation w.r.t. previous cycle"
        print >> self.log, "greater than 1.0A"
        print >> self.log, "Reduce params.cartesian_dynamics.number_of_steps"
        print >> self.log, "Max deviation : {0:1.3f}"\
          .format(xrs_previous.distances(other = self.model.xray_structure).min_max_mean().mean)

      if self.fmodel_running.r_work() > 0.75:
        raise Sorry("Simulation aborted, running Rfree > 75%")

      #Print run time stats
      if self.macro_cycle == 1 or self.macro_cycle%50 == 0:
        print >> self.log, "\n________________________________________________________________________________"
        print >> self.log, "    MC        Time     |  Current  |  Rolling  |   Total   | Temp |  Grad Wxray "
        print >> self.log, "          (ps)     (%) |   Rw   Rf |   Rw   Rf |   Rw   Rf |  (K) |   X/G       "
      print >> self.log, \
          "~{0:5d} {1:7.2f} {2:7.2f} | {3:2.1f} {4:2.1f} | {5:2.1f} {6:2.1f} | {7:2.1f} {8:2.1f} | {9:4.0f} | {10:5.2f} {11:5.2f}"\
          .format(self.macro_cycle,
                  self.time,
                  self.time / self.total_time,
                  100*self.fmodel_current.r_work(),
                  100*self.fmodel_current.r_free(),
                  100*self.fmodel_running.r_work(),
                  100*self.fmodel_running.r_free(),
                  100*self.fmodel_total.r_work(),
                  100*self.fmodel_total.r_free(),
                  self.er_data.non_solvent_temp,
                  self.er_data.xray_grad_rms / self.er_data.geo_grad_rms,
                  self.wxray)

      if self.params.verbose > 0:
        if self.macro_cycle == 1\
            or self.macro_cycle%100 == 0\
            or self.macro_cycle == self.total_macro_cycles:
          self.print_fmodels_scale_and_solvent_stats()

      if self.params.number_of_acquisition_periods > 1:
        if self.macro_cycle in self.block_store_cycle:
          self.save_multiple_fmodel()

      #End of equilibration period, reset total structure factors, atomic cords, kinetic energies
      if self.macro_cycle == self.equilibrium_macro_cycles:
        self.reset_totals()
      #
      assert self.model.xray_structure is cd_manager.structure
      assert self.fmodel_running.xray_structure is cd_manager.structure
      if self.fix_scale == True:
        assert self.fmodel_running.scale_k1() == self.er_data.fix_scale_factor
      self.macro_cycle +=1

############################## END Simulation ##################################

    self.macro_cycle = self.total_macro_cycles
    #Find optimum section of acquisition period
    if self.params.number_of_acquisition_periods > 1:
      self.optimise_multiple_fmodel()
    else:
      self.fmodel_total.set_scale_switch = 0
      self.fmodel_total.update_solvent_and_scale(
                            verbose       = self.params.verbose,
                            out           = self.log,
                            params        = self.bsp,
                            optimize_mask = False)

    #Minimize number of ensemble models
    self.ensemble_utils.ensemble_reduction()

    #PDB output
    self.write_ensemble_pdb(out = gzip.open(self.params.output_file_prefix+".pdb.gz", 'wb'))

    #Optimise fmodel_total k, b_aniso, k_sol, b_sol
    self.fmodel_total.set_scale_switch = 0
    self.print_fmodels_scale_and_solvent_stats()
    self.fmodel_total.update_solvent_and_scale(
                          verbose       = self.params.verbose,
                          out           = self.log,
                          params        = self.bsp,
                          optimize_mask = False
                          )
    self.print_fmodels_scale_and_solvent_stats()
    print >> self.log, "FINAL Rwork = %6.4f Rfree = %6.4f Rf/Rw = %6.4f"\
        %(self.fmodel_total.r_work(),
          self.fmodel_total.r_free(),
          self.fmodel_total.r_free() / self.fmodel_total.r_work()
          )
    info = self.fmodel_total.info(free_reflections_per_bin = 100,
                                  max_number_of_bins       = 999
                                  )
    info.show_remark_3(out = self.log)

    # Map output
    self.write_mtz_file()

############################## END ER ##########################################

  def show_overall(self, message = "", fmodel_running = True):
    if fmodel_running:
      message = "Running: " + message
      self.fmodel_running.info().show_rfactors_targets_scales_overall(header = message, out = self.log)
    else:
      message = "Total: " + message
      self.fmodel_total.info().show_rfactors_targets_scales_overall(header = message, out = self.log)

  def write_mtz_file(self):
    class labels_decorator:
      def __init__(self, amplitudes_label, phases_label):
        self._amplitudes = amplitudes_label
        self._phases = phases_label
      def amplitudes(self):
        return self._amplitudes
      def phases(self, root_label, anomalous_sign=None):
        assert anomalous_sign is None or not anomalous_sign
        return self._phases
    xray_suffix = "_xray"
    self.mtz_dataset_original.set_name("Original-experimental-data")
    new_dataset = self.mtz_dataset_original.mtz_crystal().add_dataset(
      name = "Experimental-data-used-in-refinement", wavelength=1)
    new_dataset.add_miller_array(
      miller_array = self.fmodel_total.f_obs(),
      column_root_label="F-obs-filtered"+xray_suffix)
    another_dataset = new_dataset.mtz_crystal().add_dataset(
      name = "Model-structure-factors-(bulk-solvent-and-all-scales-included)",
      wavelength=1)
    another_dataset.add_miller_array(
      miller_array = self.fmodel_total.f_model_scaled_with_k1_composite_work_free(),
      column_root_label="F-model"+xray_suffix)
    yet_another_dataset = another_dataset.mtz_crystal().add_dataset(
      name = "Fourier-map-coefficients", wavelength=1)
    cmo = mmtbx.maps.compute_map_coefficients(
        fmodel = self.fmodel_total,
        params = self.params.electron_density_maps.map_coefficients)
    for ma in cmo.mtz_dataset.mtz_object().as_miller_arrays():
      labels=ma.info().labels
      ld = labels_decorator(amplitudes_label=labels[0], phases_label=labels[1])
      yet_another_dataset.add_miller_array(
        miller_array      = ma,
        column_root_label = labels[0],
        label_decorator   = ld)
    yet_another_dataset.mtz_object().write(file_name = self.params.output_file_prefix+".mtz")

  def add_harmonic_restraints(self):
    utils.print_header("Add specific harmonic restraints", out = self.log)
    all_chain_proxies = self.generate_all_chain_proxies(model = self.model)
    hr_selections = utils.get_atom_selections(
        all_chain_proxies = all_chain_proxies,
        selection_strings = self.params.er_harmonic_restraints_selections,
        xray_structure    = self.model.xray_structure)
    pdb_atoms = self.pdb_hierarchy().atoms()
    print >> self.log, "\nAdd atomic harmonic restraints:"
    restraint_info = []
    for i_seq in hr_selections[0]:
      atom_info = pdb_atoms[i_seq].fetch_labels()
      print >> self.log, '    {0} {1} {2} {3} {4}     '.format(
                                   atom_info.name,
                                   atom_info.i_seq+1,
                                   atom_info.resseq,
                                   atom_info.resname,
                                   atom_info.chain_id,
                                   )
      restraint_info.append((i_seq, pdb_atoms[i_seq].xyz))
    self.er_data.er_harmonic_restraints_info = restraint_info
    self.er_data.er_harmonic_restraints_weight = self.params.er_harmonic_restraints_weight
    self.er_data.er_harmonic_restraints_slack  = self.params.er_harmonic_restraints_slack
    print >> self.log, "\n|"+"-"*77+"|\n"

  def setup_bulk_solvent_and_scale(self):
    utils.print_header("Setup bulk solvent and scale", out = self.log)
    self.show_overall(message = "pre solvent and scale")
    #
    self.fmodel_running.update_solvent_and_scale(
        params        = self.bsp,
        verbose       = self.params.verbose,
        out           = self.log,
        optimize_mask = True)

    #Fixes scale factor for rolling average #ESSENTIAL for LSQ
    if self.fix_scale == True:
      self.er_data.fix_scale_factor = self.fmodel_running.scale_k1()
      self.fmodel_running.set_scale_switch = self.er_data.fix_scale_factor
    self.show_overall(message = "post solvent and scale")

  def scale_helper(self, reference, target):
    return flex.sum(reference * target) / flex.sum(flex.pow2(target))

  def update_normalisation_factors(self):
    if self.params.update_rescale_normalisation_factors_scale_kn:
      # Restrain w.r.t. scale kn
      utils.print_header("Update Ncalc and restrain to scale kn", out = self.log)
      # Target kn
      self.scale_n1_target = self.scale_helper(target    = self.fmodel_running.n_calc,
                                               reference = self.fmodel_running.n_obs
                                               )
      # Current kn
      n_obs, n_calc =\
        self.fmodel_running.n_obs_n_calc(update_nobs_ncalc = False)
      self.scale_n1_current = self.scale_helper(target    = n_calc,
                                                reference = n_obs
                                                )
      print >> self.log, "Scale K1                     : {0:5.3f}".format(self.fmodel_running.scale_k1())
      print >> self.log, "Kn reference                 : {0:5.3f}".format(self.scale_n1_reference)
      print >> self.log, "Kn target                    : {0:5.3f}".format(self.scale_n1_target)
      print >> self.log, "Kn current                   : {0:5.3f}".format(self.scale_n1_current)
      # Scale current Ncalc
      n_calc = n_calc * (self.scale_n1_current / self.scale_n1_target) * (self.scale_n1_current / self.scale_n1_reference)
      self.fmodel_running.n_calc = n_calc
      self.scale_n1_target = self.scale_helper(target    = self.fmodel_running.n_calc,
                                               reference = self.fmodel_running.n_obs
                                               )
      print >> self.log, "Kn target updated            : {0:5.3f}".format(self.scale_n1_target)
    else:
      # Normalise to reference Sum(Ncalc)
      utils.print_header("Update and renormalise Ncalc array", out = self.log)
      eobs_norm_factor, ecalc_norm_factor =\
        self.fmodel_running.n_obs_n_calc(update_nobs_ncalc = False)
      ecalc_k = sum(self.fmodel_running.n_calc) / sum(ecalc_norm_factor)
      print >> self.log, "Sum current Ncalc        : {0:5.3f}".format(sum(self.fmodel_running.n_calc) )
      print >> self.log, "Sum updated Ncalc        : {0:5.3f}".format(sum(ecalc_norm_factor) )
      print >> self.log, "Rescaling factor         : {0:5.3f}".format(ecalc_k)
      ecalc_norm_factor = ecalc_k * ecalc_norm_factor
      self.fmodel_running.n_calc = ecalc_norm_factor
    print >> self.log, "|"+"-"*77+"|\n"

  def update_sigmaa(self):
    utils.print_header("Update sigmaa", out = self.log)
    if self.params.verbose > 0:
      print >> self.log, "Previous best Rfree      : ", self.best_r_free
      print >> self.log, "Current       Rfree      : ", self.fmodel_running.r_free()
      self.print_ml_stats()
      print >> self.log, "  Update sigmaa"
    self.sigmaa_array = self.fmodel_running.sigmaa().sigmaa().data()
    self.fmodel_running.set_sigmaa = self.sigmaa_array
    if self.params.verbose > 0:
      self.print_ml_stats()
    self.best_r_free = self.fmodel_running.r_free()
    print >> self.log, "|"+"-"*77+"|\n"

  def setup_tls_selections(self, tls_group_selection_strings):
    utils.print_header("Generating TLS selections from input parameters (not including solvent)", out = self.log)
    model_no_solvent = self.model.deep_copy()
    model_no_solvent = model_no_solvent.remove_solvent()
    all_chain_proxies = self.generate_all_chain_proxies(model = model_no_solvent)

    if len(tls_group_selection_strings) < 1:
      print >> self.log, '\nNo TLS groups supplied - automatic setup'
      # Get chain information
      chains_info = []
      for chain in model_no_solvent.pdb_hierarchy().chains():
        count_h = 0
        for atom in chain.atoms():
          if atom.element_is_hydrogen(): count_h+=1
        chain_id_non_h = (chain.id, chain.atoms_size() - count_h)
        chains_info.append(chain_id_non_h)
      # Check all chains > 63 heavy atoms for TLS fitting
      chains_size = flex.int(zip(*chains_info)[1])
      chains_size_ok = flex.bool(chains_size > 63)
      if sum(chains_size) < 63:
        print >> self.log, '\nStructure contains less than 63 atoms (non H/D, non solvent)'
        raise Sorry('Unable to perform TLS fitting')
      elif chains_size_ok.count(False) == 0:
        print >> self.log, '\nTLS selections:'
        print >> self.log, 'Chain, number atoms (non H/D)'
        for chain in chains_info:
          tls_group_selection_strings.append('chain ' + chain[0])
          print >> self.log, chain[0], chain[1]
      else:
        print >> self.log, '\nFollowing chains contain less than 63 atoms (non H/D):'
        tls_group_selection_strings.append('chain ')
        for chain in chains_info:
          tls_group_selection_strings[0] += (chain[0] + ' or chain ')
          if chain[1] < 63:
            print >> self.log, chain[0], chain[1]
        print >> self.log, 'Combining all chains to single TLS group'
        print >> self.log, 'WARNING: this may not be the optimum tls groupings to use'
        print >> self.log, 'TLS selections:'
        tls_group_selection_strings[0] = tls_group_selection_strings[0][0:-10]
        print >> self.log, tls_group_selection_strings[0]
    #
    tls_no_sol_selections =  utils.get_atom_selections(
        all_chain_proxies = all_chain_proxies,
        selection_strings = tls_group_selection_strings,
        xray_structure    = model_no_solvent.xray_structure)
    #
    tls_no_hd_selection_strings = []
    for selection_string in tls_group_selection_strings:
      no_hd_string = selection_string + ' and not (element H or element D)'
      tls_no_hd_selection_strings.append(no_hd_string)
    tls_no_sol_no_hd_selections = utils.get_atom_selections(
        all_chain_proxies = all_chain_proxies,
        selection_strings = tls_no_hd_selection_strings,
        xray_structure    = model_no_solvent.xray_structure)
    #
    assert self.tls_manager is not None
    self.tls_manager.tls_selection_strings_no_sol       = tls_group_selection_strings
    self.tls_manager.tls_selection_strings_no_sol_no_hd = tls_no_hd_selection_strings
    self.tls_manager.tls_selections_no_sol              = tls_no_sol_selections
    self.tls_manager.tls_selections_no_sol_no_hd        = tls_no_sol_no_hd_selections
    self.tls_manager.tls_operators = mmtbx.tls.tools.generate_tlsos(
        selections     = self.tls_manager.tls_selections_no_sol,
        xray_structure = model_no_solvent.xray_structure,
        value          = 0.0)

    self.model.tls_groups = mmtbx.tls.tools.tls_groups(
        selection_strings = self.tls_manager.tls_selection_strings_no_sol,
        tlsos             = self.tls_manager.tls_operators)

  def generate_all_chain_proxies(self, model = None):
    if model == None:
      model = self.model
    raw_records = [pdb.format_cryst1_record(crystal_symmetry=self.model.xray_structure.crystal_symmetry())]
    pdb_hierarchy = model.pdb_hierarchy
    raw_records.extend(pdb_hierarchy().as_pdb_string().splitlines())
    pip = model.processed_pdb_files_srv.pdb_interpretation_params
    pip.clash_guard.nonbonded_distance_threshold = -1.0
    pip.clash_guard.max_number_of_distances_below_threshold = 100000000
    pip.clash_guard.max_fraction_of_distances_below_threshold = 1.0
    pip.proceed_with_excessive_length_bonds=True
    model.processed_pdb_files_srv.pdb_interpretation_params.\
        clash_guard.nonbonded_distance_threshold=None
    processed_pdb_file, pdb_inp = model.processed_pdb_files_srv.\
      process_pdb_files(raw_records = raw_records)
    return processed_pdb_file.all_chain_proxies

  def fit_tls(self, input_model, verbose = False):
    utils.print_header("Fit TLS from reference model", out = self.log)
    model_copy = input_model.deep_copy()
    model_copy = model_copy.remove_solvent()
    print >> self.log, 'Reference model :'
    model_copy.show_adp_statistics(padded = True, out = self.log)
    start_xrs = model_copy.xray_structure.deep_copy_scatterers()
    start_xrs.convert_to_isotropic()
    start_biso = start_xrs.scatterers().extract_u_iso()/adptbx.b_as_u(1)
    model_copy.xray_structure.convert_to_anisotropic()
    tls_selection_no_sol_hd            = self.tls_manager.tls_selections_no_sol_no_hd
    tls_selection_no_sol_hd_exclusions = self.tls_manager.tls_selections_no_sol_no_hd
    pre_fitted_mean = 999999.99
    #
    for fit_cycle in xrange(self.params.max_ptls_cycles):
      fit_tlsos = mmtbx.tls.tools.generate_tlsos(
        selections     = tls_selection_no_sol_hd_exclusions,
        xray_structure = model_copy.xray_structure,
        value          = 0.0)
      print >> self.log, '\nFitting cycle : ', fit_cycle+1
      for rt,rl,rs in [[1,0,1],[1,1,1],[0,1,1],
                       [1,0,0],[0,1,0],[0,0,1],[1,1,1],
                       [0,0,1]]*10:
        fit_tlsos = mmtbx.tls.tools.tls_from_uanisos(
          xray_structure               = model_copy.xray_structure,
          selections                   = tls_selection_no_sol_hd_exclusions,
          tlsos_initial                = fit_tlsos,
          number_of_macro_cycles       = 10,
          max_iterations               = 100,
          refine_T                     = rt,
          refine_L                     = rl,
          refine_S                     = rs,
          enforce_positive_definite_TL = True,
          verbose                      = -1,
          out                          = self.log)
      fitted_tls_xrs = model_copy.xray_structure.deep_copy_scatterers()
      us_tls = mmtbx.tls.tools.u_cart_from_tls(
             sites_cart = fitted_tls_xrs.sites_cart(),
             selections = self.tls_manager.tls_selections_no_sol,
             tlsos      = fit_tlsos)
      fitted_tls_xrs.set_u_cart(us_tls)
      fitted_tls_xrs.convert_to_isotropic()
      fitted_biso = fitted_tls_xrs.scatterers().extract_u_iso()/adptbx.b_as_u(1)
      mmtbx.tls.tools.show_tls(tlsos = fit_tlsos, out = self.log)
      #For testing
      if verbose:
        pdb_hierarchy = model_copy.pdb_hierarchy
        pdb_atoms = pdb_hierarchy().atoms()
        not_h_selection = pdb_hierarchy().atom_selection_cache().selection('not element H')
        ca_selection = pdb_hierarchy().atom_selection_cache().selection('name ca')
        print >> self.log, '\nCA atoms (Name/res number/res name/chain/atom number/ref biso/fit biso::'
        for i_seq, ca in enumerate(ca_selection):
          if ca:
            atom_info = pdb_atoms[i_seq].fetch_labels()
            print >> self.log, atom_info.name, atom_info.resseq, atom_info.resname, atom_info.chain_id, " | ", i_seq, start_biso[i_seq], fitted_biso[i_seq]

      delta_ref_fit = flex.abs(start_biso - fitted_biso)
      hd_selection = model_copy.xray_structure.hd_selection()
      delta_ref_fit_no_h = delta_ref_fit.select(~hd_selection)
      delta_ref_fit_no_h_basic_stats = scitbx.math.basic_statistics(delta_ref_fit_no_h )
      start_biso_no_hd = start_biso.select(~hd_selection)
      fitted_biso_no_hd = fitted_biso.select(~hd_selection)

      if verbose:
        print >> self.log, 'pTLS                                    : ', self.params.ptls

      sorted_delta_ref_fit_no_h = sorted(delta_ref_fit_no_h)
      percentile_cutoff = sorted_delta_ref_fit_no_h[int(len(sorted_delta_ref_fit_no_h) * self.params.ptls)-1]
      print >> self.log, 'Cutoff (<)                              : ', percentile_cutoff
      print >> self.log, 'Number of atoms (non HD)                : ', delta_ref_fit_no_h.size()
      delta_ref_fit_no_h_include = flex.bool(delta_ref_fit_no_h < percentile_cutoff)
      print >> self.log, 'Number of atoms (non HD) used in fit    : ', delta_ref_fit_no_h_include.count(True)
      print >> self.log, 'Percentage (non HD) used in fit         : ', delta_ref_fit_no_h_include.count(True) / delta_ref_fit_no_h.size()

      # Convergence test
      if fitted_biso_no_hd.min_max_mean().mean == pre_fitted_mean:
        break
      else:
        pre_fitted_mean = fitted_biso_no_hd.min_max_mean().mean

      # N.B. map on to full array including hydrogens for i_seqs
      include_array = flex.bool(delta_ref_fit  < percentile_cutoff)
      #
      include_i_seq = []
      assert delta_ref_fit.size() == model_copy.xray_structure.sites_cart().size()
      assert include_array.size() == model_copy.xray_structure.sites_cart().size()
      for i_seq, include_flag in enumerate(include_array):
        if include_flag and not hd_selection[i_seq]:
          include_i_seq.append(i_seq)
      tls_selection_no_sol_hd_exclusions = []
      for group in xrange(len(tls_selection_no_sol_hd)):
        new_group = flex.size_t()
        for x in tls_selection_no_sol_hd[group]:
          if x in include_i_seq:
            new_group.append(x)
        if len(new_group) < 63:
          raise Sorry("Number atoms in TLS too small; increase size of group or reduce cut-off")
        print >> self.log, 'TLS group ', group+1, ' number atoms ', len(new_group)
        tls_selection_no_sol_hd_exclusions.append(new_group)

    #
    print >> self.log, '\nFinal non-solvent b-factor model'
    model_copy.xray_structure.convert_to_anisotropic()
    us_tls = mmtbx.tls.tools.u_cart_from_tls(
             sites_cart = model_copy.xray_structure.sites_cart(),
             selections = self.tls_manager.tls_selections_no_sol_no_hd,
             tlsos      = fit_tlsos)
    model_copy.xray_structure.set_u_cart(us_tls)
    model_copy.show_adp_statistics(padded = True, out = self.log)
    del model_copy

    #Update TLS params
    self.model.tls_groups.tlsos = fit_tlsos
    self.tls_manager.tls_operators = fit_tlsos
    self.assign_solvent_tls_groups()

  def tls_parameters_update(self):
    self.model.xray_structure.convert_to_anisotropic()
    #Apply TLS w.r.t. to atomic position
    selections = self.tls_manager.tls_selections_with_sol
    us_tls = mmtbx.tls.tools.u_cart_from_tls(
               sites_cart = self.model.xray_structure.sites_cart(),
               selections = selections,
               tlsos      = self.tls_manager.tls_operators)
    for selection in selections:
      self.model.xray_structure.set_u_cart(us_tls, selection = selection)
    self.fmodel_running.update_xray_structure(
      xray_structure = self.model.xray_structure,
      update_f_calc  = False,
      update_f_mask  = False)

  def assign_solvent_tls_groups(self):
    self.model.xray_structure.convert_to_anisotropic(selection =  self.model.solvent_selection())
    self.fmodel_running.update_xray_structure(
      xray_structure  = self.model.xray_structure,
      update_f_calc   = False,
      update_f_mask   = False)
    #
    self.tls_manager.tls_selections_with_sol = []
    for grp in self.tls_manager.tls_selections_no_sol:
      self.tls_manager.tls_selections_with_sol.append(grp.deep_copy())
    #
    if len(self.tls_manager.tls_selections_with_sol) == 1:
      pdb_atoms     = self.pdb_hierarchy().atoms()
      hoh_selection = self.model.solvent_selection()
      for n, atom in enumerate(pdb_atoms):
        if hoh_selection[n]:
          self.tls_manager.tls_selections_with_sol[0].append(n)
    else:
      model             = self.model.deep_copy()
      solvent_selection = model.solvent_selection()
      solvent_xrs       = model.xray_structure.select(solvent_selection)
      model             = model.remove_solvent()
      closest_distances = model.xray_structure.closest_distances(
                              sites_frac      = solvent_xrs.sites_frac(),
                              use_selection   = ~model.xray_structure.hd_selection(),
                              distance_cutoff = 10.0)
      assert len(solvent_xrs.sites_cart()) == len(closest_distances.i_seqs)
      number_non_solvent_atoms = model.xray_structure.sites_cart().size()
      for n, i_seq in enumerate(closest_distances.i_seqs):
        for grp in self.tls_manager.tls_selections_with_sol:
          if i_seq in grp:
            grp.append(n+number_non_solvent_atoms)
            break
    #
    self.tls_parameters_update()

  def kinetic_energy_running_average(self):
    #Kinetic energy
    atomic_weights = self.model.xray_structure.atomic_weights()
    ke = 0.5 * atomic_weights * self.er_data.velocities.dot()
    #Select non-solvent atoms
    ke = ke.select(~self.model.solvent_selection() )
    if self.er_data.ke_protein_running == None:
      self.er_data.ke_protein_running = ke
    else:
      self.er_data.ke_protein_running\
        = (self.a_prime * self.er_data.ke_protein_running) + ( (1-self.a_prime) * ke)

  def ordered_solvent_update(self):
    ensemble_ordered_solvent_manager = ensemble_ordered_solvent.manager(
      model             = self.model,
      fmodel            = self.fmodel_running,
      verbose           = self.params.verbose,
      params            = self.params.ensemble_ordered_solvent,
      velocities        = self.er_data.velocities,
      log               = self.log)
    self.model = ensemble_ordered_solvent_manager.model
    self.er_data.velocities = ensemble_ordered_solvent_manager.velocities
    self.fmodel_running.update_xray_structure(
      xray_structure = self.model.xray_structure,
      update_f_calc  = False,
      update_f_mask  = False)
    assert self.fmodel_running.xray_structure is self.model.xray_structure
    self.xray_gradient = None
    #Update atom selections
    self.pdb_hierarchy = self.model.pdb_hierarchy
    self.atom_selections()
    #Reset solvent tls groups
    if self.tls_manager is not None:
      self.assign_solvent_tls_groups()

  def reset_totals(self):
    utils.print_header("Reseting structure ensemble and total Fmodel", out = self.log)
    self.er_data.xray_structures = []
    self.er_data.pdb_hierarchys = []
    self.er_data.ke_pdb = []
    self.er_data.f_calc_data_total = None
    self.er_data.total_SF_cntr = 0
    self.er_data.f_mask_total = None
    self.er_data.total_SF_cntr_mask = 0

  #Generates list of atom selections (needed to pass to CD)
  def atom_selections(self):
    self.er_data.all_sel     = flex.bool(self.model.xray_structure.sites_cart().size(), True)
    self.er_data.solvent_sel = self.model.solvent_selection()

  def save_multiple_fmodel(self):
    utils.print_header("Saving fmodel block", out = self.log)
    #Stores fcalc, fmask, xray structure, pdb hierarchys
    print >> self.log, '{0:<23}: {1:>8} {2:>8} {3:>8} {4:>8}'.format('','MC','Block','Rwork','Rfree')
    print >> self.log, "{0:<23}: {1:8d} {2:8d} {3:8.3f} {4:8.3f}".format(
        'Fmodel block info',
        self.macro_cycle,
        self.block_store_cycle_cntr+1,
        100 * self.fmodel_total.r_work(),
        100 * self.fmodel_total.r_free() )
    fcalc_block  = self.er_data.f_calc_data_total / self.er_data.total_SF_cntr
    fmask_block  = self.er_data.f_mask_total / self.er_data.total_SF_cntr_mask
    xrs_block    = self.er_data.xray_structures
    pdb_h_block  = self.er_data.pdb_hierarchys
    ke_pdb_block = self.er_data.ke_pdb

    block_info = (fcalc_block,
                  fmask_block,
                  xrs_block,
                  pdb_h_block,
                  ke_pdb_block)

    self.block_store_cycle_cntr+1
    if self.block_store_cycle_cntr+1 == 1:
      self.block_temp_file_list = []
    filename = str(self.block_store_cycle_cntr+1)+'_block_'+self.params.output_file_prefix+'_TEMP.pZ'
    self.block_temp_file_list.append(filename)
    er_pickle(pickle_object = block_info, pickle_filename = filename)
    self.block_store_cycle_cntr += 1
    if self.macro_cycle != self.total_macro_cycles:
      self.reset_totals()

  def optimise_multiple_fmodel(self):
    utils.print_header("Block selection by Rwork", out = self.log)
    best_r_work = 1.0

    # Load all temp files
    self.fmodel_total_block_list = []
    for filename in self.block_temp_file_list:
      block_info = cPickle.load(gzip.open(filename,'rb'))
      self.fmodel_total_block_list.append(block_info)
      os.remove(filename)

    self.fmodel_total.set_scale_switch = 0
    print >> self.log, '  {0:>17} {1:>8} {2:>8} {3:>8} {4:>8}'\
      .format('Block range','Rwork','Rfree','k1','ksol','bsol')
    for x in xrange(len(self.fmodel_total_block_list)):
      x2 = x+1
      y = len(self.fmodel_total_block_list)
      while y > x:
        fcalc_tot = self.fmodel_total_block_list[x][0].deep_copy()
        fmask_tot = self.fmodel_total_block_list[x][1].deep_copy()
        cntr      = 1
        while x2 < y:
          fcalc_tot += self.fmodel_total_block_list[x2][0].deep_copy()
          fmask_tot += self.fmodel_total_block_list[x2][1].deep_copy()
          x2     += 1
          cntr   += 1
        self.fmodel_total.update(
          f_calc = self.copy_ma.array(data = (fcalc_tot / cntr)),
          f_mask = self.copy_ma.array(data = (fmask_tot / cntr)) )
        self.fmodel_total.update_solvent_and_scale(
          verbose = self.params.verbose,
          params = self.bsp,
          out = self.log,
          optimize_mask = False)
        print >> self.log, "  {0:8d} {1:8d} {2:8.3f} {3:8.3f} {4:8.3f} {5:8.3f}"\
          .format(x+1,
                  y,
                  100*self.fmodel_total.r_work(),
                  100*self.fmodel_total.r_free(),
                  self.fmodel_total.scale_k1(),
                  self.fmodel_total.fmodel_kbu().k_sols()[0],
                  self.fmodel_total.fmodel_kbu().b_sol() )
        if self.fmodel_total.r_free() < best_r_work:
          best_r_work = self.fmodel_total.r_work()
          best_r_work_block = [x,y]
          best_r_work_fcalc = (fcalc_tot / cntr)
          best_r_work_fmask = (fmask_tot / cntr)
        x2 = x+1
        y -= 1
    self.fmodel_total.update(
      f_calc = self.copy_ma.array(data = best_r_work_fcalc),
      f_mask = self.copy_ma.array(data = best_r_work_fmask) )
    self.fmodel_total.update_solvent_and_scale(
          verbose       = self.params.verbose,
          params        = self.bsp,
          out           = self.log,
          optimize_mask = False)

    print >> self.log, "\nOptimium block :"
    print >> self.log, "  {0:8d} {1:8d} {2:8.3f} {3:8.3f} {4:8.3f} {5:8.3f}"\
      .format(best_r_work_block[0]+1,
              best_r_work_block[1],
              self.fmodel_total.r_work(),
              self.fmodel_total.r_free(),
              self.fmodel_total.scale_k1(),
              self.fmodel_total.fmodel_kbu().k_sols()[0],
              self.fmodel_total.fmodel_kbu().b_sol() )
    #Update self.er_data.xray_structures and self.er_data.pdb_hierarchys to correspond to optimum fmodel_total
    self.er_data.xray_structures = []
    self.er_data.pdb_hierarchys  = []
    self.er_data.ke_pdb          = []
    for x in xrange(len(self.fmodel_total_block_list)):
      if x >= best_r_work_block[0] and x < best_r_work_block[1]:
        print  >> self.log, "Block | Number of models in block : ", x+1, " | ", len(self.fmodel_total_block_list[x][2])
        self.er_data.xray_structures.extend(self.fmodel_total_block_list[x][2])
        self.er_data.pdb_hierarchys.extend(self.fmodel_total_block_list[x][3])
        self.er_data.ke_pdb.extend(self.fmodel_total_block_list[x][4])
    assert len(self.er_data.xray_structures) == len(self.er_data.pdb_hierarchys)
    assert len(self.er_data.xray_structures) == len(self.er_data.ke_pdb)
    print >> self.log, "Number of models for PBD          : ", len(self.er_data.xray_structures)
    print >> self.log, "|"+"-"*77+"|\n"

  def print_fmodels_scale_and_solvent_stats(self):
    utils.print_header("Fmodel statistics | macrocycle: "+str(self.macro_cycle), out = self.log)
    print >> self.log, '{0:<23}: {1:>8} {2:>8} {3:>8} {4:>8}'.format('','MC','k1','Bsol','ksol')
    if self.fmodel_current is not None:
      print >> self.log, "{0:<23}: {1:8d} {2:8.3f} {3:8.3f} {4:8.3f}"\
        .format('Fmodel current',
                self.macro_cycle,
                self.fmodel_current.scale_k1(),
                self.fmodel_current.fmodel_kbu().b_sol(),
                self.fmodel_current.fmodel_kbu().k_sols()[0],
                )
    if self.fmodel_running is not None:
      print >> self.log, "{0:<23}: {1:8d} {2:8.3f} {3:8.3f} {4:8.3f}"\
        .format('Fmodel running',
                self.macro_cycle,
                self.fmodel_running.scale_k1(),
                self.fmodel_running.fmodel_kbu().b_sol(),
                self.fmodel_running.fmodel_kbu().k_sols()[0] )
    if self.fmodel_total is not None:
      print >> self.log, "{0:<23}: {1:8d} {2:8.3f} {3:8.3f} {4:8.3f}"\
        .format('Fmodel_Total',
                self.macro_cycle,
                self.fmodel_total.scale_k1(),
                self.fmodel_total.fmodel_kbu().b_sol(),
                self.fmodel_total.fmodel_kbu().k_sols()[0] )
    if self.fmodel_current is not None:
      print >> self.log, "Fmodel current bcart   : {0:14.2f} {1:5.2f} {2:5.2f} {3:5.2f} {4:5.2f} {5:5.2f}".format(*self.fmodel_current.fmodel_kbu().b_cart())
    if self.fmodel_running is not None:
      print >> self.log, "Fmodel running bcart   : {0:14.2f} {1:5.2f} {2:5.2f} {3:5.2f} {4:5.2f} {5:5.2f}".format(*self.fmodel_running.fmodel_kbu().b_cart())
    if self.fmodel_total  is not None:
      print >> self.log, "Fmodel total bcart     : {0:14.2f} {1:5.2f} {2:5.2f} {3:5.2f} {4:5.2f} {5:5.2f}".format(*self.fmodel_total.fmodel_kbu().b_cart())
    print >> self.log, "|"+"-"*77+"|\n"

  def write_ensemble_pdb(self, out):
    crystal_symmetry = self.er_data.xray_structures[0].crystal_symmetry()
    print >> out,  "REMARK   3  TIME-AVERAGED ENSEMBLE REFINEMENT"
    fmodel_info = self.fmodel_total.info()
    fmodel_info.show_remark_3(out = out)
    model_stats = mmtbx.model_statistics.model(model     = self.model,
                                               ignore_hd = False)
    # set mode_stats.geometry to None as refers to final structure NOT ensemble
    model_stats.geometry = None
    model_stats.show(out = out, pdb_deposition =True)
    # get mean geometry stats for ensemble
    self.final_geometry_pdb_string = self.ensemble_utils.ensemble_mean_geometry_stats(
        restraints_manager       = self.model.restraints_manager,
        xray_structure           = self.model.xray_structure,
        ensemble_xray_structures = self.er_data.xray_structures,
        ignore_hd                = True,
        verbose                  = False,
        out                      = self.log,
        return_pdb_string        = True)
    print >> out, self.final_geometry_pdb_string
    print >> out, pdb.format_cryst1_record(crystal_symmetry = crystal_symmetry)
    print >> out, pdb.format_scale_records(unit_cell = crystal_symmetry.unit_cell())
    atoms_reset_serial = True
    #
    cntr = 0
    assert len(self.er_data.ke_pdb) == len(self.er_data.xray_structures)
    assert len(self.er_data.pdb_hierarchys) == len(self.er_data.xray_structures)
    for i_model, xrs in enumerate(self.er_data.xray_structures):
      cntr += 1
      print >> out, "MODEL %8d"%cntr
      scatterers = xrs.scatterers()
      sites_cart = xrs.sites_cart()
      u_isos = xrs.extract_u_iso_or_u_equiv()
      occupancies = scatterers.extract_occupancies()
      u_carts = scatterers.extract_u_cart_plus_u_iso(xrs.unit_cell())
      scat_types = scatterers.extract_scattering_types()
      i_model_pdb_hierarchy = self.er_data.pdb_hierarchys[i_model]
      pdb_atoms = i_model_pdb_hierarchy.atoms()
      i_model_ke = self.er_data.ke_pdb[i_model]
      for j_seq, atom in enumerate(pdb_atoms):
        if j_seq < len(sites_cart):
          atom.xyz = sites_cart[j_seq]
          if self.params.output_running_kinetic_energy_in_occupancy_column:
            #XXX * 0.1 to fit in occ col
            atom.occ = 0.1 * i_model_ke[j_seq]
          else:
            atom.occ = 1.0 / len(self.er_data.xray_structures)
          atom.b = adptbx.u_as_b(u_isos[j_seq])
          e = scat_types[j_seq]
          if (len(e) > 1 and "+-0123456789".find(e[1]) >= 0):
            atom.element = "%2s" % e[:1]
            atom.charge = "%-2s" % e[1:]
          elif (len(e) > 2):
            atom.element = "%2s" % e[:2]
            atom.charge = "%-2s" % e[2:]
          else:
            atom.element = "%2s" % e
            atom.charge = "  "
          if (scatterers[j_seq].flags.use_u_aniso()):
            atom.uij = u_carts[j_seq]
          elif(False):
            atom.uij = self.u_cart
          else:
            atom.uij = (-1,-1,-1,-1,-1,-1)
      if (atoms_reset_serial):
        atoms_reset_serial_first_value = 1
      else:
        atoms_reset_serial_first_value = None
      out.write(i_model_pdb_hierarchy.as_pdb_string(
        append_end=False,
        atoms_reset_serial_first_value=atoms_reset_serial_first_value))
      #
      print >> out, "ENDMDL"
    print >> out, "END"

  def print_ml_stats(self):
    if self.fmodel_running.set_sigmaa is not None:
      self.run_time_stats_dict.update({'Sigma_a':self.fmodel_running.set_sigmaa})
    if self.params.target_name == 'ml':
      self.run_time_stats_dict.update({'Alpha':self.fmodel_running.alpha_beta()[0].data()})
      self.run_time_stats_dict.update({'Beta':self.fmodel_running.alpha_beta()[1].data()})
    if self.fmodel_running.n_obs is not None:
      self.run_time_stats_dict.update({'Eobs(fixed)':self.fmodel_running.n_obs})
    if self.fmodel_running.n_calc is not None:
      self.run_time_stats_dict.update({'Ecalc(fixed)':self.fmodel_running.n_calc})

    utils.print_header("ML statistics", out = self.log)
    print >> self.log, '  {0:<23}: {1:>12} {2:>12} {3:>12}'.format('','min','max','mean')
    for key in sorted(self.run_time_stats_dict.keys()):
      info = self.run_time_stats_dict[key].min_max_mean()
      print >> self.log, '  {0:<23}: {1:12.3f} {2:12.3f} {3:12.3f}'.format(
        key,
        info.min,
        info.max,
        info.mean)
    print >> self.log, "|"+"-"*77+"|\n"

################################################################################

def show_data(fmodel, n_outl, test_flag_value, f_obs_labels, log):
  info = fmodel.info()
  flags_pc = \
   fmodel.r_free_flags().data().count(True)*1./fmodel.r_free_flags().data().size()
  print >> log, "Data statistics"
  try: f_obs_labels = f_obs_labels[:f_obs_labels.index(",")]
  except ValueError: pass
  result = " \n    ".join([
    "data_label                          : %s"%f_obs_labels,
    "high_resolution                     : "+format_value("%-5.2f",info.d_min),
    "low_resolution                      : "+format_value("%-6.2f",info.d_max),
    "completeness_in_range               : "+format_value("%-6.2f",info.completeness_in_range),
    "completeness(d_min-inf)             : "+format_value("%-6.2f",info.completeness_d_min_inf),
    "completeness(6A-inf)                : "+format_value("%-6.2f",info.completeness_6_inf),
    "wilson_b                            : "+format_value("%-6.1f",fmodel.wilson_b()),
    "number_of_reflections               : "+format_value("%-8d",  info.number_of_reflections),
    "test_set_size                       : "+format_value("%-8.4f",flags_pc),
    "test_flag_value                     : "+format_value("%-d",   test_flag_value),
    "number_of_Fobs_outliers             : "+format_value("%-8d",  n_outl),
    "anomalous_flag                      : "+format_value("%-6s",  fmodel.f_obs().anomalous_flag())])
  print >> log, "   ", result

def show_model_vs_data(fmodel, log):
  d_max, d_min = fmodel.f_obs().d_max_min()
  flags_pc = fmodel.r_free_flags().data().count(True)*100./\
    fmodel.r_free_flags().data().size()
  if(flags_pc == 0): r_free = None
  else: r_free = fmodel.r_free()
  k_sol = format_value("%-5.2f",fmodel.fmodel_kbu().k_sols()[0])
  b_sol = format_value("%-7.2f",fmodel.fmodel_kbu().b_sol())
  b_cart = " ".join([("%8.2f"%v).strip() for v in fmodel.fmodel_kbu().b_cart()])
  print >> log, "Model vs data statistics"
  result = " \n    ".join([
    "r_work(re-computed)                 : "+format_value("%-6.4f",fmodel.r_work()),
    "r_free(re-computed)                 : "+format_value("%-6.4f",r_free),
    "scale_k1                            : "+format_value("%-6.4f",fmodel.scale_k1()),
    "bulk_solvent_(k_sol,b_sol)          : %s%s"%(k_sol,b_sol),
    "overall_anisotropic_scale_(b_cart)  : "+format_value("%-s",b_cart)])
  print >> log, "   ", result

def run(args, command_name = "phenix.ensemble_refinement"):
  if(len(args) == 0): args = ["--help"]
  command_line = (iotbx_option_parser(
    usage="%s reflection_file pdb_file [options]" % command_name,
    description='Example: %s data.mtz model.pdb'%command_name)
    .option(None, "--f_obs_label",
      action="store",
      default=None,
      type="string",
      help="Label for F-obs (or I-obs).")
    .option(None, "--r_free_flags_label",
      action="store",
      default=None,
      type="string",
      help="Label for free R flags.")
    .option(None, "--show_defaults",
      action="store_true",
      help="Show list of parameters.")
    ).process(args=args)
  log = sys.stdout
  if(command_line.options.show_defaults):
    master_params.show(out = log)
    return
  processed_args = utils.process_command_line_args(args = args,
    log = sys.stdout, master_params = master_params)
  cmd_params = processed_args.params
  if(cmd_params is not None):
    er_params = cmd_params.extract().ensemble_refinement
  else: cmd_params = master_params
  log = multi_out()
  log.register(label="stdout", file_object=sys.stdout)
  log.register(
    label="log_buffer",
    file_object=StringIO(),
    atexit_send_to=None)
  sys.stderr = log
  log_file = open(er_params.output_file_prefix+'.log', "w")
  log.replace_stringio(
      old_label="log_buffer",
      new_label="log",
      new_file_object=log_file)
  timer = user_plus_sys_time()
  utils.print_programs_start_header(log=log, text=command_name)
  utils.print_header("Ensemble refinement parameters", out = log)
  cmd_params.show(out = log)
  reflection_files = processed_args.reflection_files
  if(len(reflection_files) == 0):
    raise Sorry("No reflection file found.")
  crystal_symmetry = processed_args.crystal_symmetry
  if(crystal_symmetry is None):
    raise Sorry("No crystal symmetry found.")
  if(len(processed_args.pdb_file_names) == 0):
    raise Sorry("No PDB file found.")
  pdb_file_names = processed_args.pdb_file_names
  utils.print_header("Model and data statistics", out = log)
  print >> log, "Data file                               : %s"%(format_value("%5s",os.path.basename(pdb_file_names[0])))
  print >> log, "Model file                              : %s \n"%(format_value("%5s",os.path.basename(processed_args.reflection_file_names[0])))
  print >> log, "\nTLS MUST BE IN ATOM RECORDS OF INPUT PDB\n"
  rfs = reflection_file_utils.reflection_file_server(
    crystal_symmetry = crystal_symmetry,
    force_symmetry   = True,
    reflection_files = reflection_files,
    err              = StringIO())
  parameters = utils.data_and_flags_master_params().extract()
  if(command_line.options.f_obs_label is not None):
    parameters.labels = command_line.options.f_obs_label
  if(command_line.options.r_free_flags_label is not None):
    parameters.r_free_flags.label = command_line.options.r_free_flags_label
  determine_data_and_flags_result = utils.determine_data_and_flags(
    reflection_file_server  = rfs,
    parameters              = parameters,
    data_parameter_scope    = "refinement.input.xray_data",
    flags_parameter_scope   = "refinement.input.xray_data.r_free_flags",
    data_description        = "X-ray data",
    keep_going              = True,
    log                     = log)
  f_obs = determine_data_and_flags_result.f_obs
  number_of_reflections = f_obs.indices().size()

  r_free_flags = determine_data_and_flags_result.r_free_flags
  test_flag_value = determine_data_and_flags_result.test_flag_value
  if(r_free_flags is None):
    r_free_flags=f_obs.array(data=flex.bool(f_obs.data().size(), False))
    test_flag_value=None

  f_obs_label = "F-obs"
  i_obs_label = "I-obs"
  flag_label = "R-free-flags"
  if (determine_data_and_flags_result.intensity_flag):
    column_root_label = i_obs_label
  else:
    column_root_label = f_obs_label
  mtz_dataset_original = determine_data_and_flags_result.raw_data.as_mtz_dataset(
    column_root_label=column_root_label)
  mtz_dataset_original.add_miller_array(
    miller_array = determine_data_and_flags_result.raw_flags,
    column_root_label=flag_label)

  cif_file = None
  params = processed_args.params
  if(len(processed_args.pdb_file_names) == 0):
    raise Sorry("No PDB file found.")
  print >> log, "\nPDB file name : ", processed_args.pdb_file_names[0]
  cif_objects = processed_args.cif_objects
  if(cif_file is not None):
    cif_objects = []
    cif_objects.append((cif_file,
        mmtbx.monomer_library.server.read_cif(file_name = cif_file)))

  # Process PDB file
  pdb_file = processed_args.pdb_file_names[0]
  pdb_ip = mmtbx.monomer_library.pdb_interpretation.master_params.extract()
  pdb_ip.clash_guard.nonbonded_distance_threshold = -1.0
  pdb_ip.clash_guard.max_number_of_distances_below_threshold = 100000000
  pdb_ip.clash_guard.max_fraction_of_distances_below_threshold = 1.0
  pdb_ip.proceed_with_excessive_length_bonds=True
  processed_pdb_files_srv = utils.process_pdb_file_srv(
    cif_objects               = cif_objects,
    pdb_interpretation_params = pdb_ip,
    crystal_symmetry          = crystal_symmetry,
    log                       = log)
  processed_pdb_file, pdb_inp = \
    processed_pdb_files_srv.process_pdb_files(pdb_file_names = [pdb_file])

  # Remove alternative conformations if present
  hierarchy = processed_pdb_file.all_chain_proxies.pdb_hierarchy
  atoms_size_pre = hierarchy.atoms().size()
  for model in hierarchy.models() :
    for chain in model.chains() :
      for residue_group in chain.residue_groups() :
        atom_groups = residue_group.atom_groups()
        assert (len(atom_groups) > 0)
        for atom_group in atom_groups :
          if (not atom_group.altloc in ["", "A"]) :
            residue_group.remove_atom_group(atom_group=atom_group)
          else :
            atom_group.altloc = ""
        if (len(residue_group.atom_groups()) == 0) :
          chain.remove_residue_group(residue_group=residue_group)
      if (len(chain.residue_groups()) == 0) :
        model.remove_chain(chain=chain)
  atoms = hierarchy.atoms()
  new_occ = flex.double(atoms.size(), 1.0)
  atoms.set_occ(new_occ)
  atoms_size_post = hierarchy.atoms().size()
  if atoms_size_pre != atoms_size_post:
    pdb_file_removed_alt_confs = pdb_file[0:-4]+'_removed_alt_confs.pdb'
    print >> log, "\nRemoving alternative conformations"
    print >> log, "All occupancies reset to 1.0"
    print >> log, "New PDB : ", pdb_file_removed_alt_confs, "\n"
    hierarchy.write_pdb_file(file_name        = pdb_file_removed_alt_confs,
                             crystal_symmetry = pdb_inp.crystal_symmetry())
    processed_pdb_file, pdb_inp = \
    processed_pdb_files_srv.process_pdb_files(pdb_file_names = [pdb_file_removed_alt_confs])

  if er_params.high_resolution is not None:
    d_min = er_params.high_resolution
  else:
    d_min = f_obs.d_min()
  xsfppf = mmtbx.utils.xray_structures_from_processed_pdb_file(
    processed_pdb_file = processed_pdb_file,
    scattering_table   = "wk1995",
    d_min               = d_min,
    log                = log)
  if(len(xsfppf.xray_structures) > 1):
    raise Sorry("Multiple models not supported.")
  xray_structure = xsfppf.xray_structures[0].deep_copy_scatterers()

  # Geometry manager
  sctr_keys = \
         xray_structure.scattering_type_registry().type_count_dict().keys()
  has_hd = "H" in sctr_keys or "D" in sctr_keys

  geometry = processed_pdb_file.geometry_restraints_manager(
      show_energies                = False,
      plain_pairs_radius           = 5,
      params_edits                 = er_params.refinement.geometry_restraints.edits,
      params_remove                = None,
      hydrogen_bond_proxies        = None,
      hydrogen_bond_params         = None,
      custom_nonbonded_exclusions  = None,
      external_energy_function     = None,
      assume_hydrogens_all_missing = not has_hd)

  restraints_manager = mmtbx.restraints.manager(
      geometry      = geometry,
      normalization = True)

  # Refinement flags
  class rf:
    def __init__(self, size):
      self.individual_sites     = True
      self.individual_adp       = False
      self.sites_individual     = flex.bool(size, True)
      self.sites_torsion_angles = None

  refinement_flags = rf(size = xray_structure.scatterers().size())

  # Model
  model = mmtbx.model.manager(
    processed_pdb_files_srv = processed_pdb_files_srv,
    refinement_flags = refinement_flags,
    restraints_manager = restraints_manager,
    xray_structure = xray_structure,
    pdb_hierarchy = hierarchy,
    tls_groups = None,
    anomalous_scatterer_groups = None,
    log = log)

  # Geometry file
  xray_structure = model.xray_structure
  sites_cart = xray_structure.sites_cart()
  site_labels = xray_structure.scatterers().extract_labels()
  model.restraints_manager.geometry.show_sorted(
    sites_cart=sites_cart,
    site_labels=site_labels,
    f=open(er_params.output_file_prefix+'.geo','w') )

  print >> log, "Unit cell                               :", f_obs.unit_cell()
  print >> log, "Space group                             :", f_obs.crystal_symmetry().space_group_info().symbol_and_number()
  print >> log, "Number of symmetry operators            :", f_obs.crystal_symmetry().space_group_info().type().group().order_z()
  print >> log, "Unit cell volume                        : %-15.4f" % f_obs.unit_cell().volume()
  f_obs_labels = f_obs.info().label_string()
  if(cmd_params is not None):
    f_obs = f_obs.resolution_filter(
      d_min = er_params.high_resolution,
      d_max = er_params.low_resolution)
    r_free_flags = r_free_flags.resolution_filter(
      d_min = er_params.high_resolution,
      d_max = er_params.low_resolution)

  fmodel = mmtbx.utils.fmodel_simple(
               f_obs                      = f_obs,
               xray_structures            = [model.xray_structure],
               scattering_table           = "wk1995",
               r_free_flags               = r_free_flags,
               target_name                = er_params.target_name,
               bulk_solvent_and_scaling   = False,
               bss_params                 = None,
               mask_params                = None,
               twin_laws                  = None,
               skip_twin_detection        = True,
               twin_switch_tolerance      = 2.0,
               outliers_rejection         = True,
               bulk_solvent_correction    = True,
               anisotropic_scaling        = True,
               log                        = log)
  if(cmd_params is not None):
    mask_params = cmd_params.extract().ensemble_refinement.mask
  fmodel = mmtbx.f_model.manager(
               mask_params                  = mask_params,
               xray_structure               = model.xray_structure,
               f_obs                        = fmodel.f_obs(),
               r_free_flags                 = fmodel.r_free_flags(),
               target_name                  = er_params.target_name)
  hd_sel = model.xray_structure.hd_selection()
  model.xray_structure.set_occupancies(
        value     = 1.0,
        selection = hd_sel)
  model.show_occupancy_statistics(out = log)

  fmodel.update_xray_structure(
    xray_structure      = model.xray_structure,
    update_f_calc       = True,
    update_f_mask       = False,
    force_update_f_mask = False)

  n_outl = f_obs.data().size() - fmodel.f_obs().data().size()
  show_data(fmodel          = fmodel,
            n_outl          = n_outl,
            test_flag_value = test_flag_value,
            f_obs_labels    = f_obs_labels,
            log             = log)
  show_model_vs_data(fmodel = fmodel,
                     log    = log)

  ensemble_refinement = run_ensemble_refinement(
      fmodel               = fmodel,
      model                = model,
      params               = cmd_params,
      mtz_dataset_original = mtz_dataset_original,
      log                  = log)

  show_total_time(out = ensemble_refinement.log)
