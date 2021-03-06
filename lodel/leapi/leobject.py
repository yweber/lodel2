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

## @package lodel.leapi.leobject
# This module is centered around the basic LeObject class, which is the main class for all the objects managed by lodel.


import importlib
import warnings
import copy

from lodel.context import LodelContext

LodelContext.expose_modules(globals(), {
    'lodel.logger': 'logger',
    'lodel.settings': 'Settings',
    'lodel.settings.utils': 'SettingsError',
    'lodel.leapi.query': ['LeInsertQuery', 'LeUpdateQuery', 'LeDeleteQuery',
                          'LeGetQuery'],
    'lodel.leapi.exceptions': ['LeApiError', 'LeApiErrors',
                               'LeApiDataCheckError', 'LeApiDataCheckErrors', 'LeApiQueryError',
                               'LeApiQueryErrors'],
    'lodel.plugin.exceptions': ['PluginError', 'PluginTypeError',
                                'LodelScriptError', 'DatasourcePluginError'],
    'lodel.exceptions': ['LodelFatalError'],
    'lodel.plugin.hooks': ['LodelHook'],
    'lodel.plugin': ['Plugin', 'DatasourcePlugin'],
    'lodel.leapi.datahandlers.base_classes': ['DatasConstructor', 'Reference']})

## @brief Stores the name of the field present in each LeObject that indicates the name of LeObject subclass represented by this object
CLASS_ID_FIELDNAME = "classname"


## @brief Wrapper class for LeObject getter & setter
#
# This class intend to provide easy & friendly access to LeObject fields values without name collision problems
# @note Wrapped methods are : LeObject.data() & LeObject.set_data()
class LeObjectValues(object):

    # @param fieldnames_callback method
    # @param set_callback method : The LeObject.set_datas() method of corresponding LeObject class
    # @param get_callback method : The LeObject.get_datas() method of corresponding LeObject class
    def __init__(self, fieldnames_callback, set_callback, get_callback):
        self._setter = set_callback
        self._getter = get_callback

    ## @brief Provides read access to datas values
    # @note Read access should be provided for all fields
    # @param fname str : Field name
    # @return method
    def __getattribute__(self, fname):
        getter = super().__getattribute__('_getter')
        return getter(fname)

    ## @brief Provides write access to datas values
    # @note Write acces shouldn't be provided for internal or immutable fields
    # @param fname str : Field name
    # @param fval * : the field value
    # @return method
    def __setattribute__(self, fname, fval):
        setter = super().__getattribute__('_setter')
        return setter(fname, fval)


