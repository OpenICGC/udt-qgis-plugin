# -*- coding: utf-8 -*-
"""
/***************************************************************************
 UDTPlugin

In this file is where the GeneradorMMC class is defined. The main function
of this class is to run the automation process that exports the geometries
and generates the metadata of a municipal map.
***************************************************************************/
"""


class GeneradorMMC(object):

    def __init__(self, municipi_id, data_alta):
        self.municipi_id = municipi_id
        self.data_alta = data_alta

    def init(self):
        """ Main entry point """
