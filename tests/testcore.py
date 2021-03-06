# -*- coding: utf-8 -*-

""" Unit test for pyKwalify - Core """

# python std lib
import os
import unittest

# 3rd party imports
from testfixtures import compare

# pyKwalify imports
import pykwalify
from pykwalify.core import Core
from pykwalify.errors import PyKwalifyExit, UnknownError, FileNotAccessible, OptionError, NotImplemented, ParseFailure, SchemaError, CoreError, RuleError


class TestCore(unittest.TestCase):

    def setUp(self):
        pykwalify.partial_schemas = {}

    def f(self, *args):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), "files", *args)

    def testCoreDataMode(self):
        Core(source_data=3.14159,  schema_data={"type": "number"}).validate()
        Core(source_data=3.14159,  schema_data={"type": "float"}).validate()
        Core(source_data=3,        schema_data={"type": "int"}).validate()
        Core(source_data=True,     schema_data={"type": "bool"}).validate()
        Core(source_data="foobar", schema_data={"type": "str"}).validate()
        Core(source_data="foobar", schema_data={"type": "text"}).validate()
        Core(source_data="foobar", schema_data={"type": "any"}).validate()

        with self.assertRaises(SchemaError):
            Core(source_data="abc",  schema_data={"type": "number"}).validate()

        with self.assertRaises(SchemaError):
            Core(source_data=3, schema_data={"type": "float"}).validate()

        with self.assertRaises(SchemaError):
            Core(source_data=3.14159, schema_data={"type": "int"}).validate()

        with self.assertRaises(SchemaError):
            Core(source_data=1337, schema_data={"type": "bool"}).validate()

        with self.assertRaises(SchemaError):
            Core(source_data=1, schema_data={"type": "str"}).validate()

        with self.assertRaises(SchemaError):
            Core(source_data=True, schema_data={"type": "text"}).validate()

        with self.assertRaises(SchemaError):
            Core(source_data=dict, schema_data={"type": "any"}).validate()

    def test_multi_file_support(self):
        """
        This should test that multiple files is supported correctly
        """
        pass_tests = [
            # Test that include directive can be used at top level of the schema
            ([self.f("33a.yaml"), self.f("33b.yaml")], self.f("33c.yaml"), {'sequence': [{'include': 'fooone'}], 'type': 'seq'}),
            # # This test that include directive works inside sequence
            # ([self.f("33a.yaml"), self.f("33b.yaml")], self.f("33c.yaml"), {'sequence': [{'include': 'fooone'}], 'type': 'seq'}),
            # This test recursive schemas
            ([self.f("35a.yaml"), self.f("35b.yaml")], self.f("35c.yaml"), {'sequence': [{'include': 'fooone'}], 'type': 'seq'})
        ]

        failing_tests = [
            # Test include inside partial schema
            ([self.f("34a.yaml"), self.f("34b.yaml")], self.f("34c.yaml"), SchemaError, ['No partial schema found for name : fooonez : Existing partial schemas: fooone, foothree, footwo'])
        ]

        for passing_test in pass_tests:
            try:
                c = Core(source_file=passing_test[1], schema_files=passing_test[0])
                c.validate()
                compare(c.validation_errors, [], prefix="No validation errors should exist...")
            except Exception as e:
                print("ERROR RUNNING FILE: {} : {}".format(passing_test[0], passing_test[1]))
                raise e

            # This serve as an extra schema validation that tests more complex structures then testrule.py do
            compare(c.root_rule._schema_str, passing_test[2], prefix="Parsed rules is not correct, something have changed...")

        for failing_test in failing_tests:
            with self.assertRaises(failing_test[2], msg="Test files: {} : {}".format(", ".join(failing_test[0]), failing_test[1])):
                c = Core(schema_files=failing_test[0], source_file=failing_test[1])
                c.validate()

            if not c.validation_errors:
                raise AssertionError("No validation_errors was raised...")

            compare(sorted(c.validation_errors), sorted(failing_test[3]), prefix="Wrong validation errors when parsing files : {} : {}".format(failing_test[0], failing_test[1]))

    def testCore(self):
        # These tests should pass with no exception raised
        pass_tests = [
            # Test sequence with only string values
            ("1a.yaml", "1b.yaml", {'sequence': [{'type': 'str'}], 'type': 'seq'}),
            # Test sequence where the only valid items is integers
            ("3a.yaml", "3b.yaml", {'sequence': [{'type': 'int'}], 'type': 'seq'}),
            # Test sequence with only booleans
            ("4a.yaml", "4b.yaml", {'sequence': [{'type': 'bool'}], 'type': 'seq'}),
            # Test mapping with different types of data and some extra conditions
            ("8a.yaml", "8b.yaml", {'mapping': {'age': {'type': 'int'}, 'birth': {'type': 'str'}, 'email': {'pattern': '.+@.+', 'type': 'str'}, 'name': {'required': True, 'type': 'str'}}, 'type': 'map'}),
            # Test sequence with mapping with valid mapping
            ("10a.yaml", "10b.yaml", {'sequence': [{'mapping': {'email': {'type': 'str'}, 'name': {'required': True, 'type': 'str'}}, 'type': 'map'}], 'type': 'seq'}),
            # Test mapping with sequence with mapping and valid data
            ("12a.yaml", "12b.yaml", {'mapping': {'company': {'required': True, 'type': 'str'}, 'email': {'type': 'str'}, 'employees': {'sequence': [{'mapping': {'code': {'required': True, 'type': 'int'}, 'email': {'type': 'str'}, 'name': {'required': True, 'type': 'str'}}, 'type': 'map'}], 'type': 'seq'}}, 'type': 'map'}),
            # Test most of the implemented functions
            ("14a.yaml", "14b.yaml", {'sequence': [{'mapping': {'age': {'range': {'max': 30, 'min': 18}, 'type': 'int'}, 'birth': {'type': 'str'}, 'blood': {'enum': ['A', 'B', 'O', 'AB'], 'type': 'str'}, 'deleted': {'type': 'bool'}, 'email': {'pattern': '.+@.+', 'required': True, 'type': 'str'}, 'memo': {'type': 'any'}, 'name': {'required': True, 'type': 'str'}, 'password': {'range': {'max': 16, 'min': 8}, 'type': 'str'}}, 'type': 'map'}], 'type': 'seq'}),
            # This will test the unique constraint
            ("16a.yaml", "16b.yaml", {'sequence': [{'mapping': {'email': {'type': 'str'}, 'groups': {'sequence': [{'type': 'str', 'unique': True}], 'type': 'seq'}, 'name': {'required': True, 'type': 'str', 'unique': True}}, 'required': True, 'type': 'map'}], 'type': 'seq'}),
            #
            ("18a.yaml", "18b.yaml", {'mapping': {'datasources': {'allowempty': True, 'type': 'map'}}, 'type': 'map'}),
            #
            ("19a.yaml", "19b.yaml", {'mapping': {'datasources': {'allowempty': True, 'mapping': {'test1': {'type': 'str'}}, 'type': 'map'}}, 'type': 'map'}),
            #
            ("20a.yaml", "20b.yaml", {'type': 'float'}),
            # This tests number validation rule
            ("21a.yaml", "21b.yaml", {'sequence': [{'type': 'number'}], 'type': 'seq'}),
            # This test the text validation rule
            ("23a.yaml", "23b.yaml", {'sequence': [{'type': 'text'}], 'type': 'seq'}),
            # This test the text validation rule
            ("24a.yaml", "25b.yaml", {'sequence': [{'type': 'any'}], 'type': 'seq'}),
            #
            ("26a.yaml", "26b.yaml", {'type': 'any'}),
            #
            ("30a.yaml", "30b.yaml", {'sequence': [{'mapping': {'foobar': {'mapping': {'opa': {'type': 'bool'}}, 'type': 'map'}, 'media': {'type': 'int'}, 'regex;[mi.+]': {'sequence': [{'type': 'str'}], 'type': 'seq'}, 'regex;[mo.+]': {'sequence': [{'type': 'bool'}], 'type': 'seq'}}, 'matching-rule': 'any', 'type': 'map'}], 'type': 'seq'}),
            # This test that a regex that will compile
            ("31a.yaml", "31b.yaml", {'mapping': {'regex;mi.+': {'sequence': [{'type': 'str'}], 'type': 'seq'}}, 'matching-rule': 'any', 'type': 'map'}),
            # Test that type can be set to 'None' and it will validate ok
            ("37a.yaml", "37b.yaml", {'mapping': {'streams': {'required': True, 'sequence': [{'mapping': {'name': {'required': True, 'type': 'none'}, 'sampleRateMultiple': {'required': True, 'type': 'int'}}, 'type': 'map'}], 'type': 'seq'}}, 'type': 'map'}),
            # Test that range validates with map
            ("40a.yaml", "40b.yaml", {'mapping': {'foo': {'type': 'str'}, 'streams': {'type': 'str'}}, 'range': {'max': 3, 'min': 1}, 'type': 'map'}),
            # Test that range validates with seq
            ("41a.yaml", "41b.yaml", {'range': {'max': 3, 'min': 1}, 'sequence': [{'type': 'str'}], 'type': 'seq'}),
        ]

        # These tests are designed to fail with some exception raised
        fail_tests = [
            # Test sequence with defined string content type but data only has integers
            ("2a.yaml", "2b.yaml", SchemaError, ["Value: 1 is not of type 'str' : /0",
                                                 "Value: 2 is not of type 'str' : /1",
                                                 "Value: 3 is not of type 'str' : /2"]),
            # Test sequence with defined string content type but data only has booleans
            ("5a.yaml", "5b.yaml", SchemaError, ["Value: True is not of type 'str' : /0",
                                                 "Value: False is not of type 'str' : /1"]),
            # Test sequence with defined booleans but with one integer
            ("6a.yaml", "6b.yaml", SchemaError, ["Value: 1 is not of type 'bool' : /2"]),
            # Test sequence with strings and and lenght on each string
            ("7a.yaml", "7b.yaml", SchemaError, ['scalar.range.toolarge : 5 < 6 : /2']),
            # Test mapping that do not work
            ("9a.yaml", "8b.yaml", SchemaError, ["Value: twnty is not of type 'int' : /age",
                                                 'pattern.unmatch : .+@.+ --> foo(at)mail.com : /email']),
            # Test sequence with mapping with missing required key
            ("11a.yaml", "10b.yaml", SchemaError, ['required.nokey : name : /1',
                                                   'key.undefined : naem : /1',
                                                   'key.undefined : mail : /2']),
            # Test mapping with sequence with mapping and invalid data
            ("13a.yaml", "12b.yaml", SchemaError, ["Value: A101 is not of type 'int' : /employees/0/code",
                                                   'key.undefined : mail : /employees/1']),
            # TODO: write
            ("15a.yaml", "14b.yaml", SchemaError, ["Value: twenty is not of type 'int' : /0/age",
                                                   'pattern.unmatch : .+@.+ --> foo(at)mail.com : /0/email',
                                                   'enum.notexists : a : /0/blood',
                                                   'required.nokey : name : /1',
                                                   'key.undefined : given-name : /1',
                                                   'key.undefined : family-name : /1',
                                                   'scalar.range.toosmall : 8 > 6 : /0/password',
                                                   'scalar.range.toosmall : 18 > 15 : /1/age',
                                                   'scalar.range.toosmall : 18 > 6 : /0/age']),
            # TODO: The reverse unique do not currently work proper # This will test the unique constraint but should fail
            ("17a.yaml", "16b.yaml", SchemaError, ['value.notunique :: value: foo : /0/groups/3 : /0/groups/0']),
            # This tests number validation rule with wrong data
            ("22a.yaml", "22b.yaml", SchemaError, ["Value: abc is not of type 'number' : /2"]),
            # This test the text validation rule with wrong data
            ("24a.yaml", "24b.yaml", SchemaError, ["Value: True is not of type 'text' : /3"]),
            # This test that typechecking works when value in map is None
            ("36a.yaml", "36b.yaml", SchemaError, ["Value: None is not of type 'str' : /streams/0/name"]),
            # Test that range validates on 'map' raise correct error
            ("38a.yaml", "38b.yaml", SchemaError, ['map.range.toosmall : 2 > 1 : /streams']),
            # Test that range validates on 'seq' raise correct error
            ("39a.yaml", "39b.yaml", SchemaError, ['seq.range.toolarge : 2 < 3 : '])
        ]

        for passing_test in pass_tests:
            try:
                c = Core(source_file=self.f(passing_test[0]), schema_files=[self.f(passing_test[1])])
                c.validate()
                compare(c.validation_errors, [], prefix="No validation errors should exist...")
            except Exception as e:
                print("ERROR RUNNING FILES: {} : {}".format(passing_test[0], passing_test[1]))
                raise e

            # This serve as an extra schema validation that tests more complex structures then testrule.py do
            compare(c.root_rule._schema_str, passing_test[2], prefix="Parsed rules is not correct, something have changed... files : {} : {}".format(passing_test[0], passing_test[1]))

        for failing_test in fail_tests:
            try:
                c = Core(source_file=self.f(failing_test[0]), schema_files=[self.f(failing_test[1])])
                c.validate()
            except failing_test[2]:
                pass  # OK
            else:
                raise AssertionError("Exception {} not raised as expected... FILES: {} : {}".format(failing_test[2], failing_test[0], failing_test[1]))

            compare(sorted(c.validation_errors), sorted(failing_test[3]), prefix="Wrong validation errors when parsing files : {} : {}".format(failing_test[0], failing_test[1]))
