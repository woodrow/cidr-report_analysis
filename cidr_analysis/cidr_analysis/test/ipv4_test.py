#!/usr/bin/env python2.6

import unittest
from cidr_analysis import ipv4

class TestDotquadToInt(unittest.TestCase):

    def test_illegal_strings(self):
        illegal_strings = [
            # out of range
            '999.999.999.999',
            '18.1.2.600',
            # illegal characters
            'aaa.aaa.aaa.aaa',
            '18.1.2.xxx',
            # not properly formed (no dots)
            '018001002003',
            'aaaaaaaaaaaa']
        for s in illegal_strings:
            self.assertRaises(ValueError, ipv4.dotquad_to_int, s)

    def test_valid_strings(self):
        self.assertEqual(0, ipv4.dotquad_to_int('0.0.0.0'))
        self.assertEqual(0xFFFFFFFF, ipv4.dotquad_to_int('255.255.255.255'))
        self.assertEqual(2149473372, ipv4.dotquad_to_int('128.30.92.92'))

    def test_backandforth(self):
        for s in ['0.0.0.0', '255.255.255.255', '128.30.92.92']:
            self.assertEqual(s, ipv4.int_to_dotquad(ipv4.dotquad_to_int(s)))


class TestIntToDotquad(unittest.TestCase):

    def test_illegal_ints(self):
        self.assertRaises(ValueError, ipv4.int_to_dotquad, -1)
        self.assertRaises(ValueError, ipv4.int_to_dotquad, 0xFFFFFFFF+1)

    def test_valid_ints(self):
        self.assertEqual('0.0.0.0', ipv4.int_to_dotquad(0))
        self.assertEqual('255.255.255.255', ipv4.int_to_dotquad(0xFFFFFFFF))
        self.assertEqual('128.30.92.92', ipv4.int_to_dotquad(2149473372))

    def test_backandforth(self):
        for i in [0, 0xFFFFFFFF, 2149473372]:
            self.assertEqual(i, ipv4.dotquad_to_int(ipv4.int_to_dotquad(i)))
