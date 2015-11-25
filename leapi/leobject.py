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
import warnings

import leapi
import EditorialModel
from leapi.lecrud import _LeCrud
from leapi.lefactory import LeFactory
from EditorialModel.types import EmType

REL_SUP = 0
REL_SUB = 1

## @brief Main class to handle objects defined by the types of an Editorial Model
class _LeObject(object):
    
    ## @brief maps em uid with LeType or LeClass keys are uid values are LeObject childs classes
    # @todo check if this attribute shouldn't be in _LeCrud
    _me_uid = dict()
    
    ## @brief Stores the fields name associated with fieldtype of the fields that are common to every LeObject
    _leo_fieldtypes = dict()

    ## @brief Instantiate with a Model and a DataSource
    # @param **kwargs dict : datas usefull to instanciate a _LeObject
    def __init__(self, **kwargs):
        raise NotImplementedError("Abstract constructor")
    
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
    
    @classmethod
    def fieldtypes(cls):
        if cls._fieldtypes_all is None:
            cls._fieldtypes_all = dict()
            cls._fieldtypes_all.update(cls._uid_fieldtype)
            cls._fieldtypes_all.update(cls._leo_fieldtypes)
        return cls._fieldtypes_all

    ## @brief Creates new entries in the datasource
    # @param datas list : A list a dict with fieldname as key
    # @param cls
    # @return a list of inserted lodel_id
    # @see leapi.datasources.dummy.DummyDatasource.insert(), leapi.letype.LeType.insert()
    @classmethod
    def insert(cls, letype, datas):
        if isinstance(datas, dict):
            datas = [datas]

        if cls == _LeObject:
            raise NotImplementedError("Abstract method")
        letype,leclass = cls._prepare_targets(letype)
        if letype is None:
            raise ValueError("letype argument cannot be None")

        for data in datas:
            letype.check_datas_or_raise(data, complete = True)
        return cls._datasource.insert(letype, leclass, datas)
    
    ## @brief Check if a LeType is a hierarchy root
    @staticmethod
    def is_root(leo):
        if isinstance(leo, leapi.letype.LeType):
            return False
        elif isinstance(leo, LeRoot):
            return True
        raise ValueError("Invalid value for a LeType : %s"%leo)
    
    ## @brief Return a LeRoot instance
    @staticmethod
    def get_root():
        return LeRoot()

    ## @brief Delete LeObjects given filters
    # @param cls
    # @param letype LeType|str : LeType child class or name
    # @param leclass LeClass|str : LeClass child class or name
    # @param filters list : list of filters (see @ref leobject_filters)
    # @return bool
    @classmethod
    def delete(cls, letype, filters):
        filters,relationnal_filters = cls._prepare_filters(filters)
        return cls._datasource.delete(letype, leclass, filters, relationnal_filters)
    
    ## @brief Update LeObjects given filters and datas
    # @param cls
    # @param letype LeType|str : LeType child class or name
    # @param filters list : list of filters (see @ref leobject_filters)
    @classmethod
    def update(cls, letype, filters, datas):
        letype, leclass = cls._prepare_targets(letype)
        filters,relationnal_filters = cls._prepare_filters(filters, letype, leclass)
        if letype is None:
            raise ValueError("Argument letype cannot be None")
        letype.check_datas_or_raise(datas, False)
        return cls._datasource.update(letype, leclass, filters, relationnal_filters, datas)

    ## @brief Link two leobject together using a rel2type field
    # @param lesup LeType : LeType child class instance linked as superior
    # @param lesub LeType : LeType child class instance linked as subordinate
    # @param **rel_attr : Relation attributes
    # @return True if linked without problems
    # @throw LeObjectError if the link is not valid
    # @throw LeObkectError if the link already exists
    # @throw AttributeError if an non existing relation attribute is given as argument
    # @throw ValueError if the relation attrivute value check fails
    # 
    # @todo Code factorisation on relation check
    # @todo unit tests
    @classmethod
    def link_together(cls, lesup, lesub, rank = 'last', **rel_attr):
        if lesub.__class__ not in lesup._linked_types.keys():
            raise LeObjectError("Relation error : %s cannot be linked with %s"%(lesup.__class__.__name__, lesub.__class__.__name__))

        for attr_name in rel_attr.keys():
            if attr_name not in [ f for f,g in lesup._linked_types[lesub.__class__] ]:
                raise AttributeError("A rel2type between a %s and a %s doesn't have an attribute %s"%(lesup.__class__.__name__, lesub.__class__.__name__))
            if not sup._linked_types[lesub.__class__][1].check(rel_attr[attr_name]):
                raise ValueError("Wrong value '%s' for attribute %s"%(rel_attr[attr_name], attr_name))

        #Checks that attributes are uniq for this relation
        rels_attr = [ attrs for lesup, lesub, attrs in cls.links_get(lesup) if lesup == lesup ]
        for e_attrs in rels_attrs:
            if rel_attr == e_attrs:
                raise LeObjectError("Relation error : a relation with the same attributes already exists")

        return cls._datasource.add_related(lesup, lesub, rank, **rel_attr)
    
    ## @brief Get related objects
    # @param leo LeType(instance) : LeType child class instance
    # @param letype LeType(class) : the wanted LeType child class (not instance) 
    # @param leo_is_superior bool : if True leo is the superior in the relation
    # @return A dict with LeType child class instance as key and dict {rel_attr_name:rel_attr_value, ...}
    # @throw LeObjectError if the relation is not possible
    # 
    # @todo Code factorisation on relation check
    # @todo unit tests
    @classmethod
    def linked_together(cls, leo, letype, leo_is_superior = True):
        valid_link = letype in leo._linked_types.keys() if leo_is_superior else leo.__class__ in letype._linked_types.keys()

        if not valid_link:
            raise LeObjectError("Relation error : %s have no links with %s"%(
                leo.__class__ if leo_is_superior else letype,
                letype if leo_is_superior else leo.__class__
            ))

        return cls._datasource.get_related(leo, letype, leo_is_superior)
    
    ## @brief Fetch a relation and its attributes
    # @param id_relation int : the relation identifier
    # @return a tuple(lesup, lesub, dict_attr) or False if no relation exists with this id
    # @throw Exception if the relation is not a rel2type relation
    @classmethod
    def link_get(cls, id_relation):
        return cls._datasource.get_relation(id_relation)
    
    ## @brief Fetch all relations for an objects
    # @param leo LeType : LeType child class instance
    # @return a list of tuple (lesup, lesub, dict_attr)
    def links_get(cls, leo):
        return cls._datasource.get_relations(leo)
    
    ## @brief Remove a link (and attributes) between two LeObject
    # @param id_relation int : Relation identifier
    # @return True if a link has been deleted
    # @throw LeObjectError if the relation is not a rel2type
    #
    # @todo Code factorisation on relation check
    # @todo unit tests
    @classmethod
    def link_remove(cls, id_relation):
        if lesub.__class__ not in lesup._linked_types.keys():
            raise LeObjectError("Relation errorr : %s cannot be linked with %s"%(lesup.__class__.__name__, lesub.__class__.__name__))

        return cls._datasource.del_related(lesup, lesub)
    
    ## @brief Add a hierarchy relation between two LeObject
    # @param lesup LeType|LeRoot : LeType child class instance
    # @param lesub LeType : LeType child class instance
    # @param nature str : The nature of the relation @ref EditorialModel.classtypes
    # @param rank str|int :  The relation rank. Can be 'last', 'first' or an integer
    # @param replace_if_exists bool : if True delete the old superior and set the new one. If False and there is a superior raise an LeObjectQueryError
    # @return The relation ID or False if fails
    # @throw LeObjectQueryError replace_if_exists == False and there is a superior
    @classmethod
    def hierarchy_add(cls, lesup, lesub, nature, rank = 'last', replace_if_exists = False):
        #Arguments check
        if nature not in EditorialModel.classtypes.EmClassType.natures(lesub._classtype):
            raise ValueError("Invalid nature '%s' for %s"%(nature, lesup.__class__.__name__))

        if not cls.leo_is_root(lesup):
            if nature not in EditorialModel.classtypes.EmClassType.natures(lesup._classtype):
                raise ValueError("Invalid nature '%s' for %s"%(nature, lesup.__class__.__name__))
            if lesup.__class__ not in lesub._superiors[nature]:
                raise ValueError("%s is not a valid superior for %s"%(lesup.__class__, lesub.__class__))
        #else:
        #   lesup is not a LeType but a hierarchy root

        if rank not in ['first', 'last'] and not isinstance(rank, int):
            raise ValueError("Allowed values for rank are integers and 'first' or 'last' but '%s' found"%rank)

        superiors = cls.hierarchy_get(lesub, nature, leo_is_sup = False)
        if lesup in len(superiors) > 0:
            if not replace_if_exists:
                raise LeObjectQueryError("The subordinate allready has a superior")
            #remove existig superior
            if not cls.hierarchy_del(superiors[0], lesub, nature):
                raise RuntimeError("Unable to delete the previous superior")

        return self._datasource.add_superior(lesup, lesub, nature, rank)
    
    ## @brief Delete a hierarchy link between two LeObject
    # @param lesup LeType | LeRoot : LeType child class or hierarchy root
    # @param lesub LeType : LeType child class
    # @param nature str : The nature of the relation @ref EditorialModel.classtypes
    # @return True if deletion done successfully
    # @throw ValueError when bad arguments given
    @classmethod
    def hierarchy_del(cls, lesup, lesub, nature):
        if nature not in EditorialModel.classtypes.EmClassType.natures(lesub._classtype):
            raise ValueError("Invalid nature '%s' for %s"%(nature, lesup.__class__.__name__))

        if not cls.leo_is_root(lesup):
            if nature not in EditorialModel.classtypes.EmClassType.natures(lesup._classtype):
                raise ValueError("Invalid nature '%s' for %s"%(nature, lesup.__class__.__name__))
            if lesup.__class__ not in lesub._superiors[nature]:
                raise ValueError("%s is not a valid superior for %s"%(lesup.__class__, lesub.__class__))
        superiors = cls.hierarchy_get(lesub, nature, leo_is_sup = False)
        res = True
        for _lesup in superiors:
            if not cls._datasource.del_superior(_lesup, lesub, nature):
                #How to handler this ?
                res = False
        return res
    
    ## @brief Fetch neighbour in hierarchy relation
    # @param leo LeType | LeRoot : We want the neighbour of this LeObject (can be the root)
    # @param nature str : @ref EditorialModel.classtypes
    # @param leo_is_sup bool : if True leo is the superior and we want to fetch the subordinates else its the oposite
    # @return A list of LeObject ordered by depth if leo_is_sup, else a list of subordinates
    @classmethod
    def hierarchy_get(cls, leo, nature, leo_is_sup = True):
        #Checking arguments
        if not (nature is None) and not cls.is_root(leo):
            if nature not in EditorialModel.classtypes.EmClassType.natures(leo._classtype):
                raise ValueError("Invalid nature '%s' for %s"%(nature, lesup.__class__.__name__))
        
        if leo_is_sup:
            return cls._datasource.get_subordinates(leo, nature)
        else:
            return cls._datasource.get_superiors(leo, nature)

    ## @brief Preparing letype and leclass arguments
    # 
    # This function will do multiple things : 
    #  - Convert string to LeType or LeClass child instances
    #  - If both letype and leclass given, check that letype inherit from leclass
    #  - If only a letype is given, fetch the parent leclass
    # @note If we give only a leclass as argument returned letype will be None
    # @note Its possible to give letype=None and leclass=None. In this case the method will return tuple(None,None)
    # @param letype LeType|str|None : LeType child instant or its name
    # @param leclass LeClass|str|None : LeClass child instant or its name
    # @return a tuple with 2 python classes (LeTypeChild, LeClassChild)
    @classmethod
    def _prepare_targets(cls, letype = None , leclass = None):
        raise ValueError()
        warnings.warn("_LeObject._prepare_targets is deprecated", DeprecationWarning)
        if not(leclass is None):
            if isinstance(leclass, str):
                leclass = cls.name2class(leclass)
                #leclass = LeFactory.leobj_from_name(leclass)
            
            if not isinstance(leclass, type) or not (leapi.leclass.LeClass in leclass.__bases__) or leclass.__class__ == leapi.leclass.LeClass:
                raise ValueError("None | str | LeType child class excpected, but got : '%s' %s"%(leclass,type(leclass)))

        if not(letype is None):
            if isinstance(letype, str):
                letype = cls.name2class(letype)
                #letype = LeFactory.leobj_from_name(letype)

            if not isinstance(letype, type) or not leapi.letype.LeType in letype.__bases__ or letype.__class__ == leapi.letype.LeType:
                raise ValueError("None | str | LeType child class excpected, but got : %s"%type(letype))

            if leclass is None:
                leclass = letype._leclass
            elif leclass != letype._leclass:
                raise ValueError("LeType child class %s does'nt inherite from LeClass %s"%(letype.__name__, leclass.__name__))

        return (letype, leclass)

    ## @brief Check if a fieldname is valid
    # @warning This method assume that letype and leclass are returned from _LeObject._prepare_targets() method
    # @param letype LeType|None : The concerned type (or None)
    # @param leclass LeClass|None : The concerned class (or None)
    # @param fields list : List of string representing fields
    # @throw LeObjectQueryError if their is some problems
    # @throw AttributeError if letype is not from the leclass class
    # @todo Delete the checks of letype and leclass and ensure that this method is called with letype and leclass arguments from _prepare_targets()
    #
    # @see @ref leobject_filters
    @staticmethod
    def _check_fields(letype, leclass, fields):
        warnings.warn("deprecated", DeprecationWarning)
        #Checking that fields in the query_filters are correct
        if letype is None and leclass is None:
            #Only fields from the object table are allowed
            for field in fields:
                if field not in EditorialModel.classtypes.common_fields.keys():
                    raise LeObjectQueryError("Not typename and no classname given, but the field %s is not in the common_fields list"%field)
        else:
            if letype is None:
                field_l = leclass._fieldtypes.keys()
            else:
                field_l = letype._fields
            #Checks that fields are in this type
            for field in fields:
                if field not in field_l:
                    raise LeObjectQueryError("No field named '%s' in '%s'"%(field, letype.__name__))
        pass
    
    ## @brief Check that a relational field is valid
    # @param field str : a relational field
    # @return a nature
    @staticmethod
    def _prepare_relational_field(field):
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

