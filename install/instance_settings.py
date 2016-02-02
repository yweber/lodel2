#-*- coding:utf8 -*-

import pymysql
import os

sitename = 'LODEL2_INSTANCE_NAME'
lodel2_lib_path = 'LODEL2_LIB_ABS_PATH'

templates_base_dir = 'LODEL2_INSTANCE_TEMPLATES_BASE_DIR'

debug = False

em_file = 'em.json'
dynamic_code_file = 'dynleapi.py' #Warning hardcoded module name in utils.py and loader.py
acl_dyn_api = 'api.py' #Warning hardcoded module name in utils.py and loader.py

ds_package = 'MySQL'
mh_classname = 'MysqlMigrationHandler'
datasource = {
    'default': {
        'module': pymysql,
        'host': '127.0.0.1',
        'user': 'DBUSER',
        'passwd': 'DBPASSWORD',
        'db': 'DBNAME'
    }
}
