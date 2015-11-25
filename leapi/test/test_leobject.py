"""
    Tests for _LeObject and LeObject
"""

import unittest
from unittest import TestCase
from unittest.mock import patch

import EditorialModel
import leapi
import leapi.test.utils
from leapi.leobject import _LeObject

## Testing methods that need the generated code
class LeObjectTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        """ Write the generated code in a temporary directory and import it """
        cls.tmpdir = leapi.test.utils.tmp_load_factory_code()
    @classmethod
    def tearDownClass(cls):
        """ Remove the temporary directory created at class setup """
        leapi.test.utils.cleanup(cls.tmpdir)

    def test_uid2leobj(self):
        """ Testing _Leobject.uid2leobj() """
        import dyncode
        for i in dyncode.LeObject._me_uid.keys():
            cls = dyncode.LeObject.uid2leobj(i)
            if leapi.letype.LeType in cls.__bases__:
                self.assertEqual(i, cls._type_id)
            elif leapi.leclass.LeClass in cls.__bases__:
                self.assertEqual(i, cls._class_id)
            else:
                self.fail("Bad value returned : '%s'"%cls)
        i=10
        while i in dyncode.LeObject._me_uid.keys():
            i+=1
        with self.assertRaises(KeyError):
            dyncode.LeObject.uid2leobj(i)
    
    @unittest.skip("Obsolete but may be usefull for datasources tests")
    def test_prepare_targets(self):
        """ Testing _prepare_targets() method """
        from dyncode import Publication, Numero, LeObject

        test_v = {
            (None, None) : (None, None),

            (Publication, Numero): (Publication, Numero),
            (Publication, None): (Publication, None),
            (None, Numero): (Publication, Numero),

            (Publication,'Numero'): (Publication, Numero),
            ('Publication', Numero): (Publication, Numero),

            ('Publication', 'Numero'): (Publication, Numero),
            ('Publication', None): (Publication, None),
            (None, 'Numero'): (Publication, Numero),
        }

        for (leclass, letype), (rleclass, rletype) in test_v.items():
            self.assertEqual((rletype,rleclass), LeObject._prepare_targets(letype, leclass))

    @unittest.skip("Obsolete but may be usefull for datasources tests")
    def test_invalid_prepare_targets(self):
        """ Testing _prepare_targets() method with invalid arguments """
        from dyncode import Publication, Numero, LeObject, Personnes
        
        test_v = [
            ('',''),
            (Personnes, Numero),
            (leapi.leclass.LeClass, Numero),
            (Publication, leapi.letype.LeType),
            ('foobar', Numero),
            (Publication, 'foobar'),
            (Numero, Numero),
            (Publication, Publication),
            (None, Publication),
            ('foobar', 'foobar'),
            (42,1337),
            (type, Numero),
            (LeObject, Numero),
            (LeObject, LeObject),
            (Publication, LeObject),
        ]

        for (leclass, letype) in test_v:
            with self.assertRaises(ValueError):
                LeObject._prepare_targets(letype, leclass)
    @unittest.skip("Obsolete, the method should be deleted soon")
    def test_check_fields(self):
        """ Testing the _check_fields() method """
        from dyncode import Publication, Numero, LeObject, Personnes
        
        #Valid fields given
        LeObject._check_fields(None, Publication, Publication._fieldtypes.keys())
        LeObject._check_fields(Numero, None, Numero._fields)

        #Specials fields
        LeObject._check_fields(Numero, Publication,  ['lodel_id'])
        #Common fields
        LeObject._check_fields(None, None, EditorialModel.classtypes.common_fields.keys())

        #Invalid fields
        with self.assertRaises(leapi.leobject.LeObjectQueryError):
            LeObject._check_fields(None, None, Numero._fields)


