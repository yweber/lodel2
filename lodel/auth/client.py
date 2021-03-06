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


import copy
import sys
import warnings
import inspect

from lodel.context import LodelContext
LodelContext.expose_modules(globals(), {
    'lodel.settings': ['Settings'],
    'lodel.logger': 'logger',
    'lodel.plugin': [('SessionHandlerPlugin', 'SessionHandler')],
    'lodel.auth.exceptions': ['ClientError', 'ClientAuthenticationFailure',
                              'ClientPermissionDenied', 'ClientAuthenticationError'],
    'lodel.leapi.query': ['LeGetQuery'], })

## @brief Client metaclass designed to implements container accessor on
# Client Class
#
#@todo Maybe we can delete this metaclass....


class ClientMetaclass(type):

    def __init__(self, name, bases, attrs):
        return super(ClientMetaclass, self).__init__(name, bases, attrs)

    def __getitem__(self, key):
        return self.data()[key]

    def __delitem__(self, key):
        del(self.data()[key])

    def __setitem__(self, key, value):
        if self.get_session_token() is None:
            self.set_session_token(SessionHandler.start())
        data = self.data()
        data[key] = value

    def __str__(self):
        return str(self._instance)

## @brief Abstract singleton class designed to handle client informations
#
# This class is designed to handle client authentication and sessions


