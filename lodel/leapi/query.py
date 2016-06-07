#-*- coding: utf-8 -*-

import re
from .leobject import LeObject, LeApiErrors, LeApiDataCheckError
from lodel.plugin.hooks import LodelHook
from lodel import logger

class LeQueryError(Exception):
    ##@brief Instanciate a new exceptions handling multiple exceptions
    #@param msg str : Exception message
    #@param exceptions dict : A list of data check Exception with concerned
    # field (or stuff) as key
    def __init__(self, msg = "Unknow error", exceptions = None):
        self._msg = msg
        self._exceptions = dict() if exceptions is None else exceptions

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        msg = self._msg
        if isinstance(self._exceptions, dict):
            for_iter = self._exceptions.items()
        else:
            for_iter = enumerate(self.__exceptions)
        for obj, expt in for_iter:
            msg += "\n\t{expt_obj} : ({expt_name}) {expt_msg}; ".format(
                    expt_obj = obj,
                    expt_name=expt.__class__.__name__,
                    expt_msg=str(expt)
            )
        return msg

class LeQuery(object):
    
    ##@brief Hookname prefix
    _hook_prefix = None
    ##@brief arguments for the LeObject.check_data_value()
    _data_check_args = { 'complete': False, 'allow_internal': False }

    ##@brief Abstract constructor
    # @param target_class LeObject : class of object the query is about
    def __init__(self, target_class):
        if self._hook_prefix is None:
            raise NotImplementedError("Abstract class")
        if not issubclass(target_class, LeObject):
            raise TypeError("target class has to be a child class of LeObject")
        self._target_class = target_class
        self._datasource = target_class._datasource
    
    ##@brief Execute a query and return the result
    # @param **datas
    # @return the query result
    # @see LeQuery.__query()
    #
    def execute(self, datas = None):
        if len(datas) > 0:
            self._target_class.check_datas_value(
                                                    datas,
                                                    **self._data_check_args)
            self._target_class.prepare_datas() #not yet implemented
        if self._hook_prefix is None:
            raise NotImplementedError("Abstract method")
        LodelHook.call_hook(    self._hook_prefix+'_pre',
                                self._target_class,
                                datas)
        ret = self.__query(self._target_class._datasource, **datas)
        ret = LodelHook.call_hook(  self._hook_prefix+'_post',
                                    self._target_class,
                                    ret)
        return ret
    
    ##@brief Childs classes implements this method to execute the query
    # @param **datas
    # @return query result
    def __query(self, **datas):
        raise NotImplementedError("Asbtract method")
    
    ##@return a dict with query infos
    def dump_infos(self):
        return {'target_class': self._target_class}

    def __repr__(self):
        ret = "<{classname} target={target_class}>"
        return ret.format(
                            classname=self.__class__.__name__,
                            target_class = self._target_class)
        