## @brief Represents a handled object in Lodel.
class LeObject(object):

    ## @brief boolean that tells if an object is abtract or not
    _abstract = None
    ## @brief A dict that stores DataHandler instances indexed by field name
    _fields = None
    ## @brief A tuple of fieldname (or a uniq fieldname) representing uid
    _uid = None
    ## @brief Read only datasource ( see @ref lodel2_datasources )
    _ro_datasource = None
    ## @brief Read & write datasource ( see @ref lodel2_datasources )
    _rw_datasource = None
    ## @brief Store the list of child classes
    _child_classes = None
    ## @brief Name of the datasource plugin
    _datasource_name = None

    def __new__(cls, **kwargs):
        self = object.__new__(cls)
        ## @brief A dict that stores fieldvalues indexed by fieldname
        self.__datas = {fname: None for fname in self._fields}
        ## @brief Store a list of initianilized fields when instanciation not complete else store True
        self.__initialized = list()
        ## @brief Datas accessor. Instance of @ref LeObjectValues
        self.d = LeObjectValues(self.fieldnames, self.set_data, self.data)
        for fieldname, fieldval in kwargs.items():
            self.__datas[fieldname] = fieldval
            self.__initialized.append(fieldname)
        self.__is_initialized = False
        self.__set_initialized()
        return self

    # @note Can be considered as EmClass instance
    # @param **kwargs
    # @throw NotImplementedError when the class being instanciated is noted as abstract and then should not be instanciated.
    # @throw LeApiError in case of missing or invalid data.
    def __init__(self, **kwargs):
        if self._abstract:
            raise NotImplementedError(
                "%s is abstract, you cannot instanciate it." % self.__class__.__name__)

        # Checks that uid is given
        for uid_name in self._uid:
            if uid_name not in kwargs:
                raise LeApiError("Cannot instanciate a LeObject without it's identifier")
            self.__datas[uid_name] = kwargs[uid_name]
            del(kwargs[uid_name])
            self.__initialized.append(uid_name)

        # Processing given fields
        allowed_fieldnames = self.fieldnames(include_ro=False)
        err_list = dict()
        for fieldname, fieldval in kwargs.items():
            if fieldname not in allowed_fieldnames:
                if fieldname in self._fields:
                    err_list[fieldname] = LeApiError(
                        "Value given but the field is internal")
                else:
                    err_list[fieldname] = LeApiError(
                        "Unknown fieldname : '%s'" % fieldname)
            else:
                self.__datas[fieldname] = fieldval
                self.__initialized.append(fieldname)
        if len(err_list) > 0:
            raise LeApiErrors(msg="Unable to __init__ %s" % self.__class__,
                              exceptions=err_list)
        self.__set_initialized()

    #-----------------------------------#
    #   Fields datas handling methods   #
    #-----------------------------------#

    ## @brief Property method True if LeObject is initialized else False
    # @return bool
    @property
    def initialized(self):
        return self.__is_initialized

    ## @brief Returns the uid field name
    # @return str
    @classmethod
    def uid_fieldname(cls):
        return cls._uid

    ## @brief Returns a list of fieldnames
    # @param include_ro bool : if True includes the read only field names
    # @return list of string
    @classmethod
    def fieldnames(cls, include_ro=False):
        if not include_ro:
            return [fname for fname in cls._fields if not cls._fields[fname].is_internal()]
        else:
            return list(cls._fields.keys())

    ## @brief Returns a name, capitalizing the first character of each word
    # @param name str
    # @return str
    @classmethod
    def name2objname(cls, name):
        return name.title()

    ## @brief Returns the datahandler asssociated with a LeObject field
    # @param fieldname str : The field's name
    # @return A data handler instance
    # @throw NameError when the given field name doesn't exist
    #@todo update class of exception raised
    @classmethod
    def data_handler(cls, fieldname):
        if not fieldname in cls._fields:
            raise NameError("No field named '%s' in %s" % (fieldname, cls.__name__))
        return cls._fields[fieldname]

    ## @brief Returns a dictionary containing the reference datahandlers
    # @param with_backref bool : if true return only references with back_references
    # @return dict : <code>{'fieldname': datahandler, ...}</code>
    @classmethod
    def reference_handlers(cls, with_backref=True):
        return {fname: fdh
                for fname, fdh in cls.fields(True).items()
                if fdh.is_reference() and
                (not with_backref or fdh.back_reference is not None)}

    ## @brief Returns a LeObject child class from a name
    # @warning This method has to be called from dynamically generated LeObjects
    # @param leobject_name str : LeObject name
    # @return A LeObject child class
    # @throw NotImplementedError if the method is abstract (if we use the LeObject class)
    # @throw LeApiError if an unexisting name is given
    @classmethod
    def name2class(cls, leobject_name):
        if cls.__module__ == 'lodel.leapi.leobject':
            raise NotImplementedError("Abstract method")
        mod = importlib.import_module(cls.__module__)
        try:
            return getattr(mod, leobject_name)
        except (AttributeError, TypeError):
            raise LeApiError("No LeObject named '%s'" % leobject_name)

    ## @brief Checks if the class is abstract or not
    # @return bool
    @classmethod
    def is_abstract(cls):
        return cls._abstract

    ## @brief Field data handler getter
    # @param fieldname str : The field name
    # @return A datahandler instance
    # @throw NameError if the field doesn't exist
    @classmethod
    def field(cls, fieldname):
        try:
            return cls._fields[fieldname]
        except KeyError:
            raise NameError("No field named '%s' in %s" % (fieldname,
                                                           cls.__name__))
    ## @brief Returns the fields' datahandlers as a dictionary
    # @param include_ro bool : if True, includes the read-only fields (default value : False)
    # @return dict
    @classmethod
    def fields(cls, include_ro=False):
        if include_ro:
            return copy.copy(cls._fields)
        else:
            return {fname: cls._fields[fname] for fname in cls._fields\
                    if not cls._fields[fname].is_internal()}

    ## @brief Return the list of parents classes
    #
    # @note the first item of the list is the current class, the second is its parent etc...
    # @warning multiple inheritance broken by this method
    # @return a list of LeObject child classes
    # @todo multiple parent capabilities implementation
    @classmethod
    def hierarch(cls):
        res = [cls]
        cur = cls
        while True:
            cur = cur.__bases__[0]  # Multiple inheritance broken HERE
            if cur in (LeObject, object):
                break
            else:
                res.append(cur)
        return res

    ## @brief Returns a tuple of child classes
    # @return tuple
    @classmethod
    def child_classes(cls):
        return copy.copy(cls._child_classes)

    ## @brief Returns the parent class that defines the unique id
    #
    # @return a LeObject child class or false if no UID defined
    @classmethod
    def uid_source(cls):
        if cls._uid is None or len(cls._uid) == 0:
            return False
        hierarch = cls.hierarch()
        prev = hierarch[0]
        uid_handlers = set(cls._fields[name] for name in cls._uid)
        for pcls in cls.hierarch()[1:]:
            puid_handlers = set(cls._fields[name] for name in pcls._uid)
            if set(pcls._uid) != set(prev._uid) \
                    or puid_handlers != uid_handlers:
                break
            prev = pcls
        return prev

    ## @brief Initialise both datasources (ro and rw)
    #
    # This method is used once at dyncode load to replace the datasource string
    # by a datasource instance to avoid doing this operation for each query
    # @see LeObject::_init_datasource()
    @classmethod
    def _init_datasources(cls):
        if isinstance(cls._datasource_name, str):
            rw_ds = ro_ds = cls._datasource_name
        else:
            ro_ds, rw_ds = cls._datasource_name
        # Read only datasource initialisation
        cls._ro_datasource = DatasourcePlugin.init_datasource(ro_ds, True)
        if cls._ro_datasource is None:
            log_msg = "No read only datasource set for LeObject %s"
            log_msg %= cls.__name__
            logger.debug(log_msg)
        else:
            log_msg = "Read only datasource '%s' initialized for LeObject %s"
            log_msg %= (ro_ds, cls.__name__)
            logger.debug(log_msg)
        # Read write datasource initialisation
        cls._rw_datasource = DatasourcePlugin.init_datasource(rw_ds, False)
        if cls._ro_datasource is None:
            log_msg = "No read/write datasource set for LeObject %s"
            log_msg %= cls.__name__
            logger.debug(log_msg)
        else:
            log_msg = "Read/write datasource '%s' initialized for LeObject %s"
            log_msg %= (ro_ds, cls.__name__)
            logger.debug(log_msg)

    ## @brief Returns the uid of the current LeObject instance
    # @return str
    # @warning Broke multiple uid capabilities
    def uid(self):
        return self.data(self._uid[0])

    ## @brief Returns the value of a field
    # @note for fancy data accessor use @ref LeObject.g attribute @ref LeObjectValues instance
    # @param field_name str : field's name
    # @return the value
    # @throw RuntimeError if the field is not initialized yet
    # @throw NameError if name is not an existing field name
    def data(self, field_name):
        if field_name not in self._fields.keys():
            raise NameError("No such field in %s : %s" % (self.__class__.__name__, field_name))
        if not self.initialized and field_name not in self.__initialized:
            raise RuntimeError(
                "The field %s is not initialized yet (and have no value)" % field_name)
        return self.__datas[field_name]

    ## @brief Returns a dictionary containing all the fields' values
    # @return dict
    def datas(self, internal=False):
        return {fname: self.data(fname) for fname in self.fieldnames(internal)}

    ## @brief Datas setter
    # @note for fancy data accessor use @ref LeObject.g attribute @ref LeObjectValues instance
    # @param fname str : field's name
    # @param fval * : field value
    # @return the value that is really set
    # @throw NameError if fname is not valid
    # @throw AttributeError if the field is not writtable
    # @throw LeApiErrors if the data check generates an error
    def set_data(self, fname, fval):
        if fname not in self.fieldnames(include_ro=False):
            if fname not in self._fields.keys():
                raise NameError("No such field in %s : %s" % (self.__class__.__name__, fname))
            else:
                raise AttributeError("The field %s is read only" % fname)
        self.__datas[fname] = fval
        if not self.initialized and fname not in self.__initialized:
            # Add field to initialized fields list
            self.__initialized.append(fname)
            self.__set_initialized()
        if self.initialized:
            # Running full value check
            ret = self.__check_modified_values()
            if ret is None:
                return self.__datas[fname]
            else:
                raise LeApiErrors("Data check error", ret)
        else:
            # Doing value check on modified field
            # We skip full validation here because the LeObject is not fully initialized yet
            val, err = self._fields[fname].check_data_value(fval)
            if isinstance(err, Exception):
                # Revert change to be in valid state
                del(self.__datas[fname])
                del(self.__initialized[-1])
                raise LeApiErrors("Data check error", {fname: err})
            else:
                self.__datas[fname] = val

    ## @brief Updates the __initialized attribute according to LeObject internal state
    #
    # Checks the list of initialized fields and sets __initialized at True if all fields initialized
    def __set_initialized(self):
        if isinstance(self.__initialized, list):
            expected_fields = self.fieldnames(include_ro=False) + self._uid
            if set(expected_fields) == set(self.__initialized):
                self.__is_initialized = True

    ## @brief Designed to be called when datas are modified
    #
    # Makes different checks on the LeObject given it's state (fully initialized or not)
    # @return None if checks succeded else return an exception list
    def __check_modified_values(self):
        err_list = dict()
        if self.__initialized is True:
            # Data value check
            for fname in self.fieldnames(include_ro=False):
                val, err = self._fields[fname].check_data_value(self.__datas[fname])
                if err is not None:
                    err_list[fname] = err
                else:
                    self.__datas[fname] = val
            # Data construction
            if len(err_list) == 0:
                for fname in self.fieldnames(include_ro=True):
                    try:
                        field = self._fields[fname]
                        self.__datas[fname] = field.construct_data(self,
                                                                   fname,
                                                                   self.__datas,
                                                                   self.__datas[fname]
                                                                   )
                    except Exception as exp:
                        err_list[fname] = exp
            # Datas consistency check
            if len(err_list) == 0:
                for fname in self.fieldnames(include_ro=True):
                    field = self._fields[fname]
                    ret = field.check_data_consistency(self, fname, self.__datas)
                    if isinstance(ret, Exception):
                        err_list[fname] = ret
        else:
            # Data value check for initialized datas
            for fname in self.__initialized:
                val, err = self._fields[fname].check_data_value(self.__datas[fname])
                if err is not None:
                    err_list[fname] = err
                else:
                    self.__datas[fname] = val
        return err_list if len(err_list) > 0 else None

    #--------------------#
    #   Other methods    #
    #--------------------#

    ## @brief Temporary method to set private fields attribute at dynamic code generation
    #
    # This method is used in the generated dynamic code to set the _fields attribute
    # at the end of the dyncode parse
    # @warning This method is deleted once the dynamic code loaded
    # @param cls
    # @param field_list list : list of EmField instance
    @classmethod
    def _set__fields(cls, field_list):
        cls._fields = field_list

    ## @brief Checks if the data is valid for this type
    # @param datas dict : key == field name value are field values
    # @param complete bool : if True expects that values are provided for all non internal fields
    # @param allow_internal bool : if True does not raise an error if a field is internal
    # @param cls
    # @return Checked datas
    # @throw LeApiDataCheckErrors if errors are reported during check
    @classmethod
    def check_datas_value(cls, datas, complete=False, allow_internal=True):
        err_l = dict()  # Error storing
        correct = set()  # valid fields name
        mandatory = set()  # mandatory fields name
        for fname, datahandler in cls._fields.items():
            if allow_internal or not datahandler.is_internal():
                correct.add(fname)
                if complete and not hasattr(datahandler, 'default'):
                    mandatory.add(fname)
        provided = set(datas.keys())
        # searching for unknow fields
        for u_f in provided - correct:
            # Here we can check if the field is invalid or rejected because
            # it is internel
            err_l[u_f] = AttributeError("Unknown or unauthorized field '%s'" % u_f)
        # searching for missing mandatory fieldsa
        for missing in mandatory - provided:
            err_l[missing] = AttributeError("The data for field '%s' is missing" % missing)
        # Checks datas
        checked_datas = dict()
        for name, value in [(name, value) for name, value in datas.items() if name in correct]:
            dh = cls._fields[name]
            res = dh.check_data_value(value)
            checked_datas[name], err = res
            if err:
                err_l[name] = err

        if len(err_l) > 0:
            raise LeApiDataCheckErrors("Error while checking datas", err_l)
        return checked_datas

    ## @brief Checks and prepares all the data
    #
    # @warning when complete = False we are not able to make construct_datas() and _check_data_consistency()
    #
    # @param datas dict : {fieldname : fieldvalue, ...}
    # @param complete bool : If True you MUST give all the datas (default value : False)
    # @param allow_internal : Wether or not interal fields are expected in datas (default value : True)
    # @return Datas ready for use
    # @todo: complete is very unsafe, find a way to get rid of it
    @classmethod
    def prepare_datas(cls, datas, complete=False, allow_internal=True):
        if not complete:
            warnings.warn("\nActual implementation can make broken datas \
construction and consitency when datas are not complete\n")
        ret_datas = cls.check_datas_value(datas, complete, allow_internal)
        if isinstance(ret_datas, Exception):
            raise ret_datas
        if complete:
            ret_datas = cls._construct_datas(ret_datas)
            cls._check_datas_consistency(ret_datas)
        return ret_datas

    ## @brief Constructs datas values
    #
    # @param datas dict : Datas that have been returned by LeCrud.check_datas_value() methods
    # @return A new dict of datas
    # @todo IMPLEMENTATION
    @classmethod
    def _construct_datas(cls, datas):
        constructor = DatasConstructor(cls, datas, cls._fields)
        ret = {
            fname: constructor[fname]
            for fname, ftype in cls._fields.items()
            if not ftype.is_internal() or ftype.internal != 'autosql'
        }
        return ret

    ## @brief Checks datas consistency
    # 
    # @warning assert that datas is complete
    # @param cls
    # @param datas dict : Datas that have been returned by LeCrud._construct_datas() method
    # @throw LeApiDataCheckError in case of failure
    @classmethod
    def _check_datas_consistency(cls, datas):
        err_l = []
        err_l = dict()
        for fname, dh in cls._fields.items():
            ret = dh.check_data_consistency(cls, fname, datas)
            if isinstance(ret, Exception):
                err_l[fname] = ret

        if len(err_l) > 0:
            raise LeApiDataCheckError("Datas consistency checks fails", err_l)

    ## @brief Checks data consistency
    # 
    # @warning assert that datas is complete
    # @param datas dict : Data that have been returned by prepare_datas() method
    # @param type_query str : Type of query to be performed , default value : insert
    @classmethod
    def make_consistency(cls, datas, type_query='insert'):
        for fname, dh in cls._fields.items():
            ret = dh.make_consistency(fname, datas, type_query)

    ## @brief Adds a new instance of LeObject
    # @param datas dict : LeObject's data
    # @return a new uid in case of success, False otherwise
    @classmethod
    def insert(cls, datas):
        query = LeInsertQuery(cls)
        return query.execute(datas)

    ## @brief Update an instance of LeObject
    #
    # @param datas : list of new datas
    # @return LeObject
    def update(self, datas=None):
        datas = self.datas(internal=False) if datas is None else datas
        uids = self._uid
        query_filter = list()
        for uid in uids:
            query_filter.append((uid, '=', self.data(uid)))
        try:
            query = LeUpdateQuery(self.__class__, query_filter)
        except Exception as err:
            raise err

        try:
            result = query.execute(datas)
        except Exception as err:
            raise err

        return result

    ## @brief Delete an instance of LeObject
    #
    # @return 1 if the objet has been deleted
    def delete(self):
        uids = self._uid
        query_filter = list()
        for uid in uids:
            query_filter.append((uid, '=', self.data(uid)))

        query = LeDeleteQuery(self.__class__, query_filter)

        result = query.execute()

        return result

    ## @brief Deletes instances of LeObject
    # @param query_filters list
    # @return the number of deleted items
    @classmethod
    def delete_bundle(cls, query_filters):
        deleted = 0
        try:
            query = LeDeleteQuery(cls, query_filters)
        except Exception as err:
            raise err

        try:
            result = query.execute()
        except Exception as err:
            raise err
        if not result is None:
            deleted += result
        return deleted

    ## @brief Gets instances of LeObject
    #
    # @param query_filters dict : (filters, relational filters), with filters is a list of tuples : (FIELD, OPERATOR, VALUE) )
    # @param field_list list|None : list of string representing fields see
    # @ref leobject_filters
    # @param order list : A list of field names or tuple (FIELDNAME,[ASC | DESC])
    # @param group list : A list of field names or tuple (FIELDNAME,[ASC | DESC])
    # @param limit int : The maximum number of returned results
    # @param offset int : offset (default value : 0)
    # @return a list of items (lists of (fieldname, fieldvalue))
    @classmethod
    def get(cls, query_filters, field_list=None, order=None, group=None, limit=None, offset=0):
        if field_list is not None:
            for uid in [uidname
                        for uidname in cls.uid_fieldname()
                        if uidname not in field_list]:
                field_list.append(uid)
            if CLASS_ID_FIELDNAME not in field_list:
                field_list.append(CLASS_ID_FIELDNAME)
        try:
            query = LeGetQuery(
                cls, query_filters=query_filters, field_list=field_list,
                order=order, group=group, limit=limit, offset=offset)
        except ValueError as err:
            raise err

        try:
            result = query.execute()
        except Exception as err:
            raise err

        objects = list()
        for res in result:
            res_cls = cls.name2class(res[CLASS_ID_FIELDNAME])
            inst = res_cls.__new__(res_cls, **res)
            objects.append(inst)

        return objects

    ## @brief Retrieves an object given an UID
    # @param uid str : Unique ID of the searched LeObject
    # @return LeObject
    # @throw LodelFatalError if the class does not have such a UID defined or if duplicates are found
    #@todo broken multiple UID
    @classmethod
    def get_from_uid(cls, uid):
        if cls.uid_fieldname() is None:
            raise LodelFatalError(
                "No uid defined for class %s" % cls.__name__)
        uidname = cls.uid_fieldname()[0]  # Brokes composed UID
        res = cls.get([(uidname, '=', uid)])

        # dedoublonnage vu que query ou la datasource est bugué
        if len(res) > 1:
            res_cp = res
            res = []
            while len(res_cp) > 0:
                cur_res = res_cp.pop()
                if cur_res.uid() in [r.uid() for r in res_cp]:
                    logger.error("Duplicates detected in query results !!!")
                else:
                    res.append(cur_res)
        if len(res) > 1:
            raise LodelFatalError("Get from uid returned more than one \
object ! For class %s with uid value = %s" % (cls, uid))
        elif len(res) == 0:
            return None
        return res[0]
