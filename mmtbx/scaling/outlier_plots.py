from __future__ import division
from __future__ import print_function
from builtins import range
from iotbx.option_parser import option_parser
from scitbx.array_family import flex
import sys
from libtbx.utils import Sorry
from mmtbx import scaling
import math
from iotbx import data_plots


def plotit(fobs,
           sigma,
           fcalc,
           alpha,
           beta,
           epsilon,
           centric,
           out,
           limit=5.0,
           steps=1000,
           plot_title="Outlier plot"):

  fobs_a    = flex.double( [fobs] )
  fcalc_a   = flex.double( [fcalc] )
  epsilon_a = flex.double( [epsilon] )
  alpha_a   = flex.double( [alpha] )
  beta_a    = flex.double( [beta] )
  centric_a = flex.bool  ( [centric] )

  p_calc = scaling.likelihood_ratio_outlier_test(
    fobs_a,
    None,
    fcalc_a,
    epsilon_a,
    centric_a,
    alpha_a,
    beta_a)
  print(file=out)
  print("#Input parameters: ", file=out)
  print("#Title        : ", plot_title, file=out)
  print("#F-calc       : ", fcalc, file=out)
  print("#F-obs        : ", fobs, file=out)
  print("#epsilon      : ", epsilon, file=out)
  print("#alpha        : ", alpha, file=out)
  print("#beta         : ", beta, file=out)
  print("#centric      : ", centric, file=out)
  mode = p_calc.posterior_mode()[0]

  snd_der = math.sqrt(1.0/ math.fabs( p_calc.posterior_mode_snd_der()[0] )  )
  print("#A Gaussian approximation of the likelihood function", file=out)
  print("#could be constructed as follows with: ", file=out)
  print("# exp[-(fobs-mode)**2/(2*stdev**2)] /(sqrt(2 pi) stdev)", file=out)
  print("#with", file=out)
  print("#mode         = ", mode, file=out)
  print("#stdev        = ", snd_der, file=out)
  print(file=out)
  print("#The log likelihood values for the mode and ", file=out)
  print("#observed values are", file=out)
  print("#Log[P(fobs)] : ",  p_calc.log_likelihood()[0], file=out)
  print("#Log[P(mode)] : ",  p_calc.posterior_mode_log_likelihood()[0], file=out)
  print("#Their difference is:", file=out)
  print("#delta        : ",  p_calc.log_likelihood()[0]-p_calc.posterior_mode_log_likelihood()[0], file=out)
  print("#", file=out)
  mean_fobs = p_calc.mean_fobs()
  print("#mean f_obs   : ", mean_fobs[0], "   (first moment)", file=out)


  low_limit = mode-snd_der*limit
  if low_limit<0:
    low_limit=0
  high_limit = mode+limit*snd_der

  if fobs < low_limit:
    low_limit = fobs-2.0*snd_der
    if low_limit<0:
      low_limit=0
  if fobs > high_limit:
    high_limit = fobs+2.0*snd_der

  fobs_a = flex.double( list(range(steps)) )*(
    high_limit-low_limit)/float(steps)+low_limit

  fcalc_a   = flex.double( [fcalc]*steps )
  epsilon_a = flex.double( [epsilon]*steps )
  alpha_a   = flex.double( [alpha]*steps )
  beta_a    = flex.double( [beta]*steps )
  centric_a = flex.bool  ( [centric]*steps )

  p_calc = scaling.likelihood_ratio_outlier_test(
    fobs_a,
    None,
    fcalc_a,
    epsilon_a,
    centric_a,
    alpha_a,
    beta_a)

  ll = p_calc.log_likelihood()    #-p_calc.posterior_mode_log_likelihood()
  ll = flex.exp( ll )
  if (sigma is None) or (sigma <=0 ):
    sigma=fobs/30.0

  obs_gauss = (fobs_a - fobs)/float(sigma)
  obs_gauss = flex.exp( -obs_gauss*obs_gauss/2.0 ) /(
    math.sqrt(2.0*math.pi*sigma*sigma))

  max_ll = flex.max( ll )*1.10
  truncate_mask = flex.bool( obs_gauss >= max_ll )
  obs_gauss = obs_gauss.set_selected( truncate_mask, max_ll )


  ccp4_loggraph_plot = data_plots.plot_data(
    plot_title=plot_title,
    x_label = 'Fobs',
    y_label = 'P(Fobs)',
    x_data = fobs_a,
    y_data = ll,
    y_legend = 'P(Fobs|Fcalc,alpha,beta)',
    comments = 'Fobs=%5.2f, sigma=%5.2f, Fcalc=%5.2f'%(fobs,sigma,fcalc) )
  ccp4_loggraph_plot.add_data(
    y_data = obs_gauss,
    y_legend = "P(Fobs|<Fobs>,sigma)"
    )
  data_plots.plot_data_loggraph(ccp4_loggraph_plot,out)

def run(args):
  command_line = (option_parser(
    usage="mmtbx.p-plotter [options]",
    description="produces a gnuplot plot")
                  .option(None, "--fobs",
                          action="store",
                          type="float",
                          help="F obs",
                          metavar="FLOAT")
                  .option( None, "--sigma",
                          action="store",
                          type="float",
                          help="sigma Fobs",
                          metavar="FLOAT")
                  .option(None, "--fcalc",
                          action="store",
                          type="float",
                          help="F calc",
                          metavar="FLOAT")
                  .option(None, "--alpha",
                          action="store",
                          type="float",
                          help="alpha",
                          metavar="FLOAT")
                  .option(None, "--beta",
                          action="store",
                          type="float",
                          help="beta")
                  .option(None, "--epsilon",
                          action="store",
                          type="float",
                          help="epsilon")
                  .option(None, "--centric",
                          action="store_true",
                          default=False,
                          help="centricity flag")
                  .option(None, "--limit",
                          action="store",
                          type="float",
                          default=10,
                          help="plotting limit")
                  .option(None, "--steps",
                          action="store",
                          type="int",
                          default=1000,
                          help="number of steps")

                  ).process(args=args)

  if command_line.options.fobs is None:
    raise Sorry("please provide fobs")
  if command_line.options.fcalc is None:
    raise Sorry("please provide fcalc")
  if command_line.options.epsilon is None:
    raise Sorry("please provide epsilon")
  if command_line.options.alpha is None:
    raise Sorry("please provide alpha")
  if command_line.options.beta is None:
    raise Sorry("please provide beta")

  #print dir(command_line.options)
  plottery =  plotit( command_line.options.fobs,
                       command_line.options.sigma,
                       command_line.options.fcalc,
                       command_line.options.alpha,
                       command_line.options.beta,
                       command_line.options.epsilon,
                       command_line.options.centric,
                       sys.stdout,
                       command_line.options.limit,
                       command_line.options.steps)



if (__name__=="__main__"):
  run(sys.argv[0:])
