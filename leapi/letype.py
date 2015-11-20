#-*- coding: utf-8 -*-

## @package leobject API to access lodel datas
#
# This package contains abstract classes leapi.leclass.LeClass , leapi.letype.LeType, leapi.leapi._LeObject.
# Those abstract classes are designed to be mother classes of dynamically generated classes ( see leapi.lefactory.LeFactory )

## @package leapi.leobject
# @brief Abstract class designed to be implemented by LeObject
#
# @note LeObject will be generated by leapi.lefactory.LeFactory

import leapi
from leapi.leclass import LeClass
from leapi.leobject import LeObjectError

## @brief Represent an EmType data instance
# @note Is not a derivated class of LeClass because the concrete class will be a derivated class from LeClass
class LeType(object):
    
    ## @brief Stores selected fields with key = name
    _fields = list()
    ## @brief Allowed LeType superiors 
    _superiors = list()
    ## @brief Stores the class of LeClass
    _leclass = None
    ## @brief Stores the EM uid
    _type_id = None
    
    ## @brief Instanciate a new LeType
    # @param lodel_id : The lodel id
    # @param **kwargs : Datas used to populate a LeType
    def __init__(self, lodel_id, **kwargs):
        if self._leclass is None:
            raise NotImplementedError("Abstract class")

        self.lodel_id = lodel_id

        if 'type_id' in kwargs:
            if self.__class__._type_id != int(kwargs['type_id']):
                raise RuntimeError("Trying to instanciate a %s with an type_id that is not correct"%self.__class__.__name__)
        if 'class_id' in kwargs:
            if self.__class__._class_id != int(kwargs['class_id']):
                raise RuntimeError("Trying to instanciate a %s with a clas_id that is not correct"%self.__class__.__name__)

        ## Populate the object from the datas received in kwargs
        for name, value in kwargs.items():
            if name not in self._fields:
                raise AttributeError("No such field '%s' for %s"%(name, self.__class__.__name__))
            setattr(self, name, value)
    
    ## @brief Populate the LeType wih datas from DB
    # @param field_list None|list : List of fieldname to fetch. If None fetch all the missing datas
    def populate(self, field_list=None):
        if field_list == None:
            field_list = [ fname for fname in self._fields if not hasattr(self, fname) ]
        filters, rel_filters = self._prepare_filters(['lodel_id = %d'%(self.lodel_id)], self.__class__, self._leclass)

        fdatas = self._datasource.get(self._leclass, self.__class__, field_list, filters, rel_filters)
        for fname, fdats in fdatas[0].items():
            setattr(self, name, value)

    ## @brief Get a fieldname:value dict
    # @return A dict with field name as key and the field value as value
    @property
    def datas(self):
        return { fname: getattr(self, fname) for fname in self._fields if hasattr(self,fname) }
    
    ## @brief Get all the datas for this LeType
    # @return a dict with fieldname as key and field value as value
    # @warning Can represent a performance issue
    def all_datas(self):
        self.populate()
        return self.datas
    
    ## @brief Delete the LeType from Db
    # @note equivalent to LeType::delete(filters=['lodel_id = %s'%self.lodel_id)
    def db_delete(self):
        return self.delete([('lodel_id','=',repr(self.lodel_id))])
    
    ## @brief Get the linked objects lodel_id
    # @param letype LeType : Filter the result with LeType child class (not instance) 
    # @return a dict with LeType instance as key and dict{attr_name:attr_val...} as value
    # @todo unit tests
    def linked(self, letype):
        if leapi.letype.LeType not in letype.__bases__:
            raise ValueError("letype has to be a child class of LeType (not an instance) but %s found"%type(letype))
        
        if letype in self._linked_types.keys():
            get_sub = True
        elif self.__class__ in letype._linked_types.keys():
            get_sub = False
        else:
            raise ValueError("The two LeType classes %s and %s are not linked with a rel2type field"%(self.__class__.__name__, letype.__name__))

        return self._datasource.get_related(self, letype, get_sub)

    ## @brief Link this object with a LeObject as subordinate
    # @note shortcut for @ref leapi.leapi._LeObject.link_together()
    # @param lesub LeObject : The object to be linked with as subordinate
    # @param **rel_attr : keywords arguments for relations attributes
    # @return The relation_id if success else return False
    # @throw LeObjectError if the link is not valid
    # @throw LeObkectError if the link already exists
    # @throw AttributeError if an non existing relation attribute is given as argument
    # @throw ValueError if the relation attrivute value check fails
    # @see leapi.lefactory.LeFactory.link_together()
    def link(self, leo, **rel_attr):
        return leapi.lefactory.LeFactory.leobj_from_name('LeObject').link_together(self, leo, **rel_attr)
    
    ## @brief Returns linked subordinates in a rel2type given a wanted LeType child class
    # @param letype LeType(class) : The wanted LeType of result
    # @return A dict with LeType child class instance as key and dict {'id_relation':id, rel_attr_name:rel_attr_value, ...}
    # @throw LeObjectError if the relation is not possible
    # @see leapi.lefactory.LeFactory.linked_together()
    def linked_subordinates(self, letype):
        return leapi.lefactory.LeFactory.leobj_from_name('LeObject').linked_together(self, letype, True)

    ## @brief Remove a link with a subordinate
    # @param leo LeType : LeType child instance
    # @return True if a link has been deleted
    # @throw LeObjectError if the relation do not concern the current LeType
    def unlink_subordinate(self, id_relation):
        return leapi.lefactory.LeFactory.leobj_from_name('LeObject').linked_together(self, leo)

    ## @brief Remove a link bewteen this object and another
    # @param leo LeType : LeType child class instance
    # @todo unit tests
    def unlink(self, leo):
        if leo.__class__ in self._linked_types.keys():
            sup = self
            sub = leo
        elif self.__class__ in leo._linked_types.keys():
            sup = leo
            sub = self
        
        return self._datasource.del_related(sup, sub)
    
    ## @brief Add a superior
    # @param lesup LeType | LeRoot : LeType child class instance that will be the superior
    # @param nature str : The nature of the relation @ref EditorialModel.classtypes
    # @param rank str|int :  The relation rank. Can be 'last', 'first' or an integer
    # @param replace_if_exists bool : if True delete the old superior and set the new one. If False and there is a superior raise an LeObjectQueryError
    # @return The relation ID or False if fails
    def superior_add(self, leo, nature, rank = 'last', replace_if_exists = False):
        return leapi.lefactory.LeFactory.leobj_from_name('LeObject').hierarchy_add(leo, self, nature, rank, replace_if_exists)

    ## @brief Delete a superior given a relation's natue
    # @param leo LeType | LeRoot : The superior to delete
    # @param nature str : The nature of the relation @ref EditorialModel.classtypes
    # @return True if deletion is a success
    def superior_del(self, leo, nature):
        return leapi.lefactory.leobj_from_name('LeObject').hierarchy_del(leo, self, nature)
    
    ## @brief Fetch superiors by depth
    # @return A list of LeObject ordered by depth (the first is the one with the bigger depth)
    def superiors(self):
        return leapi.lefactory.leobj_from_name('LeObject').hierarchy_get(self,nature, leo_is_sup = False)

    ## @brief Fetch subordinates ordered by rank
    # @return A list of LeObject ordered by rank
    def subordinates(self):
        return leapi.lefactory.leobj_from_name('LeObject').hierarchy_get(self,nature, leo_is_sup = True)
    
    ## @brief Delete a LeType from the datasource
    # @param filters list : list of filters (see @ref leobject_filters)
    # @param cls
    # @return True if deleted False if not existing
    # @throw InvalidArgumentError if invalid parameters
    # @throw Leo exception if the lodel_id identify an object from another type
    @classmethod
    def delete(cls, filters):
        return cls.name2class('LeObject').delete(cls, filters)
        
    ## @brief Update a LeType in db
    def db_update(self):
        return self.update(filters=[('lodel_id', '=', repr(self.lodel_id))], datas = self.datas)
        
    @classmethod
    ## @brief Update some LeType in db
    # @param datas : keys are lodel_id and value are dict of fieldname => value
    # @param filters list : list of filters (see @ref leobject_filters)
    # @param cls
    # return bool
    def update(cls, filters, datas):
        return cls.leobject().update(letype = cls, filters = filters, datas = datas)
        
    ## @brief Insert a new LeType in the datasource
    # @param **datas list : A list of dict containing the datas
    # @return The lodel id of the new LeType or False
    # @thorw A leo exception if invalid stuff
    # @throw InvalidArgumentError if invalid argument
    @classmethod
    def insert(cls, datas):
        return super(LeType, cls).insert(letype=cls, datas=datas)
    
    ## @brief Check that datas are valid for this type
    # @param datas dict : key == field name value are field values
    # @param complete bool : if True expect that datas provide values for all non internal fields
    # @param allow_internal bool : if True don't raise an error if a field is internal
    # @throw TypeError If the datas are not valids
    # @throw AttributeError if datas provides values for automatic fields
    # @throw AttributeError if datas provides values for fields that doesn't exists
    @classmethod
    def check_datas_or_raise(cls, datas, complete = False, allow_internal = True):
        autom_fields = [f for f, ft in cls._fieldtypes.items() if hasattr(ft,'internal') and ft.internal]
        for dname, dval in datas.items():
            if not allow_internal and dname in autom_fields:
                raise AttributeError("The field '%s' is internal"%(dname))
            if dname not in cls._fields:
                raise AttributeError("No such field '%s' for %s"%(dname, cls.__name__))
            cls._fieldtypes[dname].check_or_raise(dval)
        
        fields = [f for f, ft in cls._fieldtypes.items() if not hasattr(ft,'internal') or not ft.internal and f in cls._fields]
        if complete and len(datas) < len(fields):
            raise LeObjectError("The argument complete was True but some fields are missing : %s"%(set(fields) - set(datas.keys())))
        
    
    ## @brief Check that datas are valid for this type
    # @param datas dict : key == field name value are field values
    # @param complete bool : if True expect that datas provide values for all non internal fields
    # @param cls
    # @return True if check pass else False
    def check_datas(cls, datas, complete = False):
        try:
            cls.check_datas_or_raise(datas, complete)
        except (TypeError, AttributeError, LeObjectError):
            return False
        return True

    ## @brief Implements the automatic checks of attributes
    # @note Run data check from fieldtypes if we try to modify an field attribute of the LeType
    # @param name str : The attribute name
    # @param value * : The value
    def __setattr__(self, name, value):
        if name in self._fields:
            self._fieldtypes[name].check_or_raise(value)
        return super(LeType, self).__setattr__(name, value)
    
