#include <cctbx/boost_python/flex_fwd.h>

#include <cctbx/sgtbx/change_of_basis_op.h>
#include <boost/python/tuple.hpp>
#include <boost/python/class.hpp>
#include <boost/python/args.hpp>
#include <boost/python/return_value_policy.hpp>
#include <boost/python/copy_const_reference.hpp>

namespace cctbx { namespace sgtbx { namespace boost_python {

namespace {

  struct change_of_basis_op_wrappers : boost::python::pickle_suite
  {
    typedef change_of_basis_op w_t;

    static w_t
    new_denominators_int_int(w_t const& o, int r_den, int t_den)
    {
      return o.new_denominators(r_den, t_den);
    }

    static w_t
    new_denominators_w_t(w_t const& o, w_t const& other)
    {
      return o.new_denominators(other);
    }

    static void
    update_w_t(w_t& o, w_t const& other)
    {
      o.update(other);
    }

    static boost::python::tuple
    getinitargs(w_t const& o)
    {
      return boost::python::make_tuple(o.c().as_xyz());
    }

    static void
    wrap()
    {
      using namespace boost::python;
      typedef return_value_policy<copy_const_reference> ccr;
      class_<w_t>("change_of_basis_op", no_init)
        .def(init<rt_mx const&, rt_mx const&>((
          arg("c"), arg("c_inv"))))
        .def(init<rt_mx const&>((arg("c"))))
        .def(init<std::string const&, optional<const char*, int, int> >((
          arg("symbol"),
          arg("stop_chars"),
          arg("r_den"),
          arg("t_den"))))
        .def(init<optional<int, int> >((
          arg("r_den")=cb_r_den,
          arg("t_den")=cb_t_den)))
        .def("is_valid", &w_t::is_valid)
        .def("identity_op", &w_t::identity_op)
        .def("is_identity_op", &w_t::is_identity_op)
        .def("new_denominators", new_denominators_int_int, (
          arg("r_den"),
          arg("t_den")))
        .def("new_denominators", new_denominators_w_t, (arg("other")))
        .def("c", &w_t::c, ccr())
        .def("c_inv", &w_t::c_inv, ccr())
        .def("select", &w_t::select, (arg("inv")), ccr())
        .def("inverse", &w_t::inverse)
        .def("mod_positive_in_place", &w_t::mod_positive_in_place)
        .def("mod_short_in_place", &w_t::mod_short_in_place)
        .def("mod_short", &w_t::mod_short)
        .def("apply",
          (rt_mx(w_t::*)(rt_mx const&) const)
          &w_t::apply, (arg("s")))
        .def("apply",
          (uctbx::unit_cell(w_t::*)(uctbx::unit_cell const&) const)
          &w_t::apply, (arg("unit_cell")))
        .def("apply",
          (miller::index<>(w_t::*)(miller::index<> const&) const)
          &w_t::apply, (arg("miller_index")))
        .def("apply",
          (af::shared<miller::index<> >(w_t::*)
            (af::const_ref<miller::index<> > const&) const)
              &w_t::apply, (arg("miller_indices")))
        .def("apply_results_in_non_integral_indices",
          (af::shared<std::size_t>(w_t::*)
            (af::const_ref<miller::index<> > const&) const)
              &w_t::apply_results_in_non_integral_indices, (
                arg("miller_indices")))
        .def("__call__",
          (fractional<>(w_t::*)(fractional<> const&) const)
          &w_t::operator(), (arg("site_frac")))
        .def("update", update_w_t, (arg("other")))
        .def("__mul__", &w_t::operator*)
        .def("as_xyz", &w_t::as_xyz, (
          arg("decimal")=false,
          arg("t_first")=false,
          arg("symbol_letters")="xyz",
          arg("separator")=","))
        .def("as_hkl", &w_t::as_hkl, (
          arg("decimal")=false,
          arg("letters_hkl")="hkl",
          arg("separator")=","))
        .def("as_abc", &w_t::as_abc, (
          arg("decimal")=false,
          arg("t_first")=false,
          arg("letters_abc")="abc",
          arg("separator")=","))
        .def("symbol", &w_t::symbol)
        .def("__str__", &w_t::symbol)
        .def_pickle(change_of_basis_op_wrappers())
      ;
    }
  };

} // namespace <anoymous>

  void wrap_change_of_basis_op()
  {
    change_of_basis_op_wrappers::wrap();
  }

}}} // namespace cctbx::sgtbx::boost_python
