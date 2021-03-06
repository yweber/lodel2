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


import unittest
from unittest import mock 
from unittest.mock import patch

import leapi_dyncode as dyncode

from lodel.leapi.datahandlers.datas import UniqID as Testee
from lodel.plugins.dummy_datasource.datasource import DummyDatasource


class UniqIDTestCase(unittest.TestCase):
        
        
    def test_base_type_is_set_to_int(self):
        self.assertEqual(Testee.base_type, 'int')
        
        
    def test_help_property_str_is_set(self):
        self.assertEqual(type(Testee.help), str)
        
        
    def test_internal_set_as_automatic_by_default(self):
        self.assertEqual(Testee().internal, 'automatic')
        
    
    def test_construct_data_sets_new_uid_if_none(self):
        set_uid = None
        mocked_returned_uid = 987654321
        
        with patch.object(DummyDatasource, 'new_numeric_id', return_value=mocked_returned_uid) as mock_method:
            returned_uid = Testee.construct_data(None, dyncode.Object, None, None, set_uid)
            
            mock_method.assert_called_once_with(dyncode.Object)
            self.assertEqual(returned_uid, mocked_returned_uid)
            

    def test_construct_data_returns_already_set_uid(self):
        set_uid = 123456789
        mocked_returned_uid = 987654321
        
        with patch.object(DummyDatasource, 'new_numeric_id', return_value=mocked_returned_uid) as mock_method:
            returned_uid = Testee.construct_data(None, dyncode.Object, None, None, set_uid)

            self.assertEqual(returned_uid, set_uid)
            
    
    def test_construct_data_does_not_call_new_numeric_id_if_id_is_set(self):
        set_uid = 123456789
        mocked_returned_uid = 987654321
        
        with patch.object(DummyDatasource, 'new_numeric_id', return_value=mocked_returned_uid) as mock_method:
            returned_uid = Testee.construct_data(None, dyncode.Object, None, None, set_uid)

            mock_method.assert_not_called()     