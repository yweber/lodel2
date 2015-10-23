#-*- coding: utf-8 -*-

## @package leobject API to access lodel datas
#
# This package contains abstract classes leobject.leclass.LeClass , leobject.letype.LeType, leobject.leobject._LeObject.
# Those abstract classes are designed to be mother classes of dynamically generated classes ( see leobject.lefactory.LeFactory )

## @package leobject.leobject
# @brief Abstract class designed to be implemented by LeObject
#
# @note LeObject will be generated by leobject.lefactory.LeFactory

import re

import leobject
import EditorialModel
from EditorialModel.types import EmType

REL_SUP = 0
REL_SUB = 1

## @brief Main class to handle objects defined by the types of an Editorial Model
class _LeObject(object):
    
    ## @brief The editorial model
    _model = None
    ## @brief The datasource
    _datasource = None
    ## @brief maps em uid with LeType or LeClass keys are uid values are LeObject childs classes
    _me_uid = dict()

    _query_re = None
    _query_operators = ['=', '<=', '>=', '!=', '<', '>', ' in ', ' not in ']
    
    ## @brief Instantiate with a Model and a DataSource
    # @param **kwargs dict : datas usefull to instanciate a _LeObject
    def __init__(self, **kwargs):
        raise NotImplementedError("Abstract constructor")
    
    ## @brief Given a ME uid return the corresponding LeClass or LeType class
    # @return a LeType or LeClass child class
    # @throw KeyError if no corresponding child classes
    @classmethod
    def uid2leobj(cls, uid):
        uid = int(uid)
        if uid not in cls._me_uid:
            raise KeyError("No LeType or LeClass child classes with uid '%d'"%uid)
        return cls._me_uid[uid]
    
    ## @brief Creates new entries in the datasource
    # @param datas list : A list a dict with fieldname as key
    # @param cls
    # @return a list of inserted lodel_id
    # @see leobject.datasources.dummy.DummyDatasource.insert(), leobject.letype.LeType.insert()
    @classmethod
    def insert(cls, letype, datas):
        if cls == _LeObject:
            raise NotImplementedError("Abstract method")
        letype,leclass = cls._prepare_targets(letype)
        if letype is None:
            raise ValueError("letype argument cannot be None")

        for data in datas:
            letype.check_datas_or_raise(data, complete = True)
        return cls._datasource.insert(letype, leclass, datas)
    
    ## @brief Delete LeObjects given filters
    # @param cls
    # @param letype LeType|str : LeType child class or name
    # @param leclass LeClass|str : LeClass child class or name
    # @param filters list : list of filters (see @ref leobject_filters)
    # @return bool
    @classmethod
    def delete(cls, letype, filters):
        letype, leclass = cls._prepare_targets(letype)
        filters,relationnal_filters = leobject.leobject._LeObject._prepare_filters(filters, letype, leclass)
        return cls._datasource.delete(letype, leclass, filters, relationnal_filters)
    
    ## @brief Update LeObjects given filters and datas
    # @param cls
    # @param letype LeType|str : LeType child class or name
    # @param filters list : list of filters (see @ref leobject_filters)
    @classmethod
    def update(cls, letype, filters, datas):
        letype, leclass = cls._prepare_targets(letype)
        filters,relationnal_filters = leobject.leobject._LeObject._prepare_filters(filters, letype, leclass)
        if letype is None:
            raise ValueError("Argument letype cannot be None")
        letype.check_datas_or_raise(datas, False)
        return cls._datasource.update(letype, leclass, filters, relationnal_filters, datas)

    ## @brief make a search to retrieve a collection of LeObject
    # @param query_filters list : list of string of query filters (or tuple (FIELD, OPERATOR, VALUE) ) see @ref leobject_filters
    # @param field_list list|None : list of string representing fields see @ref leobject_filters
    # @param typename str : The name of the LeType we want
    # @param classname str : The name of the LeClass we want
    # @param cls
    # @return responses ({string:*}): a list of dict with field:value
    @classmethod
    def get(cls, query_filters, field_list = None, typename = None, classname = None):

        letype,leclass = cls._prepare_targets(typename, classname)

        #Checking field_list
        if field_list is None or len(field_list) == 0:
            #default field_list
            if not (letype is None):
                field_list = letype._fields
            elif not (leclass is None):
                field_list = leclass._fieldtypes.keys()
            else:
                field_list = list(EditorialModel.classtypes.common_fields.keys())

        #Fetching LeType
        if letype is None:
            if 'type_id' not in field_list:
                field_list.append('type_id')


        field_list = cls._prepare_field_list(field_list, letype, leclass)
        
        #preparing filters
        filters, relationnal_filters = cls._prepare_filters(query_filters, letype, leclass)

        #Fetching datas from datasource
        datas = cls._datasource.get(leclass, letype, field_list, filters, relationnal_filters)
        
        #Instanciating corresponding LeType child classes with datas
        result = list()
        for leobj_datas in datas:
            letype = self.uid2leobj(datas['type_id']) if letype is None else letype
            result.append(letype(datas))

        return result

    @classmethod
    def _prepare_field_list(cls, field_list, letype, leclass):
        cls._check_fields(letype, leclass, [f for f in field_list if not cls._field_is_relational(f)])
        for i, field in enumerate(field_list):
            if cls._field_is_relational(field):
                field_list[i] = cls._prepare_relational_field(field)
        return field_list

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
    @staticmethod
    def _prepare_targets(letype = None , leclass = None):

        if not(leclass is None):
            if isinstance(leclass, str):
                leclass = leobject.lefactory.LeFactory.leobj_from_name(leclass)
            
            if not isinstance(leclass, type) or not (leobject.leclass.LeClass in leclass.__bases__) or leclass.__class__ == leobject.leclass.LeClass:
                raise ValueError("None | str | LeType child class excpected, but got : '%s' %s"%(leclass,type(leclass)))

        if not(letype is None):
            if isinstance(letype, str):
                letype = leobject.lefactory.LeFactory.leobj_from_name(letype)

            if not isinstance(letype, type) or not leobject.letype.LeType in letype.__bases__ or letype.__class__ == leobject.letype.LeType:
                raise ValueError("None | str | LeType child class excpected, but got : %s"%type(letype))

            if leclass is None:
                leclass = letype._leclass
            elif leclass != letype._leclass:
                raise ValueError("LeType child class %s does'nt inherite from LeClass %s"%(letype.__name__, leclass.__name__))

        return (letype, leclass)

    ## @brief Check if a fieldname is valid
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
                if not (leclass is None):
                    if letype._leclass != leclass:
                        raise AttributeError("The EmType %s is not a specialisation of the EmClass %s"%(typename, classname))
                field_l = letype._fields
            #Checks that fields are in this type
            for field in fields:
                if field not in field_l:
                    raise LeObjectQueryError("No field named '%s' in '%s'"%(field, letype.__name__))
        pass

    ## @brief Prepare filters for datasource
    # 
    # This method divide filters in two categories :
    #  - filters : standart FIELDNAME OP VALUE filter
    #  - relationnal_filters : filter on object relation RELATION_NATURE OP VALUE
    # 
    # Both categories of filters are represented in the same way, a tuple with 3 elements (NAME|NAT , OP, VALUE )
    # 
    # @warning This method assume that letype and leclass are returned from _LeObject._prepare_targets() method
    # @param filters_l list : This list can contain str "FIELDNAME OP VALUE" and tuples (FIELDNAME, OP, VALUE)
    # @param letype LeType|None : needed to check filters
    # @param leclass LeClass|None : needed to check filters
    # @return a tuple(FILTERS, RELATIONNAL_FILTERS
    #
    # @see @ref datasource_side
    @staticmethod
    def _prepare_filters(filters_l, letype = None, leclass = None):
        filters = list()
        for fil in filters_l:
            if len(fil) == 3 and not isinstance(fil, str):
                filters.append(tuple(fil))
            else:
                filters.append(_LeObject._split_filter(fil))

        #Checking relational filters (for the moment fields like superior.NATURE)
        relational_filters = [ (_LeObject._prepare_relational_field(field), operator, value) for field, operator, value in filters if _LeObject._field_is_relational(field)]
        filters = [f for f in filters if not _LeObject._field_is_relational(f[0])]
        #Checking the rest of the fields
        _LeObject._check_fields(letype, leclass, [ f[0] for f in filters ])
        
        return (filters, relational_filters)


    ## @brief Check if a field is relational or not
    # @param field str : the field to test
    # @return True if the field is relational else False
    @staticmethod
    def _field_is_relational(field):
        return field.startswith('superior.') or field.startswith('subordinate')
    
    ## @brief Check that a relational field is valid
    # @param field str : a relational field
    # @return a nature
    @staticmethod
    def _prepare_relational_field(field):
        spl = field.split('.')
        if len(spl) != 2:
            raise LeObjectQueryError("The relationalfield '%s' is not valid"%field)
        nature = spl[-1]
        if nature not in EditorialModel.classtypes.EmNature.getall():
            raise LeObjectQueryError("'%s' is not a valid nature in the field %s"%(nature, field))
        
        if spl[0] == 'superior':
            return (REL_SUP, nature)
        elif spl[0] == 'subordinate':
            return (REL_SUB, nature)
        else:
            raise LeObjectQueryError("Invalid preffix for relationnal field : '%s'"%spl[0])

    ## @brief Check and split a query filter
    # @note The query_filter format is "FIELD OPERATOR VALUE"
    # @param query_filter str : A query_filter string
    # @param cls
    # @return a tuple (FIELD, OPERATOR, VALUE)
    @classmethod
    def _split_filter(cls, query_filter):
        if cls._query_re is None:
            cls._compile_query_re()

        matches = cls._query_re.match(query_filter)
        if not matches:
            raise ValueError("The query_filter '%s' seems to be invalid"%query_filter)

        result = (matches.group('field'), re.sub(r'\s', ' ', matches.group('operator'), count=0), matches.group('value').strip())
        for r in result:
            if len(r) == 0:
                raise ValueError("The query_filter '%s' seems to be invalid"%query_filter)
        return result

    ## @brief Compile the regex for query_filter processing
    # @note Set _LeObject._query_re
    @classmethod
    def _compile_query_re(cls):
        op_re_piece = '(?P<operator>(%s)'%cls._query_operators[0].replace(' ', '\s')
        for operator in cls._query_operators[1:]:
            op_re_piece += '|(%s)'%operator.replace(' ', '\s')
        op_re_piece += ')'
        cls._query_re = re.compile('^\s*(?P<field>(((superior)|(subordinate))\.)?[a-z_][a-z0-9\-_]*)\s*'+op_re_piece+'\s*(?P<value>[^<>=!].*)\s*$', flags=re.IGNORECASE)
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
# @note The field_list arguement of leobject.leobject._LeObject.get() use the same syntax than the FIELD filter part 
# @subsection oppart OPERATOR
# The OPERATOR part of a filter is a comparison operator. There is
# - standart comparison operators : = , <, > , <=, >=, !=
# - list operators : 'in' and 'not in'
# The list of allowed operators is sotred at leobject.leobject._LeObject._query_operators . 
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
# - leobject.leobject.REL_SUB for "subordinates"
# - leobject.leobject.REL_SUP for "superiors"
#
# @note The filters translation process also check if given field are valids compared to the concerned letype and/or the leclass
