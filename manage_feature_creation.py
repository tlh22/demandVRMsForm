# -*- coding: latin1 -*-
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------
# Tim Hancock 2017

# Initialize Qt resources from file resources.py
"""
from PyQt4.QtCore import (
    QObject,
    QDate,
    pyqtSignal,
    QCoreApplication
)

from PyQt4.QtGui import (
    QMessageBox,
    QAction,
    QIcon,
    QDialogButtonBox,
    QPixmap,
    QLabel
)

from qgis.core import (
    QgsExpressionContextUtils,
    QgsMapLayerRegistry,
    QgsMessageLog, QgsFeature, QgsGeometry
)

import os

from qgis.gui import *

from TOMs.CadNodeTool.TOMsNodeTool import TOMsNodeTool

from TOMs.mapTools import *
#from TOMsUtils import *
from TOMs.constants import (
    ACTION_CLOSE_RESTRICTION,
    ACTION_OPEN_RESTRICTION
)

from TOMs.restrictionTypeUtilsClass import RestrictionTypeUtilsMixin, TOMsTransaction, setupTableNames
#from BayRestrictionForm import BayRestrictionForm

import functools
"""

# https://www.opengis.ch/2016/09/07/using-threads-in-qgis-python-plugins/
# https://snorfalorpagus.net/blog/2013/12/07/multithreading-in-qgis-python-plugins/

# Initialize Qt resources from file resources.py
from .resources import *

from qgis.PyQt.QtCore import (
    QObject,
    QDate,
    pyqtSignal,
    QCoreApplication, pyqtSlot, QThread
)

from qgis.PyQt.QtGui import (
    QIcon,
    QPixmap, QColor
)

from qgis.PyQt.QtWidgets import (
    QMessageBox,
    QAction,
    QDialogButtonBox,
    QLabel,
    QDockWidget
)

from qgis.core import (
    QgsExpressionContextUtils,
    QgsProject,
    QgsMessageLog,
    QgsFeature,
    QgsGeometry,
    QgsApplication, QgsCoordinateTransform, QgsCoordinateReferenceSystem,
    QgsGpsDetector, QgsGpsConnection, QgsGpsInformation, QgsPoint, QgsPointXY
)

from qgis.gui import (
    QgsVertexMarker,
    QgsMapToolEmitPoint
)

import os, time

#from qgis.gui import *

# from .CadNodeTool.TOMsNodeTool import TOMsNodeTool

from .mapTools import CreateRestrictionTool, CreatePointTool
#from TOMsUtils import *

from .fieldRestrictionTypeUtilsClass import FieldRestrictionTypeUtilsMixin, TOMSLayers, gpsParams
from .SelectTool import GeometryInfoMapTool

import functools


