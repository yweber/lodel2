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
from lodel.leapi.datahandlers.datas import Password as Testee


class PasswordTestCase(unittest.TestCase):
        
        
    def test_base_type_property_value_equals_password(self):
        self.assertEqual(Testee.base_type, 'password')
        
        
    def test_help_property_string_is_set(self):
        self.assertEqual(type(Testee.help), str)