class LeObjectMockDatasourceTestCase(TestCase):
    """ Testing _LeObject using a mock on the datasource """

    @classmethod
    def setUpClass(cls):
        """ Write the generated code in a temporary directory and import it """
        cls.tmpdir = leapi.test.utils.tmp_load_factory_code()
    @classmethod
    def tearDownClass(cls):
        """ Remove the temporary directory created at class setup """
        leapi.test.utils.cleanup(cls.tmpdir)
    
    @unittest.skip("Wait reimplementation in lecrud")
    @patch('leapi.datasources.dummy.DummyDatasource.insert')
    def test_insert(self, dsmock):
        from dyncode import Publication, Numero, LeObject
        ndatas = [
            [{'titre' : 'FooBar'}],
            [{'titre':'hello'},{'titre':'world'}],
        ]
        for ndats in ndatas:
            LeObject.insert(Numero,ndats)
            dsmock.assert_called_once_with(Numero, Publication, ndats)
            dsmock.reset_mock()

            LeObject.insert('Numero',ndats)
            dsmock.assert_called_once_with(Numero, Publication, ndats)
            dsmock.reset_mock()

    @unittest.skip("Wait reimplementation in lecrud")
    @patch('leapi.datasources.dummy.DummyDatasource.update')
    def test_update(self, dsmock):
        from dyncode import Publication, Numero, LeObject

        args = [
            (   ['lodel_id = 1'],
                {'titre':'foobar'},
                [('lodel_id','=','1')],
                []
            ),
            (   ['superior.parent in [1,2,3,4,5,6]', 'titre != "FooBar"'],
                {'titre':'FooBar'},
                [( 'titre','!=','"FooBar"')],
                [( (leapi.leobject.REL_SUP, 'parent') ,' in ', '[1,2,3,4,5,6]')]
            ),
        ]

        for filters, datas, ds_filters, ds_relfilters in args:
            LeObject.update(Numero, filters, datas)
            dsmock.assert_called_once_with(Numero, Publication, ds_filters, ds_relfilters, datas)
            dsmock.reset_mock()

            LeObject.update('Numero', filters, datas)
            dsmock.assert_called_once_with(Numero, Publication, ds_filters, ds_relfilters, datas)
            dsmock.reset_mock()
    
    @unittest.skip("Wait reimplementation in lecrud")
    @patch('leapi.datasources.dummy.DummyDatasource.delete')
    def test_delete(self, dsmock):
        from dyncode import Publication, Numero, LeObject

        args = [
            (
                ['lodel_id=1'],
                [('lodel_id', '=', '1')],
                []
            ),
            (
                ['subordinate.parent not in [1,2,3]', 'titre = "titre nul"'],
                [('titre','=', '"titre nul"')],
                [( (leapi.leobject.REL_SUB, 'parent'), ' not in ', '[1,2,3]')]
            ),
        ]

        for filters, ds_filters, ds_relfilters in args:
            LeObject.delete(Numero, filters)
            dsmock.assert_called_once_with(Numero, Publication, ds_filters, ds_relfilters)
            dsmock.reset_mock()

            LeObject.delete('Numero', filters)
            dsmock.assert_called_once_with(Numero, Publication, ds_filters, ds_relfilters)
            dsmock.reset_mock()
        
    @patch('leapi.datasources.dummy.DummyDatasource.get')
    @unittest.skip('Dummy datasource doesn\'t fit anymore')
    def test_get(self, dsmock):
        from dyncode import Publication, Numero, LeObject
        
        args = [
            (
                ['lodel_id', 'superior.parent'],
                ['titre != "foobar"'],

                ['lodel_id', (leapi.leobject.REL_SUP, 'parent')],
                [('titre','!=', '"foobar"')],
                []
            ),
            (
                ['lodel_id', 'titre', 'superior.parent', 'subordinate.translation'],
                ['superior.parent in  [1,2,3,4,5]'],

                ['lodel_id', 'titre', (leapi.leobject.REL_SUP,'parent'), (leapi.leobject.REL_SUB, 'translation')],
                [],
                [( (leapi.leobject.REL_SUP, 'parent'), ' in ', '[1,2,3,4,5]')]
            ),
            (
                [],
                [],

                Numero._fields,
                [],
                []
            ),
        ]

        for field_list, filters, fl_ds, filters_ds, rfilters_ds in args:
            LeObject.get(filters, field_list, Numero)
            dsmock.assert_called_with(Publication, Numero, fl_ds, filters_ds, rfilters_ds)
            dsmock.reset_mock()

    @patch('leapi.datasources.dummy.DummyDatasource.get')
    @unittest.skip('Dummy datasource doesn\'t fit anymore')
    def test_get_incomplete_target(self, dsmock):
        """ Testing LeObject.get() method with partial target specifier """
        from dyncode import Publication, Numero, LeObject

        args = [
            (
                ['lodel_id'],
                [],
                None,
                None,

                ['lodel_id', 'type_id'],
                [],
                [],
                None,
                None
            ),
            (
                [],
                [],
                None,
                None,

                list(EditorialModel.classtypes.common_fields.keys()),
                [],
                [],
                None,
                None
            ),
            (
                ['lodel_id'],
                [],
                None,
                Publication,

                ['lodel_id', 'type_id'],
                [],
                [],
                None,
                Publication
            ),
            (
                [],
                [],
                Numero,
                None,

                Numero._fields,
                [],
                [],
                Numero,
                Publication
            ),
        ]

        for field_list, filters, letype, leclass, fl_ds, filters_ds, rfilters_ds, letype_ds, leclass_ds in args:
            LeObject.get(filters, field_list, letype, leclass)
            dsmock.assert_called_with(leclass_ds, letype_ds, fl_ds, filters_ds, rfilters_ds)
            dsmock.reset_mock()

