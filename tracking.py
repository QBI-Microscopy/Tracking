#! /usr/bin/python3
"""
    QBI Meunier Tracker APP: tracking.py
    **************************************************************
    Description: This script was developed for the Meunier Lab at QBI.
    It analyses particle tracking information and produces plots for review.
    
    Requirements: Python3, PyQt5, matplotlib, numpy, plotly
    UI files: created in Qt Designer, loaded dynamically with uic
    Input: CSV Output file from Tracking program (Metamorph)
    Output: CSV file with processed data, PNG files if Plotting
    
    Copyright (C) 2015  QBI Software, The University of Queensland

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    """
__author__ = "Liz Cooper-Williams (QBI)"
__date__ = "$11/06/2015 2:09:57 PM$"
__version__ = 1.0

import csv
import argparse
import sys
import inspect
import os
import collections
import numpy as np
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point
from trackerplots.contourplot import ContourPlot
from scipy import stats


def get_filename(prompt, complaint='Unable to find file!'):
    while True:
        print(complaint)
        filename = eval(input(prompt))
        if open(filename, 'rb'):
            return filename
        else:
            raise IOError('File Error')

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
    def __init__(self, track=0, frame=0, xcoord=0, ycoord=0, intensity=0):
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
        self.msd = 0
        self.gradient = 0
        self.sd = 0

    def load(self, dx, dy, rho, theta, framecount):
        self.dx = dx
        self.dy = dy
        self.rho = rho
        self.theta = theta
        self.framecount = framecount
        self.gradient = self.dy / self.dx
        #self.sd = self.dx ** 2 + self.dy ** 2

    ''' Determines if x,y coordinates have changed
        Args: (x,y) and (x1,y1) - 2 sets of coordinates
               f - number of decimal places for rounding coord values (default is 1)
        Returns 1 if changed (moved) or 0 if not changed
       '''

    def has_moved(self):
        if ((self.x, self.y) == (0, 0) or (self.xcache, self.ycache) == (0, 0)):
            return 0
        elif ((round(self.x, self.numdecimal), round(self.y, self.numdecimal)) ==
                  (round(self.xcache, self.numdecimal), round(self.ycache, self.numdecimal))):
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
               'x': myx, 'y': myy,
               'roundx': round(myx, numdecimal),
               'roundy': round(myy, numdecimal),
               'dx': self.dx,
               'dy': self.dy,
               'rho': self.rho,  # getpolar_rho(self.dx,self.dy),
               'theta': self.theta,  # getpolar_theta(self.dy,self.dx),
               'intensity': self.intensity,
               'framecount': str(self.framecount),
               #'sd': self.sd
               }
        return row

    def set_first(self):
        if self.framecount > 1:
            self.first = self.frame - self.framecount + 1
        else:
            self.first = ''

    def getpolar_rho(self, x, y):
        rho = np.sqrt(x ** 2 + y ** 2)
        return rho

    def getpolar_theta(self, x, y):
        theta = np.arctan2(y, x)
        return theta