class Client(object, metaclass=ClientMetaclass):

    ## @brief Singleton instance
    _instance = None
    # @brief List of dict that stores field ref for login and password
    #
    # Storage specs :
    #
    # A list of dict, with keys 'login' and 'password', items are tuple.
    # - login tuple contains (LeObjectChild, FieldName, link_field) with:
    # - LeObjectChild the dynclass containing the login
    # - Fieldname the fieldname of LeObjectChild containing the login
    # - link_field None if both login and password are in the same
    # LeObjectChild. Else contains the field that make the link between
    # login LeObject and password LeObject
    # - password typle contains (LeObjectChild, FieldName)
    _infos_fields = None

    ## @brief Constant that stores the session key that stores authentication
    # informations
    _AUTH_DATANAME = '__auth_user_infos'

    ## @brief Constructor
    #@param session_token mixed : Session token provided by client to interface
    def __init__(self, session_token=None):
        logger.debug(session_token)
        if self.__class__ == Client:
            raise NotImplementedError("Abstract class")
        logger.debug("New instance of Client child class %s" %
                     self.__class__.__name__)
        if Client._instance is not None:
            old = Client._instance
            Client._instance = None
            del(old)
            logger.debug("Replacing old Client instance by a new one")
        else:
            ## first instanciation, fetching settings
            self.fetch_settings()
        # @brief Stores infos for authenticated users (None == anonymous)
        self.__user = None
        ## @brief Stores the session handler
        Client._instance = self
        ## @brief Stores LodelSession instance
        self.__data = dict()
        if session_token is not None:
            self.__data = SessionHandler.restore(session_token)
        self.__session_token = session_token

        logger.debug("New client : %s" % self)

    def __del__(self):
        del(self.__session_token)
        del(self.__data)
    ## @brief Returns session
    #@ returns the dict which stores session

    @classmethod
    def data(cls):
        return cls._instance.__data

    ## @brief Returns the user's information contained in the session's data
    @classmethod
    def user(cls):
        if '__auth_user_infos' in cls._instance.__data:
            return cls._instance.__data['__auth_user_infos']
        else:
            return None

    ## @brief Returns the session's token
    @classmethod
    def get_session_token(cls):
        return cls._instance.__session_token

    ## @brief Set the session's token
    #@param the value of the token
    @classmethod
    def set_session_token(cls, value):
        cls._instance.__session_token = value

    ## @brief Try to authenticate a user with a login and a password
    #@param login str : provided login
    #@param password str : provided password (hash)
    #@warning brokes composed UID
    #@note implements multiple login/password sources (useless ?)
    #@todo composed UID broken method
    #@todo allow to provide an authentication source
    @classmethod
    def authenticate(self, login=None, password=None):
        # Authenticate
        for infos in self._infos_fields:
            logger.debug(self._infos_fields)
            login_cls = infos['login'][0]
            pass_cls = infos['password'][0]
            qfilter = "{passfname} = {passhash}"
            uid_fname = login_cls.uid_fieldname()[0]  # COMPOSED UID BROKEN
            if login_cls == pass_cls:
                # Same EmClass for login & pass
                qfilter = qfilter.format(
                    passfname=infos['password'][1],
                    passhash=password)
            else:
                # Different EmClass, building a relational filter
                passfname = "%s.%s" % (infos['login'][2], infos['password'][1])
                qfilter = qfilter.format(
                    passfname=passfname,
                    passhash=password)
            getq = LeGetQuery(infos['login'][0], qfilter,
                              field_list=[uid_fname], limit=1)
            req = getq.execute()
            if len(req) == 1:
                self.__set_authenticated(infos['login'][0], req[0][uid_fname])
                break
        if self.is_anonymous():
            self.authentication_failure()  # Security logging

    ## @brief Attempt to restore a session given a session token
    #@param token mixed : a session token
    #@return Session data (a dict)
    #@throw ClientAuthenticationFailure if token is not valid or not
    # existing
    @classmethod
    def restore_session(cls, token):
        cls._assert_instance()
        if cls._instance.__session_token is not None:
            raise ClientAuthenticationError("Trying to restore a session, but \
a session is already started !!!")
        try:
            cls._instance.__data = SessionHandler.restore(token)
            cls._instance.__session_token = token
        except ClientAuthenticationFailure:
            logger.warning("Session restoring failed")
        return copy.copy(cls._instance.data)

    ## @brief Returns the current session token or None
    #@return A session token or None
    @classmethod
    def session_token(cls):
        cls._assert_instance()
        return cls._instance.__session_token

    ## @brief Deletes current session
    @classmethod
    def destroy(cls):
        cls._assert_instance()
        SessionHandler.destroy(cls._instance.__session_token)
        cls._instance.__session_token = None
        cls._instance.__data = dict()

    ## @brief Deletes current client and saves its session
    @classmethod
    def clean(cls):
        if cls._instance.__session_token is not None:
            SessionHandler.save(cls._instance.__session_token, cls._instance.__data)
        if Client._instance is not None:
            del(Client._instance)
        Client._instance = None

    ## @brief Tests if a client is anonymous or logged in
    #@return True if client is anonymous
    @classmethod
    def is_anonymous(cls):
        return Client._instance.user() is None

    ## @brief Method to be called on authentication failure
    #@throw ClientAuthenticationFailure
    #@throw LodelFatalError if no Client child instance is found
    @classmethod
    def authentication_failure(cls):
        cls._generic_error(ClientAuthenticationFailure)

    ## @brief Method to be called on authentication error
    #@throw ClientAuthenticationError
    #@throw LodelFatalError if no Client child instance is found
    @classmethod
    def authentication_error(cls, msg="Unknow error"):
        cls._generic_error(ClientAuthenticationError, msg)

    ## @brief Method to be called on permission denied error
    #@throw ClientPermissionDenied
    #@throw LodelFatalError if no Client child instance is found
    @classmethod
    def permission_denied_error(cls, msg=""):
        cls._generic_error(ClientPermissionDenied, msg)

    ## @brief Generic error method
    #@see Client::authentication_failure() Client::authentication_error()
    # Client::permission_denied_error()
    #@throw LodelFatalError if no Client child instance is found
    @classmethod
    def _generic_error(cls, expt, msg=""):
        cls._assert_instance()
        raise expt(Client._instance, msg)

    ## @brief Asserts that an instance of Client child class exists
    #@throw LodelFataError if no instance of Client child class is found
    @classmethod
    def _assert_instance(cls):
        if Client._instance is None:
            raise LodelFatalError("No client instance found. Abording.")

    ## @brief Class method that fetches conf
    #
    # This method populates Client._infos_fields . This attribute stores
    # informations on login and password location (LeApi object & field)
    @classmethod
    def fetch_settings(cls):
        LodelContext.expose_dyncode(globals(), 'dyncode')
        if cls._infos_fields is None:
            cls._infos_fields = list()
        else:
            # Already fetched
            return
        infos = (
            Settings.auth.login_classfield,
            Settings.auth.pass_classfield)
        res_infos = []
        for clsname, fieldname in infos:
            dcls = dyncode.lowername2class(infos[0][0])
            res_infos.append((dcls, infos[1][1]))

        link_field = None
        if res_infos[0][0] != res_infos[1][0]:
            # login and password are in two separated EmClass
            # determining the field that links login EmClass to password
            # EmClass
            for fname, fdh in res_infos[0][0].fields(True).items():
                if fdh.is_reference() and res_infos[1][0] in fdh.linked_classes():
                    link_field = fname
            if link_field is None:
                # Unable to find link between login & password EmClass
                raise AuthenticationError("Unable to find a link between \
login EmClass '%s' and password EmClass '%s'. Abording..." % (
                    res_infos[0][0], res_infos[1][0]))
        res_infos[0] = (res_infos[0][0], res_infos[0][1], link_field)
        cls._infos_fields.append(
            {'login': res_infos[0], 'password': res_infos[1]})

    ## @brief Sets a user as authenticated and starts a new session
    #@param leo LeObject child class : the LeObject the user is stored in
    #@param uid str : uniq id (in leo)
    #@return None
    @classmethod
    def __set_authenticated(cls, leo, uid):
        cls._instance.__user = {'classname': leo.__name__, 'uid': uid, 'leoclass': leo}
        # Store auth infos in session
        cls._instance.__data[cls._instance.__class__._AUTH_DATANAME] = copy.copy(
            cls._instance.__user)
