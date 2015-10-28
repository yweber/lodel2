#-*- coding: utf-8 -*-

import EditorialModel.fieldtypes.integer

## @todo This EmFieldType is a bit dirty....
class EmFieldType(EditorialModel.fieldtypes.integer.EmFieldType):
    
    help = 'Integer primary key fieldtype'

    def __init__(self, **kwargs):
        # Allowed argument => value for this EmFieldType
        allowed = {
            'default': None,
            'nullable': False,
            'uniq': False,
            'internal': 'automatic',
            'primary': True,
        }
        # Checking args
        for name, value in kwargs.items():
            if name not in allowed:
                raise TypeError("Got an unexpected argument '%s' for pk EmFieldType"%name)
            if value != allowed[name]:
                raise ValueError("The value '%s' for argument '%s' for pk EmFieldType is not allowed"%(value, name))


        super(EmFieldType, self).__init__(**kwargs)