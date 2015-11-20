#!/usr/bin/python3
'''
    QBI Meunier Tracker APP: Custom Tracker plots
    *******************************************************************************
    Copyright (C) 2015  QBI Software, The University of Queensland

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
'''
import numpy as np
import scipy.io
import os
from tracking import Tracker

class TrackerSPT:

    def __init__(self):
        # Initialize fields (default vbSPT)
        self.CylinderL = 40 # nm (length of cylindrical part only)
        self.Radius = 20  # nm    (spherical end caps, and cylinder radius)
        # initiate options
        self.timestep = 0.02 # [20ms]
        self.stepSize = 5 #[nm]
        self.locAccuracy = 0 #[nm]
        self.transMat = []#[0.958 0.0421;0.084 0.9158] # [/timestep]
        self.transRate = []#[-15 15;30 -30] # [/s]
        self.occProb = 0
        self.Dapp = 0
        self.trajLengths = 0
        self.runs = 1
        self.do_steadystate = False
        self.do_parallel = False
        self.do_single = False
        self.do_transRate = False
        self.do_transMat = False
        self.finalTraj = {}
        self.tracker = Tracker()
        self.fields = dict()
    """Output to matlab file for use with vbSPT
    """
    def save_mat(self, fullfilename):
        # List the parameters
        self.fields['trajLengths']=self.trajLengths
        self.fields['runs']=self.runs
        self.fields['do_steadystate']=self.do_steadystate
        self.fields['do_parallel']=self.do_parallel
        self.fields['do_single']=self.do_single
        self.fields['cylL']=self.CylinderL
        self.fields['cylRadius']=self.Radius
        self.fields['timestep']=self.timestep
        self.fields['stepSize']=self.stepSize
        self.fields['locAccuracy']=self.locAccuracy
        self.fields['finalTraj']=T1
        self.fields['numTraj']=len(self.trajLengths)
        self.fields['avTrajLength']=np.mean(self.trajLengths)
        self.fields['shortestTraj']=min(self.trajLengths)
        self.fields['longestTraj']=max(self.trajLengths)
        self.fields['Dapp']=self.Dapp
        self.fields['occProb']=self.occProb
        self.fields['transMat']=self.transMat
        self.fields['transRate']=self.transRate

        scipy.io.savemat(fullfilename,appendmat=True,mdict=self.fields)

    """ Load data from Tracker obj
    """
    def load_data(self, tracker):
        #detect track numbers
        self.numTraj = len(tracker.plotter)
        self.finalTraj = {}
        self.trajLengths = [0 for x in range(self.numTraj)]
        #Load from tracker data
        plotlist = list(tracker.plotter.items())
        # for each plot
        for track in plotlist:
            tracknum = track[0]
            tracklist = track[1]
            for co in tracklist:
                self.finalTraj[tracknum].append([co.x, co.y, co.frame])
            self.trajLengths[tracknum] = len(tracklist)