class captureGPSFeatures(FieldRestrictionTypeUtilsMixin):

    def __init__(self, iface, featuresWithGPSToolbar):

        QgsMessageLog.logMessage("In captureGPSFeatures::init", tag="TOMs panel")

        FieldRestrictionTypeUtilsMixin.__init__(self, iface)

        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = self.iface.mapCanvas()

        self.featuresWithGPSToolbar = featuresWithGPSToolbar
        self.gpsMapTool = False
        self.marker = None

        # This will set up the items on the toolbar
        # Create actions

        self.actionCreateRestriction = QAction(QIcon(":/plugins/featureswithgps/resources/mActionAddTrack.svg"),
                               QCoreApplication.translate("MyPlugin", "Create Restriction"),
                               self.iface.mainWindow())
        self.actionCreateRestriction.setCheckable(True)


        self.actionAddGPSLocation = QAction(QIcon(":/plugins/featureswithgps/resources/greendot3.png"),
                               QCoreApplication.translate("MyPlugin", "Add vertex"),
                               self.iface.mainWindow())
        #self.actionAddGPSLocation.setCheckable(True)

        self.actionRemoveRestriction = QAction(QIcon(":plugins/featureswithgps/resources/mActionDeleteTrack.svg"),
                                        QCoreApplication.translate("MyPlugin", "Remove Restriction"),
                                        self.iface.mainWindow())
        self.actionRemoveRestriction.setCheckable(True)

        self.actionRestrictionDetails = QAction(QIcon(":/plugins/featureswithgps/resources/mActionGetInfo.svg"),
                                         QCoreApplication.translate("MyPlugin", "Get Restriction Details"),
                                         self.iface.mainWindow())
        self.actionRestrictionDetails.setCheckable(True)

        self.actionCreateSign = QAction(QIcon(":/plugins/featureswithgps/resources/mActionSetEndPoint.svg"),
                                                    QCoreApplication.translate("MyPlugin", "Create sign"),
                                                    self.iface.mainWindow())
        self.actionCreateSign.setCheckable(True)

        # Add actions to the toolbar

        self.featuresWithGPSToolbar.addAction(self.actionCreateRestriction)
        self.featuresWithGPSToolbar.addAction(self.actionAddGPSLocation)
        self.featuresWithGPSToolbar.addAction(self.actionRestrictionDetails)
        self.featuresWithGPSToolbar.addAction(self.actionRemoveRestriction)
        self.featuresWithGPSToolbar.addAction(self.actionCreateSign)
        # Connect action signals to slots

        self.actionCreateRestriction.triggered.connect(self.doCreateRestriction)
        self.actionAddGPSLocation.triggered.connect(self.doAddGPSLocation)
        self.actionRestrictionDetails.triggered.connect(self.doRestrictionDetails)
        self.actionRemoveRestriction.triggered.connect(self.doRemoveRestriction)
        self.actionCreateSign.triggered.connect(self.doCreateSign)

        self.actionCreateRestriction.setEnabled(False)
        self.actionAddGPSLocation.setEnabled(False)
        self.actionRestrictionDetails.setEnabled(False)
        self.actionRemoveRestriction.setEnabled(False)
        self.actionCreateSign.setEnabled(False)

    def enableFeaturesWithGPSToolbarItems(self):

        QgsMessageLog.logMessage("In enablefeaturesWithGPSToolbarItems", tag="TOMs panel")
        self.gpsAvailable = False
        self.closeTOMs = False
        #self.closeCaptureGPSFeatures = False

        #self.gps_thread.gpsActivated.connect(functools.partial(self.gpsStarted))
        #self.gps_thread.gpsDeactivated.connect(functools.partial(self.gpsStopped))

        self.tableNames = TOMSLayers(self.iface)
        params = gpsParams(self.iface)

        self.tableNames.TOMsLayersNotFound.connect(self.setCloseTOMsFlag)
        #self.tableNames.gpsLayersNotFound.connect(self.setCloseCaptureGPSFeaturesFlag)
        params.gpsParamsNotFound.connect(self.setCloseCaptureGPSFeaturesFlag)

        self.prj = QgsProject().instance()
        self.dest_crs = self.prj.crs()
        QgsMessageLog.logMessage("In captureGPSFeatures::init project CRS is " + self.dest_crs.description(),
                                 tag="TOMs panel")
        self.transformation = QgsCoordinateTransform(QgsCoordinateReferenceSystem("EPSG:4326"), self.dest_crs,
                                                     self.prj)

        self.tableNames.getLayers()
        params.getParams()

        if self.closeTOMs:
            QMessageBox.information(self.iface.mainWindow(), "ERROR", ("Unable to start editing tool ..."))
            #self.actionProposalsPanel.setChecked(False)
            return   # TODO: allow function to continue without GPS enabled ...

        # Now check to see if the port is set. If not assume that just normal tools

        if self.gpsAvailable == True:

            gpsPort = params.setGpsParam("gpsPort")

            if gpsPort:
                self.gpsAvailable = True
                self.gps_thread = GPS_Thread(self.dest_crs, gpsPort)
                thread = QThread()
                self.gps_thread.moveToThread(thread)
                self.gps_thread.gpsActivated.connect(self.gpsStarted)
                self.gps_thread.gpsPosition.connect(self.gpsPositionProvided)
                self.gps_thread.gpsDeactivated.connect(functools.partial(self.gpsStopped))
                self.gps_thread.gpsError.connect(self.gpsErrorEncountered)
                #self.gps_thread.progress.connect(progressBar.setValue)
                thread.started.connect(self.gps_thread.startGPS)
                #thread.finished.connect(functools.partial(self.gpsStopped, thread))
                thread.start()
                self.thread = thread

                """if self.gps_connection:
                    QgsMessageLog.logMessage("In enableFeaturesWithGPSToolbarItems - GPS connection found ",
                                             tag="TOMs panel")
        
                    reply = QMessageBox.information(None, "Error",
                                                    "Connection found",
                                                    QMessageBox.Ok)
        
                    self.actionCreateRestriction.setEnabled(True)
                    self.actionAddGPSLocation.setEnabled(True)"""

        self.enableToolbarItems()
        self.createMapToolDict = {}

    def enableToolbarItems(self):
        self.actionCreateRestriction.setEnabled(True)
        self.actionRestrictionDetails.setEnabled(True)
        self.actionRemoveRestriction.setEnabled(True)
        self.actionCreateSign.setEnabled(True)

        if self.gpsAvailable:
            self.actionAddGPSLocation.setEnabled(True)

    def disableToolbarItems(self):
        self.actionCreateRestriction.setEnabled(False)
        self.actionRestrictionDetails.setEnabled(False)
        self.actionRemoveRestriction.setEnabled(False)
        self.actionCreateSign.setEnabled(False)

        if self.gpsAvailable:
            self.actionAddGPSLocation.setEnabled(False)

    def setCloseTOMsFlag(self):
        self.closeTOMs = True

    def setCloseCaptureGPSFeaturesFlag(self):
        self.closeCaptureGPSFeatures = True
        self.gpsAvailable = True

    def disableFeaturesWithGPSToolbarItems(self):

        QgsMessageLog.logMessage("In disablefeaturesWithGPSToolbarItems", tag="TOMs panel")
        #if not self.closeCaptureGPSFeatures:
        if self.gpsAvailable and not self.closeTOMs:
            self.gps_thread.endGPS()

        self.disableToolbarItems()

    def doCreateRestriction(self):

        QgsMessageLog.logMessage("In doCreateRestriction", tag="TOMs panel")

        self.mapTool = None

        self.currLayer = self.iface.activeLayer()

        if self.currLayer:

            if self.actionCreateRestriction.isChecked():

                QgsMessageLog.logMessage("In doCreateRestriction - tool activated", tag="TOMs panel")

                #self.iface.setActiveLayer(self.currLayer)

                self.mapTool = self.createMapToolDict.get(self.currLayer)

                if not self.mapTool:
                    self.mapTool = CreateRestrictionTool(self.iface, self.currLayer)
                    self.createMapToolDict[self.currLayer] =  self.mapTool

                self.mapTool.setAction(self.actionCreateRestriction)
                self.iface.mapCanvas().setMapTool(self.mapTool)
                self.gpsMapTool = True

                #signsLayer.editingStarted.connect(functools.partial(self.createRestrictionStarted))
                self.iface.currentLayerChanged.connect(self.changeCurrLayer)
                self.canvas.mapToolSet.connect(self.changeMapTool)

            else:

                QgsMessageLog.logMessage("In doCreateRestriction - tool deactivated", tag="TOMs panel")

                self.iface.mapCanvas().unsetMapTool(self.mapTool)
                self.mapTool = None
                self.actionCreateRestriction.setChecked(False)
                self.gpsMapTool = False

        else:

            reply = QMessageBox.information(self.iface.mainWindow(), "Information", "Please choose a layer ...",
                                            QMessageBox.Ok)

    def changeMapTool(self, newMapTool, oldMapTool):
        QgsMessageLog.logMessage("In changeMapTool: ", tag="TOMs panel")
        try:
            self.iface.currentLayerChanged.disconnect(self.changeCurrLayer)
            self.canvas.mapToolSet.disconnect(self.changeMapTool)
        except Exception:
            None

    def changeCurrLayer(self, newLayer):
        QgsMessageLog.logMessage("In changeCurrLayer - newLayer: " + str(newLayer.name()),
                                 tag="TOMs panel")
        self.iface.currentLayerChanged.disconnect(self.changeCurrLayer)
        if self.actionCreateRestriction.isChecked():
            # TODO: Check whether or not it has been switched to an allowable layer
            self.doCreateRestriction()

    """def createRestrictionStarted(self):
        self.createProcessStarted = True

    def createRestrictionMapToolDeactivated(self, inProcess):
        QgsMessageLog.logMessage("In createRestrictionMapToolDeactivated - currMapTool " + str(inProcess), tag="TOMs panel")
        self.interrupted = inProcess"""

    """def reinstateCreateRestrictionTool(self):
        QgsMessageLog.logMessage("In reinstateCreateRestrictionTool - currMapTool " + self.currCreateRestrictionTool.toolName(), tag="TOMs panel")

        self.iface.setActiveLayer(self.currLayer)
        self.mapTool = self.createMapToolDict.get(self.currLayer)

        #self.iface.mapCanvas().unsetMapTool(self.mapTool)
        #self.actionCreateSign.setChecked(False)
        #if self.currCreateRestrictionTool:
        self.iface.mapCanvas().setMapTool(self.mapTool)"""

    def doAddGPSLocation(self):

        QgsMessageLog.logMessage("In doAddGPSLocation", tag="TOMs panel")

        if self.gpsMapTool:

            status = self.mapTool.addPointFromGPS(self.curr_gps_location, self.curr_gps_info)

        else:

            reply = QMessageBox.information(self.iface.mainWindow(), "Information", "You need to activate the tool first ...",
                                            QMessageBox.Ok)

    def doRestrictionDetails(self):
        """ Select point and then display details
        """
        QgsMessageLog.logMessage("In doRestrictionDetails", tag="TOMs panel")

        # self.demandUtils.signToolChanged.emit()
        # self.demandUtils.signToolChanged.connect(self.actionToggled)
        # self.mapTool = None

        if self.actionRestrictionDetails.isChecked():

            QgsMessageLog.logMessage("In doRestrictionDetails - tool activated", tag="TOMs panel")

            self.currLayer = self.iface.activeLayer()
            # self.currLayer = QgsMapLayerRegistry.instance().mapLayersByName("MovingTrafficSigns")[0]

            self.iface.setActiveLayer(self.currLayer)
            if not self.actionRestrictionDetails.isChecked():
                QgsMessageLog.logMessage("In doRestrictionDetails - resetting mapTool", tag="TOMs panel")
                self.actionRestrictionDetails.setChecked(False)
                self.iface.mapCanvas().unsetMapTool(self.mapTool)
                self.mapTool = None
                # self.actionPan.connect()
                return

            self.actionRestrictionDetails.setChecked(True)

            self.mapTool = GeometryInfoMapTool(self.iface)
            self.mapTool.setAction(self.actionRestrictionDetails)
            self.mapTool.deactivated.connect(functools.partial(self.deactivateAction, self.actionRestrictionDetails))
            self.iface.mapCanvas().setMapTool(self.mapTool)

            self.mapTool.notifyFeatureFound.connect(self.showRestrictionDetails)

        else:

            QgsMessageLog.logMessage("In doRestrictionDetails - tool deactivated", tag="TOMs panel")

            self.mapTool.notifyFeatureFound.disconnect(self.showRestrictionDetails)
            self.iface.mapCanvas().unsetMapTool(self.mapTool)
            # del self.mapTool
            self.mapTool = None
            self.actionRestrictionDetails.setChecked(False)

    def deactivateAction(self, currAction):
        currAction.setChecked(False)

    #@pyqtSlot(str)
    def showRestrictionDetails(self, closestLayer, closestFeature):

        QgsMessageLog.logMessage(
            "In showRestrictionDetails ... Layer: " + str(closestLayer.name()),
            tag="TOMs panel")

        if closestLayer.isEditable() == True:
            if closestLayer.commitChanges() == False:
                reply = QMessageBox.information(None, "Information",
                                                "Problem committing changes" + str(closestLayer.commitErrors()),
                                                QMessageBox.Ok)
            else:
                QgsMessageLog.logMessage("In showRestrictionDetails: changes committed", tag="TOMs panel")

        if self.currLayer.readOnly() == True:
            # Set different form
            # closestLayer.editFormConfig().setUiForm(...)
            """reply = QMessageBox.information(None, "Information",
                                            "Could not start transaction on " + self.currLayer.name(), QMessageBox.Ok)
            return"""
            QgsMessageLog.logMessage("In showSignDetails - Not able to start transaction ...",
                                     tag="TOMs panel")

        else:
            if self.currLayer.startEditing() == False:
                reply = QMessageBox.information(None, "Information",
                                                "Could not start transaction on " + self.currLayer.name(),
                                                QMessageBox.Ok)
                return

        self.dialog = self.iface.getFeatureForm(closestLayer, closestFeature)
        self.setupFieldRestrictionDialog(self.dialog, closestLayer, closestFeature)

        self.dialog.show()

    def doRemoveRestriction(self):

        QgsMessageLog.logMessage("In doRemoveRestriction", tag="TOMs panel")

        #self.demandUtils.signToolChanged.emit()

        #self.mapTool = None

        if self.actionRemoveRestriction.isChecked():

            QgsMessageLog.logMessage("In doRemoveRestriction - tool activated", tag="TOMs panel")

            self.currLayer = self.iface.activeLayer()
            #self.currLayer = QgsMapLayerRegistry.instance().mapLayersByName("MovingTrafficSigns")[0]

            if self.currLayer.readOnly() == True:
                """reply = QMessageBox.information(None, "Information",
                                                "Could not start transaction on " + self.currLayer.name(), QMessageBox.Ok)"""
                QgsMessageLog.logMessage("In doRemoveRestriction - Not able to start transaction ...", tag="TOMs panel")
                self.actionRemoveRestriction.setChecked(False)
                return

            self.iface.setActiveLayer(self.currLayer)
            if not self.actionRemoveRestriction.isChecked():
                QgsMessageLog.logMessage("In doRemoveRestriction - resetting mapTool", tag="TOMs panel")
                self.actionRemoveRestriction.setChecked(False)
                self.iface.mapCanvas().unsetMapTool(self.mapTool)
                self.mapTool = None
                # self.actionPan.connect()
                return

            self.actionRemoveRestriction.setChecked(True)

            self.mapTool = GeometryInfoMapTool(self.iface)
            self.mapTool.setAction(self.actionRemoveRestriction)
            self.mapTool.deactivated.connect(functools.partial(self.deactivateAction, self.actionRemoveRestriction))
            self.iface.mapCanvas().setMapTool(self.mapTool)

            self.mapTool.notifyFeatureFound.connect(self.removeRestriction)

        else:

            QgsMessageLog.logMessage("In doRemoveRestriction - tool deactivated", tag="TOMs panel")

            self.mapTool.notifyFeatureFound.disconnect(self.removeRestriction)
            self.iface.mapCanvas().unsetMapTool(self.mapTool)
            del self.mapTool
            self.actionRemoveRestriction.setChecked(False)

    #@pyqtSlot(str)
    def removeRestriction(self, closestLayer, closestFeature):

        QgsMessageLog.logMessage(
            "In removeRestriction ... Layer: " + str(closestLayer.name()),
            tag="TOMs panel")

        if closestLayer.isEditable() == True:
            if closestLayer.commitChanges() == False:
                reply = QMessageBox.information(None, "Information",
                                                "Problem committing changes" + str(closestLayer.commitErrors()),
                                                QMessageBox.Ok)
            else:
                QgsMessageLog.logMessage("In removeRestriction: changes committed", tag="TOMs panel")

        if self.currLayer.startEditing() == False:
            reply = QMessageBox.information(None, "Information",
                                            "Could not start transaction on " + self.currLayer.name(),
                                            QMessageBox.Ok)
            return

        # TODO: Sort out this for UPDATE
        # self.setDefaultRestrictionDetails(closestFeature, closestLayer)

        closestLayer.deleteFeature(closestFeature.id())

        if closestLayer.commitChanges() == False:
            reply = QMessageBox.information(None, "Information",
                                            "Problem committing changes" + str(closestLayer.commitErrors()),
                                            QMessageBox.Ok)
        else:
            QgsMessageLog.logMessage("In removeRestriction: changes committed", tag="TOMs panel")

    def doCreateSign(self):

        QgsMessageLog.logMessage("In doCreateSign", tag="TOMs panel")

        if self.actionCreateSign.isChecked():

            self.currMapTool = self.canvas.mapTool()
            self.signsLayer = self.tableNames.setLayer("Signs")

            if self.currMapTool:
                toolText = self.currMapTool.action().text()
                QgsMessageLog.logMessage("In doCreateSign - currMapTool [" + toolText + "]", tag="TOMs panel")

                if toolText == 'Create Restriction':
                    self.currentlySelectedLayer = self.iface.activeLayer()
                else:
                    self.currentlySelectedLayer = self.signsLayer

            self.mapTool = None

            self.iface.setActiveLayer(self.signsLayer)

            self.mapTool = self.createMapToolDict.get(self.signsLayer)

            if not self.mapTool:
                self.mapTool = CreateRestrictionTool(self.iface, self.signsLayer)
                self.createMapToolDict[self.signsLayer] = self.mapTool

            QgsMessageLog.logMessage("In doCreateSign - tool activated", tag="TOMs panel")

            #self.func1 = functools.partial(self.reinstateMapTool, self.signsLayer)
            self.signsLayer.editingStopped.connect(self.reinstateMapTool)

            self.actionCreateSign.setChecked(True)

            self.mapTool = CreatePointTool(self.iface, self.signsLayer)
            self.mapTool.setAction(self.actionCreateSign)

            self.iface.mapCanvas().setMapTool(self.mapTool)

        #self.gpsMapTool = True


    def reinstateMapTool(self):

        if self.currMapTool:
            QgsMessageLog.logMessage("In reinstateMapTool ... " + self.currMapTool.toolName(), tag="TOMs panel")

            self.signsLayer.editingStopped.disconnect(self.reinstateMapTool)
            """try:
                self.signsLayer.editingStopped.disconnect(functools.partial(self.reinstateMapTool, self.signsLayer))
            except TypeError:
                pass"""

            self.iface.setActiveLayer(self.currentlySelectedLayer)
            self.iface.mapCanvas().unsetMapTool(self.mapTool)
            self.actionCreateSign.setChecked(False)

            self.iface.mapCanvas().setMapTool(self.currMapTool)


    #@pyqtSlot(QgsGpsConnection)
    def gpsStarted(self, connection):
        QgsMessageLog.logMessage("In enableTools - GPS connection found ",
                                     tag="TOMs panel")

        self.gpsConnection = connection

        # marker
        self.marker = QgsVertexMarker(self.canvas)
        self.marker.setColor(QColor(255, 0, 0))  # (R,G,B)
        self.marker.setIconSize(10)
        self.marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
        self.marker.setPenWidth(3)

        """reply = QMessageBox.information(None, "Error",
                                            "Connection found",
                                            QMessageBox.Ok)"""

        """self.actionCreateRestriction.setEnabled(True)
        self.actionAddGPSLocation.setEnabled(True)
        self.actionRestrictionDetails.setEnabled(True)
        self.actionRemoveRestriction.setEnabled(True)
        self.actionCreateSign.setEnabled(True)"""

        self.enableToolbarItems()

    #@pyqtSlot()
    def gpsStopped(self, thread):
        QgsMessageLog.logMessage("In enableTools - GPS connection stopped ",
                                     tag="TOMs panel")
        self.gps_thread.deleteLater()
        thread.quit()
        thread.wait()
        thread.deleteLater()

        if self.gpsAvailable:
            if self.canvas is not None:
                self.canvas.scene().removeItem(self.marker)

        """self.actionCreateRestriction.setEnabled(False)
        self.actionAddGPSLocation.setEnabled(False)
        self.actionRestrictionDetails.setEnabled(False)
        self.actionRemoveRestriction.setEnabled(False)"""

        self.disableToolbarItems()

    #@pyqtSlot()
    #def gpsPositionProvided(self):
    def gpsPositionProvided(self, mapPointXY, gpsInfo):
        """reply = QMessageBox.information(None, "Information",
                                            "Position provided",
                                            QMessageBox.Ok)"""
        QgsMessageLog.logMessage("In enableTools - ******** initial GPS location provided " + mapPointXY.asWkt(),
                                     tag="TOMs panel")

        self.curr_gps_location = mapPointXY
        self.curr_gps_info = gpsInfo

        wgs84_pointXY = QgsPointXY(gpsInfo.longitude, gpsInfo.latitude)
        wgs84_point = QgsPoint(wgs84_pointXY)
        wgs84_point.transform(self.transformation)
        x = wgs84_point.x()
        y = wgs84_point.y()
        new_mapPointXY = QgsPointXY(x, y)

        QgsMessageLog.logMessage("In enableTools - ******** transformed GPS location provided " + str(gpsInfo.longitude) + ":" + str(gpsInfo.latitude) + "; " + new_mapPointXY.asWkt(),
                                     tag="TOMs panel")

        if gpsInfo.pdop >= 1:  # gps ok
            self.marker.setColor(QColor(0, 200, 0))
        else:
            self.marker.setColor(QColor(255, 0, 0))
        self.marker.setCenter(mapPointXY)
        self.marker.show()
        self.canvas.setCenter(mapPointXY)

        # TODO: populate message bar with details about satellites, etc

    #@pyqtSlot(Exception, str)
    def gpsErrorEncountered(self, e):
        QgsMessageLog.logMessage("In enableTools - GPS connection has error ",
                                     tag="TOMs panel")
        """self.actionCreateRestriction.setEnabled(False)
        self.actionAddGPSLocation.setEnabled(False)"""
        self.disableToolbarItems()

