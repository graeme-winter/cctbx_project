from __future__ import division

'''
Author      : Lyubimov, A.Y.
Created     : 05/25/2016
Last Changed: 10/21/2018
Description : PRIME Result Plotter module
'''

import wx
import os
import numpy as np

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import gridspec, rc

from libtbx import utils as u

from iota.components.iota_ui_base import IOTABaseFrame, IOTABasePanel

class PlotWindow(IOTABaseFrame):
  def __init__(self, parent, id, title, plot_panel=None):
    IOTABaseFrame.__init__(self, parent, id, title)

    self.initialize_toolbar()
    self.tb_btn_quit = self.add_tool(label='Quit',
                                     bitmap=('actions', 'exit'),
                                     shortHelp='Quit')
    self.tb_btn_save = self.add_tool(label='Save',
                                     bitmap=('actions', 'save_all'),
                                     shortHelp='Save image in various formats')
    self.realize_toolbar()

    self.Bind(wx.EVT_TOOL, self.onSave, self.tb_btn_save)
    self.Bind(wx.EVT_TOOL, self.onQuit, self.tb_btn_quit)

    self.plot_panel = plot_panel

  def plot(self):
    if self.plot_panel:
      self.main_sizer.Add(self.plot_panel, 1, flag=wx.EXPAND)
      self.SetSize(self.plot_panel.canvas.GetSize())
      self.plot_panel.canvas.draw()
      self.Layout()

  def onSave(self, e):
    save_dlg = wx.FileDialog(self,
                             message="Save Image",
                             defaultDir=os.curdir,
                             defaultFile="*",
                             wildcard="*",
                             style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
                             )
    if save_dlg.ShowModal() == wx.ID_OK:
      script_filepath = save_dlg.GetPath()
      self.plot_panel.figure.savefig(script_filepath, format='pdf',
                                     bbox_inches=0)

  def onQuit(self, e):
    self.Close()

