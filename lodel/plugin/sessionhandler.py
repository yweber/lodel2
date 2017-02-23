from lodel.context import LodelContext
LodelContext.expose_modules(globals(), {
    'lodel.plugin.plugins': ['Plugin', 'MetaPlugType'],
    'lodel.plugin.exceptions': ['PluginError', 'PluginTypeError',
        'LodelScriptError', 'DatasourcePluginError'],
    'lodel.validator.validator': ['Validator']})


##@brief SessionHandlerPlugin metaclass designed to implements a wrapper
#between SessionHandlerPlugin classmethod and plugin loader functions
class SessionPluginWrapper(MetaPlugType):

    ##@brief Constant that stores all possible session actions
    #
    #Key is the SessionHandlerPlugin method name and value is SessionHandler
    #plugin function name
    _ACTIONS = {
        'start': 'start_session',
        'destroy': 'destroy_session', 
        'restore': 'restore_session',
        'save': 'save_session',
        'set': 'set_session_value',
        'get': 'get_session_value',
        'del': 'del_session_value'}

    def __init__(self, name, bases, attrs):
        super().__init__(name, bases, attrs)
        self._instance = None
        
    ##@brief Handles wrapper between class method and plugin loader functions
    def __getattribute__(self, name):
        instance = super().__getattribute__('_instance')
        if name in SessionPluginWrapper._ACTIONS:
            if instance is None:
                raise PluginError("Trying to access to SessionHandler \
functions, but no session handler initialized")
            return getattr(
                instance.loader_module(),
                SessionPluginWrapper._ACTIONS[name])
        return super().__getattribute__(name)


_glob_typename = 'session_handler'
##@brief Singleton class designed to handle session handler plugin
#
#@note This class is a singleton because only one session handler can be
#loaded by instance
class SessionHandlerPlugin(Plugin, metaclass=SessionPluginWrapper): 
    ##@brief Stores the singleton instance
    _instance = None

    _plist_confspecs = {
        'section': 'lodel2',
        'key': 'session_handler',
        'default': None,
        'validator': Validator(
            'plugin', none_is_valid=False,ptype = _glob_typename)}

    _type_conf_name = _glob_typename
            
    def __init__(self, plugin_name):
        if self._instance is None:
            super().__init__(plugin_name)
            self.__class__._instance = self
        else:
            raise RuntimeError("A SessionHandler Plugin is already plug")
    
    ##@brief Clear class
    #@see plugins.Plugin::clear()
    @classmethod
    def clear_cls(cls):
        if cls._instance is not None:
            inst = cls._instance
            cls._instance = None
            del(inst)
