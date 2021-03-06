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


## @package lodel.plugin.hooks This module deals with the Hook management in Lodel

import os
import copy
from lodel.context import LodelContext


## @brief Class designed to handle a hook's callback with a priority
class DecoratedWrapper(object):
    ##
    # @param hook function : the function to wrap
    # @param priority int : the callbacl priority
    def __init__(self, hook, priority):
        self._priority = priority
        self._hook = hook
    
    ## @brief Calls the callback
    # @param hook_name str : The name of the called hook
    # @param caller * : The caller (depends on the hook)
    # @param payload * : Datas that depends on the hook
    # @return modified payload
    def __call__(self, hook_name, caller, payload):
        return self._hook(hook_name, caller, payload)

    ## @brief Returns the string representation of the class
    # It shows the name and the priority of the hook
    def __str__(self):
        return "<LodelHook '%s' priority = %s>" % (
            self._hook.__name__, self._priority)

## @brief Decorator designed to register hook's callbacks
# @ingroup lodel2_plugins
#
# @note Decorated functions are expected to take 3 arguments :
#  - hook_name : the called hook name
#  - caller : the hook caller (depends on the hook)
#  - payload : datas depending on the hook
class LodelHook(object):
    
    ## @brief Stores all hooks (DecoratedWrapper instances)
    _hooks = dict()
    
    ##
    # @param hook_name str : the name of the hook to register to
    # @param priority int : the hook priority (default value : None)
    def __init__(self, hook_name, priority = None):
        self._hook_name = hook_name
        self._priority = 0xFFFF if priority is None else priority
    
    ## @brief called just after __init__
    # @param hook function : the decorated function
    # @return the hook argument
    def __call__(self, hook):
        if not self._hook_name in self._hooks:
            self._hooks[self._hook_name] = list()
        wrapped = DecoratedWrapper(hook, self._priority)
        self._hooks[self._hook_name].append(wrapped)
        self._hooks[self._hook_name] = sorted(self._hooks[self._hook_name], key = lambda h: h._priority)
        return hook

    ## @brief Calls a hook
    # @param hook_name str : the hook's name
    # @param caller * : the hook caller (depends on the hook)
    # @param payload * : datas for the hook
    # @return modified payload
    @classmethod
    def call_hook(cls, hook_name, caller, payload):
        LodelContext.expose_modules(globals(), {'lodel.logger': 'logger'})
        logger.debug("Calling hook '%s'" % hook_name)
        if hook_name in cls._hooks:
            for hook in cls._hooks[hook_name]:
                logger.debug("Lodel hook '%s' calls %s" % (
                    hook_name, hook))
                payload = hook(hook_name, caller, payload)
        return payload
    
    ## @brief Fetches registered hooks
    # @param names list | None : optionnal filter on name (default value : None)
    # @return dict containing for each name a list of the hooks and their priorities
    @classmethod
    def hook_list(cls, names = None):
        res = None
        if names is not None:
            res = { name: copy.copy(cls._hooks[name]) for name in cls._hooks if name in names}
        else:
            res = copy.copy(cls._hooks)
        return { name: [(hook._hook, hook._priority) for hook in hooks] for name, hooks in res.items() }
    
    ## @brief Unregister all hooks
    # @warning REALLY NOT a good idea !
    # @note implemented for testing purpose
    @classmethod
    def __reset__(cls):
        cls._hooks = dict()