class Plotter(IOTABasePanel):
  ''' Class with function to plot various PRIME charts (includes Table 1) '''

  def __init__(self, parent, info, output_dir=None, anomalous_flag=False,
               *args, **kwargs):
    IOTABasePanel.__init__(self, parent=parent, *args, **kwargs)
    self.target_anomalous_flag = anomalous_flag
    self.info = info
    self.output_dir = output_dir

  def initialize_figure(self, figsize=(8, 8)):
    self.figure = Figure(figsize=figsize)
    self.canvas = FigureCanvas(self, -1, self.figure)
    self.main_sizer.Add(self.canvas, 1, flag=wx.EXPAND)

  def table_one(self):
    ''' Constructs Table 1 for GUI or logging '''

    A = u'\N{ANGSTROM SIGN}'
    d = u'\N{DEGREE SIGN}'
    a = u'\N{GREEK SMALL LETTER ALPHA}'
    b = u'\N{GREEK SMALL LETTER BETA}'
    g = u'\N{GREEK SMALL LETTER GAMMA}'
    s = u'\N{GREEK SMALL LETTER SIGMA}'
    h = u'\u00BD'

    uc_edges = '{:4.2f}, {:4.2f}, {:4.2f}'.format(self.info['mean_a'][-1],
                                                  self.info['mean_b'][-1],
                                                  self.info['mean_c'][-1])
    uc_angles = '{:4.2f}, {:4.2f}, {:4.2f}'.format(self.info['mean_alpha'][-1],
                                                   self.info['mean_beta'][-1],
                                                   self.info['mean_gamma'][-1])
    res_total = '{:4.2f} - {:4.2f}'.format(self.info['total_res_max'][-1],
                                           self.info['total_res_min'][-1])
    res_last_shell = '{:4.2f} - {:4.2f}' \
                     ''.format(self.info['binned_resolution'][-1][-2],
                               self.info['binned_resolution'][-1][-1])
    t1_rlabels = [u.to_unicode(u'No. of accepted images'),
                  u.to_unicode(u'No. of rejected images'),
                  u.to_unicode(u'Space Group'),
                  u.to_unicode(u'Cell dimensions'),
                  u.to_unicode(u'  a, b, c ({})  '.format(A)),
                  u.to_unicode(u'  {}, {}, {} ({})    '.format(a, b, g, d)),
                  u.to_unicode(u'Resolution ({})  '.format(A)),
                  u.to_unicode(u'Completeness (%)'),
                  u.to_unicode(u'Multiplicity'),
                  u.to_unicode(u'I / {}(I) '.format(s)),
                  u.to_unicode(u'CC{} '.format(h)),
                  u.to_unicode(u'R_merge')]

    n_frames_bad = self.info['n_frames_bad_cc'][-1]      + \
                   self.info['n_frames_bad_G'][-1]       + \
                   self.info['n_frames_bad_uc'][-1]      + \
                   self.info['n_frames_bad_gamma_e'][-1] + \
                   self.info['n_frames_bad_SE'][-1]
    t1_data = [['{}'.format(self.info['n_frames_good'][-1])],
               ['{}'.format(n_frames_bad)],
               ['{}'.format(self.info['space_group_info'][
                              -1].symbol_and_number())],
               [''],
               ['{}'.format(uc_edges)],
               ['{}'.format(uc_angles)],
               ['{} ({})'.format(res_total, res_last_shell)],
               ['{:4.2f} ({:4.2f})'.format(self.info['total_completeness'][-1],
                                    self.info['binned_completeness'][-1][-1])],
               ['{:4.2f} ({:4.2f})'.format(self.info['total_n_obs'][-1],
                                          self.info['binned_n_obs'][-1][-1])],
               ['{:4.2f} ({:4.2f})'.format(self.info['total_i_o_sigi'][-1],
                                        self.info['binned_i_o_sigi'][-1][-1])],
               ['{:4.2f} ({:4.2f})'.format(self.info['total_cc12'][-1],
                                          self.info['binned_cc12'][-1][-1]*100)],
               ['{:4.2f} ({:4.2f})'.format(self.info['total_rmerge'][-1],
                                          self.info['binned_rmerge'][-1][-1])]
               ]

    return t1_rlabels, t1_data


  def stat_charts(self):
    ''' Displays charts of CC1/2, Completeness, Multiplicity and I / sig(I)
        per resolution bin after the final cycle of post-refinement '''

    gsp = gridspec.GridSpec(2, 2)

    self.figure.set_alpha(0)
    rc('font', family='sans-serif', size=12)
    rc('mathtext', default='regular')

    x = self.info['binned_resolution'][-1]
    bins = np.arange(len(x))
    xlabels = ["{:.2f}".format(i) for i in x]
    sel_bins = bins[0::len(bins) // 6]
    sel_xlabels = [xlabels[t] for t in sel_bins]

    # Plot CC1/2 vs. resolution
    ax_cc12 = self.figure.add_subplot(gsp[0])
    reslabel = 'Resolution ({})'.format(r'$\AA$')
    ax_cc12.set_xlabel(reslabel, fontsize=15)
    ax_cc12.ticklabel_format(axis='y', style='plain')
    ax_cc12.set_ylim(0, 100)

    if self.target_anomalous_flag:
      ax_cc12.set_ylabel(r'$CC_{1/2}$ anom (%)', fontsize=15)
    else:
      ax_cc12.set_ylabel(r'$CC_{1/2}$ (%)', fontsize=15)
    ax_cc12.set_xticks(sel_bins)
    ax_cc12.set_xticklabels(sel_xlabels)
    ax_cc12.grid(True)
    cc12_start_percent = [c * 100 for c in self.info['binned_cc12'][0]]
    cc12_end_percent = [c * 100 for c in self.info['binned_cc12'][-1]]
    start, = ax_cc12.plot(bins, cc12_start_percent, c='#7fcdbb', lw=2)
    end, = ax_cc12.plot(bins, cc12_end_percent, c='#2c7fb8', lw=3)
    labels = ['Initial', 'Final']
    ax_cc12.legend([start, end], labels, loc='lower left',
                          fontsize=9, fancybox=True)

    # Plot Completeness vs. resolution
    ax_comp = self.figure.add_subplot(gsp[1])
    ax_comp.set_xlabel(reslabel, fontsize=15)
    ax_comp.ticklabel_format(axis='y', style='plain')
    ax_comp.set_ylabel('Completeness (%)', fontsize=15)
    ax_comp.set_xticks(sel_bins)
    ax_comp.set_xticklabels(sel_xlabels)
    ax_comp.set_ylim(0, 100)
    ax_comp.grid(True)
    start, = ax_comp.plot(bins, self.info['binned_completeness'][0],
                         c='#7fcdbb', lw=2)
    end, = ax_comp.plot(bins, self.info['binned_completeness'][-1], c='#2c7fb8',
                   lw=3)
    labels = ['Initial', 'Final']
    ax_comp.legend([start, end], labels, loc='lower left',
                          fontsize=9, fancybox=True)

    # Plot Multiplicity (no. of observations) vs. resolution
    ax_mult = self.figure.add_subplot(gsp[2])
    ax_mult.set_xlabel(reslabel, fontsize=15)
    ax_mult.ticklabel_format(axis='y', style='plain')
    ax_mult.set_ylabel('# of Observations', fontsize=15)
    ax_mult.set_xticks(sel_bins)
    ax_mult.set_xticklabels(sel_xlabels)
    ax_mult.grid(True)
    start, = ax_mult.plot(bins, self.info['binned_n_obs'][0], c='#7fcdbb', lw=2)
    end, = ax_mult.plot(bins, self.info['binned_n_obs'][-1], c='#2c7fb8', lw=3)
    labels = ['Initial', 'Final']
    ax_mult.legend([start, end], labels, loc='lower left',
                          fontsize=9, fancybox=True)

    # Plot I / sig(I) vs. resolution
    ax_i_sigi = self.figure.add_subplot(gsp[3])
    ax_i_sigi.set_xlabel(reslabel, fontsize=15)
    ax_i_sigi.ticklabel_format(axis='y', style='plain')
    ax_i_sigi.set_ylabel(r'I / $\sigma$(I)', fontsize=15)
    ax_i_sigi.set_xticks(sel_bins)
    ax_i_sigi.set_xticklabels(sel_xlabels)
    ax_i_sigi.grid(True)
    start, = ax_i_sigi.plot(bins, self.info['binned_i_o_sigi'][0], c='#7fcdbb',
                        lw=2)
    end, = ax_i_sigi.plot(bins, self.info['binned_i_o_sigi'][-1], c='#2c7fb8',
                       lw=3)
    labels = ['Initial', 'Final']
    ax_i_sigi.legend([start, end], labels, loc='lower left',
                          fontsize=9, fancybox=True)

    self.figure.set_tight_layout(True)
