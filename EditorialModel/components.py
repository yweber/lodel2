# -*- coding: utf-8 -*-

## Main object to manipulate Editorial Model
#    parent of all other EM editing classes
#    @see EmClass, EmType, EmFieldGroup, EmField


import datetime

from Lodel.utils.mlstring import MlString
import logging
import sqlalchemy as sql
from Database import sqlutils
import EditorialModel.fieldtypes as ftypes
from collections import OrderedDict

logger = logging.getLogger('Lodel2.EditorialModel')

class EmComponent(object):

    dbconf = 'default' #the name of the engine configuration
    table = None
    ranked_in = None

    """ instaciate an EmComponent
        @param id_or_name int|str: name or id of the object
        @exception TypeError
    """
    def __init__(self, id_or_name):
        if type(self) is EmComponent:
            raise EnvironmentError('Abstract class')

        # data fields of the object
        self._fields = OrderedDict([('uid', ftypes.EmField_integer()), ('name', ftypes.EmField_char()), ('rank', ftypes.EmField_integer()), ('date_update', ftypes.EmField_date()), ('date_create', ftypes.EmField_date()), ('string', ftypes.EmField_mlstring()), ('help', ftypes.EmField_mlstring())] + self._fields)

        # populate
        if isinstance(id_or_name, int):
            self.uid = id_or_name
            self.name = None
        elif isinstance(id_or_name, str):
            self.uid = None
            self.name = id_or_name
        else:
            raise TypeError('Bad argument: expecting <int> or <str> but got : '+str(type(id_or_name)))
        self.populate()

    # access values of data fields from the object properties
    def __getattr__(self, name):
        if name != '_fields' and name in self._fields:
            return self._fields[name].value

        raise AttributeError('Error unknown attribute : '+name)

    # set values of data fields from the object properties
    def __setattr__(self, name, value):
        if name != '_fields' and hasattr(self, '_fields') and name in object.__getattribute__(self, '_fields'):
            self._fields[name].from_python(value)
        else:
            object.__setattr__(self, name, value)

    """ Lookup in the database properties of the object to populate the properties
    """
    def populate(self):
        records = self._populateDb() #Db query

        for record in records:
            for keys in self._fields.keys():
                if keys in record:
                    self._fields[keys].from_string(record[keys])

    @classmethod
    def getDbE(c):
        """ Shortcut that return the sqlAlchemy engine """
        return sqlutils.getEngine(c.dbconf)

    def _populateDb(self):
        """ Do the query on the db """
        dbe = self.__class__.getDbE()
        component = sql.Table(self.table, sqlutils.meta(dbe))
        req = sql.sql.select([component])

        if self.uid == None:
            req = req.where(component.c.name == self.name)
        else:
            req = req.where(component.c.uid == self.uid)
        c = dbe.connect()
        res = c.execute(req)
        c.close()

        res = res.fetchall()

        if not res or len(res) == 0:
            raise EmComponentNotExistError("No component found with "+('name ' + self.name if self.uid == None else 'uid ' + str(self.uid) ))

        return res

    ## Insert a new component in the database
    # This function create and assign a new UID and handle the date_create value
    # @param values The values of the new component
    # @return An instance of the created component
    #
    # @todo Check that the query didn't failed
    @classmethod
    def create(c, values):
        values['uid'] = c.newUid()
        values['date_update'] = values['date_create'] = datetime.datetime.utcnow()

        dbe = c.getDbE()
        conn = dbe.connect()
        table = sql.Table(c.table, sqlutils.meta(dbe))
        req = table.insert(values)
        res = conn.execute(req) #Check res?
        conn.close()
        return c(values['name']) #Maybe no need to check res because this would fail if the query failed


    """ write the representation of the component in the database
        @return bool
    """
    def save(self):
        values = {}
        for name, field in self._fields.items():
            values[name] = field.to_sql()

        #Don't allow creation date overwritting
        if 'date_create' in values:
            del values['date_create']
            logger.warning("date_create supplied for save, but overwritting of date_create not allowed, the date will not be changed")

        self._saveDb(values)

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


    """ delete this component data in the database
        @return bool
    """
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

                        self.rank = new_rank

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

                            self.rank += new_rank
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

                            self.rank -= new_rank
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
    def newUid(c):
        """ This function register a new component in uids table
            @return The new uid
        """
        dbe = c.getDbE()

        uidtable = sql.Table('uids', sqlutils.meta(dbe))
        conn = dbe.connect()
        req = uidtable.insert(values={'table':c.table})
        res = conn.execute(req)

        uid = res.inserted_primary_key[0]
        logger.debug("Registering a new UID '"+str(uid)+"' for '"+c.table+"' component")

        conn.close()

        return uid


class EmComponentNotExistError(Exception):
    pass
