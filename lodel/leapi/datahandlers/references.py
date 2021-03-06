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


from lodel.context import LodelContext
LodelContext.expose_modules(globals(), {
    'lodel.leapi.datahandlers.base_classes': ['Reference', 'MultipleRef',
                                              'SingleRef'],
    'lodel.logger': 'logger',
    'lodel.exceptions': ['LodelException', 'LodelExceptions',
                         'LodelFatalError', 'DataNoneValid',
                         'FieldValidationError']})

## @brief Child class of SingleRef. The object referenced must exist
class Link(SingleRef):
    pass


## @brief Child class of MultipleRef where references are represented in the form of a python list
# All the objects referenced must exist
class List(MultipleRef):

    ## @brief instanciates a list reference
    # @param max_length int
    # @param kwargs
    #   - allowed_classes list | None : list of allowed em classes if None no restriction
    #   - internal bool

    def __init__(self, max_length=None, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def empty(cls):
        return list()

    ## @brief Check and cast value in appropriate type
    # @param value *
    # @throw FieldValidationError if value is unappropriate or can not be cast
    # @return value
    def _check_data_value(self, value):
        value = super()._check_data_value(value)
        try:
            return list(value)
        except Exception as e:
            raise FieldValidationError("Given iterable is not castable in \
a list : %s" % e)


## @brief Child class of MultipleRef where references are represented in the form of a python set
class Set(MultipleRef):

    ## @brief instanciates a set reference
    # @param kwargs : named arguments
    #   - allowed_classes list | None : list of allowed em classes if None no restriction
    #   - internal bool : if False, the field is not internal
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def empty(cls):
        return set()

    ## @brief Check and cast value in appropriate type
    # @param value *
    # @throw FieldValidationError if value is unappropriate or can not be cast
    # @return value
    def _check_data_value(self, value):
        value = super()._check_data_value(value)
        try:
            return set(value)
        except Exception as e:
            raise FieldValidationError("Given iterable is not castable in \
a set : %s" % e)


## @brief Child class of MultipleRef where references are represented in the form of a python dict
class Map(MultipleRef):

    ## @brief instanciates a dict reference
    # @param kwargs : named arguments
    #   - allowed_classes list | None : list of allowed em classes if None no restriction
    #   - internal bool : if False, the field is not internal
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def empty(cls):
        return dict()

    ## @brief Check and cast value in appropriate type
    # @param value *
    # @throw FieldValidationError if value is unappropriate or can not be cast
    # @return value
    def _check_data_value(self, value):
        value = super()._check_data_value(value)
        if not isinstance(value, dict):
            raise FieldValidationError("Values for dict fields should be dict")
        return value


## @brief This Reference class is designed to handler hierarchy with some constraint
class Hierarch(MultipleRef):

    directly_editable = False

    ## @brief Instanciate a data handler handling hierarchical relation with constraints
    # @param back_reference tuple : Here it is mandatory to have a back ref (like a parent field)
    # @param max_depth int | None :  limit of depth
    # @param max_childs int | Nine : maximum number of childs by nodes
    # @param kwargs : 
    #   - allowed_classes list | None : list of allowed em classes if None no restriction
    #   - internal bool : if False, the field is not internal
    def __init__(self, back_reference, max_depth=None, max_childs=None, **kwargs):
        super().__init__(back_reference=back_reference,
                         max_depth=max_depth,
                         max_childs=max_childs,
                         **kwargs)

    @classmethod
    def empty(cls):
        return tuple()

    ## @brief Check and cast value in appropriate type
    # @param value *
    # @throw FieldValidationError if value is unappropriate or can not be cast
    # @return value
    def _check_data_value(self, value):
        value = super()._check_data_value(value)
        if  not (isinstance(value, list) or isinstance(value, str)):
            raise FieldValidationError(
                "List or string expected for a set field")
        return value
