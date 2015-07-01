#-*- coding: utf-8 -*-

from EditorialModel.fieldtypes import EmField_integer
from EditorialModel.components import EmComponent

from Database import sqlutils
import sqlalchemy as sqla

import logging

logger = logging.getLogger('Lodel2.EditorialModel')


## Em_Field_Type (Class)
#
# Represents an association between a field and a type
class Em_Field_Type(object):

    table = 'em_field_type'
    _fields = [('type_id', EmField_integer), ('field_id', EmField_integer)]

    ## __init__ (Function)
    #
    # Instanciates an Em_Field_Type object with data fetched from the database
    #
    # @param type_id integer: Identifier of the type
    # @param field_id integer: Identifier of the field
    def __init__(self, type_id, field_id):
        self.table = Em_Field_Type.table
        self._fields = self.__class__._fields
        self.type_id = type_id
        self.field_id = field_id

    ## Create (Function)
    #
    # Creates a relation between a field and a type
    #
    # @static
    #
    # @param emType EmType: Object representing the Type
    # @param emField EmField: Object representing the Field
    # @return Em_Field_Type object
    @classmethod
    def create(cls, em_type, em_field):
        values = {
            'type_id': em_type.uid,
            'field_id': em_field.uid
        }

        created_relation = Em_Field_Type._create_db(**values)
        return created_relation

    @classmethod
    def _create_db(cls, **kwargs):
        dbe = EmComponent.db_engine()
        conn = dbe.connect()
        table = sqla.Table(cls.table, sqlutils.meta(dbe))
        req = table.insert(kwargs)
        res = conn.execute(req)
        conn.close()
        return Em_Field_Type(kwargs['type_id'], kwargs['field_id'])

    ## Delete (Function)
    #
    # Deletes a relation between a field and a type
    #
    # @return Boolean
    def delete(self):
        return self._delete_db()

    def _delete_db(self):
        dbe = EmComponent.db_engine()
        table = sqla.Table(self.table, sqlutils.meta(dbe))
        req = table.delete().where(table.c.type_id == self.type_id).where(table.c.field_id == self.field_id)
        conn = dbe.connect()
        try:
            conn.execute(req)
            res = True
        except:
            res = False
        conn.close()

        return res

    ## Exists (Function)
    #
    # Checks if a the relation exists in the database
    #
    # @return True if success, False if failure
    def exists(self):
        return self._exists_db()

    ## _ExistsDb (Function)
    #
    # Queries the database to see if a relation exists or not
    #
    # @return True if success, False if failure
    def _exists_db(self):
        dbe = EmComponent.db_engine()
        table = sqla.Table(self.table, sqlutils.meta(dbe))
        req = table.select().where(table.c.type_id == self.type_id).where(table.c.field_id == self.field_id)
        conn = dbe.connect()
        res = conn.execute(req).fetchall()
        conn.close()
        return len(res) > 0
