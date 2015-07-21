#! /usr/bin/python
# Tracking.py
# for Andreas
# Description: Count of tracking particles
# Input: Output file from Tracking program (in csv)
# Output: csv file with count
__author__ = "Liz Cooper-Williams (QBI)"
__date__ = "$11/06/2015 2:09:57 PM$"
__version__ = 1.1

import csv
import argparse
import sys
import inspect
import os
import copy
import collections
import numpy as np
import matplotlib.pyplot as plt


def get_filename(prompt, complaint='Unable to find file!'):
    while True:
        filename = eval(input(prompt))
        if open(filename, 'rb'):
            return filename
        else:
            raise IOError('File Error')
        print(complaint)
        return filename


def file_check(fn):
    try:
        open(fn, "r")
        return 1
    except IOError:
        print("Error: File not found or cannot be accessed:", fn)
        return 0
    except PermissionError:
        print("Error: File maybe open in another program or does not exist:", fn)
        return 0

class Coord:
    def __init__(self, track=0, frame=0, xcoord=0,ycoord=0, intensity=0):
        self.track = track
        self.frame = frame
        self.x = xcoord
        self.y = ycoord
        self.dx = 0
        self.dy = 0
        self.rho = 0
        self.theta = 0
        self.intensity = intensity
        self.framecount = 1


    def get_headers(self):
        return self.fieldnames
        ''' Determines if x,y coordinates have changed
    Args: (x,y) and (x1,y1) - 2 sets of coordinates
           f - number of decimal places for rounding coord values (default is 1)
    Returns 1 if changed (moved) or 0 if not changed
   '''
    def has_moved(self):
        if((self.x,self.y) == (0,0) or (self.xcache,self.ycache) ==(0,0)):
            return 0
        elif ((round(self.x,self.numdecimal), round(self.y,self.numdecimal)) ==
        (round(self.xcache,self.numdecimal), round(self.ycache,self.numdecimal))):
            return 0
        else:
            return 1



    '''Returns compiled row to output
       fieldnames must match fieldnames in Tracker
       '''
    def get_rowoutput(self, numdecimal):
        myx = self.x
        myy = self.y

        row = {'Track': str(self.track),
                'Frame': str(self.frame),
                'x':myx, 'y':myy,
                'roundx':round(myx, numdecimal),
                'roundy':round(myy, numdecimal),
                'dx': self.dx,
                'dy': self.dy,
                'rho': self.getpolar_rho(self.dx,self.dy),
                'theta' : self.getpolar_theta(self.dx,self.dy),
                'intensity': self.intensity,
                'framecount': str(self.framecount)
                }
        return row

    def set_first(self):
        if self.framecount > 1:
            self.first = self.frame-self.framecount+1
        else:
            self.first = ''

    def getpolar_rho(self, x,y):
        rho = np.sqrt(x**2 + y**2)
        return rho

    def getpolar_theta(self, x,y):
        theta = np.arctan2(y,x)
        return theta


