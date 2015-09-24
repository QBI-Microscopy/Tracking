#!/usr/bin/python
#Custom Tracker plots
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.backends.backend_qt5agg
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from matplotlib.widgets import LassoSelector
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D


class TrackerPlot:

    def __init__(self):

        self.ax = plt.gca()
        self.canvas = self.ax.figure.canvas
        self.lasso = LassoSelector(self.ax, self.onselect)
        self.poly = None
        self.addlassobuttons()

    def testcontour(self):
        #contour plot test data:
        delta = 0.025
        x = np.arange(-3.0, 3.0, delta)
        y = np.arange(-2.0, 2.0, delta)
        X, Y = np.meshgrid(x, y)
        Z1 = mlab.bivariate_normal(X, Y, 1.0, 1.0, 0.0, 0.0)
        Z2 = mlab.bivariate_normal(X, Y, 1.5, 0.5, 1, 1)
        # difference of Gaussians
        Z = 10.0 * (Z2 - Z1)

        plt.contour(X, Y, Z, 20)

    def selectROI(self,event):
        if (self.lasso.active):
            self.lasso.active=False
            self.canvas.draw_idle()
        else:
            self.lasso.active=True

    def saveROI(self,event):
        if (self.poly):
            print('Saving Polygon coords:',self.poly)
            #msg = self.tracker.plot_region(self.poly.xy)
           # self.updateStatus(msg)

    def onselect(self,verts):
        print(verts)
        #roi = path.Path(verts)
        self.poly = Polygon(verts, animated=True)
        x, y = zip(*self.poly.xy)
        line = Line2D(x, y, marker='o', markerfacecolor='r', animated=True)
        self.ax.add_line(line)
        #self.canvas.draw_idle()
         #plt.show()

    def addlassobuttons(self):
        tbar = self.canvas.toolbar
        #Lasso tool
        icon1 = QtGui.QPixmap('resources/pencil.png')
        button_roiSelect = QtWidgets.QAction(QtGui.QIcon(icon1),'ROI',tbar)
        helpmsg = "Select ROI tool"
        button_roiSelect.setToolTip(helpmsg)
        button_roiSelect.triggered.connect(self.selectROI)
        button_roiSelect.setStatusTip(helpmsg)
        #Save selection
        icon2 = QtGui.QPixmap('resources/chart.png')
        button_roi = QtWidgets.QAction(QtGui.QIcon(icon2),'SaveROI',tbar)
        helpmsg = "Save ROI and create ROI plot"
        button_roi.setToolTip(helpmsg)
        button_roi.triggered.connect(self.saveROI)
        button_roi.setStatusTip(helpmsg)

        #Add to toolbar
        tbar.addAction(button_roiSelect)
        tbar.addAction(button_roi)
        self.roiSelect = button_roiSelect
        self.roiAction = button_roi


if __name__ == "__main__":
    print("Plotting test plot")
    tp = TrackerPlot()
    tp.testcontour()
    plt.show()