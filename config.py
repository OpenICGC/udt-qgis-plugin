# +---------------------+
# | VARIABLES I ENTORNS |
# +---------------------+

import os.path as path

# Plugin Local Dir
PLUGIN_LOCAL_DIR = r'C:\Users\fmart\Documents\Work\ICGC\Plugin_UDT'

##############################################################
# GENERADOR MMC

# Llistat de ID Area dels municipis que tenen línia de costa
municipis_costa = ["494", "607", "209", "458", "260", "131", "189", "659", "746", "445", "855", "579", "84", "571", "767",
                   "533", "572", "141", "191", "697", "860", "472", "108", "785", "480", "593", "138", "748", "154",
                   "758", "678", "49", "499", "137", "128", "935", "617", "66", "243", "524", "675", "261", "900",
                   "78", "320", "180", "742", "264", "803", "133", "226", "655", "928", "229", "231", "41", "843",
                   "534", "672", "884", "145", "251", "424", "426", "234", "713", "43", "17", "685", "822", "933"]

# Generador MMC Paths
GENERADOR_LOCAL_DIR = path.join(PLUGIN_LOCAL_DIR, 'Generador-MMC')
GENERADOR_INPUT_DIR = path.join(GENERADOR_LOCAL_DIR, '01_Entrada')
GENERADOR_WORK_DIR = path.join(GENERADOR_LOCAL_DIR, '02_Treball')
GENERADOR_OUTPUT_DIR = path.join(GENERADOR_LOCAL_DIR, '03_Sortida')
GENERADOR_WORK_GPKG = path.join(GENERADOR_WORK_DIR, 'generador_mmc_database.gpkg')
# Data
DIC_NOM_MUNICIPIS = path.join(GENERADOR_WORK_DIR, 'dic_nom_municipis.csv')
DIC_LINES = path.join(GENERADOR_WORK_DIR, 'dic_linies_data.csv')
COAST_TXT = path.join(GENERADOR_WORK_DIR, 'treball_fulls5m_costa.txt')
SHAPEFILES_PATH = r'ESRI\Shapefiles'


# ADT POSTGIS CREDENTIALS
HOST = '172.30.29.7'
DBNAME = 'ADT3'
USER = 'adt_ro'
PWD = 'Barcel0n3$'
SCHEMA = 'sidm3'
