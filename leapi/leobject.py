#-*- coding: utf-8 -*-

## @package leobject API to access lodel datas
#
# This package contains abstract classes leapi.leclass.LeClass , leapi.letype.LeType, leapi.leapi._LeObject.
# Those abstract classes are designed to be mother classes of dynamically generated classes ( see leapi.lefactory.LeFactory )

## @package leapi.leobject
# @brief Abstract class designed to be implemented by LeObject
#
# @note LeObject will be generated by leapi.lefactory.LeFactory

import re
import copy
import warnings

import leapi
from leapi.lecrud import _LeCrud, REL_SUP, REL_SUB
from leapi.lefactory import LeFactory
import EditorialModel
from EditorialModel.types import EmType

## @brief Main class to handle objects defined by the types of an Editorial Model
class _LeObject(_LeCrud):
    
    ## @brief maps em uid with LeType or LeClass keys are uid values are LeObject childs classes
    # @todo check if this attribute shouldn't be in _LeCrud
    _me_uid = dict()
    
    ## @brief Stores the fields name associated with fieldtype of the fields that are common to every LeObject
    _leo_fieldtypes = dict()
    
    ## @brief Stores the names of the fields storing the EM class uid and EM type uid
    _me_uid_field_names = tuple(None, None)
    
    ## @brief Instanciate a partial LeObject with a lodel_id
    # @note use the get_instance method to fetch datas and instanciate a concret LeObject
    def __init__(self, lodel_id):
        #Warning ! Handles only single pk
        uid_fname, uid_ft = list(self._uid_fieldtype.items())[0]
        new_id, err = uid_ft.check_data_value(lodel_id)
        if not (err is None):
            raise err
        setattr(self, uid_fname, lodel_id)
    
    ## @return Corresponding populated LeObject
    def get_instance(self):
        uid_fname = self.uidname()
        qfilter = '{uid_fname} = {uid}'.format(uid_fname = uid_fname, uid = getattr(self, uid_fname))
        return leobject.get([qfilter])[0]
    
    ## @return True if the LeObject is partially instanciated
    def is_partial(self):
        return not hasattr(self, '_classtype')

    ## @brief Check if a LeObject is the relation tree Root
    # @todo implementation
    def is_root(self):
        return False

    ## @brief Dirty & quick comparison implementation
    def __cmp__(self, other):
        return 0 if self == other else 1
    ## @brief Dirty & quick equality implementation
    # @todo check class
    def __eq__(self, other):
        uid_fname = self.uidname()
        if not hasattr(other, uid_fname):
            return False
        return getattr(self, uid_fname) == getattr(other, uid_fname)
        
        
    ## @brief Quick str cast method implementation
    def __str__(self):
        return "<%s lodel_id=%d>"%(self.__class__, getattr(self, self.uidname()))

    def __repr__(self):
        return self.__str__()
    
    ## @brief Given a ME uid return the corresponding LeClass or LeType class
    # @return a LeType or LeClass child class
    # @throw KeyError if no corresponding child classes
    # @todo check if this method shouldn't be in _LeCrud
    @classmethod
    def uid2leobj(cls, uid):
        uid = int(uid)
        if uid not in cls._me_uid:
            raise KeyError("No LeType or LeClass child classes with uid '%d'"%uid)
        return cls._me_uid[uid]

    ## @brief instanciate the relevant lodel object using a dict of datas
    @classmethod
    def object_from_data(cls, datas):
        return cls.uid2leobj(datas['type_id'])(**datas)

    @classmethod
    def fieldtypes(cls):
        if cls._fieldtypes_all is None:
            cls._fieldtypes_all = dict()
            cls._fieldtypes_all.update(cls._uid_fieldtype)
            cls._fieldtypes_all.update(cls._leo_fieldtypes)
        return cls._fieldtypes_all

    @classmethod
    def typefilter(cls):
        if hasattr(cls, '_type_id'):
            return ('type_id','=', cls._type_id)
        elif hasattr(cls, '_class_id'):
            return ('class_id', '=', cls._class_id)
        else:
            raise ValueError("Cannot generate a typefilter with %s class"%cls.__name__)
    
    ## @brief Delete LeObjects from db given filters and a classname
    # @note if no classname given, take the caller class
    # @param filters list : 
    # @param classname None|str : the classname or None
    # @return number of deleted LeObjects
    # @see leapi.lecrud._LeCrud.delete()
    @classmethod
    def delete(cls, filters, classname = None):
        ccls = cls if classname is None else cls.name2class(classname)
        new_filters = copy.copy(filters)
        new_filters.append(ccls.typefilter())
        return _LeCrud.delete(ccls, new_filters)

    ## @brief Check that a relational field is valid
    # @param field str : a relational field
    # @return a nature
    @staticmethod
    def _prepare_relational_fields(field):
        spl = field.split('.')
        if len(spl) != 2:
            return ValueError("The relationalfield '%s' is not valid"%field)
        nature = spl[-1]
        if nature not in EditorialModel.classtypes.EmNature.getall():
            return ValueError("'%s' is not a valid nature in the field %s"%(nature, field))
        
        if spl[0] == 'superior':
            return (REL_SUP, nature)
        elif spl[0] == 'subordinate':
            return (REL_SUB, nature)
        else:
            return ValueError("Invalid preffix for relationnal field : '%s'"%spl[0])

## @brief Class designed to represent the hierarchy roots
# @see _LeObject.get_root() _LeObject.is_root()
class LeRoot(object):
    pass

class LeObjectError(Exception):
    pass

class LeObjectQueryError(LeObjectError):
    pass
