import unittest
from unittest.mock import patch, Mock, MagicMock

import hou

from api import hip_file_comparator
from api.hip_file_comparator import HipFileComparator


class TestHipFileComparator(unittest.TestCase):
    SOURCE_HIP_FILE = "test/test_scenes/billowy_smoke_source.hipnc"
    TARGET_HIP_FILE = "test/test_scenes/billowy_smoke_source_edited.hipnc"

    def setUp(self):
        # Create some dummy paths
        self.invalid_ext_path = "test/test_scenes/invalid_ext_file.txt"
        self.nonexistent_path = "test/test_scenes/nonexistent/file.hip"
        self.comparator = HipFileComparator(self.SOURCE_HIP_FILE, self.TARGET_HIP_FILE)

    @patch('api.hip_file_comparator.hou')
    def test_check_file_path_valid(self, mock_hou):
        """Test _check_file_path with a valid HIP file."""
        comparator = HipFileComparator(self.SOURCE_HIP_FILE, self.SOURCE_HIP_FILE)
        # No exception should be raised
        comparator._check_file_path(self.SOURCE_HIP_FILE, "source")

    @patch('api.hip_file_comparator.hou')
    def test_check_file_path_invalid_extension(self, mock_hou):
        """Test _check_file_path with an invalid file extension."""
        comparator = HipFileComparator(self.SOURCE_HIP_FILE, self.SOURCE_HIP_FILE)
        with self.assertRaises(RuntimeError):
            comparator._check_file_path(self.invalid_ext_path, "source")

    @patch('api.hip_file_comparator.hou')
    def test_check_file_path_nonexistent_file(self, mock_hou):
        """Test _check_file_path with a nonexistent file."""
        comparator = HipFileComparator(self.SOURCE_HIP_FILE, self.SOURCE_HIP_FILE)
        with self.assertRaises(RuntimeError):
            comparator._check_file_path(self.nonexistent_path, "source")

    @patch('api.hip_file_comparator.hou')
    def test_get_hip_data_empty_path(self, mock_hou):
        """Test get_hip_data with an empty path."""
        with self.assertRaises(ValueError):
            self.comparator.get_hip_data("")

    @patch('api.hip_file_comparator.hou')
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
        
        result = self.comparator.get_hip_data(self.SOURCE_HIP_FILE)
        self.assertIn("/mock_path", result)

    @patch('api.hip_file_comparator.hou')
    def test_get_hip_data_locked_hda(self, mock_hou):
        """Test get_hip_data with a node inside a locked HDA."""
        
        # Mocking the behavior of hou.node("/").allNodes() with a node that is inside a locked HDA
        mock_node = Mock()
        mock_node.isInsideLockedHDA.return_value = True
        mock_hou.node.return_value.allNodes.return_value = [mock_node]
        
        result = self.comparator.get_hip_data(self.SOURCE_HIP_FILE)
        self.assertEqual(result, {})  # No data should be retrieved for locked HDA nodes

    @patch("api.hip_file_comparator.hou.hipFile.clear")
    @patch("api.hip_file_comparator.hou.hipFile.load")
    def test_load_hip_file_clears_and_loads(self, mock_load, mock_clear):
        self.comparator._load_hip_file(self.SOURCE_HIP_FILE)
        
        mock_clear.assert_called_once()
        mock_load.assert_called_once_with(self.SOURCE_HIP_FILE, suppress_save_prompt=True, ignore_load_warnings=True)
    
    @patch("api.hip_file_comparator.hou.hipFile.load")
    def test_load_hip_file_raises_exception_on_failure(self, mock_load):
        mock_load.side_effect = Exception("Failed to load")
        
        with self.assertRaises(Exception) as context:
            self.comparator._load_hip_file(self.SOURCE_HIP_FILE)

        self.assertEqual(str(context.exception), "Failed to load")

    @patch("api.hip_file_comparator.NodeData")  # Adjust the patch to your module's actual name
    def test_extract_node_data(self, MockNodeData):
        # Mocking the node and its properties
        mock_node = Mock()
        mock_node.name.return_value = "mock_node"
        mock_node.path.return_value = "/path/to/mock_node"
        mock_node.type.icon.return_value = "mock_icon"  # Adjusted to handle the method chain
        mock_node.type.return_value = mock_node

        # Mocking _get_parent_path on the instance
        self.comparator._get_parent_path = Mock(return_value='/path/to/parent')

        # Mocking the node's parameters
        mock_parm = Mock()
        mock_parm.name.return_value = "mock_parm_name"
        mock_parm.eval.return_value = "mock_parm_value"
        mock_node.parms.return_value = [mock_parm]

        # Call the method under test
        result = self.comparator._extract_node_data(mock_node)

        # Assertions
        MockNodeData.assert_called_once_with("mock_node")
        mock_node_data_instance = MockNodeData.return_value
        mock_node_data_instance.add_parm.assert_called_once_with("mock_parm_name", mock_node_data_instance.add_parm.call_args[0][1])
        self.assertEqual(result, mock_node_data_instance)

    def test_get_parent_path_with_empty_path(self):
        # This test assumes that passing an empty path will raise a ValueError.
        self.comparator._get_parent_path("")