##@brief Abstract class handling query with filters
#
#@todo add handling of inter-datasource queries
#
#@warning relationnal filters on multiple classes from different datasource
# will generate a lot of subqueries
class LeFilteredQuery(LeQuery):
    
    ##@brief The available operators used in query definitions
    _query_operators = [
                        ' = ',
                        ' <= ',
                        ' >= ',
                        ' != ',
                        ' < ',
                        ' > ',
                        ' in ',
                        ' not in ',
                        ' like ',
                        ' not like ']
    
    ##@brief Regular expression to process filters
    _query_re = None

    ##@brief Abtract constructor for queries with filter
    #@param target_class LeObject : class of object the query is about
    #@param query_filters list : with a tuple (only one filter) or a list of 
    # tuple or a dict: {OP,list(filters)} with OP = 'OR' or 'AND for tuple
    # (FIELD,OPERATOR,VALUE)
    def __init__(self, target_class, query_filters = None):
        super().__init__(target_class)
        ##@brief The query filter tuple(std_filter, relational_filters)
        self.__query_filter = None
        ##@brief Stores potential subqueries (used when a query implies
        # more than one datasource.
        #
        # Subqueries are tuple(target_class_ref_field, LeGetQuery)
        self.subqueries = None
        self.set_query_filter(query_filters)
    
    ##@brief Abstract FilteredQuery execution method
    #
    # This method takes care to execute subqueries before calling super execute
    def execute(self, datas = None):
        #copy originals filters
        orig_filters = copy.copy(self.__query_filter)
        std_filters, rel_filters = self.__query_filter

        for rfield, subq in self.subqueries:
            subq_res = subq.execute()
            std_filters.append(
                (rfield, ' in ', subq_res))
        self.__query_filter = (std_filters, rel_filters)
        try:
            res = super().execute()
        except Exception as e:
            #restoring filters even if an exception is raised
            self.__query_filter = orig_filter
            raise e #reraise
        #restoring filters
        self.__query_filter = orig_filters
        return res

    ##@brief Add filter(s) to the query
    #
    # This method is also able to slice query if different datasources are
    # implied in the request
    #
    #@param query_filter list|tuple|str : A single filter or a list of filters
    #@see LeFilteredQuery._prepare_filters()
    def set_query_filter(self, query_filter):
        if isinstance(query_filter, str):
            query_filter = [query_filter]
        #Query filter prepration
        filters_orig , rel_filters = self._prepare_filters(query_filter)
        # Here we now that each relational filter concern only one datasource
        # thank's to _prepare_relational_fields

        #Multiple datasources detection
        self_ds_name = self._target_class._datasource_name
        result_rel_filters = list() # The filters that will stay in the query
        other_ds_filters = dict()
        for rfilter in rel_filters:
            (rfield, ref_dict), op, value = rfilter
            #rfield : the field in self._target_class
            tmp_rel_filter = dict() #designed to stores rel_field of same DS
            # First step : simplification
            # Trying to delete relational filters done on referenced class uid
            for tclass, tfield in ref_dict.items():
                #tclass : reference target class
                #tfield : referenced field from target class
                if tfield == tclass.uid_fieldname:
                    #This relational filter can be simplified as 
                    # ref_field, op, value
                    # Note : we will have to dedup filters_orig
                    filters_orig.append((rfield, op, value))
                    del(ref_dict[tclass])
            #Determine what to do with other relational filters given 
            # referenced class datasource
            #Remember : each class in a relational filter has the same 
            # datasource
            tclass = list(ref_dict.keys())[0]
            cur_ds = tclass._datasource_name
            if cur_ds == self_ds_name:
                # Same datasource, the filter stay is self query
                result_rel_filters.append(((rfield, ref_dict), op, value))
            else:
                # Different datasource, we will have to create a subquery
                if cur_ds not in other_ds_filters:
                    other_ds_filters[cur_ds] = list()
                other_ds_filters[cur_ds].append(
                    ((rfield, ref_dict), op, value))
        #deduplication of std filters
        filters_orig = list(set(filters_orig))
        # Sets __query_filter attribute of self query
        self.__query_filter = (filters_orig, result_rel_filters)

        #Sub queries creation
        subq = list()
        for ds, rfilters in other_ds_filters.items():
            for rfilter in rfilters:
                (rfield, ref_dict), op, value = rfilter
                for tclass, tfield in ref_dict.items():
                    query = LeGetQuery(
                        target_class = tclass,
                        query_filter = [(tfield, op, value)],
                        field_list = [tfield])
                    subq.append((rfield, query))
        self.subqueries = subq
    
    ##@return informations
    def dump_infos(self):
        ret = super().dump_infos()
        ret['query_filter'] = self.__query_filter
        ret['subqueries'] = self.subqueries
        return ret

    def __repr__(self):
        res = "<{classname} target={target_class} query_filter={query_filter}"
        res = ret.format(
            classname=self.__class__.__name__,
            query_filter = self.__query_filter,
            target_class = self._target_class)
        if len(self.subqueries) > 0:
            for n,subq in enumerate(self.subqueries):
                res += "\n\tSubquerie %d : %s"
                res %= (n, subq)
        res += '>'
        return res

    ## @brief Prepare filters for datasource
    # 
    #A filter can be a string or a tuple with len = 3.
    #
    #This method divide filters in two categories :
    #
    #@par Simple filters
    #
    #Those filters concerns fields that represent object values (a title,
    #the content, etc.) They are composed of three elements : FIELDNAME OP
    # VALUE . Where :
    #- FIELDNAME is the name of the field
    #- OP is one of the authorized comparison operands ( see 
    #@ref LeFilteredQuery.query_operators )
    #- VALUE is... a value
    #
    #@par Relational filters
    #
    #Those filters concerns on reference fields ( see the corresponding
    #abstract datahandler @ref lodel.leapi.datahandlers.base_classes.Reference)
    #The filter as quite the same composition than simple filters :
    # FIELDNAME[.REF_FIELD] OP VALUE . Where :
    #- FIELDNAME is the name of the reference field
    #- REF_FIELD is an optionnal addon to the base field. It indicate on wich
    #field of the referenced object the comparison as to be done. If no
    #REF_FIELD is indicated the comparison will be done on identifier.
    #
    #@param cls
    #@param filters_l list : This list of str or tuple (or both)
    #@return a tuple(FILTERS, RELATIONNAL_FILTERS
    #@todo move this doc in another place (a dedicated page ?)
    def _prepare_filters(self, filters_l):
        filters = list()
        res_filters = list()
        rel_filters = list()
        err_l = dict()
        #Splitting in tuple if necessary
        for i,fil in enumerate(filters_l):
            if len(fil) == 3 and not isinstance(fil, str):
                filters.append(tuple(fil))
            else:
                try:
                    filters.append(self.split_filter(fil))
                except ValueError as e:
                    err_l["filter %d" % i] = e

        for field, operator, value in filters:
            err_key = "%s %s %s" % (field, operator, value) #to push in err_l
            # Spliting field name to be able to detect a relational field
            field_spl = field.split('.')
            if len(field_spl) == 2:
                field, ref_field = field_spl
            elif len(field_spl) == 1:
                ref_field = None
            else:
                err_l[field] = NameError(   "'%s' is not a valid relational \
field name" % fieldname)
                continue   
            # Checking field against target_class
            ret = self._check_field(self._target_class, field)
            if isinstance(ret, Exception):
                err_l[field] = ret
                continue
            field_datahandler = self._target_class.field(field)
            if ref_field is not None and not field_datahandler.is_reference():
                # inconsistency
                err_l[field] = NameError(   "The field '%s' in %s is not \
a relational field, but %s.%s was present in the filter"
                                            % ( field,
                                                self._target_class.__name__,
                                                field,
                                                ref_field))
            if field_datahandler.is_reference():
                #Relationnal field
                if ref_field is None:
                    # ref_field default value
                    ref_uid = set(
                        [lc._uid for lc in field_datahandler.linked_classes])
                    if len(ref_uid) == 1:
                        ref_field = ref_uid[0]
                    else:
                        if len(ref_uid) > 1:
                            msg = "The referenced classes are identified by \
fields with different name. Unable to determine wich field to use for the \
reference"
                        else:
                            msg = "Unknow error when trying to determine wich \
field to use for the relational filter"
                        err_l[err_key] = RuntimeError(msg)
                        continue
                # Prepare relational field
                ret = self._prepare_relational_fields(field, ref_field)
                if isinstance(ret, Exception):
                    err_l[err_key] = ret
                    continue
                else:
                    rel_filters.append((ret, operator, value))
            else:
                res_filters.append((field,operator, value))
        
        if len(err_l) > 0:
            raise LeApiDataCheckError(
                                        "Error while preparing filters : ",
                                        err_l)
        return (res_filters, rel_filters)

    ## @brief Check and split a query filter
    # @note The query_filter format is "FIELD OPERATOR VALUE"
    # @param query_filter str : A query_filter string
    # @param cls
    # @return a tuple (FIELD, OPERATOR, VALUE)
    @classmethod
    def split_filter(cls, query_filter):
        if cls._query_re is None:
            cls.__compile_query_re()
        matches = cls._query_re.match(query_filter)
        if not matches:
            msg = "The query_filter '%s' seems to be invalid"
            raise ValueError(msg % query_filter)
        result = (
            matches.group('field'),
            re.sub(r'\s', ' ', matches.group('operator'), count=0),
            matches.group('value').strip())

        result = [r.strip() for r in result]
        for r in result:
            if len(r) == 0:
                msg = "The query_filter '%s' seems to be invalid"
                raise ValueError(msg % query_filter)
        return result

    ## @brief Compile the regex for query_filter processing
    # @note Set _LeObject._query_re
    @classmethod
    def __compile_query_re(cls):
        op_re_piece = '(?P<operator>(%s)'
        op_re_piece %= cls._query_operators[0].replace(' ', '\s')
        for operator in cls._query_operators[1:]:
            op_re_piece += '|(%s)'%operator.replace(' ', '\s')
        op_re_piece += ')'

        re_full = '^\s*(?P<field>([a-z_][a-z0-9\-_]*\.)?[a-z_][a-z0-9\-_]*)\s*'
        re_full += op_re_piece+'\s*(?P<value>.*)\s*$'

        cls._query_re = re.compile(re_full, flags=re.IGNORECASE)
        pass

    @classmethod
    def _check_field(cls, target_class, fieldname):
        try:
            target_class.field(fieldname)
        except NameError as e:
            msg = "No field named '%s' in %s'"
            msg %= (fieldname, target_class.__name__)
            return NameError(msg)

    ##@brief Prepare a relational filter
    #
    #Relational filters are composed of a tuple like the simple filters
    #but the first element of this tuple is a tuple to :
    #
    #<code>( (FIELDNAME, {REF_CLASS: REF_FIELD}), OP, VALUE)</code>
    # Where :
    #- FIELDNAME is the field name is the target class
    #- the second element is a dict with :
    # - REF_CLASS as key. It's a LeObject child class
    # - REF_FIELD as value. The name of the referenced field in the REF_CLASS
    #
    #Visibly the REF_FIELD value of the dict will vary only when
    #no REF_FIELD is explicitly given in the filter string notation
    #and REF_CLASSES has differents uid
    #
    #@par String notation examples
    #<pre>contributeur IN (1,2,3,5)</pre> will be transformed into :
    #<pre>(
    #       (
    #           contributeur, 
    #           {
    #               auteur: 'lodel_id',
    #               traducteur: 'lodel_id'
    #           } 
    #       ),
    #       ' IN ',
    #       [ 1,2,3,5 ])</pre>
    #@todo move the documentation to another place
    #
    #@param fieldname str : The relational field name
    #@param ref_field str|None : The referenced field name (if None use
    #uniq identifiers as referenced field
    #@return a well formed relational filter tuple or an Exception instance
    def _prepare_relational_fields(self, fieldname, ref_field = None):
        datahandler = self._target_class.field(fieldname)
        # now we are going to fetch the referenced class to see if the
        # reference field is valid
        ref_classes = datahandler.linked_classes
        ref_dict = dict()
        if ref_field is None:
            for ref_class in ref_classes:
                ref_dict[ref_class] = ref_class.uid_fieldname
        else:
            r_ds = None
            for ref_class in ref_classes:
                if r_ds is None:
                    r_ds = ref_class._datasource_name
                elif ref_class._datasource_name != r_ds:
                    return RuntimeError("All referenced class doesn't have the same datasource. Query not possible")
                if ref_field in ref_class.fieldnames(True):
                    ref_dict[ref_class] = ref_field
                else:
                    msg = "Warning the class %s is not considered in \
the relational filter %s"
                    msg %= (ref_class.__name__, ref_field)
                    logger.debug(msg)
        if len(ref_dict) == 0:
            return NameError(   "No field named '%s' in referenced objects %s"
                                % (ref_field, ref_class.__name__))
        return (fieldname, ref_dict)
 

