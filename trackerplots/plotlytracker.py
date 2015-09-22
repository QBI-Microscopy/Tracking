#!/usr/bin/python
#Create contour plots
import csv
import argparse
import sys
import inspect
import os
import copy
import collections
import numpy as np
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.backends.backend_qt5agg
import matplotlib.pyplot as plt
import scipy.interpolate
import plotly.plotly as py
import plotly.tools as tls
from plotly.graph_objs import *

class PlotlyTracker:

    def __init__(self):
        self.initlists()
        self.inputheaders = ['Track', 'Frame','x','y','roundx', 'roundy',
         'dx', 'dy','rho', 'theta', 'intensity','framecount']
        self.xylist = dict()


    def initlists(self):
        #initialize
        self.x = []
        self.y = []
        self.z = []
        self.t = []
        self.name = ''
        self.intervals = 100 #interpolation of resolution
    '''Load from a CSV file produced by TrackerApp
    '''
    def load(self,inputfilename):
        #Open input file
        if sys.version_info >= (3,0,0):
            fi = open(inputfilename, 'r', newline='')
        else:
            fi = open(inputfilename, 'rb')
        self.name = os.path.basename(inputfilename)
        self.initlists()
        with fi as csvfile:
            csvfile.seek(0)
            fh = csv.DictReader(csvfile)
            for row in fh:
                self.x.append(float(row['x']))
                self.y.append(float(row['y']))
                self.z.append(float(row['rho']))
                self.t.append(int(row['Frame']))

    def loadrow(self,x,y,z,t):
        self.x.append(x)
        self.y.append(y)
        self.z.append(z)
        self.t.append(t)

    def quiver_region(self,fname='test'):
        plotly_fig = tls.mpl_to_plotly(fig)

        x = self.x
        y = self.y
        z = self.z

        # Set up a regular grid of interpolation points
        xi, yi = np.linspace(min(x), max(x), intervals), np.linspace(min(y), max(y), intervals)
        xi, yi = np.meshgrid(xi, yi)

        # Interpolate
        rbf = scipy.interpolate.Rbf(x, y, z, function='linear')
        zi = rbf(xi, yi)
        quiver = tls.TraceFactory.create_quiver()
        data = Data([quiver])
        plotly_fig = Figure(data=data)
        unique_url = py.plot(plotly_fig, filename = self.name)
        msg =("Plotly Plot saved to " + unique_url)

        plt.close()
        return msg


## Main
if __name__ == "__main__":
#####Plotly needs an account - follow instructions: https://plot.ly/python/getting-started/
    print(inspect.getfile(inspect.currentframe())) # script filename (usually with path)
    defaultSrcPath = os.getcwd() # current directory
    defaultDataPath = 'sampledata'
    print("Default path: " , defaultDataPath)
    defaultDatafile = defaultDataPath + '/ROI_111_114.csv'

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", dest = "filename",
        default = defaultDatafile, help="Full path to input file")

    args = parser.parse_args()
   # if (not file_check(args.filename)):
   #     sys.exit()

    tplot = PlotlyTracker()
    tplot.load(args.filename)
    print("Loaded: ", len(tplot.xylist))
    msg = tplot.quiver_region()
    print(msg)
