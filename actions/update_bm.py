# -*- coding: utf-8 -*-
"""
/***************************************************************************
 UDTPlugin

In this file is where the UpdateBM class is defined. The main function
of this class is to run the automation process that updates the Municipal Base
of Catalonia with the newest boundary lines.
***************************************************************************/
"""

import datetime
import os

from qgis.core import (QgsVectorLayer,
                       QgsVectorFileWriter,
                       QgsCoordinateReferenceSystem,
                       QgsGeometry,
                       QgsMessageLog,
                       Qgis,
                       QgsProcessingFeatureSourceDefinition,
                       QgsExpression)
from qgis.core.additions.edit import edit
from PyQt5.QtWidgets import QMessageBox

import processing

from ..config import *
from .adt_postgis_connection import PgADTConnection

from ..utils import remove_temp_shapefiles

# 202102011500
# 202107011400

# TODO IMPORTANTE: faltan las líneas y geometrías que no tienen SR


class UpdateBM:
    """ Update BM-5M class """

    def __init__(self, date_last_update):
        # Initialize instance attributes
        # Common
        self.date_last_update = date_last_update
        self.crs = QgsCoordinateReferenceSystem("EPSG:25831")
        # ADT PostGIS connection
        self.pg_adt = PgADTConnection(HOST, DBNAME, USER, PWD, SCHEMA)
        self.pg_adt.connect()
        # Get current datetime and add 1 hour
        self.new_data_alta = self.get_new_data_alta()
        self.date_last_update_tr = self.convert_str_to_date()
        # Paths and layers
        # Set input layers
        self.lines_input_path = os.path.join(UPDATE_BM_INPUT_DIR, 'bm5mv21sh0tlm1_ACTUAL_0.shp')
        self.lines_input_layer = QgsVectorLayer(self.lines_input_path)
        # Set work layers
        self.lines_work_path = os.path.join(UPDATE_BM_WORK_DIR, 'bm5mv21sh0tlm1_WORK_0.shp')
        self.lines_work_layer = None
        # Set output layer's path
        self.lines_output_path = os.path.join(UPDATE_BM_OUTPUT_DIR, 'bm5mv21sh0tlm1_NEW_0.shp')
        # Report config
        self.report_path = os.path.join(UPDATE_BM_LOG_DIR, f'BM_update_{self.new_data_alta}.txt')
        self.new_rep_list = []
        self.new_rep_parcial_list = []
        self.new_mtt_list = []
        self.new_mtt_parcial_list = []

    # #####################
    # Getters and setters
    def get_new_lines(self):
        """ Endpoint to get the new Rep and MTT lines since the last update """
        self.get_new_rep()
        self.get_new_mtt()

    def get_new_rep(self):
        """ Return the new Rep lines since the last update """
        rep_table = self.pg_adt.get_table('replantejament')
        rep_table.selectByExpression(f'"data_doc" > \'{self.date_last_update_tr}\' and "data_doc" != \'9999-12-31\'')

        for rep in rep_table.getSelectedFeatures():
            line_id = rep['id_linia']
            if rep['abast_rep'] == '1':
                self.new_rep_parcial_list.append(int(line_id))
                continue
            self.new_rep_list.append(int(line_id))

        QgsMessageLog.logMessage(f'Nous replantejaments: {", ".join(map(str, self.new_rep_list))}', level=Qgis.Info)
        if self.new_rep_parcial_list:
            QgsMessageLog.logMessage(f'Nous replantejaments parcials o on falten trams per definir: {", ".join(map(str, self.new_rep_parcial_list))}', level=Qgis.Info)

    def get_new_mtt(self):
        """ Return the new MTT lines since the last update """
        mtt_table = self.pg_adt.get_table('memoria_treb_top')
        mtt_table.selectByExpression(f'"data_doc" > \'{self.date_last_update_tr}\' and "data_doc" != \'9999-12-31\'')

        for mtt in mtt_table.getSelectedFeatures():
            line_id = mtt['id_linia']
            if mtt['abast_mtt'] == '1':
                self.new_mtt_parcial_list.append(int(line_id))
                continue
            self.new_mtt_list.append(int(line_id))

        QgsMessageLog.logMessage(f'Noves MTT: {", ".join(map(str, self.new_mtt_list))}', level=Qgis.Info)
        if self.new_mtt_parcial_list:
            QgsMessageLog.logMessage(f'Noves MTT parcials o on falten trams per definir: {", ".join(map(str, self.new_mtt_parcial_list))}', level=Qgis.Info)

    @staticmethod
    def get_lines_geometry(lines_list, layer_type):
        """
        Get the new geometry of every new boundary line

        :param lines_list: list of the new lines ID
        :type lines_list: list

        :param layer_type: type of the lines layers. Could be 'rep' or 'mtt'
        :type layer_type: str

        :return: dict with the geometry of every new line
        :rtype: dict
        """
        if layer_type == 'rep':
            layer = QgsVectorLayer(os.path.join(UPDATE_BM_WORK_DIR, 'REP_dissolved_temp.shp'))
        elif layer_type == 'mtt':
            layer = QgsVectorLayer(os.path.join(UPDATE_BM_WORK_DIR, 'MTT_dissolved_temp.shp'))

        line_geom_dict = {}
        for line_id in lines_list:
            layer.selectByExpression(f'"id_linia"={line_id}')
            for line in layer.getSelectedFeatures():
                line_geom = line.geometry()
                line_geom_dict[line_id] = line_geom

        return line_geom_dict

    @staticmethod
    def get_expression(lines_list):
        """
        Return a QGIS expression with the given lines ID

        :param lines_list: list of the new lines ID
        :type lines_list: list

        :return: QGIS expression to filter by the new lines ID
        :rtype: str
        """
        expression = f'"id_linia"={lines_list[0]}'

        for id_linia in lines_list[1:]:
            expression = f'{expression} OR "id_linia"={id_linia}'

        return expression

    # ####################
    # Date and time management
    @staticmethod
    def get_new_data_alta():
        """
        Get the new update date

        :return: new update date
        :rtype: str
        """
        current_date = datetime.datetime.now()
        hour = datetime.timedelta(hours=1)
        new_data_alta = current_date + hour

        return new_data_alta.strftime("%Y%m%d%H00")

    def convert_str_to_date(self):
        """
        Convert the string date to Python date format

        :return: date transformed from string to date format
        :rtype: date
        """
        date = f'{self.date_last_update[0:4]}-{self.date_last_update[4:6]}-{self.date_last_update[6:8]}'
        date_tr = datetime.datetime.strptime(date, '%Y-%m-%d')
        date_tr = date_tr.replace(second=0, microsecond=0)

        return date_tr

    # ####################
    # Data management
    def copy_data_to_work(self):
        """ Copy the input data to the working environment """
        QgsVectorFileWriter.writeAsVectorFormat(self.lines_input_layer, self.lines_work_path, 'utf-8', self.crs,
                                                'ESRI Shapefile')

        self.lines_work_layer = QgsVectorLayer(self.lines_work_path)

    def copy_sidm3_to_work(self):
        """
        Copy the new lines geometries from the database to the working environment. Only copies the selected
        lines that are ready for updating
        """
        key = 'id_tram_linia'

        # REP
        rep_layer = self.pg_adt.get_layer('v_tram_linia_rep', key)
        expression_rep = self.get_expression(self.new_rep_list)
        rep_layer.selectByExpression(expression_rep)
        rep_path = os.path.join(UPDATE_BM_WORK_DIR, 'REP_noves_linies.shp')
        QgsVectorFileWriter.writeAsVectorFormat(rep_layer, rep_path, 'utf-8', self.crs,
                                                'ESRI Shapefile', onlySelected=True)
        rep_layer.removeSelection()

        # MTT
        mtt_layer = self.pg_adt.get_layer('v_tram_linia_mem', key)
        expression_mtt = self.get_expression(self.new_mtt_list)
        mtt_layer.selectByExpression(expression_mtt)
        mtt_path = os.path.join(UPDATE_BM_WORK_DIR, 'MTT_noves_linies.shp')
        QgsVectorFileWriter.writeAsVectorFormat(mtt_layer, mtt_path, 'utf-8', self.crs,
                                                'ESRI Shapefile', onlySelected=True)
        mtt_layer.removeSelection()

    @staticmethod
    def dissolve_line_trams(line_layer, line_type):
        """
        Use the QGIS native dissolve algorithm to dissolve the lines layer by line ID

        :param line_layer: name of the layer to dissolve
        :type line_layer: str

        :param line_type: type of the lines layers. Could be 'REP' or 'MTT'
        :type line_type: str
        """
        params = {'INPUT': line_layer, 'FIELD': ['id_linia'],
                  'OUTPUT': os.path.join(UPDATE_BM_WORK_DIR, f'{line_type}_dissolved_temp.shp')}
        processing.run("native:dissolve", params)

    def update_new_lines(self):
        """ Endpoint to update the new lines geometries and attributes """
        self.update_new_rep()
        self.update_new_mtt()

    def update_new_rep(self):
        """ Update the geometries and attributes of the new REP lines """
        new_rep_lines_layer = QgsVectorLayer(os.path.join(UPDATE_BM_WORK_DIR, 'REP_noves_linies.shp'))
        # Dissolve the replantejament's lines layer
        self.dissolve_line_trams(new_rep_lines_layer, 'REP')
        # Get a dict with the new lines's geometry and its ID
        rep_lines_geom = self.get_lines_geometry(self.new_rep_list, 'rep')

        with edit(self.lines_work_layer):
            for line in self.lines_work_layer.getFeatures():
                line_id = line['IDLINIA']
                if line_id in self.new_rep_list and line_id in rep_lines_geom:
                    new_line_geom = rep_lines_geom[line_id]
                    self.lines_work_layer.changeGeometry(line.id(), new_line_geom)

        # Loop again to update attributes
        # It seems not compatible to update the geometry and the attributes in the same loop
        with edit(self.lines_work_layer):
            for line in self.lines_work_layer.getFeatures():
                line_id = line['IDLINIA']
                if line_id in self.new_rep_list and line_id in rep_lines_geom:
                    line['ESTAT'] = 1
                    line['DATAALTA'] = self.new_data_alta
                    self.lines_work_layer.updateFeature(line)

    def update_new_mtt(self):
        """ Update the geometries and the attributes of the new MTT lines """
        new_mtt_lines_layer = QgsVectorLayer(os.path.join(UPDATE_BM_WORK_DIR, 'MTT_noves_linies.shp'))
        # Dissolve the replantejament's lines layer
        self.dissolve_line_trams(new_mtt_lines_layer, 'MTT')
        # Get a dict with the new lines's geometry and its ID
        mtt_lines_geom = self.get_lines_geometry(self.new_mtt_list, 'mtt')

        with edit(self.lines_work_layer):
            for line in self.lines_work_layer.getFeatures():
                line_id = line['IDLINIA']
                if line_id in self.new_mtt_list and line_id in mtt_lines_geom:
                    new_line_geom = mtt_lines_geom[line_id]
                    self.lines_work_layer.changeGeometry(line.id(), new_line_geom)

        # Loop again to update attributes.
        # It seems not compatible to update the geometry and the attributes in the same loop
        with edit(self.lines_work_layer):
            for line in self.lines_work_layer.getFeatures():
                line_id = line['IDLINIA']
                if line_id in self.new_mtt_list and line_id in mtt_lines_geom:
                    line['ESTAT'] = 2
                    line['DATAALTA'] = self.new_data_alta
                    self.lines_work_layer.updateFeature(line)

    def export_lines_layer(self):
        """ Export the working lines layer as the output lines layer, with all the updated data """
        QgsVectorFileWriter.writeAsVectorFormat(self.lines_work_layer, self.lines_output_path, 'utf-8', self.crs,
                                                'ESRI Shapefile')

    # #####################
    # Municipality base update
    def update_bm(self):
        """
        Main entry point. Updates the municipality boundary base

        :return new_data_alta: new update date. It's necessary to allow the module to open the report
        :rtype: str
        """
        self.get_new_lines()
        self.write_report()
        try:
            self.copy_data_to_work()
            self.copy_sidm3_to_work()
            self.update_new_lines()
            self.export_lines_layer()
        except Exception as e:
            msg = f"-- ATENCIÓ -- El procés d'actualització no s'ha dut a terme correctament -- {e}"
            QgsMessageLog.logMessage(msg, level=Qgis.Warning)
            with open(self.report_path, 'a+') as f:
                f.write(msg)
        remove_temp_shapefiles(UPDATE_BM_WORK_DIR)

        return self.new_data_alta   # Return the new date as the key variable that allows the module to open the report

    # #####################
    # Check the data that the proccess needs
    def check_bm_data(self):
        """
        Check that exists the necessary input data

        :return: boolean that means if the input data exists or not
        :rtype: boolean
        """
        input_layers = self.check_input_lines_layer()
        if not input_layers:
            return
        date_last_update_ok = self.check_date_last_update_inputs()
        if not date_last_update_ok:
            return

        return True

    def check_input_lines_layer(self):
        """
        Check that the input lines layer exists

        :return: boolean that means if the input lines layer exists or not
        :rtype: boolean
        """
        if os.path.exists(self.lines_input_path):
            return True
        else:
            box = QMessageBox()
            box.setIcon(QMessageBox.Warning)
            box.setText("Falta la capa de línies de la BM\nanterior a la carpeta d'entrades.")
            box.exec_()
            return False

    def check_date_last_update_inputs(self):
        """
        Check that the input last's update date exists

        :return: boolean that means if the input last's update date exists in the lines layer attributes or not
        :rtype: boolean
        """
        self.lines_input_layer.selectByExpression(f'"DATAALTA"=\'{self.date_last_update}\'')
        count = self.lines_input_layer.selectedFeatureCount()
        if count == 0:
            box = QMessageBox()
            box.setIcon(QMessageBox.Warning)
            box.setText("La data de l'última actualització introduïda\nno existeix a les dades d'entrada.")
            box.exec_()
            return False
        else:
            return True

    # #####################
    # Report management
    def write_report(self):
        """ Write the log report with the necessary info """
        # Remove the report if it already exists
        if os.path.exists(self.report_path):
            os.remove(self.report_path)
        # Write the report
        with open(self.report_path, 'a+') as f:
            f.write("--------------------------------------------------------------------\n")
            f.write(f"Actualització de la Base Municipal de Catalunya 1:5000\n")
            f.write(f"Data de l'actualització: {self.new_data_alta}\n")
            f.write("--------------------------------------------------------------------\n")
            f.write("\n")
            f.write("Línies actualitzades:\n")
            f.write("-------------------------\n")
            f.write(f'Nous replantejaments:         {", ".join(map(str, self.new_rep_list))}\n')
            if self.new_rep_parcial_list:
                f.write(f'Nous replantejaments parcials o on falten trams per definir:          {", ".join(map(str, self.new_rep_parcial_list))}\n')
            f.write(f'Nº total de replantejaments nous: {len(self.new_rep_list) + len(self.new_rep_parcial_list)}\n')
            f.write("-------------------------\n")
            f.write(f'Noves MTT:            {", ".join(map(str, self.new_mtt_list))}\n')
            if self.new_mtt_parcial_list:
                f.write(f'Noves MTT parcials o on falten trams per definir:         {", ".join(map(str, self.new_mtt_parcial_list))}\n')
            f.write(f'Nº total de MTT noves: {len(self.new_mtt_list) + len(self.new_mtt_parcial_list)}\n')
            f.write("-------------------------\n")
            f.write("\nImportant: els Replantejaments o MTT parcials o on falten trams no s'han actualitzat. S'ha de fer manualment.\n")


if __name__ == '__main__':
    date_ = input("Última data d'alta: ")
    bm_updater = UpdateBM(date_)
    bm_updater.update_bm()