##@brief A query to insert a new object
class LeInsertQuery(LeQuery):
    
    _hook_prefix = 'leapi_insert_'
    _data_check_args = { 'complete': True, 'allow_internal': False }

    def __init__(self, target_class):
        super().__init__(target_class)
    
    ## @brief Implements an insert query operation, with only one insertion
    # @param **datas : datas to be inserted
    def __query(self, **datas):
        nb_inserted = self._datasource.insert(self._target_class,**datas)
        if nb_inserted < 0:
            raise LeQueryError("Insertion error")
        return nb_inserted
    """
    ## @brief Implements an insert query operation, with multiple insertions
    # @param datas : list of **datas to be inserted
    def __query(self, datas):
        nb_inserted = self._datasource.insert_multi(
            self._target_class,datas_list)
        if nb_inserted < 0:
            raise LeQueryError("Multiple insertions error")
        return nb_inserted
    """

    ## @brief Execute the insert query
    def execute(self, **datas):
        return super().execute(**datas)
        
##@brief A query to update datas for a given object
class LeUpdateQuery(LeFilteredQuery):
    
    _hook_prefix = 'leapi_update_'
    _data_check_args = { 'complete': True, 'allow_internal': False }

    def __init__(self, target_class, query_filter):
        super().__init__(target_class, query_filter)
    
    ##@brief Implements an update query
    # @param **datas : datas to update
    # @returns the number of updated items
    # @exception when the number of updated items is not as expected
    def __query(self, **datas):
        # select _uid corresponding to query_filter
        l_uids=self._datasource.select( self._target_class,
                                        list(self._target_class.getuid()),
                                        query_filter,
                                        None,
                                        None,
                                        None,
                                        None,
                                        0,
                                        False)
        # list of dict l_uids : _uid(s) of the objects to be updated,
        # corresponding datas
        nb_updated = self._datasource.update(   self._target_class,
                                                l_uids,
                                                **datas)
        if nb_updated != len(l_uids):
            msg = "Number of updated items: %d is not as expected: %d "
            msg %= (nb_updated, len(l_uids))
            raise LeQueryError(msg)
        return nb_updated
    
    ## @brief Execute the update query
    def execute(self, **datas):
        return super().execute(**datas)

