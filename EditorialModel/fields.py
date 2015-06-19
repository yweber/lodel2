#-*- coding: utf-8 -*-

from EditorialModel.components import EmComponent, EmComponentNotExistError
from EditorialModel.fieldtypes import *
from EditorialModel.fields_types import Em_Field_Type
from EditorialModel.fieldgroups import EmFieldGroup
from EditorialModel.classes import EmClass
from EditorialModel.types import EmType

from Database import sqlutils
from Database.sqlwrapper import SqlWrapper
from Database.sqlquerybuilder import SqlQueryBuilder

import sqlalchemy as sql

import EditorialModel
import logging

logger = logging.getLogger('Lodel2.EditorialModel')

## EmField (Class)
#
# Represents one data for a lodel2 document
class EmField(EmComponent):

    table = 'em_field'
    _fields = [
        ('fieldtype', EmField_char),
        ('fieldgroup_id', EmField_integer),
        ('rel_to_type_id', EmField_integer),
        ('rel_field_id', EmField_integer),
        ('optional', EmField_boolean),
        ('internal', EmField_boolean),
        ('icon', EmField_integer)
    ]

    ## Create (Function)
    #
    # Creates a new EmField and instanciates it
    #
    # @static
    #
    # @param kwargs dict: Dictionary of the values to insert in the field record
    #
    # @throw TypeError
    # @see EmComponent::__init__()
    # @staticmethod
    @classmethod
    def create(c, **kwargs):
        try:
            exists = EmField(kwargs['name'])
        except EmComponentNotExistError:
            values = {
                'name' : kwargs['name'],
                'fieldgroup_id' : kwargs['fieldgroup_id'],
                'fieldtype' : kwargs['fieldtype'].name,
                'optional' : 1 if 'optional' in kwargs else 0,
                'internal' : 1 if 'internal' in kwargs else 0,
                'rel_to_type_id': 0 if 'rel_to_type_id' not in kwargs else kwargs['rel_to_type_id'],
                'rel_field_id': 0 if 'rel_field_id' not in kwargs else kwargs['rel_field_id'],
                'icon': 0 if 'icon' not in kwargs else kwargs['icon']
            }

            createdField = super(EmField,c).create(**values)
            if createdField:
                # The field was created, we then add its column in the corresponding class' table
                is_field_column_added = EmField.addFieldColumnToClassTable(createdField)
                if is_field_column_added:
                    return createdField

            exists = createdField

        return exists


    ## addFieldColumnToClassTable (Function)
    #
    # Adds a column representing the field in its class' table
    #
    # @static
    #
    # @param emField EmField: the object representing the field
    # @return True in case of success, False if not
    @classmethod
    def addFieldColumnToClassTable(c, emField):
        field_type = "%s%s" % (EditorialModel.fieldtypes.get_field_type(emField.fieldtype).sql_column(), " DEFAULT 0" if emField.fieldtype=='integer' else '')
        field_uid = emField.uid
        field_class_table = emField.get_class_table()
        return SqlWrapper().addColumn(tname=field_class_table, colname=emField.name, coltype=field_type)

    ## get_class_table (Function)
    #
    # Gets the name of the table of the class corresponding to the field
    #
    # @return Name of the table
    def get_class_table(self):
        return self._get_class_tableDb()

    ## _get_class_tableDb (Function)
    #
    # Executes a request to the database to get the name of the table in which to add the field
    #
    # @return Name of the table
    def _get_class_tableDb(self):
        dbe = self.getDbE()
        conn = dbe.connect()
        typetable = sql.Table(EmType.table, sqlutils.meta(dbe))
        fieldtable = sql.Table(EmField.table, sqlutils.meta(dbe))
        reqGetClassId = typetable.select().where(typetable.c.uid==fieldtable.c.rel_to_type_id)
        resGetClassId = conn.execute(reqGetClassId).fetchall()
        class_id = dict(zip(resGetClassId[0].keys(), resGetClassId[0]))['class_id']

        classtable = sql.Table(EmClass.table, sqlutils.meta(dbe))
        reqGetClassTable = classtable.select().where(classtable.c.uid == class_id)
        resGetClassTable = conn.execute(reqGetClassTable).fetchall()
        classTableName = dict(zip(resGetClassTable[0].keys(), resGetClassTable[0]))['name']

        return classTableName