## @page leobject_filters LeObject query filters
# The LeObject API provide methods that accept filters allowing the user
# to query the database and fetch LodelEditorialObjects.
#
# The LeObject API translate those filters for the datasource. 
# 
# @section api_user_side API user side filters
# Filters are string expressing a condition. The string composition
# is as follow : "<FIELD> <OPERATOR> <VALUE>"
# @subsection fpart FIELD
# @subsubsection standart fields
# Standart fields, represents a value of the LeObject for example "title", "lodel_id" etc.
# @subsubsection rfields relationnal fields
# relationnal fields, represents a relation with the object hierarchy. Those fields are composed as follow :
# "<RELATION>.<NATURE>".
#
# - Relation can takes two values : superiors or subordinates
# - Nature is a relation nature ( see EditorialModel.classtypes )
# Examples : "superiors.parent", "subordinates.translation" etc.
# @note The field_list arguement of leapi.leapi._LeObject.get() use the same syntax than the FIELD filter part 
# @subsection oppart OPERATOR
# The OPERATOR part of a filter is a comparison operator. There is
# - standart comparison operators : = , <, > , <=, >=, !=
# - list operators : 'in' and 'not in'
# The list of allowed operators is sotred at leapi.leapi._LeObject._query_operators . 
# @subsection valpart VALUE
# The VALUE part of a filter is... just a value...
#
# @section datasource_side Datasource side filters
# As said above the API "translate" filters before forwarding them to the datasource. 
#
# The translation process transform filters in tuple composed of 3 elements
# ( @ref fpart , @ref oppart , @ref valpart ). Each element is a string.
#
# There is a special case for @ref rfields : the field element is a tuple composed with two elements
# ( RELATION, NATURE ) where NATURE is a string ( see EditorialModel.classtypes ) and RELATION is one of
# the defined constant : 
#
# - leapi.leapi.REL_SUB for "subordinates"
# - leapi.leapi.REL_SUP for "superiors"
#
# @note The filters translation process also check if given field are valids compared to the concerned letype and/or the leclass
