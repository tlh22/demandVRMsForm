#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------
# Tim Hancock 2017

"""
Series of functions to deal with restrictionsInProposals. Defined as static functions to allow them to be used in forms ... (not sure if this is the best way ...)

"""
from qgis.PyQt.QtWidgets import (
    QMessageBox,
    QAction,
    QDialogButtonBox,
    QLabel,
    QDockWidget,
    QDialog,
    QLabel,
    QPushButton,
    QApplication,
    QComboBox, QSizePolicy, QGridLayout,
    QWidget
)

from qgis.PyQt.QtGui import (
    QIcon,
    QPixmap,
    QImage, QPainter
)

from qgis.PyQt.QtCore import (
    QObject,
    QTimer,
    QThread,
    pyqtSignal,
    pyqtSlot, Qt
)

from qgis.PyQt.QtSql import (
    QSqlDatabase
)

from qgis.core import (
    Qgis,
    QgsExpressionContextScope,
    QgsExpressionContextUtils,
    QgsExpression,
    QgsFeatureRequest,
    QgsMessageLog,
    QgsFeature,
    QgsGeometry,
    QgsTransaction,
    QgsTransactionGroup,
    QgsProject,
    QgsSettings
)

from qgis.gui import *
import functools
import time, datetime
import os, uuid
#import cv2
import math

from abc import ABCMeta
from TOMs.generateGeometryUtils import generateGeometryUtils
from TOMs.restrictionTypeUtilsClass import (TOMsParams, TOMsLayers, originalFeature, RestrictionTypeUtilsMixin)
from restrictionsWithGNSS.fieldRestrictionTypeUtilsClass import (FieldRestrictionTypeUtilsMixin)

from TOMs.ui.TOMsCamera import (formCamera)
from restrictionsWithGNSS.ui.imageLabel import (imageLabel)

cv2_available = True
try:
    import cv2
except ImportError:
    QgsMessageLog.logMessage("Not able to import cv2 ...", tag="TOMs panel")
    cv2_available = False

import uuid
from TOMs.core.TOMsMessageLog import TOMsMessageLog
from .demand_form import VRM_DemandForm

ZOOM_LIMIT = 5

class vrmParams(TOMsParams):
    def __init__(self):
        TOMsParams.__init__(self)
        #self.iface = iface

        #TOMsMessageLog.logMessage("In gpsParams.init ...", level=Qgis.Info)

        self.TOMsParamsList.extend([
                          "CameraNr",
                          "DemandGpkg"
                               ])

