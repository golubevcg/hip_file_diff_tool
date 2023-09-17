import unittest
from collections import OrderedDict
from api.node_data import NodeData


class TestNodeData(unittest.TestCase):
    def setUp(self):
        self.node = NodeData(name="TestNode")

    def test_initialization(self):
        self.assertEqual(self.node.name, "TestNode")
        self.assertIsNone(self.node.path)
        self.assertEqual(self.node.type, "")
        self.assertEqual(self.node.icon, "")
        self.assertIsNone(self.node.tag)
        self.assertEqual(self.node.parent_path, "")
        self.assertEqual(self.node.parms, OrderedDict())
        self.assertIsNone(self.node.color)
        self.assertEqual(self.node.alpha, 255)
        self.assertFalse(self.node.is_hatched)

    def test_add_parm(self):
        self.node.add_parm("param1", 123)
        self.assertIn("param1", self.node.parms)
        self.assertEqual(self.node.parms["param1"], 123)

    def test_get_parm_by_name_existing(self):
        self.node.add_parm("param1", 123)
        self.assertEqual(self.node.get_parm_by_name("param1"), 123)

    def test_get_parm_by_name_non_existing(self):
        with self.assertRaises(ValueError):
            self.node.get_parm_by_name("non_existing")

    def test_repr(self):
        self.assertEqual(repr(self.node), "TestNode\n")
