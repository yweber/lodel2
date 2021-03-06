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


from werkzeug.wrappers import Response
from ..template.loader import TemplateLoader

# This module contains the web UI controllers that will be called from the web ui class

##@brief Render a template and return a respone
#@param tpl str : template relativ path
#@param tpl_vars : templates variables (obsolete)
#@param mimetype
#@param status_code
#@param **kwargs : new version of tpl_vars
#@return a response...
def get_response(tpl='empty.html', tpl_vars={}, mimetype='text/html', status_code=200, **kwargs):
    tpl_vars.update(kwargs)
    loader = TemplateLoader()
    response = Response(loader.render_to_response(tpl, template_vars=tpl_vars), mimetype=mimetype)
    response.status_code = status_code
    return response

## @brief gets the html template corresponding to a given component type
# @param type str : name of the component type
# @param params dict : extra parameters to customize the template
def get_component_html(type='text', params={}):
    params['type'] = type
    template_loader = TemplateLoader()
    return template_loader.render_to_html(template_file='components/components.html', template_vars=params)

def index(request):
    return get_response('index/index.html')


def not_found(request):
    return get_response('errors/404.html', status_code=404)


def test(request):
    if 'id' not in request.url_args:
        id = None
    else:
        id = request.url_args['id']

    template_vars = {
        'id': id,
        'params': request.GET
    }
    return get_response('test.html', tpl_vars=template_vars)
    
