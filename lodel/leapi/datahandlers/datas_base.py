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


#-*- coding: utf-8 -*-
import warnings
import datetime
import time
import os
from lodel.context import LodelContext


LodelContext.expose_modules(globals(), {
    'lodel.leapi.datahandlers.base_classes': ['DataField'],
    'lodel.exceptions': ['LodelException', 'LodelExceptions',
                         'LodelFatalError', 'DataNoneValid', 'FieldValidationError']})


##
## @brief Data field designed to handle boolean values
class Boolean(DataField):

    help = 'A basic boolean field'
    base_type = 'bool'

    ## @brief A boolean field
    def __init__(self, **kwargs):
        ##
        # @remarks Commented out code left in the code base. Consider deletion.
        #if 'check_data_value' not in kwargs:
        #    kwargs['check_data_value'] = self._check_data_value
        super().__init__(ftype='bool', **kwargs)

    ##
    # @brief Checks value.
    #
    # @param value mixed:
    # @throw FieldValidationError: if value is not valid
    # @return value
    def _check_data_value(self, value):
        value = super()._check_data_value(value)   
        if not isinstance(value, bool):
            raise FieldValidationError("The value '%s' is not, and will never, be a boolean" % value)
        return value


##
# @brief Data field designed to handle integer values.
class Integer(DataField):

    help = 'Basic integer field'
    base_type = 'int'
    cast_type = int

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    ##
    # @brief Checks and casts value in appropriate type
    #
    # @param value *:
    # @param strict bool: Whether the value type should be treated strictly or cast.
    # @throw FieldValidationError: if value is inappropriate or can not be cast
    # @return value
    def _check_data_value(self, value, strict=False):
        value = super()._check_data_value(value)
        if (strict and not isinstance(value, int)):
            raise FieldValidationError("The value '%s' is not a python type integer" % value)
        try:
            if strict:
                value = int(value)
            else:
                value = int(float(value))
        except(ValueError, TypeError):
            raise FieldValidationError("The value '%s' is not an integer nor could be cast to." % value)
        return value


##
# @brief Data field designed to handle string
class Varchar(DataField):

    help = 'Basic string (varchar) field. Default size is 64 characters'
    base_type = 'char'

    ##
    # @brief A string field
    #
    # @brief max_length int: The maximum length of this field
    def __init__(self, max_length=64, **kwargs):
        self.max_length = int(max_length)
        super().__init__(**kwargs)

    ##
    # @brief checks if this class can override the given data handler
    #
    # @param data_handler DataHandler
    # @return bool
    def can_override(self, data_handler):
        if not super().can_override(data_handler):
            return False
        if data_handler.max_length != self.max_length:
            return False
        return True
        
    ##
    # @brief Check and cast value in appropriate type
    #
    # @param value *:
    # @throw FieldValidationError if value is inappropriate or can not be cast
    # @return value
    def _check_data_value(self, value):
        value = super()._check_data_value(value)   
        if not isinstance(value, str):
            raise FieldValidationError("The value '%s' can't be a str" % value)
        if len(value) > self.max_length:
            raise FieldValidationError("The value '%s' is longer than the maximum length of this field (%s)" % (value, self.max_length))
        return value


##
# @brief Data field designed to handle date & time
class DateTime(DataField):

    help = 'A datetime field. Take two boolean options now_on_update and now_on_create'
    base_type = 'datetime'

    ##
    # @brief A datetime field
    #
    # @param now_on_update bool : If true, the date is set to NOW on update
    # @param now_on_create bool : If true, the date is set to NEW on creation
    # @param **kwargs
    #
    # @remarks Is it intended that DateTime objects can not be instantiated with
    #            a provided arbitrary string value or something else? 
    def __init__(self, now_on_update=False, now_on_create=False, **kwargs):
        self.now_on_update = now_on_update
        self.now_on_create = now_on_create
        self.datetime_format = '%Y-%m-%d' if 'format' not in kwargs else kwargs['format']
        super().__init__(**kwargs)

    ##
    # @brief Check and cast value in appropriate type
    #
    # @param value mixed:
    # @throw FieldValidationError: if value is inappropriate or can not be cast
    # @return value
    def _check_data_value(self, value):
        value = super()._check_data_value(value)
        if isinstance(value, str):
            try:
                value = datetime.datetime.fromtimestamp(time.mktime(time.strptime(value, self.datetime_format)))
            except ValueError:
                raise FieldValidationError("The value '%s' cannot be converted as a datetime" % value)
        if not isinstance(value, datetime.datetime):
            raise FieldValidationError("Tue value has to be a string or a datetime")
        return value

    def _construct_data(self, emcomponent, fname, datas, cur_value):
        if (self.now_on_create and cur_value is None) or self.now_on_update:
            return datetime.datetime.now()
        return cur_value


##
# @brief Data field designed to handle long string
class Text(DataField):

    help = 'A text field (big string)'
    base_type = 'text'

    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(ftype='text', **kwargs)
     
    ##
    # @brief Check and cast value in appropriate type
    #
    # @param value *
    # @throw FieldValidationError if value is unappropriate or can not be cast
    # @return value
    def _check_data_value(self, value):
        value = super()._check_data_value(value)   
        if not isinstance(value, str):
            raise FieldValidationError("The content passed to this Text field is not a convertible to a string")
        return value


##
# @brief Data field designed to handle Files
class File(DataField):

    base_type = 'file'

    ##
    # @brief a file field
    #
    # @param upload_path str : None by default
    # @param **kwargs
    def __init__(self, upload_path=None, **kwargs):
        self.upload_path = upload_path
        super().__init__(**kwargs)

    ##
    # @todo Add a check for the validity of the given value (should have a correct path syntax)
    def _check_data_value(self, value):
        return super()._check_data_value(value)   
