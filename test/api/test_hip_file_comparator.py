import unittest
from unittest.mock import patch, Mock

from api.comparators.hip_comparator import HipFileComparator
from api.utilities import COLORS
from api.data.item_data import ItemState
from api.data.node_data import NodeData
from api.data.param_data import ParamData
import hou


class TestHipFileComparator(unittest.TestCase):
    SOURCE_HIP_FILE = "test/fixtures/billowy_smoke_source.hipnc"
    TARGET_HIP_FILE = "test/fixtures/billowy_smoke_source_edited.hipnc"

    def setUp(self):
        # Create some dummy paths
        self.invalid_ext_path = "test/fixtures/invalid_ext_file.txt"
        self.nonexistent_path = "test/fixtures/nonexistent/file.hip"
        self.hip_comparator = HipFileComparator(
            self.SOURCE_HIP_FILE, self.TARGET_HIP_FILE
        )

    @patch("api.hip_file_comparator.hou")
    def test_check_file_path_valid(self, mock_hou):
        """Test _check_file_path with a valid HIP file."""
        comparator = HipFileComparator(
            self.SOURCE_HIP_FILE, self.SOURCE_HIP_FILE
        )
        # No exception should be raised
        comparator._check_file_path(self.SOURCE_HIP_FILE, "source")

    @patch("api.hip_file_comparator.hou")
    def test_check_hip_file_path_invalid_extension(self, mock_hou):
        """
        Test HipFileComparator._check_file_path with an invalid file extension.
        """
        comparator = HipFileComparator(
            self.SOURCE_HIP_FILE, self.SOURCE_HIP_FILE
        )
        with self.assertRaises(RuntimeError):
            comparator._check_file_path(self.invalid_ext_path, "source")
            comparator._check_file_path(self.SOURCE_HDA_FILE, "source")

    @patch("api.hip_file_comparator.hou")
    def test_check_file_path_nonexistent_file(self, mock_hou):
        """Test _check_file_path with a nonexistent file."""
        comparator = HipFileComparator(
            self.SOURCE_HIP_FILE, self.SOURCE_HIP_FILE
        )
        with self.assertRaises(RuntimeError):
            comparator._check_file_path(self.nonexistent_path, "source")

    @patch("api.hip_file_comparator.hou")
    def test_get_hip_data_empty_path(self, mock_hou):
        """Test get_hip_data with an empty path."""
        with self.assertRaises(ValueError):
            self.hip_comparator.get_hip_data("")

    @patch("api.hip_file_comparator.hou")
    def test_get_hip_data_valid(self, mock_hou):
        """Test get_hip_data with a valid HIP file."""

        # Mocking the behavior of hou.node("/").allNodes()
        mock_node = Mock()
        mock_node.isInsideLockedHDA.return_value = False
        mock_node.path.return_value = "/mock_path"
        mock_node.name.return_value = "mock_name"

        mock_node_type = Mock()
        mock_node_type.icon.return_value = "mock_icon"
        mock_node.type.return_value = mock_node_type

        mock_parm = Mock()
        mock_parm.name.return_value = "mock_parm_name"
        mock_parm.eval.return_value = "mock_value"
        mock_node.parms.return_value = [mock_parm]

        mock_hou.node.return_value.allNodes.return_value = [mock_node]

        result = self.hip_comparator.get_hip_data(self.SOURCE_HIP_FILE)
        self.assertIn("/mock_path", result)

    @patch("api.hip_file_comparator.hou.hipFile.clear")
    @patch("api.hip_file_comparator.hou.hipFile.load")
    def test_load_hip_file_clears_and_loads(self, mock_load, mock_clear):
        self.hip_comparator._load_hip_file(self.SOURCE_HIP_FILE)

        mock_clear.assert_called_once()
        mock_load.assert_called_once_with(
            self.SOURCE_HIP_FILE,
            suppress_save_prompt=True,
            ignore_load_warnings=True,
        )

    @patch("api.hip_file_comparator.hou.hipFile.load")
    def test_load_hip_file_raises_exception_on_failure(self, mock_load):
        mock_load.side_effect = Exception("Failed to load")

        with self.assertRaises(Exception) as context:
            self.hip_comparator._load_hip_file(self.SOURCE_HIP_FILE)

        self.assertEqual(str(context.exception), "Failed to load")

    @patch("api.hip_file_comparator.NodeData")
    def test_extract_node_data(self, MockNodeData):
        # Mocking the node and its properties
        mock_node = Mock()
        mock_node.name.return_value = "mock_node"
        mock_node.path.return_value = "/path/to/mock_node"
        mock_node.type.icon.return_value = (
            "mock_icon"  # Adjusted to handle the method chain
        )
        mock_node.type.return_value = mock_node

        # Mocking _get_parent_path on the instance
        self.hip_comparator._get_parent_path = Mock(return_value="/path/to/parent")

        # Mocking the node's parameters
        mock_parm = Mock()
        mock_parm.name.return_value = "mock_parm_name"
        mock_parm.eval.return_value = "mock_parm_value"
        mock_node.parms.return_value = [mock_parm]

        # Call the method under test
        result = self.hip_comparator._extract_node_data(mock_node)

        # Assertions
        MockNodeData.assert_called_once_with("mock_node")
        mock_node_data_instance = MockNodeData.return_value
        mock_node_data_instance.add_parm.assert_called_once_with(
            "mock_parm_name", mock_node_data_instance.add_parm.call_args[0][1]
        )
        self.assertEqual(result, mock_node_data_instance)

    def test_get_parent_path_with_empty_path(self):
        # This test assumes that passing an empty path will raise a ValueError.
        self.hip_comparator._get_parent_path("")
    
    def test_extract_node_data_from_hip(self):
        self.hip_comparator._load_hip_file(self.SOURCE_HIP_FILE)
        node = hou.node('/obj/billowy_smoke')
        node_data = self.hip_comparator._extract_node_data(node)

        self.assertEqual(node_data.name, node.name())
        self.assertEqual(node_data.path, node.path())
        self.assertEqual(node_data.type, node.type())
        self.assertEqual(node_data.icon, node.type().icon())
        self.assertEqual(node_data.parent_path, self.hip_comparator._get_parent_path(node))

        for parm in node.parms():
            param_data = node_data.get_parm_by_name(parm.name())
            self.assertIsNotNone(param_data)
            self.assertEqual(param_data.name, parm.name())
            self.assertEqual(param_data.value, parm.eval())

    def test_validate_file_paths_both_set(self):
        try:
            self.hip_comparator._validate_file_paths()
        except ValueError as e:
            self.fail(f"_validate_file_paths raised ValueError unexpectedly: {e}")

    def test_update_source_file(self):
        test_hip_comparator = HipFileComparator(
            self.SOURCE_HIP_FILE, self.TARGET_HIP_FILE
        )
                
        with self.assertRaises(RuntimeError) as context:
            test_hip_comparator.source_file = None
            
        self.assertEqual(str(context.exception), "Incorrect source path specified. Such file doesn't exist.")

    @patch("api.node_data.NodeData")
    @patch("api.param_data.ParamData")
    def test_compare_node_params_edited(self, MockParamData, MockNodeData):
        comparator = HipFileComparator(
            self.SOURCE_HIP_FILE, 
            self.TARGET_HIP_FILE
        )

        # Create mock objects for source and target nodes and params
        source_param = Mock()
        source_param.value = "source_value"

        source_param2 = Mock()
        source_param2.value = "value2"

        source_parms_dummy = {
            "test_param": source_param,
            "test_param2": source_param2
        }
        source_node_data = Mock(items=source_parms_dummy)

        # Set up the source node's params dictionary to simulate having a param
        source_node_data.parms = source_parms_dummy

        target_param = Mock()
        target_param.value = "target_value"

        target_param2 = Mock()
        target_param2.value = "value2"

        # Set up the target node's params dictionary to simulate having a param
        target_parms_dummy = {
            "test_param": source_param,
            "test_param2": target_param2
        }
        target_node_data = Mock(items=target_parms_dummy)
        target_node_data.parms = target_parms_dummy

        dummy_path = "dummy_path"
        # Set the source and target nodes in the comparator's internal dictionaries
        comparator.source_nodes = {
            dummy_path : source_node_data,
        }
        comparator.target_nodes = {
            dummy_path : target_node_data,
        }

        # Mock the ParamData object returned by get_parm_by_name
        source_node_data.get_parm_by_name.return_value = source_param
        target_node_data.get_parm_by_name.return_value = target_param

        # Call the method under test
        comparator._compare_node_params(dummy_path, source_node_data)

        # Assert that the state and visual properties are set as expected
        self.assertEqual(
            comparator.source_nodes[dummy_path].state, 
            ItemState.EDITED
        )
        self.assertEqual(
            comparator.source_nodes[dummy_path].color, 
            COLORS["red"]
        )
        self.assertEqual(comparator.source_nodes[dummy_path].alpha, 100)

        self.assertEqual(
            comparator.target_nodes[dummy_path].state, 
            ItemState.EDITED
        )
        self.assertEqual(
            comparator.target_nodes[dummy_path].color, 
            COLORS["green"]
        )
        self.assertEqual(comparator.target_nodes[dummy_path].alpha, 100)
        
    def test_mark_node_as_created(self):
        hip_comparator = HipFileComparator(
            self.SOURCE_HIP_FILE, self.TARGET_HIP_FILE
        )

        target_node = NodeData("")
        target_node.parent_path = 'parent/path'

        node_path = 'dummy_path'
        hip_comparator.target_nodes[node_path] = target_node

        hip_comparator._mark_node_as_created(node_path)

        # Assert that a NodeData object is created with an empty string
        new_data = NodeData("")
        new_data.parent_path = 'parent/path'
        new_data.state = ItemState.CREATED
        new_data.alpha = 100
        new_data.is_hatched = True
        
        # Assert that the state, color, and alpha properties of the NodeData 
        # object in self.target_nodes are updated correctly
        self.assertEqual(
            hip_comparator.target_nodes[node_path].state, ItemState.CREATED
        )
        self.assertEqual(
            hip_comparator.target_nodes[node_path].color, COLORS["green"]
        )
        self.assertEqual(hip_comparator.target_nodes[node_path].alpha, 100)

    def test_mark_node_as_deleted(self):
        hip_comparator = HipFileComparator(
            self.SOURCE_HIP_FILE, self.TARGET_HIP_FILE
        )

        source_node_data = NodeData("")
        source_node_data.parent_path = 'parent/path'
        
        node_path = 'dummy_path'
        hip_comparator.source_nodes[node_path] = source_node_data

        hip_comparator._mark_node_as_deleted(node_path, source_node_data)

        # Assert that the state, color, 
        # and alpha properties of the source_node_data 
        # are updated correctly
        self.assertEqual(
            source_node_data.state, ItemState.DELETED
        )
        self.assertEqual(
            source_node_data.color, COLORS["red"]
        )
        self.assertEqual(source_node_data.alpha, 100)

    def test_handle_created_params(self):
        hip_comparator = HipFileComparator(
            self.SOURCE_HIP_FILE, self.TARGET_HIP_FILE
        )

        # Creating mock nodes and params
        source_node = NodeData("")
        target_node = NodeData("")
        target_param = ParamData("new_param", "", "value")
        target_node.add_parm("new_param", target_param)

        # Adding the mock nodes to the comparator's internal dictionaries
        hip_comparator.source_nodes['/path'] = source_node
        hip_comparator.target_nodes['/path'] = target_node

        hip_comparator._handle_created_params()

        # Assert that the state, color, and alpha properties of the target param are updated
        self.assertEqual(target_param.state, ItemState.CREATED)
        self.assertEqual(target_param.color, COLORS["green"])
        self.assertEqual(target_param.alpha, 55)

        # Assert that the state, color, and alpha properties of the target node are updated
        self.assertEqual(target_node.state, ItemState.EDITED)
        self.assertEqual(target_node.color, COLORS["green"])
        self.assertEqual(target_node.alpha, 100)

        # Assert that the source node has the new param with the expected properties
        created_param = source_node.get_parm_by_name("new_param")
        self.assertIsNotNone(created_param)
        self.assertEqual(created_param.state, ItemState.CREATED)
        self.assertEqual(created_param.alpha, 55)
        self.assertTrue(created_param.is_hatched)
        self.assertFalse(created_param.is_active)

        # Assert that the state and alpha properties of the source node are updated
        self.assertEqual(source_node.state, ItemState.EDITED)
        self.assertEqual(source_node.alpha, 100)

    def test_compare(self):
        
        self.hip_comparator.compare()

        edited_node_path = "/obj/billowy_smoke/smoke_base"
        edted_param_name = "radx"
        source_parm_val = 1.0

        edited_source_node = self.hip_comparator.source_nodes[
            edited_node_path
        ]

        edited_source_parm = edited_source_node.get_parm_by_name(
            edted_param_name
        )

        target_parm_val = 2.0
        edited_target_node = self.hip_comparator.target_nodes[
            edited_node_path
        ]
        edited_target_parm = edited_target_node.get_parm_by_name(
            edted_param_name
        )

        self.assertEqual(edited_source_node.state, ItemState.EDITED)
        self.assertEqual(edited_source_node.color, COLORS["red"])

        self.assertEqual(edited_target_node.state, ItemState.EDITED)
        self.assertEqual(edited_target_node.color, COLORS["green"])

        self.assertEqual(edited_source_parm.value, source_parm_val)
        self.assertEqual(edited_target_parm.value, target_parm_val)

        self.assertEqual(edited_source_parm.state, ItemState.EDITED)
        self.assertEqual(edited_target_parm.state, ItemState.EDITED)

        self.assertEqual(edited_source_parm.color, COLORS["red"])
        self.assertEqual(edited_source_parm.alpha, 55)

        self.assertEqual(edited_target_parm.color, COLORS["green"])
        self.assertEqual(edited_target_parm.alpha, 55)

        created_node_path = "/obj/billowy_smoke/null1"
        create_node_parm = "copyinput"
        created_source_node = self.hip_comparator.source_nodes[
            created_node_path
        ]
        created_source_parm = created_source_node.get_parm_by_name(
            create_node_parm
        )

        self.assertEqual(created_source_node.name, "")
        self.assertEqual(created_source_node.state, ItemState.EDITED)
        self.assertEqual(created_source_node.is_hatched, True)

        self.assertEqual(created_source_parm.value, "")
        self.assertEqual(created_source_parm.state, ItemState.CREATED)
        self.assertEqual(created_source_parm.is_hatched, True)
      
        created_target_node = self.hip_comparator.target_nodes[
            created_node_path
        ]
        created_target_parm = created_target_node.get_parm_by_name(
            create_node_parm
        )

        self.assertEqual(created_target_node.name, "null1")
        self.assertEqual(created_target_node.state, ItemState.EDITED)
        self.assertEqual(created_target_parm.is_hatched, False)

        self.assertEqual(created_target_parm.value, 1)
        self.assertEqual(created_target_parm.state, ItemState.CREATED)
        self.assertEqual(created_target_parm.is_hatched, False)