class Tracker():

    def __init__(self):
        self.counter = 0
        self.track = 0
        self.ln = 0
        self.cache = 0
        self.numdecimal = 1
        self.coordlist = dict()
        self.plotter = dict()
        self.allplot = collections.OrderedDict()
        self.fieldnames = ['Track', 'Frame','x','y','roundx', 'roundy',
         'dx', 'dy','rho', 'theta', 'intensity','framecount']
        self.inputheaders = ['TRACK NUMBER', 'frame number', 'x', 'y', 'intensity']
        self.outputdir = '.'
        self.fromplot = 0
        self.toplot = 0
        self.init_allplots()
        
    def init_allplots(self):
        #for all tracks
        self.allx = []
        self.ally = []
        self.allrho = []
        self.alltheta = []
        self.alltracks = 0
    ''' Calculates average of sequence of int, float
     returns average or 0 if empty sequence
    '''
    def avg(self,seq):
        if (len(seq) > 0):
            return sum(seq)/len(seq)
        else:
            return 0

    def get_headers(self):
        #return keys Coord.getrowoutput(0)
        return self.fieldnames

    def set_cache(self,c):
        self.cache = c
    
    def set_outputdir(self, odir):
        self.outputdir = odir
    
    def set_fromplot(self, fromplot):
        self.fromplot = fromplot
    def set_toplot(self, toplot):
        self.toplot = toplot    
    def checkinputheaders(self, inputfilename):
        valid = True
        #Open input file
        if sys.version_info >= (3,0,0):
            fi = open(inputfilename, 'r', newline='')
        else:
            fi = open(inputfilename, 'rb')
        with fi as csvfile:
            inputreader = csv.DictReader(csvfile)
            for hdr in self.inputheaders:
                if hdr not in inputreader.fieldnames:
                    valid = False
                    break
        
        return valid     
                    
    def load_input(self,inputfilename):
        #Open input file
        if sys.version_info >= (3,0,0):
            fi = open(inputfilename, 'r', newline='')
        else:
            fi = open(inputfilename, 'rb')

        with fi as csvfile:
            fh = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            for row in fh:
                self.ln = fh.line_num
                if (len(row) == 0):
                    fh.next()
                #Change in x,y wrt next row:  x(t+1) - x(t)
                coord = Coord(int(row['TRACK NUMBER']),
                        int(row['frame number']),
                        float(row['x']),float(row['y']),
                        float(row['intensity']) )

                if (self.track != coord.track):
                    print("TRACK:" + str(self.track))
                    self.track = int(row['TRACK NUMBER'])
                else:
                    self.cache.dx = coord.x - self.cache.x
                    self.cache.dy = coord.y - self.cache.y
                    roundx = round(self.cache.x,self.numdecimal)
                    roundy = round(self.cache.y,self.numdecimal)

                    if (roundx,roundy) in self.coordlist:
                        self.cache.framecount += 1
                        self.coordlist[(roundx,roundy)].append(self.cache)
                    else:
                        self.coordlist.update({(roundx,roundy):[]})
                        self.coordlist[(roundx,roundy)].append(self.cache)
                self.set_cache(coord)
                self.counter += 1

    def write_output(self, outfilename):
        if sys.version_info >= (3,0,0):
            fo = open(outfilename, 'w', newline='')
        else:
            fo = open(outfilename, 'wb')
        print("DEBUG: Output file=", outfilename)
        with fo as outfile:
            fieldnames = self.get_headers()
            writer = csv.DictWriter(outfile, delimiter=',',dialect=csv.excel, fieldnames=fieldnames)
            writer.writeheader()
            for co in self.coordlist:
                
                if (len(self.coordlist[co]) > 1):
                    avg_dx = []
                    avg_dy = []
                    avg_intensity =[]
                    avg_frame = []
                    co1 = self.coordlist[co][0]
                    
                    for avgco in self.coordlist[co]:
                        #All coords averaged VS per track
                        avg_dx.append(avgco.dx)
                        avg_dy.append(avgco.dy)
                        avg_frame.append(avgco.frame)
                        avg_intensity.append(avgco.intensity)
                    myco = Coord(co1.track, self.avg(avg_frame),co1.x, co1.y,self.avg(avg_intensity))
                    myco.dx = self.avg(avg_dx)
                    myco.dy = self.avg(avg_dy)
                    myco.framecount = len(self.coordlist[co])
                else:
                    myco = self.coordlist[co][0]
                writer.writerow(myco.get_rowoutput(self.numdecimal))
                if (myco.track not in self.plotter):
                    self.plotter.update({myco.track:[]})
                self.plotter[myco.track].append(myco)
        
    def plottrack(self, trak, totalplots=0):
        #create a plot of a track
        plotdir=self.outputdir
        x = []
        y = []
        rho = []
        theta = []
        mytitle = "Track: " + str(trak)
        print(mytitle)
        for tn in self.plotter[trak]:
            x.append(tn.x)
            y.append(tn.y)
            rho.append(tn.getpolar_rho(tn.dx,tn.dy))
            theta.append(tn.getpolar_theta(tn.dx,tn.dy))
        print("Points:", len(x))
        fig = plt.figure(trak)
        lines = plt.quiver(x,y,rho,theta)
        plt.setp(lines, color='b', linewidth=0.2)
        plt.xlabel('x')
        plt.ylabel('y')
        plt.title(mytitle)
        #Write to file
        filename = plotdir + "Track_" + str(trak) + ".png"
        fig.savefig(filename, dpi=300, orientation='landscape', format='png')
        #Total plots if option set
        if (totalplots > 0):
            self.allx += x
            self.ally += y
            self.allrho += rho
            self.alltheta += theta
            self.alltracks += 1
        plt.cla()
        plt.clf()
        plt.close()
        msg ="Plot saved to " + filename
        print(msg)
        return msg

    def create_plots(self):
        #Check input
        plotdir=self.outputdir
        start=self.fromplot
        end=self.toplot
        #output msgs
        msgs = []
        #limit popups
        showplots = True
        if (end-start) > 10:
           showplots = False
        #for all tracks
        allx = []
        ally = []
        allrho = []
        alltheta = []
        alltracks = 0
        counter = 0
        for trak in self.plotter:
            #for each track
            x = []
            y = []
            rho = []
            theta = []
            if (counter >= start and counter < end):
                mytitle = "Track: " + str(trak)
                print(mytitle)
                for tn in self.plotter[trak]:
                    x.append(tn.x)
                    y.append(tn.y)
                    rho.append(tn.getpolar_rho(tn.dx,tn.dy))
                    theta.append(tn.getpolar_theta(tn.dx,tn.dy))
                print("Points:", len(x))
                fig = plt.figure(trak)
                lines = plt.quiver(x,y,rho,theta)
                plt.setp(lines, color='b', linewidth=0.2)
                plt.xlabel('x')
                plt.ylabel('y')
                plt.title(mytitle)
                #Write to file
                filename = plotdir + "Track_" + str(trak) + ".png"
                fig.savefig(filename, dpi=300, orientation='landscape', format='png')
                print("Plot saved to ", filename)
                msgs.append("Plot saved to " + filename)
                #Popup if OK
                if (showplots):
                    plt.show()
                plt.cla()
                plt.clf()
                plt.close()
                #ADD ALL TRACKS TO ONE
                allx += x
                ally += y
                allrho += rho
                alltheta += theta
                alltracks += 1
            counter += 1
        #Print all
        fig = plt.figure(len(self.plotter) + 1)
        mytitle = "All " + str(alltracks) + " tracks (" + str(len(allx)) + " points)"
        print(mytitle)
        lines = plt.quiver(allx,ally,allrho,alltheta)
        plt.setp(lines, color='b', linewidth=0.2)
        plt.xlabel('x')
        plt.ylabel('y')
        plt.title(mytitle)
        plt.show()
        filename = plotdir + "Tracks_" + start + "_" + end + ".png"
        fig.savefig(filename, dpi=300, orientation='landscape',format='png')
        print("Plot saved to ", filename)
        msgs.append("Plot saved to " + filename)
        plt.close()
        
        return msgs

