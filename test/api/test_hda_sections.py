from pathlib import Path
import unittest

from api.data.hda_data import HdaData, HdaDefintion


class TestHdaSections(unittest.TestCase):
    def setUp(self):
        hda_source_path = Path(
            Path(__file__).parent.parent, "fixtures/BoxHDA_source.hda"
        ).as_posix()

        hda_target_path = Path(
            Path(__file__).parent.parent, "fixtures/BoxHDA_edited.hda"
        ).as_posix()

        self.hda_source = HdaData(hda_source_path).latest_definition()
        self.hda_target = HdaData(hda_target_path).latest_definition()

    def test_provided_hda_diff(self):
        expected_diff = {
            "OnCreated": [
                "--- ",
                "+++ ",
                "@@ -1 +1 @@",
                '-print("oncreated")',
                '+print("oncreaded")',
            ],
            "PythonModule": [
                "--- ",
                "+++ ",
                "@@ -1,2 +1 @@",
                ' print("module")',
                '-print("yoyoyo")',
            ],
            "Help": [],
            "Tools.shelf": [],
        }
        output_diff = HdaDefintion.diff_definition_sections(
            self.hda_source, self.hda_target
        )
        self.assertEqual(output_diff, expected_diff)
