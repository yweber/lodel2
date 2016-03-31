# -*- coding: utf-8 -*-
from ..data_field import DataField


class DataHandler(DataField):

    help = 'A basic boolean field'
    base_type = 'bool'

    ## @brief A boolean field
    def __init__(self, **kwargs):
        if 'check_data_value' not in kwargs:
            kwargs['check_data_value'] = self.check_value
        super().__init__(ftype='bool', **kwargs)

    def _check_data_value(self, value):
        error = None
        try:
            value = bool(value)
        except(ValueError, TypeError):
            error = TypeError("The value '%s' is not, and will never, be a boolean" % value)
        return (value, error)

    def can_override(self, data_handler):

        if data_handler.__class__.base_type != self.__class__.base_type:
            return False

        return True