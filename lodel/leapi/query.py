#-*- coding: utf-8 -*-

from .leobject import LeObject


class LeQueryError(Exception):
    pass


## @brief Handle CRUD operations on datasource
class LeQuery(object):
    
    ## @brief Constructor
    # @param target_class LeObject class or childs : The LeObject child class concerned by this query
    def __init__(self, target_class):
        if not issubclass(target_class, LeObject):
            raise TypeError("target_class have to be a child class of LeObject")
        self._target_class = target_class


## @brief Handles insert queries
class LeInsertQuery(LeQuery):

    # Name of the corresponding action
    action = 'insert'

    def __init__(self, target_class):
        super().__init__(target_class)
        if target_class.is_abstract():
            raise LeQueryError("Target EmClass cannot be abstract for an InsertQuery")


## @brief Handles Le*Query with a query_filter argument
# @see LeGetQuery, LeUpdateQuery, LeDeleteQuery
class LeFilteredQuery(LeQuery):
    # Name of the corresponding action
    action = 'update'


## @brief Handles Get queries
class LeGetQuery(LeFilteredQuery):
    # Name of the corresponding action
    action = 'get'


## @brief Handles Update queries
class LeUpdateQuery(LeFilteredQuery):
    # Name of the corresponding action
    action = 'update'


## @brief Handles Delete queries
class LeDeleteQuery(LeFilteredQuery):
    # Name of the corresponding action
    action = 'delete'
