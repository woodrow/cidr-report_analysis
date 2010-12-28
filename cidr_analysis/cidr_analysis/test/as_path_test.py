#!/usr/bin/env python2.6

import unittest
from cidr_analysis import as_path

class TestExtractASN(unittest.TestCase):

    def test_illegal_brackets(self):
        self.assertRaises(ValueError, as_path.extract_asn, '(123,345)')
        self.assertRaises(ValueError, as_path.extract_asn, '[123,345]')

    def test_illegal_string(self):
        self.assertRaises(ValueError, as_path.extract_asn, '123 {345,456}')
        self.assertRaises(ValueError, as_path.extract_asn, '123i')

    def test_valid_single_as(self):
        self.assertEqual(123, as_path.extract_asn('123'))
        self.assertEqual(123, as_path.extract_asn(' 123 '))
        self.assertEqual(345, as_path.extract_asn('{345}'))
        self.assertEqual(345, as_path.extract_asn('{ 345 }'))

    def test_multiple_as_set(self):
        self.assertEqual(0, as_path.extract_asn('{123,345}'))
        self.assertEqual(0, as_path.extract_asn('{123, 345}'))


class TestDeprependASPath(unittest.TestCase):

    def test_prepended(self):
        self.assertEqual([1],as_path.deprepend_as_path([1]*100))
        self.assertEqual([1, 2, 3, 4, 5],
            as_path.deprepend_as_path([1, 1, 2, 3, 3, 4, 5, 5]))
        self.assertEqual([1, 2, 3, 1, 2, 1],
            as_path.deprepend_as_path([1, 1, 2, 3, 3, 1, 1, 1, 2, 1]))

    def test_unprepended(self):
        path = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.assertEqual(path, as_path.deprepend_as_path(path))


class TestDeloopASPath(unittest.TestCase):

    def test_nonloops(self):
        path = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.assertEqual(path, as_path.deloop_as_path(path))

    def test_simple_loops(self):
        # from straightenRV manpage
        self.assertEqual([1, 2, 5], as_path.deloop_as_path([1, 2, 3, 2, 5]))

    def test_complex_loops(self):
        # from straightenRV manpage
        self.assertEqual(None, as_path.deloop_as_path([1, 2, 3, 2, 3, 4]))
        self.assertEqual(None, as_path.deloop_as_path([1, 2, 3, 2, 4, 5, 4]))


class TestNormalizeASPath(unittest.TestCase):

    def test_private_asns(self):
        path = ['1', '65535', '2', '{65400}', '65000', '{3}']
        norm_path = [1, 2, 3]
        self.assertEqual(norm_path, as_path.normalize_as_path(path))

    def test_straightenrv_example(self):
        path = ['0', '4006', '209', '15254', '15251', '15254', '15254',
            '15254', '15254']
        norm_path = [0, 4006, 209, 15254]
        self.assertEqual(norm_path, as_path.normalize_as_path(path))
        # and also with ints
        path = [0, 4006, 209, 15254, 15251, 15254, 15254, 15254, 15254]
        self.assertEqual(norm_path, as_path.normalize_as_path(path))

    def test_composed_cases(self):
        path = ['1','1','{1}', '2', '3', '3', '2', '3', '{2}', '{2,3}']
        norm_path = [1, 2, 0]
        self.assertEqual(norm_path, as_path.normalize_as_path(path))
        path = ['1','1','{1}', '2', '3', '3', '2', '3', '{3}', '{2,3}']
        norm_path = None
        self.assertEqual(norm_path, as_path.normalize_as_path(path))
        path = ['{2,3}', '{3,4}', '{4,5}', '{5,6}']
        norm_path = [0]
        self.assertEqual(norm_path, as_path.normalize_as_path(path))