## Main
if __name__ == "__main__":

    print(inspect.getfile(inspect.currentframe())) # script filename (usually with path)
    defaultSrcPath = os.getcwd() # current directory
    defaultDataPath = 'D:/Data/DevTracking/data'
    print("Default path: " , defaultDataPath)
    defaultDatafile = defaultDataPath + '/trackfile.csv'
    defaultOutfile = defaultDataPath + '/output/outfile.csv'

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", dest = "filename",
        default = defaultDatafile, help="Full path to input file")
    parser.add_argument("-o", "--output", dest = "outfilename",
        default = defaultOutfile, help="Full path to output file")
    parser.add_argument("-n", "--num", dest = "numdecimal",
        default = 1, help="Number of decimal places for rounding")
    parser.add_argument("-p", "--plots", dest = "pythonplot",
        default = '1', help="Generate quiverplots (default is 0, all is -1, none is 0, range is 0-10 (no spaces)")

    args = parser.parse_args()
    if (not file_check(args.filename)):
        sys.exit()
    if (not file_check(args.outfilename)):
        sys.exit()
    #update data path if not default
    if (args.outfilename != defaultOutfile):
        idx = args.outfilename.rindex(os.path.sep)
        defaultDataPath = args.outfilename[0:idx]
    tracker = Tracker()
    tracker.numdecimal = int(args.numdecimal)
    #Check input file has correct headings
    if (not tracker.checkinputheaders(args.filename)):
       print("***ERROR: CSV Input file headers not matching, exiting ***")
       print("CSV HEADERS SHOULD BE:")
       for hdr in tracker.inputheaders:
           print(hdr)
    else:
        print("Starting ...")
        tracker.load_input(args.filename)
        tracker.write_output(args.outfilename)
        print("...Completed")
        print("TOTAL ROWS:", tracker.counter)
    
        if (tracker.counter > 0):
            print("Output file written to: ", args.outfilename)
            ## ADDED PLOTS
            plotstart = 0
            plotend = 0
            if ( '-' in args.pythonplot):
                parts = args.pythonplot.split('-')
                plotstart = int(parts[0])
                plotend = int(parts[1])
                plotnum = plotend - plotstart
            else:
                plotnum = int(args.pythonplot)
           
            if (plotnum < 0):
                plotnum = tracker.counter
                plotstart = 0
                plotend = tracker.counter
            if (plotnum > 0):
                if (plotend - plotstart) != plotnum:
                    plotstart = 0
                    plotend = plotnum
                
                print("Creating plots=", plotnum)
                tracker.set_outputdir(defaultDataPath + os.path.sep)
                tracker.set_fromplot(plotstart)
                tracker.set_toplot(plotend)
                tracker.create_plots(defaultDataPath, plotstart, plotend)
        else:
            print("Error occurred - please check data files")

    
