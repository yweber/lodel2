#-*- coding: utf-8 -*-

import sys
import os.path
import re
import socket
import inspect
import copy

from lodel.context import LodelContext
LodelContext.expose_modules(globals(), {
    'lodel.exceptions': ['LodelException', 'LodelExceptions',
        'LodelFatalError', 'FieldValidationError']})

## @package lodel.settings.validator Lodel2 settings validators/cast module
#
# Validator are registered in the Validator class.
# @note to get a list of registered default validators just run
# <pre>$ python scripts/settings_validator.py</pre>

##@brief Exception class that should be raised when a validation fails
class ValidationError(Exception):
    pass

##@brief Handles settings validators
#
# Class instance are callable objects that takes a value argument (the value to validate). It raises
# a ValidationError if validation fails, else it returns a properly
# casted value.
#@todo implement an IP validator and use it in multisite confspec
class Validator(object):
    
    _validators = dict()
    _description = dict()
    
    ##@brief Instanciate a validator
    #@param name str : validator name
    #@param none_is_valid bool : if True None will be validated
    #@param **kwargs : more arguement for the validator
    def __init__(self, name, none_is_valid = False, **kwargs):
        if name is not None and name not in self._validators:
            raise LodelFatalError("No validator named '%s'" % name)
        self.__none_is_valid = none_is_valid
        self.__name = name
        self._opt_args = kwargs

    ##@brief Call the validator
    # @param value *
    # @return properly casted value
    # @throw ValidationError
    def __call__(self, value):
        if self.__none_is_valid and value is None:
            return None
        try:
            ret = self._validators[self.__name](value, **self._opt_args)
            return ret
        except Exception as e:
            raise ValidationError(e)
    
    ##@brief Register a new validator
    # @param name str : validator name
    # @param callback callable : the function that will validate a value
    # @param description str
    @classmethod
    def register_validator(cls, name, callback, description=None):
        if name in cls._validators:
            raise NameError("A validator named '%s' allready exists" % name)
        # Broken test for callable
        if not inspect.isfunction(callback) and not inspect.ismethod(callback) and not hasattr(callback, '__call__'):
            raise TypeError("Callable expected but got %s" % type(callback))
        cls._validators[name] = callback
        cls._description[name] = description
    
    ##@brief Get the validator list associated with description
    @classmethod
    def validators_list(cls):
        return copy.copy(cls._description)

    ##@brief Create and register a list validator
    # @param elt_validator callable : The validator that will be used for validate each elt value
    # @param validator_name str
    # @param description None | str
    # @param separator str : The element separator
    # @return A Validator instance
    @classmethod
    def create_list_validator(cls, validator_name, elt_validator, description = None, separator = ','):
        def list_validator(value):
            res = list()
            errors = list()
            for elt in value.split(separator):
                elt = elt_validator(elt)
                if len(elt) > 0:
                    res.append(elt)
            return res
        description = "Convert value to an array" if description is None else description
        cls.register_validator(
                                validator_name,
                                list_validator,
                                description)
        return cls(validator_name)
 
    ##@brief Create and register a list validator which reads an array and returns a string
    # @param elt_validator callable : The validator that will be used for validate each elt value
    # @param validator_name str
    # @param description None | str
    # @param separator str : The element separator
    # @return A Validator instance
    @classmethod
    def create_write_list_validator(cls, validator_name, elt_validator, description = None, separator = ','):
        def write_list_validator(value):
            res = ''
            errors = list()
            for elt in value:
                res += elt_validator(elt) + ','
            return res[:len(res)-1]
        description = "Convert value to a string" if description is None else description
        cls.register_validator(
                                validator_name,
                                write_list_validator,
                                description)
        return cls(validator_name)
    
    ##@brief Create and register a regular expression validator
    # @param pattern str : regex pattern
    # @param validator_name str : The validator name
    # @param description str : Validator description
    # @return a Validator instance
    @classmethod
    def create_re_validator(cls, pattern, validator_name, description = None):
        def re_validator(value):
            if not re.match(pattern, value):
                raise ValidationError("The value '%s' doesn't match the following pattern '%s'" % pattern)
            return value
        #registering the validator
        cls.register_validator(
                                validator_name,
                                re_validator,
                                ("Match value to '%s'" % pattern) if description is None else description)
        return cls(validator_name)

    
    ## @return a list of registered validators
    @classmethod
    def validators_list_str(cls):
        result = ''
        for name in sorted(cls._validators.keys()):
            result += "\t%016s" % name
            if name in cls._description and cls._description[name] is not None:
                result += ": %s" % cls._description[name]
            result += "\n"
        return result

