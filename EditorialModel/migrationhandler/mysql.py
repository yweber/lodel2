# -*- coding: utf-8 -*-

import copy
import _mysql as mysqlclient
import _mysql_exceptions

import EditorialModel

# The global MH algorithm is as follow :
# A create_table(table_name, pk_name, pk_opt) method that create a table
# with one pk field
# An add_column(table_name, field_name, field_opt) method that add a column to a table
#
# The create_default_table method will call both methods to create the object and relation tables
#
# Supported operations :
# - EmClass creation
# - EmClass deletion (untested)
# - EmField creation
# - EmField deletion (untested)
#
# Unsupported operations :
# - EmClass rename
# - EmField rename

## @brief Modify a MySQL database given editorial model changes
class MysqlMigrationHandler(EditorialModel.migrationhandler.dummy.DummyMigrationHandler):
    
    _object_tname = 'object'
    _relation_tname = 'relation'

    ## @brief Construct a MysqlMigrationHandler
    # @param host str : The db host
    # @param user str : The db user
    # @param password str : The db password
    # @param db str : The db name
    def __init__(self, host, user, password, db, db_engine = 'InnoDB', foreign_keys = True, debug = False, dryrun = False, drop_if_exists = False):
        #Connect to MySQL
        self.db = mysqlclient.connect(host=host, user=user, passwd=password, db=db)
        self.debug = debug
        self.dryrun = dryrun
        self.db_engine = db_engine
        self.foreign_keys = foreign_keys if db_engine == 'InnoDB' else False
        self.drop_if_exists = drop_if_exists
        #Create default tables
        self._create_default_tables(self.drop_if_exists)
        pass
    
    ## @brief Modify the db given an EM change
    def register_change(self, em, uid, initial_state, new_state, engine = None):
        if engine is None:
            engine = self.db_engine
        if isinstance(em.component(uid), EditorialModel.classes.EmClass):
            if initial_state is None:
                #EmClass creation
                self.create_emclass_table(em, uid, engine)
            elif new_state is None:
                #EmClass deletion
                self.delete_emclass_table(em, uid)
        elif isinstance(em.component(uid), EditorialModel.fields.EmField):
            emfield = em.component(uid)
            if initial_state is None:
                #EmField creation
                if not(emfield.name in EditorialModel.classtypes.common_fields.keys()):
                    self.add_col_from_emfield(em,uid)
            elif new_state is None:
                #EmField deletion
                if not (emfield.name in EditorialModel.classtypes.common_fields.keys()):
                    self.del_col_from_emfield(em, uid)
                pass
        pass

    def register_model_state(self, em, state_hash):
        pass

    ## @brief Exec a query
    def _query(self, query):
        if self.debug:
            print(query+"\n")
        if not self.dryrun:
            self.db.query(query)
    
    ## @brief Given an EmField uid add a column to the corresponding table
    # @param em Model : A Model instance
    # @param uid int : An EmField uid
    # @return None
    def add_col_from_emfield(self, em, uid):
        emfield = em.component(uid)
        if not isinstance(emfield, EditorialModel.fields.EmField):
            raise ValueError("The given uid is not an EmField uid")

        emclass = emfield.em_class
        tname = self._emclass2table_name(emclass)
        self._add_column(tname, emfield.name, emfield.fieldtype_instance())
        # Refresh the table triggers
        cols_l = self._class2cols(emclass)
        self._generate_triggers(tname, cols_l)


    ## @brief Given a class uid create the coressponding table
    def create_emclass_table(self, em, uid, engine):
        emclass = em.component(uid)
        if not isinstance(emclass, EditorialModel.classes.EmClass):
            raise ValueError("The given uid is not an EmClass uid")
        pkname, pktype = self._common_field_pk
        table_name = self._emclass2table_name(emclass)
        self._create_table(table_name, pkname, pktype, engine=engine)
        
        if self.foreign_keys:
            self._add_fk(table_name, self._object_tname, pkname, pkname)
    
    ## @brief Given an EmClass uid delete the corresponding table
    def delete_emclass_table(self, em, uid):
        emclass = emcomponent(uid)
        if not isinstance(emclass, EditorialModel.classes.EmClass):
            raise ValueError("The give uid is not an EmClass uid")
        tname = self._idname_escape(self._emclass2table_name(emclass.name))
        # Delete the table triggers to prevent errors
        self._generate_triggers(tname, dict())

        self._query("""DROP TABLE {table_name};""".format(table_name = tname))

    ## @brief Given an EmField delete the corresponding column
    # @param em Model : an @ref EditorialModel.model.Model instance
    # @param uid int : an EmField uid
    def delete_col_from_emfield(self, em, uid):
        emfield = em.component(uid)
        if not isinstance(emfield, EditorialModel.fields.EmField):
            raise ValueError("The given uid is not an EmField uid")

        emclass = emfield.em_class
        tname = self._emclass2table_name(emclass)
        # Delete the table triggers to prevent errors
        self._generate_triggers(tname, dict())

        self._del_column(tname, emfield.name)
        # Refresh the table triggers
        cols_ls = self._class2cols(emclass)
        self._generate_triggers(tname, cols_l)
    
    ## @brief Delete a column from a table
    # @param tname str : The table name
    # @param fname str : The column name
    def _del_column(self, tname, fname):
        tname = self._idname_escape(tname)
        fname = self._idname_escape(fname)

        self._query("""ALTER TABLE {table_name} DROP COLUMN {col_name};""".format(table_name = tname, col_name = fname))
    
    ## @brief Construct a table name given an EmClass instance
    # @param emclass EmClass : An EmClass instance
    # @return a table name
    def _emclass2table_name(self, emclass):
        return "class_%s"%emclass.name
        
    ## @brief Generate a columns_fieldtype dict given an EmClass uid
    # @param emclass EmClass : An EmClass instance
    # @return A dict with column name as key and EmFieldType instance as value
    def _class2cols(self, emclass):
        if not isinstance(emclass, EditorialModel.classes.EmClass):
            raise ValueError("The given uid is not an EmClass uid")
        return { f.name: f.fieldtype_instance() for f in emclass.fields() }

    ## @brief Create object and relations tables
    # @param drop_if_exist bool : If true drop tables if exists
    def _create_default_tables(self, drop_if_exist = False):
        if_exists = 'drop' if drop_if_exist else 'nothing'
        #Object tablea
        tname = self._object_tname
        pk_name, pk_ftype = self._common_field_pk
        self._create_table(tname, pk_name, pk_ftype, engine=self.db_engine, if_exists = if_exists)
        #Adding columns
        cols = { fname: self._common_field_to_ftype(fname) for fname in EditorialModel.classtypes.common_fields }
        for fname, ftype in cols.items():
            if fname != pk_name:
                self._add_column(tname, fname, ftype)
        #Creating triggers
        self._generate_triggers(tname, cols)

        #Relation table
        tname = self._relation_tname
        pk_name, pk_ftype = self._relation_pk
        self._create_table(tname, pk_name, pk_ftype, engine = self.db_engine, if_exists = if_exists)
        #Adding columns
        for fname, ftype in self._relation_cols.items():
            self._add_column(tname, fname, ftype)
        #Creating triggers
        self._generate_triggers(tname, self._relation_cols)

    ## @return true if the name changes
    def _name_change(self, initial_state, new_state):
        return 'name' in initial_state and initial_state['name'] != new_state['name']
    
    ## @brief Create a table with primary key
    # @param table_name str : table name
    # @param pk_name str : pk column name
    # @param pk_specs str : see @ref _field_to_sql()
    # @param engine str : The engine to use with this table
    # @param charset str : The charset of this table
    # @param if_exist str : takes values in ['nothing', 'drop']
    # @return None
    def _create_table(self, table_name, pk_name, pk_ftype, engine, charset = 'utf8', if_exists = 'nothing'):
        #Escaped table name
        etname = self._idname_escape(table_name)
        pk_type = self._field_to_type(pk_ftype)
        pk_specs = self._field_to_specs(pk_ftype)

        if if_exists == 'drop':
            self._query("""DROP TABLE IF EXISTS {table_name};""".format(table_name = etname))
            qres = """
CREATE TABLE {table_name} (
{pk_name} {pk_type} {pk_specs},
PRIMARY KEY({pk_name})
) ENGINE={engine} DEFAULT CHARSET={charset};"""
        elif if_exists == 'nothing':
            qres = """CREATE TABLE IF NOT EXISTS {table_name} (
{pk_name} {pk_type} {pk_specs},
PRIMARY KEY({pk_name})
) ENGINE={engine} DEFAULT CHARSET={charset};"""
        else:
            raise ValueError("Unexpected value for argument if_exists '%s'."%if_exists)

        self._query(qres.format(
            table_name = self._idname_escape(table_name),
            pk_name = self._idname_escape(pk_name),
            pk_type = pk_type,
            pk_specs = pk_specs,
            engine = engine,
            charset = charset
        ))

    ## @brief Add a column to a table
    # @param table_name str : The table name
    # @param col_name str : The columns name
    # @param col_fieldtype EmFieldype the fieldtype
    # @return None
    def _add_column(self, table_name, col_name, col_fieldtype, drop_if_exists = False):
        add_col = """ALTER TABLE {table_name}
ADD COLUMN {col_name} {col_type} {col_specs};"""
        
        etname = self._idname_escape(table_name)
        ecname = self._idname_escape(col_name)

        add_col = add_col.format(
            table_name = etname,
            col_name = ecname,
            col_type = self._field_to_type(col_fieldtype),
            col_specs = self._field_to_specs(col_fieldtype),
        )
        try:
            self._query(add_col)
        except _mysql_exceptions.OperationalError as e:
            if drop_if_exists:
                self._del_column(table_name, col_name)
                self._add_column(table_name, col_name, col_fieldtype, drop_if_exists)
            else:
                #LOG
                print("Aborded, column `%s` exists"%col_name)
    
    ## @brief Add a foreign key
    # @param src_table_name str : The name of the table where we will add the FK
    # @param dst_table_name str : The name of the table the FK will point on
    # @param src_col_name str : The name of the concerned column in the src_table
    # @param dst_col_name str : The name of the concerned column in the dst_table
    def _add_fk(self, src_table_name, dst_table_name, src_col_name, dst_col_name):
        stname = self._idname_escape(src_table_name)
        dtname = self._idname_escape(dst_table_name)
        scname = self._idname_escape(src_col_name)
        dcname = self._idname_escape(dst_col_name)

        fk_name = self._fk_name(src_table_name, dst_table_name)
        
        self._del_fk(src_table_name, dst_table_name)

        self._query("""ALTER TABLE {src_table}
ADD CONSTRAINT {fk_name}
FOREIGN KEY ({src_col}) references {dst_table}({dst_col});""".format(
            fk_name = self._idname_escape(fk_name),
            src_table = stname,
            src_col = scname,
            dst_table = dtname,
            dst_col = dcname
        ))
    
    ## @brief Given a source and a destination table, delete the corresponding FK
    # @param src_table_name str : The name of the table where the FK is
    # @param dst_table_name str : The name of the table the FK point on
    # @warning fails silently
    def _del_fk(self, src_table_name, dst_table_name):
        try:
            self._query("""ALTER TABLE {src_table}
DROP FOREIGN KEY {fk_name}""".format(
                src_table = self._idname_escape(src_table_name),
                fk_name = self._idname_escape(self._fk_name(src_table_name, dst_table_name))
            ))
        except _mysql_exceptions.OperationalError: pass
    
    def _fk_name(self, src_table_name, dst_table_name):
        return "fk_%s_%s"%(src_table_name, dst_table_name)


    ## @brief Generate triggers given a table_name and its columns fieldtypes
    # @param table_name str : Table name
    # @param cols_ftype dict : with col name as key and column fieldtype as value
    # @return None
    def _generate_triggers(self, table_name, cols_ftype):
        colval_l_upd = dict() #param for update trigger
        colval_l_ins = dict() #param for insert trigger

        for cname, cftype in cols_ftype.items():
            if cftype.ftype == 'datetime':
                if cftype.now_on_update:
                    colval_l_upd[cname] = 'NOW()'
                if cftype.now_on_create:
                    colval_l_ins[cname] = 'NOW()'

        self._table_trigger(table_name, 'UPDATE', colval_l_upd)
        self._table_trigger(table_name, 'INSERT', colval_l_ins)
        

    ## @brief Create trigger for a table
    #
    # Primarly designed to create trigger for DATETIME types
    # The method generates triggers of the form
    # 
    # CREATE TRIGGER BEFORE <moment> ON <table_name>
    # FOR EACH ROW SET <for colname, colval in cols_val>
    # NEW.<colname> = <colval>,
    # <endfor>;
    # @param table_name str : The table name
    # @param moment str : can be 'update' or 'insert'
    # @param cols_val dict : Dict with column name as key and column value as value
    # @return None
    def _table_trigger(self, table_name, moment, cols_val):
        trigger_name = self._idname_escape("%s_%s_trig"%(table_name, moment))
        #Try to delete the trigger
        drop_trig = """DROP TRIGGER IF EXISTS {trigger_name};""".format(trigger_name = trigger_name)
        self._query(drop_trig)

        col_val_l = ', '.join([ "NEW.%s = %s"%(self._idname_escape(cname), cval)for cname, cval in cols_val.items() ])
        #Create a trigger if needed
        if len(col_val_l) > 0:
            trig_q = """CREATE TRIGGER {trigger_name} BEFORE {moment} ON {table_name}
FOR EACH ROW SET {col_val_list};""".format(
                trigger_name = trigger_name,
                table_name = self._idname_escape(table_name),
                moment = moment,
                col_val_list = col_val_l
            )
            self._query(trig_q)

    ## @brief Identifier escaping
    def _idname_escape(self, idname):
        if '`' in idname:
            raise ValueError("Invalid name : '%s'"%idname)
        return '`%s`'%idname

    ## @brief Forge a create table query
    # @param table_name str : The name of the table we want to create
    # @param colspecs list : List of tuple (fieldname, EmFieldTypes)
    # @return A MySQL create table query
    #def _create_table_query(self, table_name, colspecs):
    #    pass
    
    ## @brief Forge a drop column query
    # @param table_name str : The name of the concerned table
    # @param colname str : The name of the column we want to drop
    # @return A MySQL drop column query
    def _drop_column_query(self, table_name, colname):
        pass

    ## @brief Forge an add column query
    # @param table_name str : The name of the concerned table
    # @param colspec tuple : A tuple (colname, EmFieldType)
    # @return A MySQL add column query
    def _add_colum_query(self, table_name, colspec):
        pass

    ## @brief Returns column specs from fieldtype
    # @param emfieldtype EmFieldType : An EmFieldType insance
    # @todo escape default value
    def _field_to_specs(self, emfieldtype):
        colspec = ''
        if not emfieldtype.nullable:
            colspec = 'NOT NULL'
        if hasattr(emfieldtype, 'default'):
            colspec += ' DEFAULT '
            if emfieldtype.default is None:
                colspec += 'NULL '
            else:
                colspec += emfieldtype.default #ESCAPE VALUE HERE !!!!

        if emfieldtype.name == 'pk':
            colspec += ' AUTO_INCREMENT'

        return colspec


    ## @brief Given a fieldtype return a MySQL type specifier
    # @param emfieldtype EmFieldType : A fieldtype
    # @return the corresponding MySQL type
    def _field_to_type(self, emfieldtype):
        ftype = emfieldtype.ftype
        
        if ftype == 'char' or ftype == 'str':
            res = "VARCHAR(%d)"%emfieldtype.max_length
        elif ftype == 'text':
            res = "TEXT"
        elif ftype == 'datetime':
            res = "DATETIME"
            # client side workaround for only one column with CURRENT_TIMESTAMP : giving NULL to timestamp that don't allows NULL
            # cf. https://dev.mysql.com/doc/refman/5.0/en/timestamp-initialization.html#idm139961275230400
            # The solution for the migration handler is to create triggers : 
            # CREATE TRIGGER trigger_name BEFORE INSERT ON `my_super_table`
            # FOR EACH ROW SET NEW.my_date_column = NOW();
            # and
            # CREATE TRIGGER trigger_name BEFORE UPDATE ON
            
        elif ftype == 'bool':
            res = "BOOL"
        elif ftype == 'int':
            res = "INT"
        elif ftype == 'rel2type':
            res = "INT"
        else:
            raise ValueError("Unsuported fieldtype ftype : %s"%ftype)

        return res
    
    ## @brief Returns a tuple (pkname, pk_ftype)
    @property
    def _common_field_pk(self):
        for fname, fta in EditorialModel.classtypes.common_fields.items():
            if fta['fieldtype'] == 'pk':
                return (fname, self._common_field_to_ftype(fname))
        return (None, None)
    
    ## @brief Returns a tuple (rel_pkname, rel_ftype)
    # @todo do it
    @property
    def _relation_pk(self):
        return ('id_relation', EditorialModel.fieldtypes.pk.EmFieldType())

    @property
    def _relation_cols(self):
        from_name = EditorialModel.fieldtypes.generic.GenericFieldType.from_name
        return {
            'id_sup': from_name('integer')(),
            'id_sub': from_name('integer')(),
            'rank': from_name('integer')(),
            'depth': from_name('integer')(),
            'nature': from_name('char')(max_lenght=10),
        }

    ## @brief Given a common field name return an EmFieldType instance
    # @param cname str : Common field name
    # @return An EmFieldType instance
    def _common_field_to_ftype(self, cname):
        fta = copy.copy(EditorialModel.classtypes.common_fields[cname])
        fto = EditorialModel.fieldtypes.generic.GenericFieldType.from_name(fta['fieldtype'])
        del(fta['fieldtype'])
        return fto(**fta)
        