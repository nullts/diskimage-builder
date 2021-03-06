# Copyright 2013 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

from testtools import TestCase
from fixtures import EnvironmentVariable, TempDir

from diskimage_builder.elements import expand_dependencies
from diskimage_builder.elements import get_elements_dir

data_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'test-elements'))


def _populate_element(element_dir, element_name, element_deps=[]):
        element_home = os.path.join(element_dir, element_name)
        os.mkdir(element_home)
        deps_path = os.path.join(element_home, 'element-deps')
        with open(deps_path, 'w') as deps_file:
            deps_file.write("\n".join(element_deps))


class TestElementDeps(TestCase):

    def setUp(self):
        super(TestElementDeps, self).setUp()
        self.element_dir = self.useFixture(TempDir()).path
        _populate_element(self.element_dir, 'requires-foo', ['foo'])
        _populate_element(self.element_dir, 'foo')
        _populate_element(self.element_dir,
                          'requires-requires-foo',
                          ['requires-foo'])
        _populate_element(self.element_dir, 'self', ['self'])
        _populate_element(self.element_dir, 'circular1', ['circular2'])
        _populate_element(self.element_dir, 'circular2', ['circular1'])

    def test_non_transitive_deps(self):
        result = expand_dependencies(['requires-foo'],
                                     elements_dir=self.element_dir)
        self.assertEquals(set(['requires-foo', 'foo']), result)

    def test_missing_deps(self):
        self.assertRaises(SystemExit, expand_dependencies, ['fake'],
                          self.element_dir)

    def test_transitive_deps(self):
        result = expand_dependencies(['requires-requires-foo'],
                                     elements_dir=self.element_dir)
        self.assertEquals(set(['requires-requires-foo',
                               'requires-foo',
                               'foo']), result)

    def test_no_deps(self):
        result = expand_dependencies(['foo'],
                                     elements_dir=self.element_dir)
        self.assertEquals(set(['foo']), result)

    def test_self(self):
        result = expand_dependencies(['self'],
                                     elements_dir=self.element_dir)
        self.assertEquals(set(['self']), result)

    def test_circular(self):
        result = expand_dependencies(['circular1'],
                                     elements_dir=self.element_dir)
        self.assertEquals(set(['circular1', 'circular2']), result)


class TestElements(TestCase):
    def test_depends_on_env(self):
        self.useFixture(EnvironmentVariable('ELEMENTS_PATH', '/foo/bar'))
        self.assertEquals('/foo/bar', get_elements_dir())

    def test_env_not_set(self):
        self.useFixture(EnvironmentVariable('ELEMENTS_PATH', ''))
        self.assertRaises(Exception, get_elements_dir, ())