class GPS_Thread(QObject):

    #https://gis.stackexchange.com/questions/307209/accessing-gps-via-pyqgis

    gpsActivated = pyqtSignal(QgsGpsConnection)
    """ signal will be emitted when gps is activated"""
    gpsDeactivated = pyqtSignal()
    gpsError = pyqtSignal(Exception)
    gpsPosition = pyqtSignal(object, object)

    def __init__(self):
        #QThread.__init__(self)
        #self.iface=iface
        self.prj=QgsProject().instance()
        self.connectionRegistry = QgsApplication.gpsConnectionRegistry()
        #self.canvas = self.iface.mapCanvas()
        super(GPS_Thread, self).__init__()
        try:
            self.gps_active = False

            # set up transformation
            self.dest_crs = self.prj.crs()
            self.transformation = QgsCoordinateTransform(QgsCoordinateReferenceSystem("EPSG:4326"), self.dest_crs,
                                                         QgsProject.instance())

            #self.marker = None
            #gps

            self.gpsCon = None

            QgsMessageLog.logMessage("In GPS_Thread - initialised ... ",
                                     tag="TOMs panel")
        except Exception as e:
            QgsMessageLog.logMessage(("In GPS - exception: " + str(e)), tag="TOMs panel")
            self.gpsError.emit(e)

    def startGPS(self):

        try:
            QgsMessageLog.logMessage("In GPS_Thread - running ... ",
                                     tag="TOMs panel")
            self.gpsCon = None
            self.port = "COM6"  # TODO: Add menu to select port
            self.gpsDetector = QgsGpsDetector(self.port)
            self.gpsDetector.detected[QgsGpsConnection].connect(self.connection_succeed)
            self.gpsDetector.detectionFailed.connect(self.connection_failed)

            self.gpsDetector.advance()

        except Exception as e:
            QgsMessageLog.logMessage(("In GPS - exception: " + str(e)),
                                     tag="TOMs panel")
            self.gpsError.emit(e)

    def endGPS(self):
        try:
            QgsMessageLog.logMessage(("In GPS - GPS deactivated ...."),
                                     tag="TOMs panel")
            """if self.gpsCon is not None:
                self.gpsCon.close()
            if self.canvas is not None:
                self.canvas.scene().removeItem(self.marker)"""
            self.gps_active = False
            """self.connectionRegistry.unregisterConnection(self.gpsCon)
            self.gpsDeactivated.emit()"""

        except Exception as e:
            QgsMessageLog.logMessage(("In GPS - exception: " + str(e)),
                                     tag="TOMs panel")
            self.gpsError.emit(e)

    def connection_succeed(self, connection):
        try:
            QgsMessageLog.logMessage(("In GPS - GPS connected ...."),
                                     tag="TOMs panel")
            self.gps_active = True
            self.gpsCon = connection

            self.gpsCon.stateChanged.connect(self.status_changed)

            self.connectionRegistry.registerConnection(connection)
            #marker
            """self.marker = QgsVertexMarker(self.canvas)
            self.marker.setColor(QColor(255, 0, 0))  # (R,G,B)
            self.marker.setIconSize(10)
            self.marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
            self.marker.setPenWidth(3)"""

            self.gpsActivated.emit(connection)

        except Exception as e:
            QgsMessageLog.logMessage(("In GPS - exception: " + str(e)),
                                     tag="TOMs panel")
            self.gpsError.emit(e)

    def connection_failed(self):
        if not self.gps_active:
            QgsMessageLog.logMessage(("In GPS - GPS connection failed ...."),
                                     tag="TOMs panel")
            self.endGPS()

    def status_changed(self,gpsInfo):
        try:
            if self.gpsCon.status() == 3: #data received
                """QgsMessageLog.logMessage(("In GPS - fixMode:" + str(gpsInfo.fixMode)),
                                         tag="TOMs panel")
                QgsMessageLog.logMessage(("In GPS - pdop:" + str(gpsInfo.pdop)),
                                         tag="TOMs panel")
                QgsMessageLog.logMessage(("In GPS - satellitesUsed:" + str(gpsInfo.satellitesUsed)),
                                         tag="TOMs panel")
                QgsMessageLog.logMessage(("In GPS - longitude:" + str(gpsInfo.longitude)),
                                         tag="TOMs panel")
                QgsMessageLog.logMessage(("In GPS - latitude:" + str(gpsInfo.latitude)),
                                         tag="TOMs panel")
                QgsMessageLog.logMessage(("In GPS - ====="),
                                         tag="TOMs panel")"""
                wgs84_pointXY = QgsPointXY(gpsInfo.longitude, gpsInfo.latitude)
                wgs84_point = QgsPoint(wgs84_pointXY)
                wgs84_point.transform(self.transformation)
                x = wgs84_point.x()
                y = wgs84_point.y()
                mapPointXY = QgsPointXY(x, y)
                self.gpsPosition.emit(mapPointXY, gpsInfo)
                time.sleep(1)

                QgsMessageLog.logMessage(("In GPS - location:" + mapPointXY.asWkt()),
                                         tag="TOMs panel")
                """if gpsInfo.pdop >= 1:  # gps ok
                    self.marker.setColor(QColor(0, 200, 0))
                else:
                    self.marker.setColor(QColor(255, 0, 0))
                self.marker.setCenter(mapPointXY)
                self.marker.show()
                self.canvas.setCenter(mapPointXY)"""

            else:
                if self.gpsCon is not None:
                    self.gpsCon.close()
                self.connectionRegistry.unregisterConnection(self.gpsCon)
                self.gpsDeactivated.emit()

        except Exception as e:
            QgsMessageLog.logMessage(("In GPS - exception: " + str(e)),
                                     tag="TOMs panel")
            self.gpsError.emit(e)

    def getLocationFromGPS(self):
        QgsMessageLog.logMessage(
            "In CreateFeatureWithGPSTool - addPointFromGPS",
            tag="TOMs panel")
        # assume that GPS is connected and get current co-ords ...
        GPSInfo = self.gpsCon.currentGPSInformation()
        lon = GPSInfo.longitude
        lat = GPSInfo.latitude
        QgsMessageLog.logMessage(
            "In CreateFeatureWithGPSTool:addPointFromGPS - lat: " + str(lat) + " lon: " + str(lon),
            tag="TOMs panel")
        # ** need to be able to convert from lat/long to Point
        gpsPt = self.transformation.transform(QgsPointXY(lon,lat))

        #self.gpsPosition.emit(gpsPt)

        # opportunity to add details about GPS point to another table

        return gpsPt
