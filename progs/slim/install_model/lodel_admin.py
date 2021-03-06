#!/usr/bin/env python3
# 
# This file is part of Lodel 2 (https://github.com/OpenEdition)
#
# Copyright (C) 2015-2017 Cléo UMS-3287
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#



import sys
import os, os.path
import argparse

##@brief Dirty hack to avoid problems with simlink to lodel2 lib folder
#
#In instance folder we got a loader.py (the one we want to import here when
#writing "import loader". The problem is that lodel_admin.py is a simlink to
#LODEL2LIB_FOLDER/install/lodel_admin.py . In this folder there is the 
#generic loader.py template. And when writing "import loader" its 
#LODEL2LIB_FOLDER/install/loader.py that gets imported.
#
#In order to solve this problem the _simlink_hack() function delete the
#LODEL2LIB_FOLDER/install entry from sys.path
#@note This problem will be solved once lodel lib dir will be in 
#/usr/lib/python3/lodel
def _simlink_hack():
    sys.path[0] = os.getcwd()

## @brief Utility method to generate python code given an emfile and a
# translator
# @param model_file str : An em file
# @param translator str : a translator name
# @return python code as string
def generate_dyncode(model_file, translator):
    from lodel.editorial_model.model import EditorialModel
    from lodel.leapi import lefactory

    model = EditorialModel.load(translator, filename  = model_file)
    dyncode = lefactory.dyncode_from_em(model)
    return dyncode

## @brief Utility method to generate a python file representing leapi dyncode
# given an em file and the associated translator name
#
# @param model_file str : An em file
# @param translator str : a translator name
# @param output_filename str : the output file
def create_dyncode(model_file, translator, output_filename):
    from lodel import logger
    dyncode = generate_dyncode(model_file, translator)
    with open(output_filename, 'w+') as out_fd:
        out_fd.write(dyncode)
    out_fd.close()
    logger.info("Dynamic leapi code written in %s", output_filename)


## @brief Refresh dynamic leapi code from settings
def refresh_dyncode():
    import loader
    from lodel.settings import Settings
    # EditorialModel update/refresh
    
    # TODO

    # Dyncode refresh
    create_dyncode( Settings.editorialmodel.emfile,
                    Settings.editorialmodel.emtranslator,
                    Settings.editorialmodel.dyncode)


def init_all_dbs():
    import loader
    loader.start()
    import leapi_dyncode as dyncode
    from lodel.plugin.datasource_plugin import DatasourcePlugin
    from lodel.settings.utils import SettingsError
    from lodel.leapi.leobject import LeObject
    from lodel.plugin import Plugin
    from lodel import logger

    ds_cls = dict() # EmClass indexed by rw_datasource
    for cls in dyncode.dynclasses:
        ds = cls._datasource_name
        if ds not in ds_cls:
            ds_cls[ds] = [cls]
        else:
            ds_cls[ds].append(cls)
    
    for ds_name in ds_cls:
        mh = DatasourcePlugin.init_migration_handler(ds_name)
        #Retrieve plugin_name & ds_identifier for logging purpose
        plugin_name, ds_identifier = DatasourcePlugin.plugin_name(
            ds_name, False)
        try:
            mh.init_db(ds_cls[ds_name])
        except Exception as e:
            msg = "Migration failed for datasource %s(%s.%s) when running \
init_db method: %s"
            msg %= (ds_name, plugin_name, ds_identifier, e)
        logger.info("Database initialisation done for %s(%s.%s)" % (
            ds_name, plugin_name, ds_identifier))

def list_registered_hooks():
    import loader
    loader.start()
    from lodel.plugin.hooks import LodelHook
    hlist = LodelHook.hook_list()
    print("Registered hooks are : ")
    for name in sorted(hlist.keys()):
        print("\t- %s is registered by : " % name)
        for reg_hook in hlist[name]:
            hook, priority = reg_hook
            msg = "\t\t- {modname}.{funname} with priority : {priority}"
            msg = msg.format(
                modname = hook.__module__,
                funname = hook.__name__,
                priority = priority)
            print(msg)
        print("\n")

##@brief update plugin's discover cache
#@note impossible to give arguments from a Makefile...
#@todo write a __main__ to be able to run ./lodel_admin
def update_plugin_discover_cache(path_list = None):
    os.environ['LODEL2_NO_SETTINGS_LOAD'] = 'True'
    import loader
    from lodel.plugin.plugins import Plugin
    res = Plugin.discover(path_list)
    print("Plugin discover result in %s :\n" % res['path_list'])
    for pname, pinfos in res['plugins'].items():
        print("\t- %s %s -> %s" % (
            pname, pinfos['version'], pinfos['path']))

if __name__ == '__main__':
    _simlink_hack()
    import loader
    loader.start()
    from lodel.plugin.scripts import main_run
    main_run()
