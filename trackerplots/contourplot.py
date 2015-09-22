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

class ContourPlot:

    def __init__(self):
        self.initlists()
        self.inputheaders = ['Track', 'Frame','x','y','roundx', 'roundy',
         'dx', 'dy','rho', 'theta', 'intensity','framecount']
        self.xylist = dict()
        self.linesonly = False
        self.showtitle = True
        self.newfig = True

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

    def loadarrays(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def contour_region(self,fname='test'):
        print("Plotting contour plot")
        MAX = 1000000
        intervals = self.intervals
        totalpoints = len(self.x)
        if (len(self.name)>0):
            fname = self.name

        if (totalpoints > 0 & totalpoints < MAX):
            if self.newfig:
                fig = plt.figure()
            mytitle = "Speed heatmap: " + fname + "(" + str(totalpoints) + " points)"
            print(mytitle)
            x = self.x
            y = self.y
            z = self.z
            #t = self.t
            #margin = 10 * (min(x)/100)
            # Set up a regular grid of interpolation points
            xi, yi = np.linspace(min(x), max(x), intervals), np.linspace(min(y), max(y), intervals)
            xi, yi = np.meshgrid(xi, yi)

            # Interpolate
            rbf = scipy.interpolate.Rbf(x, y, z, function='linear')
            zi = rbf(xi, yi)
            #fig = plt.figure()
            plt.contour(xi,yi,zi)
            if not self.linesonly:
                plt.imshow(zi, vmin=min(z), vmax=max(z), origin='lower', extent=[min(x), max(x), min(y), max(y)])
                plt.scatter(x, y, c=z)
            plt.colorbar()
            plt.xlabel('x')
            plt.ylabel('y')
            if self.showtitle:
                plt.title(mytitle)
            plt.show()
        else:
            print("No data to plot")


## Main
if __name__ == "__main__":

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

    tplot = ContourPlot()
    tplot.load(args.filename)
    print("Loaded: ", len(tplot.xylist))
    tplot.contour_region()
