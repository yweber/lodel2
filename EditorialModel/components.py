# -*- coding: utf-8 -*-

## @file components.py
# Defines the EditorialModel::components::EmComponent class and the EditorialModel::components::ComponentNotExistError exception class

import datetime

from Lodel.utils.mlstring import MlString
import logging
import sqlalchemy as sql
from Database import sqlutils
import EditorialModel.fieldtypes as ftypes
from collections import OrderedDict

logger = logging.getLogger('Lodel2.EditorialModel')

## This class is the mother class of all editorial model objects
#
# It gather all the properties and mechanism that are common to every editorial model objects
# @see EditorialModel::classes::EmClass, EditorialModel::types::EmType, EditorialModel::fieldgroups::EmFieldGroup, EditorialModel::fields::EmField
# @pure
class EmComponent(object):

    ## The name of the engine configuration
    # @todo Not a good idea to store it here
    dbconf = 'default'
    ## The table in wich we store data for this object
    # None for EmComponent
    table = None
    ## Used by EmComponent::modify_rank
    ranked_in = None

    ## Read only properties
    _ro_properties = [ 'date_update', 'date_create', 'uid', 'rank', 'deleted']

    ## @brief List fields name and fieldtype
    #
    # This is a list that describe database fields common for each EmComponent child classes.
    # A database field is defined here by a tuple(name, type) with name a string and type an EditorialModel.fieldtypes.EmFieldType
    # @warning The EmFieldType in second position in the tuples must be a class type and not a class instance !!!
    # @see EditorialModel::classes::EmClass::_fields EditorialModel::fieldgroups::EmFieldGroup::_fields EditorialModel::types::EmType::_fields EditorialModel::fields::EmField::_fields
    _fields = [
        ('uid', ftypes.EmField_integer),
        ('name', ftypes.EmField_char),
        ('rank', ftypes.EmField_integer),
        ('date_update', ftypes.EmField_date),
        ('date_create', ftypes.EmField_date),
        ('string', ftypes.EmField_mlstring),
        ('help', ftypes.EmField_mlstring)
    ]

    ## Instaciate an EmComponent
    # @param id_or_name int|str: name or id of the object
    # @throw TypeError if id_or_name is not an integer nor a string
    # @throw NotImplementedError if called with EmComponent
    def __init__(self, id_or_name):

        if type(self) is EmComponent:
            raise NotImplementedError('Abstract class')

        ## @brief An OrderedDict storing fields name and values
        # Values are handled by EditorialModel::fieldtypes::EmFieldType
        # @warning \ref _fields instance property is not the same than EmComponent::_fields class property. In the instance property the EditorialModel::fieldtypes::EmFieldType are instanciated to be able to handle datas
        # @see EmComponent::_fields EditorialModel::fieldtypes::EmFieldType
        self._fields = OrderedDict([ (name, ftype()) for (name,ftype) in (EmComponent._fields + self.__class__._fields) ] )

        # populate
        if isinstance(id_or_name, int):
            self._fields['uid'].value = id_or_name #read only propertie set
        elif isinstance(id_or_name, str):
            self.name = id_or_name
        else:
            raise TypeError('Bad argument: expecting <int> or <str> but got : '+str(type(id_or_name)))
        self.table = self.__class__.table
        self.populate()

    ## Access values of data fields from the object properties
    # @param name str: The propertie name
    # @throw AttributeError if attribute don't exists
    def __getattr__(self, name):
        if name != '_fields' and name in self._fields:
            return self._fields[name].value
        else:
            return super(EmComponent, self).__getattribute__(name)

        #raise AttributeError('Error unknown attribute : '+name)

    def __getattribute__(self, name):
        if super(EmComponent, self).__getattribute__('deleted'):
            #raise EmComponentNotExistError("This component has been deleted")
            raise EmComponentNotExistError("This "+super(EmComponent, self).__getattribute__('__class__').__name__+" has been deleted")
        res = super(EmComponent, self).__getattribute(name)
        return res

    ## Set values of data fields from the object properties
    # @param name str: The propertie name
    # @param value *: The value
    def __setattr__(self, name, value):
        if name in  self.__class__._ro_properties:
            raise TypeError("Propertie '"+name+"' is readonly")

        if name != '_fields' and hasattr(self, '_fields') and name in object.__getattribute__(self, '_fields'):
            self._fields[name].from_python(value)
        else:
            object.__setattr__(self, name, value)

    ## Lookup in the database properties of the object to populate the properties
    # @throw EmComponentNotExistError if the instance is not anymore stored in database
    def populate(self):
        records = self._populateDb() #Db query

        for record in records:
            for keys in self._fields.keys():
                if keys in record:
                    self._fields[keys].from_string(record[keys])

        super(EmComponent, self).__setattr__('deleted', False)

    @classmethod
    ## Shortcut that return the sqlAlchemy engine
    def getDbE(c):
        return sqlutils.getEngine(c.dbconf)
    
    ## Do the query on the database for EmComponent::populate()
    # @throw EmComponentNotExistError if the instance is not anymore stored in database
    def _populateDb(self):
        dbe = self.__class__.getDbE()
        component = sql.Table(self.table, sqlutils.meta(dbe))
        req = sql.sql.select([component])

        if self.uid == None:
            req = req.where(component.c.name == self.name)
        else:
            req = req.where(component.c.uid == self.uid)
        c = dbe.connect()
        res = c.execute(req)

        res = res.fetchall()
        c.close()

        if not res or len(res) == 0:
            raise EmComponentNotExistError("No "+self.__class__.__name__+" found with "+('name ' + self.name if self.uid == None else 'uid ' + str(self.uid) ))

        return res

    ## Insert a new component in the database
    #
    # This function create and assign a new UID and handle the date_create and date_update values
    #
    # @param **kwargs : Names arguments representing object properties
    # @return An instance of the created component
    # @throw TypeError if an element of kwargs isn't a valid object propertie or if a mandatory argument is missing
    #
    # @todo Check that the query didn't failed
    # @todo Check that every mandatory _fields are given in args
    # @todo Put a real rank at creation
    # @todo Stop using datetime.datetime.utcnow() for date_update and date_create init
    @classmethod
    def create(cl, **kwargs):
        for argname in kwargs:
            if argname in ['date_update', 'date_create', 'rank', 'uid']: #Automatic properties
                raise TypeError("Invalid argument : "+argname)

        #TODO check that every mandatory _fields are here like below for example
        #for name in cl._fields:
        #    if cl._fields[name].notNull and cl._fields[name].default == None:
        #        raise TypeError("Missing argument : "+name)

        kwargs['uid'] = cl.newUid()
        kwargs['date_update'] = kwargs['date_create'] = datetime.datetime.utcnow()

        dbe = cl.getDbE()
        conn = dbe.connect()

        kwargs['rank'] = -1 #Warning !!!

        table = sql.Table(cl.table, sqlutils.meta(dbe))
        req = table.insert(kwargs)
        res = conn.execute(req) #Check res?
        conn.close()
        return cl(kwargs['name']) #Maybe no need to check res because this would fail if the query failed


    ## Write the representation of the component in the database
    # @return bool
    # @todo stop using datetime.datetime.utcnow() for date_update update
    def save(self):
        values = {}
        for name, field in self._fields.items():
            values[name] = field.to_sql()

        #Don't allow creation date overwritting
        """
        if 'date_create' in values:
            del values['date_create']
            logger.warning("date_create supplied for save, but overwritting of date_create not allowed, the date will not be changed")
        """
        values['date_update'] = datetime.datetime.utcnow()

        self._saveDb(values)
    
    ## Do the query in the datbase for EmComponent::save()
    # @param values dict: A dictionnary of the values to insert
    # @throw RunTimeError if it was unable to do the Db update
    def _saveDb(self, values):
        """ Do the query on the db """
        dbe = self.__class__.getDbE()
        component = sql.Table(self.table, sqlutils.meta(dbe))
        req = sql.update(component, values = values).where(component.c.uid == self.uid)

        c = dbe.connect()
        res = c.execute(req)
        c.close()
        if not res:
            raise RuntimeError("Unable to save the component in the database")


    ## Delete this component data in the database
    # @return bool
    # @todo Use something like __del__ instead (or call it at the end)
    # @throw RunTimeError if it was unable to do the deletion
    def delete(self):
        #<SQL>
        dbe = self.__class__.getDbE()
        component = sql.Table(self.table, sqlutils.meta(dbe))
        req= component.delete().where(component.c.uid == self.uid)
        c = dbe.connect()
        res = c.execute(req)
        c.close
        if not res:
            raise RuntimeError("Unable to delete the component in the database")

        super(EmComponent, self).__setattr__('deleted', True)
        #</SQL>
        pass

    ## modify_rank
    #
    # Permet de changer le rank d'un component, soit en lui donnant un rank précis, soit en augmentant ou reduisant sont rank actuelle d'une valleur donné.
    #
    # @param new_rank int: le rank ou modificateur de rank
    # @param sign str: Un charactère qui peut être : '=' pour afecter un rank, '+' pour ajouter le modificateur de rank ou '-' pour soustraire le modificateur de rank.
    #
    # @return bool: True en cas de réussite False en cas d'echec.
    # @throw TypeError if an argument isn't from the expected type
    # @thrown ValueError if an argument as a wrong value but is of the good type
    def modify_rank(self, new_rank, sign = '='):

        if(type(new_rank) is int):
            if(new_rank >= 0):
                dbe = self.__class__.getDbE()
                component = sql.Table(self.table, sqlutils.meta(dbe))
                req = sql.sql.select([component.c.uid, component.c.rank])

                if(type(sign) is not str):
                    logger.error("Bad argument")
                    raise TypeError('Excepted a string (\'=\' or \'+\' or \'-\') not a '+str(type(sign)))

                if(sign == '='):

                    req = sql.sql.select([component.c.uid, component.c.rank])
                    req = req.where((getattr(component.c, self.ranked_in) == getattr(self, self.ranked_in)) & (component.c.rank == new_rank))
                    c = dbe.connect()
                    res = c.execute(req)
                    res = res.fetchone()
                    c.close()

                    if(res != None):
                        if(new_rank < self.rank):
                            req = req.where((getattr(component.c, self.ranked_in) == getattr(self, self.ranked_in)) & ( component.c.rank >= new_rank) & (component.c.rank < self.rank))
                        else:
                            req = req.where((getattr(component.c, self.ranked_in) == getattr(self, self.ranked_in)) & (component.c.rank <= new_rank) & (component.c.rank > self.rank))

                        c = dbe.connect()
                        res = c.execute(req)
                        res = res.fetchall()

                        vals = list()
                        vals.append({'id' : self.uid, 'rank' : new_rank})

                        for row in res:
                            if(new_rank < self.rank):
                                vals.append({'id' : row.uid, 'rank' : row.rank+1})
                            else:
                                vals.append({'id' : row.uid, 'rank' : row.rank-1})


                        req = component.update().where(component.c.uid == sql.bindparam('id')).values(rank = sql.bindparam('rank'))
                        c.execute(req, vals)
                        c.close()

                        self._fields['rank'].value = new_rank

                    else:
                        logger.error("Bad argument")
                        raise ValueError('new_rank to big, new_rank - 1 doesn\'t exist. new_rank = '+str((new_rank)))
                elif(sign == '+'):
                    req = sql.sql.select([component.c.uid, component.c.rank])
                    req = req.where((getattr(component.c, self.ranked_in) == getattr(self, self.ranked_in)) & (component.c.rank == self.rank + new_rank))
                    c = dbe.connect()
                    res = c.execute(req)
                    res = res.fetchone()
                    c.close()

                    if(res != None):
                        if(new_rank != 0):
                            req = req.where((getattr(component.c, self.ranked_in) == getattr(self, self.ranked_in)) & (component.c.rank <= self.rank + new_rank) & (component.c.rank > self.rank))

                            c = dbe.connect()
                            res = c.execute(req)
                            res = res.fetchall()

                            vals = list()
                            vals.append({'id' : self.uid, 'rank' : self.rank + new_rank})

                            for row in res:
                                vals.append({'id' : row.uid, 'rank' : row.rank - 1})

                            req = component.update().where(component.c.uid == sql.bindparam('id')).values(rank = sql.bindparam('rank'))
                            c.execute(req, vals)
                            c.close()
                            
                            self._fields['rank'] += new_rank
                        else:
                            logger.error("Bad argument")
                            raise ValueError('Excepted a positive int not a null. new_rank = '+str((new_rank)))
                    else:
                        logger.error("Bad argument")
                        raise ValueError('new_rank to big, rank + new rank doesn\'t exist. new_rank = '+str((new_rank)))
                elif(sign == '-'):
                    if((self.rank + new_rank) > 0):
                        if(new_rank != 0):
                            req = req.where((getattr(component.c, self.ranked_in) == getattr(self, self.ranked_in)) & (component.c.rank >= self.rank - new_rank) & (component.c.rank < self.rank))

                            c = dbe.connect()
                            res = c.execute(req)
                            res = res.fetchall()

                            vals = list()
                            vals.append({'id' : self.uid, 'rank' : self.rank - new_rank})

                            for row in res:
                                vals.append({'id' : row.uid, 'rank' : row.rank + 1})

                            req = component.update().where(component.c.uid == sql.bindparam('id')).values(rank = sql.bindparam('rank'))
                            c.execute(req, vals)
                            c.close()

                            self._fields['rank'] -= new_rank
                        else:
                            logger.error("Bad argument")
                            raise ValueError('Excepted a positive int not a null. new_rank = '+str((new_rank)))
                    else:
                        logger.error("Bad argument")
                        raise ValueError('new_rank to big, rank - new rank is negative. new_rank = '+str((new_rank)))
                else:
                    logger.error("Bad argument")
                    raise ValueError('Excepted a string (\'=\' or \'+\' or \'-\') not a '+str((sign)))

            else:
                logger.error("Bad argument")
                raise ValueError('Excepted a positive int not a negative. new_rank = '+str((new_rank)))
        else:
            logger.error("Bad argument")
            raise TypeError('Excepted a int not a '+str(type(new_rank)))


    def __repr__(self):
        if self.name is None:
            return "<%s #%s, 'non populated'>" % (type(self).__name__, self.uid)
        else:
            return "<%s #%s, '%s'>" % (type(self).__name__, self.uid, self.name)

    @classmethod
    ## Register a new component in UID table
    # 
    # Use the class property table
    # @return A new uid (an integer)
    def newUid(cl):
        if cl.table == None:
            raise NotImplementedError("Abstract method")

        dbe = cl.getDbE()

        uidtable = sql.Table('uids', sqlutils.meta(dbe))
        conn = dbe.connect()
        req = uidtable.insert(values={'table':cl.table})
        res = conn.execute(req)

        uid = res.inserted_primary_key[0]
        logger.debug("Registering a new UID '"+str(uid)+"' for '"+cl.table+"' component")

        conn.close()

        return uid

## An exception class to tell that a component don't exist
class EmComponentNotExistError(Exception):
    pass