##@brief A query to delete an object
class LeDeleteQuery(LeFilteredQuery):
    
    _hook_prefix = 'leapi_delete_'

    def __init__(self, target_class, query_filter):
        super().__init__(target_class, query_filter)

    ## @brief Execute the delete query
    def execute(self):
        return super().execute()
    
    ##@brief Implements delete query operations
    # @returns the number of deleted items
    # @exception when the number of deleted items is not as expected
    def __query(self):
        # select _uid corresponding to query_filter
        l_uids = self._datasource.select(   self._target_class,
                                            list(self._target_class.getuid()),
                                            query_filter,
                                            None,
                                            None,
                                            None,
                                            None,
                                            0,
                                            False)
        # list of dict l_uids : _uid(s) of the objects to be deleted
        nb_deleted = datasource.update(self._target_class,l_uids, **datas)
        if nb_deleted != len(l_uids):
            msg = "Number of deleted items %d is not as expected %d "
            msg %= (nb_deleted, len(l_uids))
            raise LeQueryError(msg)
        return nb_deleted

class LeGetQuery(LeFilteredQuery):
    
    _hook_prefix = 'leapi_get_'

    ##@brief Instanciate a new get query
    #@param target_class LeObject : class of object the query is about
    #@param query_filters dict : {OP, list of query filters }
    # or tuple (FIELD, OPERATOR, VALUE) )
    #@param field_list list|None : list of string representing fields see 
    # @ref leobject_filters
    #@param order list : A list of field names or tuple (FIELDNAME,[ASC | DESC])
    #@param group list : A list of field names or tuple (FIELDNAME,[ASC | DESC])
    #@param limit int : The maximum number of returned results
    #@param offset int : offset
    def __init__(self, target_class, query_filter, **kwargs):
        super().__init__(target_class, query_filter)
        
        ##@brief The fields to get
        self.__field_list = None
        ##@brief An equivalent to the SQL ORDER BY
        self.__order = None
        ##@brief An equivalent to the SQL GROUP BY
        self.__group = None
        ##@brief An equivalent to the SQL LIMIT x
        self.__limit = None
        ##@brief An equivalent to the SQL LIMIT x, OFFSET
        self.__offset = 0
        
        # Checking kwargs and assigning default values if there is some
        for argname in kwargs:
            if argname not in (
                'field_list', 'order', 'group', 'limit', 'offset'):
                raise TypeError("Unexpected argument '%s'" % argname)

        if 'field_list' not in kwargs:
            self.set_field_list(target_class.fieldnames(include_ro = True))
        else:
            self.set_field_list(kwargs['field_list'])

        if 'order' in kwargs:
            #check kwargs['order']
            self.__order = kwargs['order']
        if 'group' in kwargs:
            #check kwargs['group']
            self.__group = kwargs['group']
        if 'limit' in kwargs:
            try:
                self.__limit = int(kwargs[limit])
                if self.__limit <= 0:
                    raise ValueError()
            except ValueError:
                msg = "limit argument expected to be an interger > 0"
                raise ValueError(msg)
        if 'offset' in kwargs:
            try:
                self.__offset = int(kwargs['offset'])
                if self.__offset < 0:
                    raise ValueError()
            except ValueError:
                msg = "offset argument expected to be an integer >= 0"
                raise ValueError(msg)
    
    ##@brief Set the field list
    # @param field_list list | None : If None use all fields
    # @return None
    # @throw LeQueryError if unknown field given
    def set_field_list(self, field_list):
        err_l = dict()
        for fieldname in field_list:
            ret = self._check_field(self._target_class, fieldname)
            if isinstance(ret, Exception):
                msg = "No field named '%s' in %s"
                msg %= (fieldname, self._target_class.__name__)
                expt = NameError(msg)
                err_l[fieldname] =  expt
        if len(err_l) > 0:
            msg = "Error while setting field_list in a get query"
            raise LeQueryError(msg = msg, exceptions = err_l)
        self.__field_list = list(set(field_list))
    
    ##@brief Execute the get query
    def execute(self):
        return super().execute()

    ##@brief Implements select query operations
    # @returns a list containing the item(s)
    def __query(self, datasource):
        # select datas corresponding to query_filter
        l_datas=datasource.select(  self._target_class,
                                    list(self.field_list),
                                    self.query_filter,
                                    None,
                                    self.__order,
                                    self.__group,
                                    self.__limit,
                                    self.offset,
                                    False)
        return l_datas
    
    ##@return a dict with query infos
    def dump_infos(self):
        ret = super().dump_infos()
        ret.update( {   'field_list' : self.__field_list,
                        'order' : self.__order,
                        'group' : self.__group,
                        'limit' : self.__limit,
                        'offset': self.__offset,
        })
        return ret

    def __repr__(self):
        res = "<LeGetQuery target={target_class} filter={query_filter} \
field_list={field_list} order={order} group={group} limit={limit} \
offset={offset}"
        res = res.format(**self.dump_infos())
        if len(self.subqueries) > 0:
            for n,subq in enumerate(self.subqueries):
                res += "\n\tSubquerie %d : %s"
                res %= (n, subq)
        res += ">"
        return res