class Tracker:
    def __init__(self):
        self.counter = 0
        self.track = 0
        self.ln = 0
        self.cache = 0
        self.numdecimal = 1
        self.coordlist = dict()
        self.plotter = dict()  # Store coords by track number for individual plots
        self.avgplotter = dict()  # Store averaged coords by track number for full plot
        self.msd = collections.OrderedDict() #dict()
        self.fieldnames = ['Track', 'Frame', 'x', 'y', 'roundx', 'roundy',
                           'dx', 'dy', 'rho', 'theta', 'intensity', 'framecount']
        self.inputheaders = ['TRACK NUMBER', 'frame number', 'x', 'y', 'intensity']
        self.outputdir = '.'
        self.fromplot = 0
        self.toplot = 0
        self.init_allplots()
        self.roilist = []
        self.framerate = 1

    def init_allplots(self):
        # for all tracks
        self.allx = []
        self.ally = []
        self.allrho = []
        self.alltheta = []
        self.alltracks = 0

    ''' Calculates average of sequence of int, float
     returns average or 0 if empty sequence
    '''

    def avg(self, seq):
        if (len(seq) > 0):
            return sum(seq) / len(seq)
        else:
            return 0

    '''
    Calculate MSD for each time interval per track
    Spatial displacement: pos at given t from initial pos
    MSD =<(x(t) - x0)^2>
    '''
    def calculate_msd(self, plot):
        # ptrack = self.getPlotByIndex(self.plotter,tracknum)
        ptracknum = plot[0]
        ptracklist = plot[1]

        # Sort by timeframe
        if (len(ptracklist) > 0):
            tracklist = sorted(ptracklist, key=lambda t: t.frame)
        else:
            tracklist = ptracklist
        msdlist = dict()  # hashlist of msd per time interval
        ln = len(tracklist)
        #compare with each coord for each time interval : 1T, 2T 3T
        for i in range(1, ln - 1):
            sd = 0
            ctr = 0
            for j in range(0, ln - i):
                c1 = tracklist[j+i]
                c2 = tracklist[j]
                sd = sd + (c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2
                ctr = ctr + 1
            if (ctr > 0):
                t = round(i * self.framerate,2)
                msdlist.update({i : (sd / ctr)})


        # save updated list
        self.msd.update({ptracknum: msdlist})

    def get_headers(self):
        # return keys Coord.getrowoutput(0)
        return self.fieldnames

    def set_cache(self, c):
        self.cache = c

    def set_outputdir(self, odir):
        self.outputdir = odir

    def set_fromplot(self, fromplot):
        self.fromplot = fromplot

    def set_toplot(self, toplot):
        self.toplot = toplot

    '''Checks CSV file to see if valid and if contains headers
       returns 0 if not valid, 1 if valid with headers, 2 valid but no headers
    '''

    def checkinputheaders(self, inputfilename):
        valid = 1
        # Open input file
        if sys.version_info >= (3, 0, 0):
            fi = open(inputfilename, 'r', newline='')
        else:
            fi = open(inputfilename, 'rb')
        with fi as csvfile:
            if (csv.Sniffer().has_header(csvfile.read(1024))):
                print("DEBUG: CSV file has headers")
                csvfile.seek(0)
                inputreader = csv.DictReader(csvfile)
                for hdr in self.inputheaders:
                    if hdr not in inputreader.fieldnames:
                        valid = 0
                        break
            else:
                csvfile.seek(0)
                dialect = csv.Sniffer().sniff(csvfile.read(1024))
                print("DEBUG: Delimiter = ", dialect.delimiter)
                csvfile.seek(0)
                reader = csv.reader(csvfile, dialect=dialect)
                for row in reader:
                    print("DEBUG: Row[0]=", row[0])
                    if (int(row[0]) > 0 and
                                int(row[1]) > 0 and
                                float(row[2]) > 0 and
                                float(row[3]) > 0 and
                                float(row[5]) > 0):
                        valid = 2
                        break
                    else:
                        valid = 0
                        break

        return valid

    def load_input(self, inputfilename, minpoints=0, minlength=0.00, maxlength=100.00):
        # Open input file
        if sys.version_info >= (3, 0, 0):
            fi = open(inputfilename, 'r', newline='')
        else:
            fi = open(inputfilename, 'rb')

        with fi as csvfile:
            hasheader = csv.Sniffer().has_header(csvfile.read(1024))
            csvfile.seek(0)
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            csvfile.seek(0)
            fh = csv.reader(csvfile, dialect)
            tracklist = dict()
            for row in fh:
                self.ln = fh.line_num
                # print("Row " , fh.line_num)
                if (len(row) == 0 or (self.ln == 1 and hasheader)):
                    continue
                # Change in x,y wrt next row:  x(t+1) - x(t)
                # coord = Coord(int(row['TRACK NUMBER']),
                #        int(row['frame number']),
                #        float(row['x']),float(row['y']),
                #        float(row['intensity']) )
                coord = Coord(int(row[0]),
                              int(row[1]),
                              float(row[2]), float(row[3]),
                              float(row[5]))

                if (self.track != coord.track):
                    print("TRACK:" + str(self.track))
                    # self.track = int(row['TRACK NUMBER'])
                    self.track = int(row[0])
                    # load to list for filtering
                    tracklist.update({self.track: []})
                else:
                    self.cache.dx = coord.x - self.cache.x
                    self.cache.dy = coord.y - self.cache.y
                    tracklist[self.track].append(self.cache)
                self.set_cache(coord)

            # Filter tracklist then save by coord indexed list
            for track in tracklist:
                tracks = sorted(tracklist[track], key=lambda t: t.frame)
                first = tracks[0]
                last = tracks[-1]
                tracklength = np.sqrt((last.x - first.x) ** 2 + (last.y - first.y) ** 2)
                if (len(tracks) >= minpoints and tracklength >= minlength and tracklength <= maxlength):
                    for co in tracks:
                        roundx = round(co.x, self.numdecimal)
                        roundy = round(co.y, self.numdecimal)

                        if (roundx, roundy) in self.coordlist:
                            co.framecount += 1
                        else:
                            self.coordlist.update({(roundx, roundy): []})
                        # load derived values
                        # load(self, dx,dy,rho,theta,framecount):
                        co.load(co.dx, co.dy, co.getpolar_rho(co.dx, co.dy), co.getpolar_theta(co.dx, co.dy),
                                co.framecount)
                        self.coordlist[(roundx, roundy)].append(co)
                        self.counter += 1
                        # Add all filtered coords to plotter list (for Averaged coords - avgplotter)
                        self.addto_plotter(self.plotter, co)

            # Update plots with msd for full track
            for p in self.plotter.items():
                self.calculate_msd(p)

    def addto_plotter(self, plotter, co):
        if (co.track not in plotter):
            plotter.update({co.track: []})
        plotter[co.track].append(co)

    def write_output(self, outfilename):
        msg = "Starting output..."
        try:
            if sys.version_info >= (3, 0, 0):
                fo = open(outfilename, 'w', newline='')
            else:
                fo = open(outfilename, 'wb')
        except IOError:
            msg = "ERROR: cannot access output file (maybe open in another program): " + outfilename
            return msg
        with fo as outfile:
            fieldnames = self.get_headers()
            writer = csv.DictWriter(outfile, delimiter=',', dialect=csv.excel, fieldnames=fieldnames)
            writer.writeheader()

            for co in self.coordlist:

                if (len(self.coordlist[co]) > 1):
                    avg_dx = []
                    avg_dy = []
                    avg_intensity = []
                    avg_frame = []
                    co1 = self.coordlist[co][0]

                    for avgco in self.coordlist[co]:
                        # All coords averaged VS per track
                        avg_dx.append(avgco.dx)
                        avg_dy.append(avgco.dy)
                        avg_frame.append(avgco.frame)
                        avg_intensity.append(avgco.intensity)
                    myco = Coord(co1.track, self.avg(avg_frame), co1.x, co1.y, self.avg(avg_intensity))
                    myco.dx = self.avg(avg_dx)
                    myco.dy = self.avg(avg_dy)
                    myco.load(myco.dx, myco.dy,
                              myco.getpolar_rho(myco.dx, myco.dy),
                              myco.getpolar_theta(myco.dx, myco.dy),
                              len(self.coordlist[co]))
                    # myco.dx = self.avg(avg_dx)
                    # myco.dy = self.avg(avg_dy)
                    # myco.rho = myco.getpolar_rho(myco.dx,myco.dy)
                    # myco.theta = myco.getpolar_theta(myco.dx,myco.dy)
                    # myco.framecount = len(self.coordlist[co])
                else:
                    myco = self.coordlist[co][0]
                    # myco.rho = myco.getpolar_rho(myco.dx,myco.dy)
                    # myco.theta = myco.getpolar_theta(myco.dx,myco.dy)

                writer.writerow(myco.get_rowoutput(self.numdecimal))
                # group by tracknum for averaging
                self.addto_plotter(self.avgplotter, myco)

        msg = "Completed"
        return msg

    '''Write saved data to file and update plotter
    '''

    def save_data(self, outfilename, excluded=[]):
        msg = "Saving data ..."
        ctr = 0;
        newplotter = dict()
        try:
            if sys.version_info >= (3, 0, 0):
                fo = open(outfilename, 'w', newline='')
            else:
                fo = open(outfilename, 'wb')
        except IOError:
            msg = "ERROR: cannot access output file (maybe open in another program): " + outfilename
            return msg
        with fo as outfile:
            fieldnames = self.get_headers()
            writer = csv.DictWriter(outfile, delimiter=',', dialect=csv.excel, fieldnames=fieldnames)
            writer.writeheader()
            plotlist = list(self.plotter.items())
            # for each plot
            for track in plotlist:
                tracknum = track[0]
                tracklist = track[1]
                if (tracknum not in excluded):
                    ctr = ctr + 1
                    newplotter.update({tracknum: tracklist})
                    for co in tracklist:
                        writer.writerow(co.get_rowoutput(self.numdecimal))
        self.plotter = newplotter
        msg = str(ctr) + " tracks written to " + outfilename
        return msg, ctr
    """ Output MSD per time interval per track for max intervals
    Format: 'dT'. 'track1' 'track2' ...
    """
    def save_msd(self, outfilename, excluded=[],max=10):
        msg = "Saving data ..."
        ctr = 0;
        newplotter = dict()
        fieldnames = ['dT']
        plotlist = list(self.msd.items())
        numcols = self.find_max_tracknum(plotlist)
        #initialise & organise data
        msdlist = [[0 for x in range(numcols+ 1)] for x in range(max + 1)]
        msdlist[0][0] = 'dT'
        for track in plotlist:
            tracknum = track[0]
            tracklist = track[1]
            if (tracknum not in excluded):
                newplotter.update({tracknum: tracklist})
                fieldnames.append('track' + str(tracknum))

                msdlist[0][tracknum] = 'track' + str(tracknum)
                ctr = ctr + 1
                for m in tracklist.items():
                    dt = int(m[0])
                    if (dt <= max):
                        msdlist[dt][0] = dt
                        msdlist[dt][tracknum] = m[1]
        self.msd = newplotter # non-excluded plots

        try:
            if sys.version_info >= (3, 0, 0):
                fo = open(outfilename, 'w', newline='')
            else:
                fo = open(outfilename, 'wb')
        except IOError:
            msg = "ERROR: cannot access output file (maybe open in another program): " + outfilename
            return msg

        with fo as outfile:
            writer = csv.DictWriter(outfile, delimiter=',', dialect=csv.excel, fieldnames=fieldnames)
            writer.writeheader()
            y = []
            se = []
            x = []
            #Syntax: writer.writerow({'dT': k,'track' + str(tracknum): v})
            for rownum in range(1, max + 1):
                row ={}
                for colnum in range(len(plotlist) + 1):
                    if msdlist[0][colnum]:
                        row[msdlist[0][colnum]]= msdlist[rownum][colnum]
                writer.writerow(row)
                #Averaged per time interval
                y.append(np.mean(msdlist[rownum][1:-1]))
                se.append(np.std(msdlist[rownum][1:-1]))
                x.append(msdlist[rownum][0])

        self.show_avg_msd(x,y,se)

        msg = str(ctr) + " MSD tracks written to " + outfilename
        return msg

    def find_max_tracknum(self,plotlist):
        tracknums = []
        for track in plotlist:
            tracknums.append(track[0])
        return max(tracknums)
    # def write_msd(self,msdlist,outfilename,fieldnames):
    #     try:
    #         if sys.version_info >= (3, 0, 0):
    #             fo = open(outfilename, 'w', newline='')
    #         else:
    #             fo = open(outfilename, 'wb')
    #     except IOError:
    #         msg = "ERROR: cannot access output file (maybe open in another program): " + outfilename
    #         return msg
    #     total = len(list(self.msd.items()))
    #     if (len(msdlist) > 0):
    #
    #         with fo as outfile:
    #             writer = csv.DictWriter(outfile, delimiter=',', dialect=csv.excel, fieldnames=fieldnames)
    #             writer.writeheader()
    #             #writer.writerow({'dT': k,'track' + str(tracknum): v})
    #             for rownum in range(1, max + 1):
    #                 row ={}
    #                 for colnum in range(total + 1):
    #                    row[msdlist[0][colnum]]= msdlist[rownum][colnum]
    #                 writer.writerow(row)
    #
    #     else:
    #         msg = "ERROR: msd data not found"
    #         return msg

    """ Show MSD plots averaged
       Requires msdlist from generate_msdlist
       """
    def show_avg_msd(self,x=[],y=[],se=[]):
        #if (len(x) <= 0): TODO
        slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
        fig = plt.figure()
        plt.xlim(min(x) - 1, max(x) + 1)
        plt.xlabel('dT')
        plt.ylabel('MSD (um2)')
        plt.title('Avg MSD (slope=' + str(slope) + ')')
        plt.errorbar(x, y, se, linestyle='-', color='r',marker='o')
        plt.show()

    def load_plotdata(self, inputfilename):
        # Open input file
        if sys.version_info >= (3, 0, 0):
            fi = open(inputfilename, 'r', newline='')
        else:
            fi = open(inputfilename, 'rb')
        # clear plotter
        self.plotter = dict()
        with fi as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                coord = Coord(int(row['Track']),
                              int(row['Frame']),
                              float(row['x']), float(row['y']),
                              float(row['intensity']))
                coord.load(float(row['dx']), float(row['dy']),
                           float(row['rho']), float(row['theta']),
                           int(row['framecount']))
                self.addto_plotter(self.plotter, coord)

    '''Plot quiver plots with averaged coordinate data
    '''

    def plottrack(self, trak, totalplots=0, arrow=0.1, png=1):
        if (trak in self.avgplotter):

            # create a plot of a track
            plotdir = self.outputdir
            x = []
            y = []
            rho = []
            theta = []
            mytitle = "Track: " + str(trak)
            print(mytitle)
            msg = mytitle
            # sort track frames
            tracklist = sorted(self.avgplotter[trak], key=lambda t: t.frame)

            for tn in tracklist:
                x.append(tn.x)
                y.append(tn.y)
                rho.append(tn.getpolar_rho(tn.dx, tn.dy))
                theta.append(tn.getpolar_theta(tn.dx, tn.dy))
            print("Points:", len(x))
            # Total plots if option set to show later
            if (totalplots > 0):
                self.allx += x
                self.ally += y
                self.allrho += rho
                self.alltheta += theta
                self.alltracks += 1
            if (png):
                fig = plt.figure(trak)
                plt.xlabel('x')
                plt.ylabel('y')
                plt.title(mytitle)

                lines = plt.quiver(x, y, rho, theta)
                plt.setp(lines, color='b', antialiased=True)
                # Write to file
                filename = plotdir + "Track_" + str(trak) + ".png"
                fig.savefig(filename, dpi=300, orientation='landscape', format='png')
                msg = "Plot saved to " + filename
                plt.cla()
                plt.clf()
                plt.close()
        else:
            msg = "Track " + str(trak) + " has no data - skipped"
        print(msg)
        return msg

    def create_plots(self):
        # Check input
        plotdir = self.outputdir
        start = self.fromplot
        end = self.toplot
        # output msgs
        msgs = []
        # limit popups
        showplots = True
        if (end - start) > 10:
            showplots = False
        # for all tracks
        allx = []
        ally = []
        allrho = []
        alltheta = []
        alltracks = 0
        counter = 0
        for trak in self.avgplotter:
            # for each track
            x = []
            y = []
            rho = []
            theta = []
            if (counter >= start and counter < end):
                mytitle = "Track: " + str(trak)
                print(mytitle)
                for tn in self.avgplotter[trak]:
                    x.append(tn.x)
                    y.append(tn.y)
                    rho.append(tn.getpolar_rho(tn.dx, tn.dy))
                    theta.append(tn.getpolar_theta(tn.dx, tn.dy))
                print("Points:", len(x))
                fig = plt.figure(trak)
                lines = plt.quiver(x, y, rho, theta)
                plt.setp(lines, color='b', linewidth=0.2)
                plt.xlabel('x')
                plt.ylabel('y')
                plt.title(mytitle)
                # Write to file
                filename = plotdir + "Track_" + str(trak) + ".png"
                fig.savefig(filename, dpi=300, orientation='landscape', format='png')
                print("Plot saved to ", filename)
                msgs.append("Plot saved to " + filename)
                # Popup if OK
                if (showplots):
                    plt.show()
                plt.cla()
                plt.clf()
                plt.close()
                # ADD ALL TRACKS TO ONE
                allx += x
                ally += y
                allrho += rho
                alltheta += theta
                alltracks += 1
            counter += 1
        # Print all
        fig = plt.figure(len(self.avgplotter) + 1)
        mytitle = "All " + str(alltracks) + " tracks (" + str(len(allx)) + " points)"
        print(mytitle)
        lines = plt.quiver(allx, ally, allrho, alltheta)
        plt.setp(lines, color='b', linewidth=0.2)
        plt.xlabel('x')
        plt.ylabel('y')
        plt.title(mytitle)
        plt.show()
        filename = plotdir + "Tracks_" + start + "_" + end + ".png"
        fig.savefig(filename, dpi=300, orientation='landscape', format='png')
        print("Plot saved to ", filename)
        msgs.append("Plot saved to " + filename)
        plt.close()

        return msgs

    def plot_region(self, mlpoly):
        poly = Polygon(mlpoly)
        # reset coords
        self.roilist = []
        tplot = ContourPlot()

        sname = '1'
        for co in self.coordlist:
            for myco in self.coordlist[co]:
                if poly.contains(Point(myco.x, myco.y)):
                    sname = str(int(myco.x)) + '_' + str(int(myco.y))
                    self.roilist.append(myco)
                    tplot.loadrow(myco.x, myco.y, myco.rho, myco.frame)
        msg = 'Total ROI points=' + str(len(self.roilist))
        print(msg)
        fname = self.outputdir + 'ROI_' + sname + '.csv'
        msg = msg + ": " + self.print_region(fname)
        tplot.contour_region('ROI_' + sname)
        return msg

    def print_region(self, outfilename):
        msg = "Starting ROI output..."
        try:
            if sys.version_info >= (3, 0, 0):
                fo = open(outfilename, 'w', newline='')
            else:
                fo = open(outfilename, 'wb')
        except IOError:
            msg = "ERROR: cannot access output file (maybe open in another program): " + outfilename
            return msg
        with fo as outfile:
            fieldnames = self.get_headers()
            writer = csv.DictWriter(outfile, delimiter=',', dialect=csv.excel, fieldnames=fieldnames)
            writer.writeheader()
            for myco in self.roilist:
                writer.writerow(myco.get_rowoutput(self.numdecimal))
        msg = 'ROI coordinates written to ' + outfilename
        print(msg)
        return msg

    def getPlotByIndex(self, plotter, idx):
        plotlist = list(plotter.items())
        ptrack = plotlist[idx]
        # ptracknum = ptrack[0]
        # ptracklist = ptrack[1]
        return ptrack


## Main
if __name__ == "__main__":

    print(inspect.getfile(inspect.currentframe()))  # script filename (usually with path)
    defaultSrcPath = os.getcwd()  # current directory
    defaultDataPath = 'sampledata'
    print("Default path: ", defaultDataPath)
    defaultDatafile = defaultDataPath + '/trackfile.csv'
    defaultOutfile = defaultDataPath + '/outfile.csv'

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", dest="filename",
                        default=defaultDatafile, help="Full path to input file")
    parser.add_argument("-o", "--output", dest="outfilename",
                        default=defaultOutfile, help="Full path to output file")
    parser.add_argument("-n", "--num", dest="numdecimal",
                        default=1, help="Number of decimal places for rounding")
    parser.add_argument("-p", "--plots", dest="pythonplot",
                        default='1',
                        help="Generate quiverplots (default is 0, all is -1, none is 0, range is 0-10 (no spaces)")

    args = parser.parse_args()
    if (not file_check(args.filename)):
        sys.exit()
    # if (not file_check(args.outfilename)):
    #    sys.exit()
    # update data path if not default
    if (args.outfilename != defaultOutfile):
        idx = args.outfilename.rindex(os.path.sep)
        defaultDataPath = args.outfilename[0:idx]
    tracker = Tracker()
    tracker.numdecimal = int(args.numdecimal)
    # Check input file has correct headings
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
            if ('-' in args.pythonplot):
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
