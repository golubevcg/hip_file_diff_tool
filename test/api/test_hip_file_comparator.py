import unittest
from unittest.mock import patch, Mock

from api.hip_file_comparator import HdaFileComparator, HipFileComparator, COLORS
from api.node_data import NodeState
import hou


class TestHipFileComparator(unittest.TestCase):
    SOURCE_HIP_FILE = "test/test_scenes/billowy_smoke_source.hipnc"
    TARGET_HIP_FILE = "test/test_scenes/billowy_smoke_source_edited.hipnc"
    SOURCE_HDA_FILE = "test/test_scenes/BoxHDA_source.hda"
    TARGET_HDA_FILE = "test/test_scenes/BoxHDA_edited.hda"

    def setUp(self):
        # Create some dummy paths
        self.invalid_ext_path = "test/test_scenes/invalid_ext_file.txt"
        self.nonexistent_path = "test/test_scenes/nonexistent/file.hip"
        self.hip_comparator = HipFileComparator(
            self.SOURCE_HIP_FILE, self.TARGET_HIP_FILE
        )
        self.hda_comparator = HdaFileComparator(
            self.SOURCE_HDA_FILE, self.TARGET_HDA_FILE
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
    def test_check_hda_file_path_invalid_extension(self, mock_hou):
        """
        Test HdaFileComparator._check_file_path with an invalid file extension.
        """
        comparator = HdaFileComparator(
            self.SOURCE_HDA_FILE, self.TARGET_HDA_FILE
        )
        with self.assertRaises(RuntimeError):
            comparator._check_file_path(self.invalid_ext_path, "source")
            comparator._check_file_path(self.SOURCE_HIP_FILE, "source")

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
    def test_get_hda_data_empty_path(self, mock_hou):
        """Test get_hda_data with an empty path."""
        with self.assertRaises(ValueError):
            self.hda_comparator.get_hda_data("")

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

    @patch("api.hip_file_comparator.hou")
    def test_get_hip_data_locked_hda(self, mock_hou):
        """Test get_hip_data with a node inside a locked HDA."""

        # Mocking the behavior of hou.node("/").allNodes()
        # with a node that is inside a locked HDA
        mock_node = Mock()
        mock_node.isInsideLockedHDA.return_value = True
        mock_hou.node.return_value.allNodes.return_value = [mock_node]

        result = self.hip_comparator.get_hip_data(self.SOURCE_HIP_FILE)
        self.assertEqual(
            result, {}
        )  # No data should be retrieved for locked HDA nodes

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

    def test_update_target_file(self):
        test_hip_comparator = HipFileComparator(
            self.SOURCE_HIP_FILE, self.TARGET_HIP_FILE
        )
                
        with self.assertRaises(RuntimeError) as context:
            test_hip_comparator.target_file = None
            
        self.assertEqual(str(context.exception), "Incorrect target path specified. Such file doesn't exist.")

    '''
    @patch("api.node_data.NodeData")
    @patch("api.param_data.ParamData")
    def test_compare_node_params(self, MockParamData, MockNodeData):
        # Initialize HipFileComparator with dummy paths
        comparator = HipFileComparator("dummy_source_path", "dummy_target_path")

        # Create mock objects for source and target nodes and params
        source_node_data = MockNodeData()
        source_param = MockParamData()
        target_param = MockParamData()

        # Set up the source node's params dictionary to simulate having a param
        source_node_data.parms = {"test_param": source_param}

        # Set up the target node's params dictionary to simulate having a param
        target_node_data = MockNodeData()
        target_node_data.parms = {"test_param": target_param}

        # Set the source and target nodes in the comparator's internal dictionaries
        comparator.source_nodes = {"dummy_path": source_node_data}
        comparator.target_nodes = {"dummy_path": target_node_data}

        # Mock the ParamData object returned by get_parm_by_name
        source_node_data.get_parm_by_name.return_value = source_param
        target_node_data.get_parm_by_name.return_value = target_param

        # Simulate different param values between source and target to trigger the edit logic
        source_param.value = "value1"
        target_param.value = "value2"

        # Call the method under test
        comparator._compare_node_params("dummy_path", source_node_data)

        # Assert that the state and visual properties are set as expected
        self.assertEqual(source_node_data.state, NodeState.EDITED)
        self.assertEqual(source_node_data.color, COLORS["red"])
        self.assertEqual(source_node_data.alpha, 100)

        self.assertEqual(target_node_data.state, NodeState.EDITED)
        self.assertEqual(target_node_data.color, COLORS["green"])
        self.assertEqual(target_node_data.alpha, 100)

        self.assertEqual(source_param.state, NodeState.EDITED)
        self.assertEqual(source_param.color, COLORS["red"])
        self.assertEqual(source_param.alpha, 55)

        self.assertEqual(target_param.state, NodeState.EDITED)
        self.assertEqual(target_param.color, COLORS["green"])
        self.assertEqual(target_param.alpha, 55)'''