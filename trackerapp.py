#!/usr/bin/python3
"""
    QBI Meunier Tracker APP: GUI for tracker.py (trackerapp.py)
    **************************************************************
    Description: This script was developed for the Meunier Lab at QBI.
    It analyses particle tracking information and produces plots for review.
    
    Requirements: Python3, PyQt5, matplotlib, numpy, plotly, scipy
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
__date__ = "$15/06/2015 11:03:33 AM$"
__version__ = 1.0

import os
from os.path import expanduser

homedir = expanduser("~")
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import QSettings
from tracking import Tracker
from trackerplots.trackerplot import TrackerPlot
from trackerplots.contourplot import ContourPlot
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas)


# create a progressBar while running plotter
class progress(QtWidgets.QDialog):
    signal = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.finished = False
        # Set up the user interface from Designer.
        self.ui = uic.loadUi("tracker_progress.ui", self)
        # self.ui.btnStart.clicked.connect(self.start)
        self.ui.btnStop.clicked.connect(self.stop)


    def update(self, i):
        self.ui.progressBar.setValue(i)

    def total(self, total):
        self.ui.progressBar.setMaximum(total)

    def stop(self):
        # self.signal.emit(1)
        self.finished = True
        self.close()

    def closeEvent(self, event):
        self.stop()
        self.close()


class MyApp(QtWidgets.QMainWindow):
    notify = QtCore.pyqtSignal(int)

    def __init__(self):
        super(MyApp, self).__init__()
        uifile = os.getcwd() + os.path.sep + "tracker.ui"
        self.ui = uic.loadUi(uifile, self)
        # Load Config
        configfile = homedir + os.path.sep + '.trackerconfig.ini'
        print("Config:", configfile)
        self.settings = QSettings(configfile, QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False)
        # load ini
        # Initial window size/pos last saved if available
        self.resize(self.settings.value('size', QtCore.QSize(730, 760)))
        self.move(self.settings.value('pos', QtCore.QPoint(50, 50)))
        self.ui.txtInput.setText(self.settings.value('datafile', '.'))
        self.ui.txtOutputdir.setText(self.settings.value('outputdir', '.'))
        self.ui.spinArrowsize.setValue(float(self.settings.value('arrow', '0.20')))
        self.ui.spinContours.setValue(float(self.settings.value('contours', '0')))
        self.ui.spinDec.setValue(float(self.settings.value('decimal', '1')))
        self.ui.spinFramerate.setValue(float(self.settings.value('framerate', '1')))
        if (len(self.ui.txtInput.text()) > 5 and len(self.ui.txtOutputdir.text()) > 5 and len(
                self.ui.txtOutputfile.text()) > 5):
            self.ui.btnRunScript.setEnabled(True)
        # Set Graphics views
        self.init_graphics_views()
        # Set actions
        self.ui.btnRunScript.clicked.connect(self.runscript)
        self.ui.btnFileBrowser.clicked.connect(self.popupInput)
        self.ui.btnFolderBrowser.clicked.connect(self.popupOutput)
        self.ui.btnClear.clicked.connect(self.clearfields)
        self.ui.toolButtonHelp.clicked.connect(self.helpdialog)
        self.ui.btnReviewSave.clicked.connect(self.saveData)
        self.ui.btnReviewDataset.clicked.connect(self.loadData)
        self.ui.checkExclude.clicked.connect(self.excludeTrack)
        self.ui.spinCurrentTrack.valueChanged.connect(self.loadTrack, self.ui.spinCurrentTrack.value())
        # self.ui.groupSD.clicked.connect(self.loadTrack,self.ui.spinCurrentTrack.value())
        self.ui.groupBoxTracks.setEnabled(False)
        # Setup ProgressBar
        self.progress = progress(self)
        self.finished = False
        # Allow save fig
        self.fig = None
        self.tracker = None
        self.p1 = None
        self.p2 = None
        self.fname = None  # external file set

    def init_graphics_views(self):
        # Set Graphics views
        self.scene = QtWidgets.QGraphicsScene(0, 0, self.ui.graphicsView1.width() - 2,
                                              self.ui.graphicsView1.height() - 2)
        self.ui.graphicsView1.setScene(self.scene)
        self.scene2 = QtWidgets.QGraphicsScene(0, 0, self.ui.graphicsView2.width() - 2,
                                               self.ui.graphicsView2.height() - 2)
        self.ui.graphicsView2.setScene(self.scene2)

    def loadparams(self):
        paramslist = QtGui.QStandardItemModel(self.ui.listOutput)
        numplots = 0  # default none
        # Check input
        plotfrom = int(self.ui.spinPlotFrom.value())
        plotto = int(self.ui.spinPlotTo.value())
        # Plot first plot
        if (plotfrom <= 1 and plotto <= 1 and plotfrom != plotto):
            plotfrom = 1
            plotto = 2
        elif plotfrom == 0 and plotfrom != plotto:
            plotfrom = 1
        elif plotto != 0:
            plotto += 1
        # swap if values are incorrect
        if plotto < plotfrom:
            tmp = plotfrom
            plotfrom = plotto
            plotto = tmp
        if (self.ui.checkBoxAllPlots.isChecked()):
            numplots = -1
        else:
            numplots = plotto - plotfrom
        # Set params
        outputparams = {
            "Input": self.ui.txtInput.text(),
            "OutputDir": self.ui.txtOutputdir.text(),
            "OutputFname": self.ui.txtOutputfile.text(),
            "OutputFile": self.ui.txtOutputdir.text() + os.path.sep + self.ui.txtOutputfile.text(),
            "Decimals": int(self.ui.spinDec.value()),
            "Minpoints": int(self.ui.spinMinpoints.value()),
            "Minlength": float(self.ui.spinMinlength.value()),
            "Maxlength": float(self.ui.spinMaxlength.value()),
            "Plots": numplots,
            "from": plotfrom,
            "to": plotto
        }

        # Display settings
        opstring = "Input: " + outputparams['Input']
        params = QtGui.QStandardItem(opstring)
        paramslist.appendRow(params)
        opstring = "Output: " + outputparams['OutputFile']
        params = QtGui.QStandardItem(opstring)
        paramslist.appendRow(params)
        opstring = "Decimals: " + str(outputparams['Decimals'])
        params = QtGui.QStandardItem(opstring)
        paramslist.appendRow(params)
        if numplots < 0:
            plotsval = 'All'
        elif numplots == 0:
            plotsval = 'None'
        else:
            plotsval = str(outputparams['from']) + " to " + str(outputparams['to'])
        opstring = "Plots: " + plotsval
        params = QtGui.QStandardItem(opstring)
        paramslist.appendRow(params)
        self.ui.listOutput.setModel(paramslist)

        # Check valid entries
        valid = True
        for op, opval in outputparams.items():
            if (opval is None):
                valid = False
                break
        if (not valid):
            return None
        else:
            return outputparams

    def clearfields(self):
        for widget in self.ui.centralwidget.children():
            if isinstance(widget, QtWidgets.QScrollArea):
                self.clearStatus()

    def popupInput(self):
        browser = QtWidgets.QFileDialog(self)
        browser.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        fname = browser.getOpenFileName(self, 'Choose a data file',
                                        self.settings.value('datafile', '.'),
                                        'CSV files (*.csv *.trc)')
        if fname:
            self.ui.txtInput.setText(str(fname[0]))
            # Check if both files selected
            if self.ui.txtOutputdir.text():
                self.ui.btnRunScript.setEnabled(True)

    def popupOutput(self):
        browser2 = QtWidgets.QFileDialog(self)
        browser2.setFileMode(QtWidgets.QFileDialog.Directory)
        browser2.setOption(QtWidgets.QFileDialog.ShowDirsOnly)
        dname = browser2.getExistingDirectory(self, 'Select output folder', '')
        if dname:
            self.ui.txtOutputdir.setText(dname)
            # Check if both files selected
            if self.ui.txtInput.text():
                self.ui.btnRunScript.setEnabled(True)

    def runscript(self):
        params = self.loadparams();
        if (params is None):
            self.updateStatus("***ERROR: Settings invalid, exiting ***")
            return 0
        # setup Tracker
        tracker = Tracker()

        # Check input file has correct headings
        validinput = tracker.checkinputheaders(params['Input'])
        if (not validinput):
            self.updateStatus("***ERROR: Input file not valid, exiting ***")
            self.updateStatus("Order of rows (with/without headers) should be:")
            for hdr in tracker.inputheaders:
                self.updateStatus(hdr)
            return 0

        # Generate output file
        tracker.numdecimal = int(params['Decimals'])
        minpoints = int(params['Minpoints'])
        minlength = float(params['Minlength'])
        maxlength = float(params['Maxlength'])
        tracker.framerate = round(self.ui.spinFramerate.value() / 60, 2)
        self.updateStatus("Starting ...")
        tracker.load_input(params['Input'], minpoints, minlength, maxlength)
        self.updateStatus("... Input loaded ...")
        outputfilename = params['OutputFile']
        msg = tracker.write_output(outputfilename)
        self.updateStatus(msg)

        # Generate quiver plots (if required)
        if ("Completed" in msg) and (tracker.counter > 0):
            self.updateStatus("TOTAL ROWS: " + str(tracker.counter))
            self.updateStatus("TOTAL AVG TRACKS: " + str(len(tracker.avgplotter)))
            self.updateStatus("TOTAL TRACKS: " + str(len(tracker.plotter)))
            plotnum = int(params['Plots'])
            msgs = []
            # All plots
            if (plotnum < 0):
                plotnum = len(tracker.avgplotter)
                params['from'] = 1
                params['to'] = plotnum + 1

            if (plotnum > 0):
                outputdir = params['OutputDir'] + os.path.sep
                tracker.set_outputdir(outputdir)
                tracker.set_fromplot(params['from'])
                tracker.set_toplot(params['to'])
                self.updateStatus("Creating " + str(plotnum) + " plots")

                # Extract subset
                r = range(params['from'], params['to'])
                # Run plots in a thread
                self.tracker = tracker
                self.startPlots(r)

            # Save settings
            self.settings.setValue('datafile', params['Input'])
            self.settings.setValue('outputdir', params['OutputDir'])
        else:
            self.updateStatus("Error occurred - please check data files")

    '''Create plots from output data - requires loaded tracker and range of plot numbers to plot
    '''

    def startPlots(self, plotrange):
        tracker = self.tracker
        self.updateStatus("Output plots to " + tracker.outputdir)
        msgs = []
        self.progress.total(len(plotrange))
        self.progress.finished = False
        self.progress.show()
        self.notify.connect(self.progress.update)

        # run plots
        tracker.init_allplots()
        totalplots = self.ui.checkBoxMatlab.isChecked()
        arrowwidth = self.ui.spinArrowsize.value()
        pngplots = self.ui.checkPNG.isChecked()
        i = 0
        for n in plotrange:
            if (self.progress.finished == False):
                trak = self.tracker.getPlotByIndex(self.tracker.avgplotter, n - 1)
                i += 1
                self.progress.update(i)
                QtWidgets.QApplication.processEvents()
                msg = tracker.plottrack(trak[0], totalplots, arrowwidth, pngplots)
                # self.updateStatus(msg)
        self.progress.stop()
        msg = "Track plots done"
        self.updateStatus(msg)
        # create total plot - Matlab
        if (totalplots > 0):
            self.fig = plt.figure(tracker.alltracks + 1)
            mytitle = "Quiver plot (avg) of " + str(len(tracker.plotter)) + " tracks (" + str(
                len(tracker.allx)) + " points)"
            # mytitle = "Quiver plot (avg) of " + str(tracker.alltracks) + " tracks (" + str(len(tracker.allx)) + " points)"
            lines = plt.quiver(tracker.allx, tracker.ally, tracker.allrho, tracker.alltheta, units='x', pivot='tip',
                               width=arrowwidth)
            plt.setp(lines, antialiased=True)
            plt.title(mytitle)

            # save to file
            if (pngplots):
                filename = tracker.outputdir + "Tracks_" + str(plotrange[0]) + "to" + str(plotrange[-1]) + ".png"
                self.fig.savefig(filename, dpi=300, orientation='landscape', format='png')
                self.updateStatus("Total Plot saved to " + filename)

            if (self.ui.checkBoxMatlab.isChecked()):
                self.tp = TrackerPlot()
                # overwrite saveROI action
                self.tp.roiAction.triggered.connect(self.plotROI)
                if self.ui.spinContours.value() > 0:
                    intervals = self.ui.spinContours.value()
                    msg = "Plotting Contour overlay with %d intervals ... please wait" % intervals
                    self.updateStatus(msg)
                    # Add contours
                    tplot = ContourPlot()
                    tplot.loadarrays(tracker.allx, tracker.ally, tracker.allrho)
                    tplot.intervals = intervals
                    tplot.showtitle = False
                    tplot.linesonly = True
                    tplot.newfig = False
                    tplot.contour_region(mytitle)
                    self.updateStatus("... done")
                plt.show()
            # load in graphicsview
            self.total = len(tracker.plotter)  # tracker.alltracks #total averaged tracks
            self.initPlotReview()
            self.ui.labelReviewPanel.setText("Loaded " + str(self.total) + " tracks")

    def initPlotReview(self):
        self.ui.groupBoxTracks.setEnabled(True)
        self.current = 1
        self.excluded = []
        self.ui.spinCurrentTrack.setValue(self.current)
        self.ui.spinCurrentTrack.setMaximum(self.total)
        self.ui.labelTotalTracks.setText(" of " + str(self.total))

        if (self.fname is not None):
            self.ui.labelReviewPanel.setText("Loaded " + str(self.total) + " tracks from " + self.fname)
        else:
            self.ui.labelReviewPanel.setText("Loaded " + str(self.total) + " tracks")

    ''' Overwritten event for TrackerPlot.roiAction button
    '''

    def plotROI(self, event):
        if (self.tp.poly):
            print('Polygon coords:', self.tp.poly)
            msg = self.tracker.plot_region(self.tp.poly.xy)
            self.updateStatus(msg)

    def showTrackXY(self, track, tracknum, x, y):
        tracklength = np.sqrt((x[-1] - x[0]) ** 2 + (y[-1] - y[0]) ** 2)
        fig = plt.figure(track, dpi=45, frameon=False)
        plt.suptitle("Plot " + str(track) + ": Track " + str(tracknum) + " (" + str(len(x)) + " points, length=" + str(
            round(tracklength, 4)) + ")")
        plt.xlabel('x')
        plt.ylabel('y')
        plt.plot(x, y)
        # plot first point
        plt.plot(x[0], y[0], 'ro')  # end point: ,x[-1],y[-1],'rx')
        return fig

    def showMSD(self, track, tracknum, msd):
        fig = plt.figure(dpi=45, frameon=False)
        plt.suptitle("Plot " + str(track) + ": MSD for Track " + str(tracknum))
        plt.xlabel('time (s)')
        plt.ylabel('Mean Square Displacement(MSD)')
        tracklist = sorted(msd.items(), key=lambda t: t[0])
        msdlist = []
        t1 = []
        for s in tracklist:
            msdlist.append(s[1])
            t1.append(s[0])

        plt.plot(t1, msdlist)
        return fig

    def loadTrack(self, track):
        ptrack = self.tracker.getPlotByIndex(self.tracker.plotter, track - 1)
        ptracknum = ptrack[0]
        ptracklist = ptrack[1]
        print("loadTrack: plot=" + str(track) + " track=" + str(ptracknum) + " num points=" + str(len(ptracklist)))
        # Sort by timeframe
        if (len(ptracklist) > 0):
            tracklist = sorted(ptracklist, key=lambda t: t.frame)
        else:
            tracklist = ptracklist
        x = []
        y = []
        dx = []
        dy = []
        sd = []
        frames = []
        cg = []  # cumulative gradient
        for tn in tracklist:
            dx.append(tn.dx)
            dy.append(tn.dy)
            x.append(tn.x)
            y.append(tn.y)
            frames.append(tn.frame)
            sd.append(tn.sd)
            cg.append(tn.gradient)

        # convert timeframe via fps
        t0 = frames[0]

        if (t0 > 1):
            tf = [x - t0 for x in frames]
        else:
            tf = frames
        t1 = [f * self.tracker.framerate for f in tf]
        # Get MSD plots per track
        msdtrack = self.tracker.msd[ptracknum]

        # Display plots
        # graphicsView1
        if (self.p1 is not None):
            plt.close(self.p1)
        fig1 = self.showTrackXY(track, ptracknum, x, y)
        self.p1 = fig1
        self.canvas = FigureCanvas(fig1)
        self.scene.addWidget(self.canvas)
        self.canvas.draw()
        # graphicsView2
        if (self.p2 is not None):
            plt.close(self.p2)
        # MSD track  - should test that it is generated TODO
        fig2 = self.showMSD(track, ptracknum, msdtrack)
        self.canvas2 = FigureCanvas(fig2)
        self.scene2.addWidget(self.canvas2)
        self.canvas2.draw()
        self.p2 = fig2
        # Update track review
        if track in self.excluded:
            self.ui.checkExclude.setChecked(True)
        else:
            self.ui.checkExclude.setChecked(False)
        self.current = track
        self.ui.txtCurrent = track

    def excludeTrack(self):
        self.excluded.append(self.current)

    ''' saveData
        Definition: outputs coordinates per plot (except exclusions)
    '''

    def saveData(self):
        params = self.loadparams();
        outputfilename = params['OutputFile']
        # Allow user to choose
        browser = QtWidgets.QFileDialog(self)
        browser.setFileMode(QtWidgets.QFileDialog.Directory)
        browser.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        self.total = len(self.tracker.plotter) - len(self.excluded)
        idnum = str(self.total) + '_' + str(self.ui.spinMinpoints.value()) + \
                '_' + str(int(self.ui.spinMinlength.value())) + '_' + str(int(self.ui.spinMaxlength.value()))
        outputfilename = str.replace(outputfilename, '.csv', '_' + idnum + '.csv')
        fname, _ = browser.getSaveFileName(self, 'Save as', outputfilename, 'CSV files (*.csv)')

        if fname:
            msg, total = self.tracker.save_data(fname, self.excluded)
            self.updateStatus(msg)
            fname = str.replace(fname, '.csv', '_msd.csv')
            msg = self.tracker.save_msd(fname, self.excluded)
            self.updateStatus(msg)
            self.total = total
            self.initPlotReview()
            self.loadTrack(1)

    '''Load generated data files for review (and save) ONLY
    '''

    def loadData(self):
        # Allow user to choose
        browser = QtWidgets.QFileDialog(self)
        browser.setFileMode(QtWidgets.QFileDialog.Directory)
        browser.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        fname, _ = browser.getOpenFileName(self, 'Choose a data file',
                                           self.settings.value('datafile', '.'),
                                           'CSV files (*.csv *.trc)')
        if fname:
            self.tracker.load_plotdata(fname)
            self.fname = fname
            msg = "Plot data loaded from :" + fname + " [" + str(len(self.tracker.plotter)) + " tracks]"
            self.updateStatus(msg)
            self.ui.groupPlots.setEnabled(False)  # deactivate other controls as not available for review - use clear
            self.total = len(self.tracker.plotter)
            self.initPlotReview()

    def updateStatus(self, txtout):
        statusoutput = self.ui.listOutput.model()
        status = QtGui.QStandardItem(txtout)
        statusoutput.appendRow(status)

    def clearStatus(self):
        statusoutput = self.ui.listOutput.model()
        statusoutput.clear()
        self.tracker = None
        self.ui.groupPlots.setEnabled(True)
        self.ui.groupBoxTracks.setEnabled(False)
        if (self.p1 is not None):
            plt.close(self.p1)
        if (self.p2 is not None):
            plt.close(self.p2)
        self.init_graphics_views()

    def helpdialog(self):
        dialog = QtWidgets.QDialog()
        dialog.ui = uic.loadUi("tracker_help.ui", dialog)
        dialog.show()

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 'Message', "Are you sure you want to quit?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if (reply == QtWidgets.QMessageBox.Yes):
            event.accept()
            # Write window size and position to config file
            self.settings.setValue("size", self.size())
            self.settings.setValue("pos", self.pos())
            self.settings.setValue("arrow", self.ui.spinArrowsize.value())
            self.settings.setValue("contours", self.ui.spinContours.value())
            self.settings.setValue("decimal", self.ui.spinDec.value())
            self.settings.setValue("framerate", self.ui.spinFramerate.value())
            self.progress.close()
            if (self.fig is not None):
                plt.close(self.fig)
        else:
            event.ignore()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = MyApp()
    MainWindow.show()

    sys.exit(app.exec_())
