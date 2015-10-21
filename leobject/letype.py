#-*- coding: utf-8 -*-

from Lodel.utils.classinstancemethod import classinstancemethod
from leobject.leclass import LeClass
from leobject.leobject import LeObjectError

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
                raise RuntimeError("Trying to instanciate a %s with an EM uid that is not correct"%self.__class__.__name__)

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

        fdatas = self._datasource.get(self._leclass, self.__class__, 'lodel_id = %d'%self.lodel_id)
        for fname, fdats in fdatas[0].items():
            setattr(self, name, value)

    ## @brief Get a fieldname:value dict
    # @warning Giving True as full argument can represent a performances issue
    # @param full bool : If true populate the object before returning the datas
    # @return A dict with field name as key and the field value as value
    @property
    def datas(self, full=False):
        if full:
            self.populate()
        return { fname: getattr(self, fname) for fname in self._fields if hasattr(self,fname) }
            

    ## @brief Delete the LeType from Db
    # @note equivalent to LeType::delete(this.lodel_id)
    @classinstancemethod
    def delete(self):
        pass
    
    ## @brief Delete a LeType from the datasource
    # @param lodel_id int : The lodel_id identifying the LeType
    # @param return True if deleted False if not existing
    # @throw InvalidArgumentError if invalid parameters
    # @throw Leo exception if the lodel_id identify an object from another type
    @delete.classmethod
    def delete(cls, uid_l):
        pass

    @classinstancemethod
    ## @brief Update a LeType in db
    def update(self):
        pass

    @update.classmethod
    ## @brief Update some LeType in db
    # @param datas : keys are lodel_id and value are dict of fieldname => value
    # @throw Some exception for some errors in datas
    def update(cls, datas):
        pass

    ## @brief Insert a new LeType in the datasource
    # @param **datas : A dict containing the datas
    # @return The lodel id of the new LeType or False
    # @thorw A leo exception if invalid stuff
    # @throw InvalidArgumentError if invalid argument
    @classmethod
    def insert(cls, **datas):
        cls.check_datas_or_raise(datas, complete=True)
        super(LeType, cls).insert(typename=cls.__name__, **datas)
        pass
    
    ## @brief Check that datas are valid for this type
    # @param datas dict : key == field name value are field values
    # @param complete bool : if True expect that datas provide values for all non internal fields
    # @throw TypeError If the datas are not valids
    # @throw AttributeError if datas provides values for automatic fields
    # @throw AttributeError if datas provides values for fields that doesn't exists
    @classmethod
    def check_datas_or_raise(cls, datas, complete = False):
        autom_fields = [f.name for f in cls._fieldtypes if f.internal]
        for dname, dval in datas.items():
            if dname in autom_fields:
                raise AttributeError("The field '%s' is internal"%(dname))
            if dname not in cls._fields:
                raise AttributeError("No such field '%s' for %s"%(dname, self.__class__.__name__))
            cls._fieldtypess[dname].check_or_raise(dval)
        
        fields = [f.name for f in cls._fieldtypes if not f.internal]
        if complete and len(datas) < len(fields):
            raise LeObjectError("The argument complete was True but some fields are missing : %s"%(set(fields) - set(datas.keys())))
    
    ## @brief Check that datas are valid for this type
    # @param datas dict : key == field name value are field values
    # @param complete bool : if True expect that datas provide values for all non internal fields
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
        if name in self._fields.keys():
            self._fields[name].check_or_raise(value)
        return super(LeType, self).__setattr__(name, value)
    
    ## @brief Fetch superiors
    # @param nature str : The relation nature
    # @return if no nature given return a dict with nature as key and arrays of LeObject as value. Else return an array of LeObject
    def superiors(self, nature = None):
        pass

    ## @brief Fetch subordinates
    # @param nature str : The relation nature
    # @return if no nature given return a dict with nature as key and arrays of LeObject as value. Else return an array of LeObject
    def subordinates(self, nature = None):
        pass

    ## @brief Add a superior
    # @param nature str : The raltion nature
    # @param leo LeObject : The superior
    # @param return True if done False if already done
    # @throw A Leo exception if trying to link with an invalid leo
    # @throw InvalidArgumentError if invalid argument
    def set_superior(self, nature, leo):
        pass
    
