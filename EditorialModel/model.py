#-*- coding: utf-8 -*-

## @package EditorialModel.model
# Contains the class managing and editorial model

import EditorialModel
import DataSource.dummy.migrationhandler
from EditorialModel.backend.dummy_backend import EmBackendDummy
from EditorialModel.classes import EmClass
from EditorialModel.fields import EmField
from EditorialModel.types import EmType
from EditorialModel.exceptions import EmComponentCheckError, EmComponentNotExistError, MigrationHandlerChangeError
import hashlib


## @brief Manages the Editorial Model
class Model(object):

    components_class = [EmClass, EmType, EmField]

    ## Constructor
    #
    # @param backend unknown: A backend object instanciated from one of the classes in the backend module
    # @param migration_handler : A migration handler
    def __init__(self, backend, migration_handler=None):
        if migration_handler is None:
            self.migration_handler = DataSource.dummy.migrationhandler.MigrationHandler()
        elif issubclass(migration_handler.__class__, DataSource.dummy.migrationhandler.MigrationHandler):
            self.migration_handler = migration_handler
        else:
            raise TypeError("migration_handler should be an instance from a subclass of DummyMigrationhandler")
        self.backend = None
        self.set_backend(backend)

        self._components = {'uids': {}, 'EmClass': [], 'EmType': [], 'EmField': []}
        self.load()

    def __hash__(self):
        components_dump = ""
        for _, comp in self._components['uids'].items():
            components_dump += str(hash(comp))
        hashstring = hashlib.new('sha512')
        hashstring.update(components_dump.encode('utf-8'))
        return int(hashstring.hexdigest(), 16)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    @staticmethod
    ## Given a name return an EmComponent child class
    # @param class_name str : The name to identify an EmComponent class
    # @return A python class or False if the class_name is not a name of an EmComponent child class
    def emclass_from_name(class_name):
        for cls in Model.components_class:
            if cls.__name__ == class_name:
                return cls
        return False

    @staticmethod
    ## Given a python class return a name
    # @param em_class : The python class we want the name
    # @return A class name as string or False if cls is not an EmComponent child class
    def name_from_emclass(em_class):
        if em_class not in Model.components_class:
            return False
        return em_class.__name__

    ## Loads the structure of the Editorial Model
    #
    # Gets all the objects contained in that structure and creates a dict indexed by their uids
    # @todo Change the thrown exception when a components check fails
    # @throw ValueError When a component class don't exists
    def load(self):
        datas = self.backend.load()
        for uid, kwargs in datas.items():
            #Store and delete the EmComponent class name from datas
            cls_name = kwargs['component']
            del kwargs['component']

            cls = self.emclass_from_name(cls_name)

            if cls:
                kwargs['uid'] = uid
                # create a dict for the component and one indexed by uids, store instanciated component in it
                self._components['uids'][uid] = cls(model=self, **kwargs)
                self._components[cls_name].append(self._components['uids'][uid])
            else:
                raise ValueError("Unknow EmComponent class : '" + cls_name + "'")

        #Sorting by rank
        for component_class in Model.components_class:
            self.sort_components(component_class)

        #Check integrity
        loaded_comps = [(uid, component) for uid, component in self._components['uids'].items()]
        for uid, component in loaded_comps:
            try:
                component.check()
            except EmComponentCheckError as exception_object:
                raise EmComponentCheckError("The component with uid %d is not valid. Check returns the following error : \"%s\"" % (uid, str(exception_object)))
            #Everything is done. Indicating that the component initialisation is over
            component.init_ended()

    ## Saves data using the current backend
    # @param filename str | None : if None use the current backend file (provided at backend instanciation)
    def save(self, filename=None):
        return self.backend.save(self, filename)

    ## Given a EmComponent child class return a list of instances
    # @param cls EmComponent|str : A python class
    # @return a list of instances or False if the class is not an EmComponent child
    # @todo better implementation
    def components(self, cls=None):
        if isinstance(cls, str):
            cls = self.emclass_from_name(cls)
            if not cls:
                return False
        if cls is None:
            return [self.component(uid) for uid in self._components['uids']]
        key_name = self.name_from_emclass(cls)
        return False if key_name is False else self._components[key_name]

    ## Return an EmComponent given an uid
    # @param uid int : An EmComponent uid
    # @return The corresponding instance or False if uid don't exists
    def component(self, uid):
        return False if uid not in self._components['uids'] else self._components['uids'][uid]

    ## @brief Search in all the editorial model for a component with a specific name
    # @param name str : the searched name
    # @param comp_cls str|EmComponent : filter on component type (see components() method)
    # @return a list of component with a specific name
    def component_from_name(self, name, comp_cls=None):
        if comp_cls == EmField or comp_cls == 'EmField':
            res = list()
            for field, fieldname in [(f, f.name) for f in self.components('EmField')]:
                if fieldname == name:
                    res.append(field)
            return res

        for comp, compname in [(c, c.name) for c in self.components(comp_cls)]:
            if compname == name:
                return comp

        return False

    ## Sort components by rank in Model::_components
    # @param component_class pythonClass : The type of components to sort
    # @throw AttributeError if emclass is not valid
    # @warning disabled the test on component_class because of EmField new way of working
    def sort_components(self, component_class):
        #if component_class not in self.components_class:
        #    raise AttributeError("Bad argument emclass : '" + str(component_class) + "', excpeting one of " + str(self.components_class))

        self._components[self.name_from_emclass(component_class)] = sorted(self.components(component_class), key=lambda comp: comp.rank)

    ## Return a new uid
    # @return a new uid
    def new_uid(self):
        used_uid = [int(uid) for uid in self._components['uids'].keys()]
        return sorted(used_uid)[-1] + 1 if len(used_uid) > 0 else 1

    ## Create a component from a component type and datas
    #
    # @note if datas does not contains a rank the new component will be added last
    # @note datas['rank'] can be an integer or two specials strings 'last' or 'first'
    #
    # @warning The uid parameter is designed to be used only by Model.load()
    # @param uid int|None : If given, don't generate a new uid
    # @param component_type str : a component type ( component_class, component_fieldgroup, component_field or component_type )
    # @param datas dict : the options needed by the component creation
    # @return The created EmComponent
    # @throw ValueError if datas['rank'] is not valid (too big or too small, not an integer nor 'last' or 'first' )
    # @todo Handle a raise from the migration handler
    # @todo Transform the datas arg in **datas ?
    def create_component(self, component_type, datas, uid=None):
        if not (uid is None) and (not isinstance(uid, int) or uid <= 0 or uid in self._components['uids']):
            raise ValueError("Invalid uid provided : %s" % repr(uid))

        if component_type not in [n for n in self._components.keys() if n != 'uids']:
            raise ValueError("Invalid component_type rpovided")
        else:
            em_obj = self.emclass_from_name(component_type)

        rank = 'last'
        if 'rank' in datas and not datas['rank'] is None:
            rank = datas['rank']
            del datas['rank']

        datas['uid'] = uid if uid else self.new_uid()
        em_component = em_obj(model=self, **datas)

        em_component.rank = em_component.get_max_rank() + 1  # Inserting last by default

        self._components['uids'][em_component.uid] = em_component
        self._components[component_type].append(em_component)

        if rank != 'last':
            em_component.set_rank(1 if rank == 'first' else rank)

        #everything done, indicating that initialisation is over
        em_component.init_ended()

        #register the creation in migration handler
        try:
            self.migration_handler.register_change(self, em_component.uid, None, em_component.attr_dump())
        except MigrationHandlerChangeError as exception_object:
            #Revert the creation
            self.components(em_component.__class__).remove(em_component)
            del self._components['uids'][em_component.uid]
            raise exception_object

        self.migration_handler.register_model_state(self, hash(self))

        if uid is None:
            #Checking the component
            em_component.check()
            if component_type == 'EmClass':
                # !!! If uid is not None it means that we shouldn't create components automatically !!!
                self.add_default_class_fields(em_component.uid)

        return em_component

    ## @brief Create a new EmClass
    def add_class(self, name, classtype, string=None, help_text=None, date_update = None, date_create = None, rank = None):
        datas = locals()
        del(datas['self'])
        return self.create_component('EmClass', datas)
    
    ## @brief Create a new EmType
    def add_type(self, name, emclass, fields_list = None, superiors_list = None, icon='0', sortcolumn='rank', string = None, help_text = None, date_update = None, date_create = None, rank = None):
        datas = locals()
        del(datas['self'])
        emclass = datas['emclass']
        del(datas['emclass'])
        datas['class_id'] = emclass.uid if isinstance(emclass, EmClass) else emclass
        return self.create_component('EmType', datas)
    
    ## @brief Add a new EmField
    def add_field(self, name, emclass, fieldtype, **kwargs):
        kwargs['name'] = name
        kwargs['fieldtype'] = fieldtype
        kwargs['class_id'] = emclass.uid if isinstance(emclass, EmClass) else emclass
        return self.create_component('EmField', kwargs)

    ## @brief Add to a class (if not exists) the default fields
    #
    # @param class_uid int : An EmClass uid
    # @throw ValueError if class_uid in not an EmClass uid
    def add_default_class_fields(self, class_uid):
        if class_uid not in self._components['uids']:
            raise ValueError("The uid '%d' don't exists" % class_uid)
        emclass = self._components['uids'][class_uid]
        if not isinstance(emclass, EditorialModel.classes.EmClass):
            raise ValueError("The uid '%d' is not an EmClass uid" % class_uid)

        """
        fgroup_name = EmClass.default_fieldgroup

        if fgroup_name not in [fg.name for fg in emclass.fieldgroups() ]:
            #Creating the default fieldgroup if not existing
            fg_datas = { 'name' : fgroup_name, 'class_id': emclass.uid }
            fgroup = self.create_component('EmFieldGroup', fg_datas)
            fgid = fgroup.uid
        else:
            for fg in emclass.fieldgroups():
                if fg.name == fgroup_name:
                    fgid = fg.uid
                    break
        """

        default_fields = emclass.default_fields_list()
        for fname, fdatas in default_fields.items():
            if not (fname in [f.name for f in emclass.fields()]):
                #Adding the field
                fdatas['name'] = fname
                fdatas['class_id'] = class_uid
                self.create_component('EmField', fdatas)

    ## Delete a component
    # @param uid int : Component identifier
    # @throw EmComponentNotExistError
    # @todo unable uid check
    # @todo Handle a raise from the migration handler
    def delete_component(self, uid):
        em_component = self.component(uid)
        if not em_component:
            raise EmComponentNotExistError()

        if em_component.delete_check():
            #register the deletion in migration handler
            self.migration_handler.register_change(self, uid, self.component(uid).attr_dump(), None)

            # delete internal lists
            self._components[self.name_from_emclass(em_component.__class__)].remove(em_component)
            del self._components['uids'][uid]

            #Register the new EM state
            self.migration_handler.register_model_state(self, hash(self))
            return True

        return False

    ## Changes the current backend
    #
    # @param backend unknown: A backend object
    def set_backend(self, backend):
        if issubclass(backend.__class__, EmBackendDummy):
            self.backend = backend
        else:
            raise TypeError('Backend should be an instance of a EmBackednDummy subclass')

    ## Returns a list of all the EmClass objects of the model
    def classes(self):
        return list(self._components[self.name_from_emclass(EmClass)])

    ## Use a new migration handler, re-apply all the ME to this handler
    #
    # @param new_mh MigrationHandler: A migration_handler object
    # @warning : if a relational-attribute field (with 'rel_field_id') comes before it's relational field (with 'rel_to_type_id'), this will blow up
    def migrate_handler(self, new_mh):
        new_me = Model(EmBackendDummy(), new_mh)
        relations = {'fields_list': [], 'superiors_list': []}

        # re-create component one by one, in components_class[] order
        for cls in self.components_class:
            for component in self.components(cls):
                component_type = self.name_from_emclass(cls)
                component_dump = component.attr_dump()
                # Save relations between component to apply them later
                for relation in relations.keys():
                    if relation in component_dump and component_dump[relation]:
                        relations[relation].append((component.uid, component_dump[relation]))
                        del component_dump[relation]
                new_me.create_component(component_type, component_dump, component.uid)

        # apply selected field  to types
        for fields_list in relations['fields_list']:
            uid, fields = fields_list
            for field_id in fields:
                new_me.component(uid).select_field(new_me.component(field_id))

        # add superiors to types
        for superiors_list in relations['superiors_list']:
            uid, sup_list = superiors_list
            for nature, superiors_uid in sup_list.items():
                for superior_uid in superiors_uid:
                    new_me.component(uid).add_superior(new_me.component(superior_uid), nature)

        del new_me

        self.migration_handler = new_mh
