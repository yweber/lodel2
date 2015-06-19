# -*- coding: utf-8 -*-

## @file classes.py
# @see EditorialModel::classes::EmClass

import logging as logger

from EditorialModel.components import EmComponent, EmComponentNotExistError
from Database import sqlutils
import sqlalchemy as sql

import EditorialModel.fieldtypes as ftypes
import EditorialModel

## @brief Manipulate Classes of the Editorial Model
# Create classes of object.
#@see EmClass, EmType, EmFieldGroup, EmField
class EmClass(EmComponent):
    table = 'em_class'
    
    ## @brief Specific EmClass fields
    # @see EditorialModel::components::EmComponent::_fields
    _fields = [
        ('classtype', ftypes.EmField_char),
        ('icon', ftypes.EmField_integer),
        ('sortcolumn', ftypes.EmField_char)
    ]

    ## Create a new class
    # @param name str: name of the new class
    # @param class_type EmClasstype: type of the class
    # @return An EmClass instance
    @classmethod
    def create(c, name, class_type):
        try:
            res = EmClass(name)
            logger.info("Trying to create an EmClass that allready exists")
        except EmComponentNotExistError:
            res = c._createDb(name, class_type)
            logger.debug("EmClass successfully created")

        return res

    @classmethod
    ## Isolate SQL for EmClass::create
    # @todo Remove hardcoded default value for icon
    # @return An instance of EmClass
    def _createDb(c, name, class_type):
        """ Do the db querys for EmClass::create() """

        #Create a new entry in the em_class table
        values = { 'name':name, 'classtype':class_type['name'], 'icon':0 }
        resclass = super(EmClass,c).create(**values)


        dbe = c.getDbE()
        conn = dbe.connect()

        #Create a new table storing LodelObjects of this EmClass
        meta = sql.MetaData()
        emclasstable = sql.Table(name, meta,
            sql.Column('uid', sql.VARCHAR(50), primary_key = True))
        emclasstable.create(conn)

        conn.close()

        return resclass


    ## Retrieve list of the field_groups of this class
    # @return field_groups [EmFieldGroup]:
    def fieldgroups(self):
        records = self._fieldgroupsDb()
        fieldgroups = [ EditorialModel.fieldgroups.EmFieldGroup(int(record.uid)) for record in records ]

        return fieldgroups

    ## Isolate SQL for EmClass::fieldgroups
    # @return An array of dict (sqlalchemy fetchall)
    def _fieldgroupsDb(self):
        dbe = self.__class__.getDbE()
        emfg = sql.Table(EditorialModel.fieldgroups.EmFieldGroup.table, sqlutils.meta(dbe))
        req = emfg.select().where(emfg.c.class_id == self.uid)

        conn = dbe.connect()
        res = conn.execute(req)
        return res.fetchall()


    ## Retrieve list of fields
    # @return fields [EmField]:
    def fields(self):
        pass

    ## Retrieve list of type of this class
    # @return types [EmType]:
    def types(self):
        records = self._typesDb()
        types = [ EditorialModel.types.EmType(int(record.uid)) for record in records ]

        return types

    ## Isolate SQL for EmCLass::types
    # @return An array of dict (sqlalchemy fetchall)
    def _typesDb(self):
        dbe = self.__class__.getDbE()
        emtype = sql.Table(EditorialModel.types.EmType.table, sqlutils.meta(dbe))
        req = emtype.select().where(emtype.c.class_id == self.uid)
        conn = dbe.connect()
        res = conn.execute(req)
        return res.fetchall()

    ## Add a new EmType that can ben linked to this class
    # @param  t EmType: type to link
    # @return success bool: done or not
    def link_type(self, t):
        pass

    ## Retrieve list of EmType that are linked to this class
    #  @return types [EmType]:
    def linked_types(self):
        pass