class VRMsUtilsMixin(FieldRestrictionTypeUtilsMixin):
    def __init__(self, iface):
        #RestrictionTypeUtilsMixin.__init__(self, iface)
        self.iface = iface
        self.settings = QgsSettings()

        #self.params = gpsParams()

        #self.TOMsUtils = RestrictionTypeUtilsMixin(self.iface)

    def setDefaultFieldRestrictionDetails(self, currRestriction, currRestrictionLayer, currDate):
        TOMsMessageLog.logMessage("In setDefaultFieldRestrictionDetails: {}".format(currRestrictionLayer.name()), level=Qgis.Info)

        # TODO: Need to check whether or not these fields exist. Also need to retain the last values and reuse
        # gis.stackexchange.com/questions/138563/replacing-action-triggered-script-by-one-supplied-through-qgis-plugin

        try:
            currRestriction.setAttribute("LastUpdateDateTime", currDate)
        except Exception as e:
            TOMsMessageLog.logMessage("In setDefaultFieldRestrictionDetails. Problem with setting LastUpdateDateTime: {}".format(e),
                                      level=Qgis.Info)

    def setupFieldRestrictionDialog(self, restrictionDialog, currRestrictionLayer, currRestriction):

        self.params.getParams()

        # Create a copy of the feature
        self.origFeature = originalFeature()
        self.origFeature.setFeature(currRestriction)

        if restrictionDialog is None:
            reply = QMessageBox.information(None, "Error",
                                            "setupFieldRestrictionDialog. Correct form not found",
                                            QMessageBox.Ok)
            TOMsMessageLog.logMessage(
                "In setupRestrictionDialog. dialog not found",
                level=Qgis.Warning)
            return

        restrictionDialog.attributeForm().disconnectButtonBox()
        button_box = restrictionDialog.findChild(QDialogButtonBox, "button_box")

        if button_box is None:
            TOMsMessageLog.logMessage(
                "In setupRestrictionDialog. button box not found",
                level=Qgis.Warning)
            return

        """
        button_box.accepted.connect(functools.partial(self.onSaveFieldRestrictionDetails, currRestriction,
                                      currRestrictionLayer, restrictionDialog))

        button_box.rejected.connect(functools.partial(self.onRejectFieldRestrictionDetailsFromForm, restrictionDialog, currRestrictionLayer))

        restrictionDialog.attributeForm().attributeChanged.connect(functools.partial(self.onAttributeChangedClass2_local, currRestriction, currRestrictionLayer))
        """

        self.photoDetails_field(restrictionDialog, currRestrictionLayer, currRestriction)

        #self.addVRMWidget(restrictionDialog, currRestrictionLayer, currRestriction)

        #self.addScrollBars(restrictionDialog)

    def onAttributeChangedClass2_local(self, currFeature, layer, fieldName, value):

        #self.TOMsUtils.onAttributeChangedClass2(currFeature, layer, fieldName, value)

        TOMsMessageLog.logMessage(
            "In field:FormOpen:onAttributeChangedClass 2 - layer: " + str(layer.name()) + " (" + fieldName + "): " + str(value), level=Qgis.Info)


        # self.currRestriction.setAttribute(fieldName, value)
        try:

            currFeature[layer.fields().indexFromName(fieldName)] = value
            #currFeature.setAttribute(layer.fields().indexFromName(fieldName), value)

        except Exception as e:

            reply = QMessageBox.information(None, "Error",
                                                "onAttributeChangedClass2. Update failed for: " + str(layer.name()) + " (" + fieldName + "): " + str(value),
                                                QMessageBox.Ok)  # rollback all changes


        self.storeLastUsedDetails(layer.name(), fieldName, value)

        return

    def onSaveFieldRestrictionDetails(self, currFeature, currFeatureLayer, dialog):
        TOMsMessageLog.logMessage("In onSaveFieldRestrictionDetails:  currFeatureID: ".format(currFeature.id()), level=Qgis.Info)

        try:
            self.camera1.endCamera()
            self.camera2.endCamera()
            self.camera3.endCamera()
        except:
            None

        status = currFeatureLayer.updateFeature(currFeature)

        #status = dialog.attributeForm().close()

        try:
            currFeatureLayer.commitChanges()
        except Exception as e:
            reply = QMessageBox.information(None, "Information", "Problem committing changes: {}".format(e), QMessageBox.Ok)

        TOMsMessageLog.logMessage("In onSaveDemandDetails: changes committed", level=Qgis.Info)

        status = dialog.close()

    def onRejectFieldRestrictionDetailsFromForm(self, restrictionDialog, currFeatureLayer):
        TOMsMessageLog.logMessage("In onRejectFieldRestrictionDetailsFromForm", level=Qgis.Info)

        try:
            self.camera1.endCamera()
            self.camera2.endCamera()
            self.camera3.endCamera()
        except:
            None

        currFeatureLayer.rollBack()
        restrictionDialog.reject()

        #del self.mapTool

    def createConnection(self):
        con = QSqlDatabase.addDatabase("QSQLITE")

        photoPath = QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable('DemandGpkg')
        projectFolder = QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable('project_folder')

        path_absolute = os.path.join(projectFolder, photoPath)

        if path_absolute == None:
            reply = QMessageBox.information(None, "Information", "Please set value for Demand Gpkg.", QMessageBox.Ok)
            return

        # con.setDatabaseName("C:\\Users\\marie_000\\Documents\\MHTC\\VRM_Test.gpkg")
        # con.setDatabaseName("Z:\\Tim\\SYS20-12 Zone K, Watford\\Test\\Mapping\\Geopackages\\SYS2012_Demand_VRMs.gpkg")
        con.setDatabaseName(path_absolute)
        # "Z:\\Tim\\SYS20-12 Zone K, Watford\\Test\\Mapping\\Geopackages\\SYS2012_Demand.gpkg"
        if not con.open():
            QMessageBox.critical(None, "Cannot open memory database",
                                 "Unable to establish a database connection.\n\n"
                                 "Click Cancel to exit.", QMessageBox.Cancel)
            return False

        TOMsMessageLog.logMessage("In createConnection: db name: {} ".format(con.databaseName()),
                                  level=Qgis.Warning)
        # query = QtSql.QSqlQuery()
        return True

    def addVRMWidget(self, restrictionDialog, currRestrictionLayer, currRestriction):
        self.VRMtab = restrictionDialog.findChild(QWidget, "VRMs")
        theseVRMs = VRM_DemandForm(self.iface, self.VRMtab)
