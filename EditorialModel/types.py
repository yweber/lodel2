#-*- coding: utf-8 -*-

from EditorialModel.fields_types import Em_Field_Type
from Database import sqlutils
import sqlalchemy as sql

from EditorialModel.components import EmComponent, EmComponentNotExistError
from EditorialModel.fieldgroups import EmFieldGroup
from EditorialModel.classtypes import EmNature, EmClassType
import EditorialModel.fieldtypes as ftypes
import EditorialModel.classes

## Represents type of documents
# A type is a specialisation of a class, it can select optional field,
# they have hooks, are organized in hierarchy and linked to other
# EmType with special fields called relation_to_type fields
#
# @see EditorialModel::components::EmComponent
class EmType(EmComponent):
    table = 'em_type'

    ## @brief Specific EmClass fields
    # @see EditorialModel::components::EmComponent::_fields
    _fields = [
        ('class_id', ftypes.EmField_integer),
        ('icon', ftypes.EmField_integer),
        ('sortcolumn', ftypes.EmField_char)
        ]

    @classmethod
    ## Create a new EmType and instanciate it
    # @param name str: The name of the new type
    # @param em_class EmClass: The class that the new type will specialize
    # @return An EmType instance
    #
    # @see EmComponent::__init__()
    # 
    # @todo Remove hardcoded default value for icon
    # @todo check that em_class is an EmClass object
    def create(c, name, em_class):
        try:
            exists = EmType(name)
        except EmComponentNotExistError:
            return super(EmType, c).create(name=name, class_id=em_class.uid, icon=0)

        return exists
    
    ## Get the list of associated fieldgroups
    # @return A list of EmFieldGroup instance
    def field_groups(self):
        fg_table = sqlutils.getTable(EmFieldGroup)
        req = fg_table.select(fg_table.c.uid).where(fg_table.c.class_id == self.class_id)
        conn = self.__class__.getDbE().connect()
        res = conn.execute(req)
        rows = res.fetchall()
        conn.close()

        return [ EmFieldGroup(row['uid']) for row in rows ]

    ## Get the list of associated fields
    # @return A list of EmField instance
    # @todo handle optionnal fields
    def fields(self):
        res = []
        for fguid in self.field_groups():
            res += EmFieldGroup(fguid).fields()
        return res
        pass

    ## Select_field (Function)
    #
    # Indicates that an optional field is used
    #
    # @param field EmField: The optional field to select
    # @throw ValueError, TypeError
    # @todo change exception type and define return value and raise condition
    def select_field(self, field):
        Em_Field_Type.create(self, field)

    ## Unselect_field (Function)
    #
    # Indicates that an optional field will not be used
    #
    # @param field EmField: The optional field to unselect
    # @throw ValueError, TypeError
    # @todo change exception type and define return value and raise condition
    def unselect_field(self, field):
        emFieldType = Em_Field_Type(self.uid, field.uid)
        emFieldType.delete()
        del emFieldType

    ## Get the list of associated hooks
    # @note Not conceptualized yet
    # @todo Conception
    def hooks(self):
        pass

    ## Add a new hook
    # @param hook EmHook: An EmHook instance
    # @throw TypeError
    # @note Not conceptualized yet
    # @todo Conception
    def add_hook(self, hook):
        pass

    ## Delete a hook
    # @param hook EmHook: An EmHook instance
    # @throw TypeError
    # @note Not conceptualized yet
    # @todo Conception
    # @todo Maybe we don't need a EmHook instance but just a hook identifier
    def del_hook(self,hook):
        pass


    @classmethod
    ## Return an sqlalchemy table for type hierarchy
    # @return sqlalchemy em_type_hierarchy table object
    # @todo Don't hardcode table name
    def _tableHierarchy(cl):
        return sql.Table('em_type_hierarchy', cl.getDbE())

    ## Return the EmClassType of the type
    # @return EditorialModel.classtypes.*
    def _getClassType(self):
        return getattr(EmClassType, EmClass(self.class_id).class_type)

    ## @brief Get the list of subordinates EmType
    # Get a list of EmType instance that have this EmType for superior
    #
    # @return Return a dict with relation nature as keys and values as a list of subordinates
    # EmType instance
    #
    # @throw RuntimeError if a nature fetched from db is not valid
    def subordinates(self):

        conn = self.getDbE().connect()
        htable = self.__class__._tableHierarchy()
        req = htable.select(htable.c.subordinate_id, htable.c.nature).where(htable.c.superior_id == self.uid)
        res = conn.execute(req)
        rows = res.fetchall()
        conn.close()

        result = dict()
        for nname in EmNature.__dict__():
            result[getattr(EmNature, nname)] = []
        
        for row in rows:
            if row['nature'] not in result:
                #Maybe security issue ?
                logger.error("Unreconized nature in Database for EmType<"+str(self.uid)+"> subordinate <"+str(row['subordinate_id'])+"> : '"+row['nature']+"'")
                raise RuntimeError("Unreconized nature from database : "+row['nature'])

            result[row['nature']].append( EmType(row['subordinate_id']) )

        return result

    ## Add a superior in the type hierarchy
    # @param em_type EmType: An EmType instance
    # @param relation_nature str: The name of the relation's nature
    # @throw TypeError when em_type not an EmType instance
    # @throw ValueError when relation_nature isn't reconized or not allowed for this type
    # @todo define return value and raise condition
    def add_superior(self, em_type, relation_nature):
        pass

    ## Delete a superior in the type hierarchy
    # @param em_type EmType: An EmType instance
    # @throw TypeError when em_type isn't an EmType instance
    # @todo define return value and raise condition
    def del_superior(self, em_type):
        pass

    ## @brief Get the list of linked type
    # Types are linked with special fields called relation_to_type fields
    # @return a list of EmType
    # @see EmFields
    def linked_types(self):
        pass

