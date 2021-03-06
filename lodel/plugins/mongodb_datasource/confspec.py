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
    'lodel.validator.validator': ['Validator']})

## @brief Mongodb datasource plugin confspec
# @ingroup plugin_mongodb_datasource
#
# Describes mongodb plugin configuration and the corresponding validators
CONFSPEC = {
    'lodel2.datasource.mongodb_datasource.*':{
        'read_only': (False, Validator('bool')),
        'host': ('localhost', Validator('host')),
        'port': (None, Validator('string', none_is_valid = True)),
        'db_name':('lodel', Validator('string')),
        'username': (None, Validator('string')),
        'password': (None, Validator('string'))
    }
}
