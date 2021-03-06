# -*- coding: utf-8 -*-
"""
/***************************************************************************
 UDTPlugin

In this file is where the connection to the ADT PostGIS database is
defined and the data returned.
***************************************************************************/
"""

from qgis.core import QgsVectorLayer, QgsDataSourceUri, QgsProviderRegistry


class PgADTConnection:
    def __init__(self, host, dbname, user, password, schema):
        """ Constructor """
        self.uri = QgsDataSourceUri()
        self.host = host
        self.dbname = dbname
        self.port = '5342'
        self.schema = schema
        self.user = user
        self.pwd = password

    def connect(self):
        """ Connect to the ADT PostGIS Database """
        self.uri = QgsDataSourceUri()
        self.uri.setConnection(self.host, "5432", self.dbname, self.user, self.pwd)

    def get_table(self, table_name):
        """
        Return a table from the ADT PostGIS Database

        :param table_name: Name of the table to get from the database
        :type table_name: str

        :return QgsVectorLayer: Layer of the table to get from the database
        :rtype QgsVectorLayer: QgsVectorLayer
        """
        self.uri.setDataSource(self.schema, table_name, None)
        return QgsVectorLayer(self.uri.uri(False), table_name, "postgres")

    def get_layer(self, layer_name, akey=''):
        """
        Return a layer from the ADT PostGIS Database

        :param layer_name: Name of the layer to get from the database
        :type layer_name: str

        :param akey: Unique ID of the layer
        :type akey: str

        :return QgsVectorLayer: Layer to get from the database
        :rtype QgsVectorLayer: QgsVectorLayer
        """
        # Geometry column -- shape
        self.uri.setDataSource(self.schema, layer_name, 'shape', '', aKeyColumn=akey)
        self.uri.setSrid('25831')
        return QgsVectorLayer(self.uri.uri(False), layer_name, "postgres")
