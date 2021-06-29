# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ImageDownloader
                                 A QGIS plugin
 Satellite image downloader and index calculator
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-06-24
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Ayoub Saouidi
        email                : ayoub.saviola@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt import QtWidgets
from PyQt5.QtWidgets import QFileDialog
from qgis.PyQt.QtWidgets import QAction

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .imagedownloader_dialog import ImageDownloaderDialog
import os.path

# # LANDSATXPLORE
from landsatxplore.api import API
from landsatxplore.earthexplorer import EarthExplorer
# import openapi
import requests , zipfile, io
from tqdm import tqdm
import wget
import urllib
import json

loggedIn = False;

class ImageDownloader:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'ImageDownloader_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Image Downloader')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('ImageDownloader', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/imagedownloader/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u''),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Image Downloader'),
                action)
            self.iface.removeToolBarIcon(action)


    # Navigation  To Download
    def goToDownloadPage(self,evt):
        if evt.button() == QtCore.Qt.LeftButton:
            # Do Something #
            self.dlg.Pages.setCurrentIndex(2)

    # Navigation to Index
    def goToIndexPage(self,evt):
        if evt.button() == QtCore.Qt.LeftButton:
            # Do Something #
            self.dlg.Pages.setCurrentIndex(3)

    # Navigation to Auth
    def goToAuthentificationPage(self,evt):
        if evt.button() == QtCore.Qt.LeftButton:
            # Do Something #
            self.dlg.Pages.setCurrentIndex(1)

    # Navigation to SignUp
    def goToSignUpPage(self,evt):
        if evt.button() == QtCore.Qt.LeftButton:
            # Do Something #
            self.dlg.Pages.setCurrentIndex(0)

    # Logout
    def logout(self,evt):
        if evt.button() == QtCore.Qt.LeftButton:
            # Do Something #
            self.dlg.close()

    # Login
    def login(self,evt):
        global token
        if evt.button() == QtCore.Qt.LeftButton:
            #  Inputs Data
            var_username = self.dlg.loginInput.text()
            var_password = self.dlg.passwordInput.text()
            # Do Something 
            endpoint = "https://satimage-api.herokuapp.com/login"
            body = { "username": str(var_username), "password": str(var_password)}
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            response = requests.post(url=endpoint,data=body,headers=headers)
            print(response)
            print(response.json())
            if response.status_code == 200:
                token = response.json()['access_token']
                print(token)
                self.dlg.Pages.setCurrentIndex(2)

    # SignUp
    def signUp(self,evt):
        if evt.button() == QtCore.Qt.LeftButton:
            #  Inputs Data
            var_email = self.dlg.emailSUInput.text()
            var_password = self.dlg.passwordSUInput.text()
            # Do Something #
            endpoint = "https://satimage-api.herokuapp.com/user"
            body = {"email": var_email,"password": var_password}
            headers = {"Content-Type" : "application/json",'Accept': 'application/json'}
            response = requests.post(url=endpoint,data=json.dumps(body),headers=headers)
            print(response)
            print(response.json())
            if response.status_code == 200:
                self.dlg.Pages.setCurrentIndex(2)

    # ConnectToApi
    def searchData(self,evt):

        if evt.button() == QtCore.Qt.LeftButton:
            # Body of Request
            var_latitude=36.04
            var_longitude=-5.18
            startDate=self.dlg.dateEdit.date().toString('yyyyMMdd')
            endDate=self.dlg.dateEdit_2.date().toString('yyyy-MM-dd')
            cloud=self.dlg.horizontalSlider.value()
            dataSet = 'Sentinel-3'

            self.patchUser(dataSet,var_latitude,var_longitude,cloud,startDate)

            endpoint = "https://satimage-api.herokuapp.com/users/1/images"
            # body = {"satellite": str(dataSet), "latitude": lat,"longitude": lon,"cloud_coverage": cloudCover,"download_image_from": startDate}
            headers = {"Authorization": "Bearer "+str(token),'accept': 'application/json'}
            print(token)
            response = requests.get(url=endpoint,headers=headers)
            print(response)
            print(response.json())
            imagesPackage = response.json()
            if response.status_code == 200:
                if imagesPackage :     
                    i=0
                    self.dlg.resultTable.clear()
                    # HEADER
                    self.dlg.resultTable.setHorizontalHeaderLabels(['ID', 'Name', 'Downloaded']);
                    for image in imagesPackage:
                        print(image)
                        self.dlg.resultTable.insertRow(self.dlg.resultTable.rowCount())
                        # item = QtWidgets.QTableWidgetItem(image['id'])
                        # self.dlg.resultTable.setItem(self.dlg.resultTable.rowCount(), 0, item)
                        item = QtWidgets.QTableWidgetItem(image['name'])
                        self.dlg.resultTable.setItem(self.dlg.resultTable.rowCount()-1, 0, item)
                        item = QtWidgets.QTableWidgetItem( 'Yes' if image['is_downloaded'] else 'No')
                        self.dlg.resultTable.setItem(self.dlg.resultTable.rowCount()-1, 1, item)
                        i=i+1
                else :
                    i=0
                    self.dlg.resultTable.clear()
                    # HEADER
                    self.dlg.resultTable.setHorizontalHeaderLabels( ['ID', 'Name', 'Downloaded']);
                    for x in range(1,4):
                        # print(x)
                        self.dlg.resultTable.insertRow(self.dlg.resultTable.rowCount())
                        item = QtWidgets.QTableWidgetItem('1')
                        self.dlg.resultTable.setItem(self.dlg.resultTable.rowCount()-1, 0, item)
                        item = QtWidgets.QTableWidgetItem('Image number 1')
                        self.dlg.resultTable.setItem(self.dlg.resultTable.rowCount()-1, 1, item)
                        item = QtWidgets.QTableWidgetItem('Yes')
                        self.dlg.resultTable.setItem(self.dlg.resultTable.rowCount()-1, 2, item)
                        i=i+1

    # -----Patch User------
    def patchUser(self,dataSet,lat,lon,cloudCover,startDate):
        # Do Something 
        endpoint = "https://satimage-api.herokuapp.com/users/1"
        body = {"satellite": str(dataSet), "latitude": lat,"longitude": lon,"cloud_coverage": cloudCover,"download_image_from": startDate}
        headers = {"Authorization": "Bearer "+str(token),"content-type" : "application/json",'accept': 'application/json'}
        print(token)
        response = requests.patch(url=endpoint,data=json.dumps(body),headers=headers)
        print(response)
        print(response.json())
        if response.status_code == 200:
            print('Got All Images')


    def downloadData(self,evt):
        if evt.button() == QtCore.Qt.LeftButton:
            if self.dlg.resultTable.selectionModel().hasSelection() :
                selectedRow = self.dlg.resultTable.currentRow()
                name = (self.dlg.resultTable.item(selectedRow, 0).text())
                print(name)
                endpoint = "https://satimage-api.herokuapp.com/images/"+name+"/download"
                headers = {'accept': 'application/json'}
                response = requests.get(url=endpoint,stream=True)
                print(response)
                # WORKING BUT NOT GOOD
                # zipName = os.path.join('E:\\Data',name)
                # zipFile = open(zipName,"wb")
                # zipFile.write(response.content)
                # zipFile.close()
                


    def exportFiles(self, file_name):
        default_dir ="/data"
        default_filename = os.path.join(default_dir, file_name)
        filename, _ = QFileDialog.getSaveFileName(self, "Save Image", default_filename, ".zip")
        if filename:
            print(filename)


    def NDVI_5(self,Band4,Band3,OutputNDVI):
         input_rasterA = QgsRasterLayer(Band4, 'Raster1')
          #QgsProject.instance().addMapLayer(input_rasterA)
        
         input_rasterB = QgsRasterLayer(Band3, 'Raster2')
         #QgsProject.instance().addMapLayer(input_rasterB)
        
         output_raster = OutputNDVI
         parameters = {'INPUT_A': input_rasterA,'INPUT_B': input_rasterB,
         'BAND_A' : 1,
         'BAND_B' : 1,        
         'FORMULA': "((A-B)/(A+B))",
         'OUTPUT' : output_raster}
         processing.runAndLoadResults('gdal:rastercalculator', parameters)


    def CloudCouverageDisplay(self):
        var=self.dlg.horizontalSlider.value()
        self.dlg.cloudLabel.setText(str(var)+'%')

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = ImageDownloaderDialog()
            self.dlg.horizontalSlider.valueChanged.connect(self.CloudCouverageDisplay)



        # NAV BAR
        self.dlg.downloadNavItem.mousePressEvent = self.goToDownloadPage
        self.dlg.indexNavItem.mousePressEvent = self.goToIndexPage
        self.dlg.authentificationItem.mousePressEvent = self.goToAuthentificationPage
        self.dlg.logoutBtn.mousePressEvent = self.logout
        # Login Submit Events
        self.dlg.submitSUBtn.mousePressEvent = self.signUp
        self.dlg.loginBtn.mousePressEvent = self.login
        self.dlg.createAccountLink.mousePressEvent = self.goToSignUpPage
        self.dlg.searchBtn.mousePressEvent = self.searchData
        self.dlg.downloadBtn.mousePressEvent = self.downloadData
        

        # Satellites Values
        self.dlg.comboBox.addItem('')
        for x in range(1,5):
            self.dlg.comboBox.addItem('Sentinel-' + str(x))

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