##@brief Integer value validator callback
def int_val(value):
    return int(value)

##@brief Output file validator callback
# @return A file object (if filename is '-' return sys.stderr)
def file_err_output(value):
    if not isinstance(value, str):
        raise ValidationError("A string was expected but got '%s' " % value)
    if value == '-':
        return None
    return value

##@brief Boolean value validator callback
def boolean_val(value):
    if isinstance(value, bool):
        return value
    if value.strip().lower() == 'true' or value.strip() == '1':
        value = True
    elif value.strip().lower() == 'false' or value.strip() == '0':
        value = False
    else:
        raise ValidationError("A boolean was expected but got '%s' " % value)
    return bool(value)

##@brief Validate a directory path
def directory_val(value):
    res = Validator('strip')(value)
    if not os.path.isdir(res):
        raise ValidationError("Folowing path don't exists or is not a directory : '%s'"%res)
    return res

##@brief Validate a loglevel value
def loglevel_val(value):
    valids = ['DEBUG', 'INFO', 'WARNING', 'SECURITY', 'ERROR', 'CRITICAL']
    if value.upper() not in valids:
        raise ValidationError(
                "The value '%s' is not a valid loglevel" % value)
    return value.upper()

##@brief Validate a path
def path_val(value):
    if value is None or not os.path.exists(value):
        raise ValidationError(
                "path '%s' doesn't exists" % value)
    return value

##@brief Validate None
def none_val(value):
    if value is None:
        return None
    raise ValidationError("This settings cannot be set in configuration file")

##@brief Validate a string
def str_val(value):
    try:
        return str(value)
    except Exception as e:
        raise ValidationError("Not able to convert value to string : " + str(e))

##@brief Validate using a regex
def regex_val(value, pattern):
    if re.match(pattern, value) is None:
        raise ValidationError("The value '%s' is not validated by : \
r\"%s\"" %(value, pattern))
    return value

##@brief Validate a hostname (ipv4 or ipv6)
def host_val(value):
    if value == 'localhost':
        return value
    ok = False
    try:
        socket.inet_aton(value)
        return value
    except (TypeError,OSError):
        pass
    try:
        socket.inet_pton(socket.AF_INET6, value)
        return value
    except (TypeError,OSError):
        pass
    try:
        socket.getaddrinfo(value, 80)
        return value
    except (TypeError,socket.gaierror):
        msg = "The value '%s' is not a valid host"
        raise ValidationError(msg % value)

def custom_list_validator(value, validator_name, validator_kwargs = None):
    validator_kwargs = dict() if validator_kwargs is None else validator_kwargs
    validator = Validator(validator_name, **validator_kwargs)
    for item in value.split():
        validator(item)
    return value.split()

#
#   Default validators registration
#

Validator.register_validator(
    'custom_list',
    custom_list_validator,
    'A list validator that takes a "validator_name" as argument')

Validator.register_validator(
    'dummy',
    lambda value:value,
    'Validate anything')

Validator.register_validator(
    'none',
    none_val,
    'Validate None')

Validator.register_validator(
    'string',
    str_val,
    'Validate string values')

Validator.register_validator(
    'strip',
    str.strip,
    'String trim')

Validator.register_validator(
    'int',
    int_val,
    'Integer value validator')

Validator.register_validator(
    'bool',
    boolean_val,
    'Boolean value validator')

Validator.register_validator(
    'errfile',
    file_err_output,
    'Error output file validator (return stderr if filename is "-")')

Validator.register_validator(
    'directory',
    directory_val,
    'Directory path validator')

Validator.register_validator(
    'loglevel',
    loglevel_val,
    'Loglevel validator')

Validator.register_validator(
    'path',
    path_val,
    'path validator')

Validator.register_validator(
    'host',
    host_val,
    'host validator')

Validator.register_validator(
    'regex',
    regex_val,
    'RegEx name validator (take re as argument)')

Validator.create_list_validator(
    'list',
    Validator('strip'),
    description = "Simple list validator. Validate a list of values separated by ','",
    separator = ',')

Validator.create_list_validator(
    'directory_list',
    Validator('directory'),
    description = "Validator for a list of directory path separated with ','",
    separator = ',')

Validator.create_write_list_validator(
    'write_list',
    Validator('directory'),
    description = "Validator for an array of values which will be set in a string, separated by ','",
    separator = ',')

Validator.create_re_validator(
    r'^https?://[^\./]+.[^\./]+/?.*$',
    'http_url',
    'Url validator')
