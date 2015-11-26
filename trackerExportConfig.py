#!/usr/bin/python3
"""
    QBI Meunier Tracker APP: Export Configuration
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
"""
from PyQt5.QtWidgets import QDialog
from PyQt5 import uic

class ExportConfig(QDialog):
    def __init__(self, parent = None):
        super(ExportConfig, self).__init__(parent)
        self.ui = uic.loadUi("tracker_exportconfig.ui",self)
        #self.ui.buttons.accepted.connect(self.accept)
        #self.ui.buttons.rejected.connect(self.reject)

    # get values from the dialog
    def length(self):
        return self.ui.spinEConfigLength.value()
    def radius(self):
        return self.ui.spinEConfigRadius.value()
    def timestep(self):
        return self.ui.spinEConfigTimestep.value()
    def stepsize(self):
        return self.ui.spinEConfigStepsize.value()
    def units(self):
        return self.ui.cboEConfigUnits.itemData(self.ui.cboEConfigUnits.currentIndex())

    # static method to create the dialog and return (date, time, accepted)
    @staticmethod
    def getExportConfig(parent = None):
        dialog = ExportConfig(parent)
        result = dialog.exec_()

        return (dialog.length(),dialog.radius(),dialog.timestep(),
                dialog.stepsize(),dialog.units(), result == QDialog.Accepted)