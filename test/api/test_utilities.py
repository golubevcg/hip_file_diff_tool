import unittest
from collections import OrderedDict
from api.utilities import ordered_dict_insert, get_ordered_dict_key_index


class TestUtilities(unittest.TestCase):

    def test_ordered_dict_insert(self):
        od = OrderedDict([('a', 1), ('b', 2), ('c', 3)])
        
        # Insert in the middle
        od_new = ordered_dict_insert(od, 1, 'x', 99)
        self.assertEqual(list(od_new.items()), [('a', 1), ('x', 99), ('b', 2), ('c', 3)])
        
        # Insert at the beginning
        od_new = ordered_dict_insert(od, 0, 'x', 99)
        self.assertEqual(list(od_new.items()), [('x', 99), ('a', 1), ('b', 2), ('c', 3)])
        
        # Insert at the end
        od_new = ordered_dict_insert(od, 3, 'x', 99)
        self.assertEqual(list(od_new.items()), [('a', 1), ('b', 2), ('c', 3), ('x', 99)])
        
        # Insert with negative index (similar to list behavior)
        od_new = ordered_dict_insert(od, -1, 'x', 99)
        self.assertEqual(list(od_new.items()), [('a', 1), ('b', 2), ('x', 99), ('c', 3)])
        
    def test_get_ordered_dict_key_index(self):
        od = OrderedDict([('a', 1), ('b', 2), ('c', 3)])
        
        # Check key index in the middle
        self.assertEqual(get_ordered_dict_key_index(od, 'b'), 1)
        
        # Check key index at the start
        self.assertEqual(get_ordered_dict_key_index(od, 'a'), 0)
        
        # Check key index at the end
        self.assertEqual(get_ordered_dict_key_index(od, 'c'), 2)
        
        # Check for non-existing key
        with self.assertRaises(KeyError):
            get_ordered_dict_key_index(od, 'x')