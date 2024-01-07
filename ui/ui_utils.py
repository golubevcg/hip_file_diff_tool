import os
import sys
from hutil.Qt.QtWidgets import QMessageBox


def generate_link_to_clipboard(qapplication: 'QApplication', item_path: str) -> None:
    """
    Generates a link for an item to launch a hip file difference tool and copies it to the clipboard.

    Parameters:
    qapplication (QApplication): The main application instance where UI elements are accessed.
    item_path (str): The path of the item for which the link is generated.
    
    The function retrieves source and target file paths from the application's line edits, 
    checks for the necessary executable paths, constructs the command, and copies it to the clipboard.
    """
    source_file_path = qapplication.source_file_line_edit.text()
    target_file_path = qapplication.target_file_line_edit.text()
    if not source_file_path or not target_file_path:
        QMessageBox.warning(
            qapplication,
            "Invalid Paths",
            "Source file or target files are empty, cannot generate link",
        )
        return

    hython_executable_path = os.environ.get('HOUDINI_HYTHON', sys.executable)
    diff_tool_path = os.environ.get('HOUDINI_AGOL_DIFF_TOOL', qapplication.main_path)

    link = (
        f'& "{hython_executable_path}" '
        f'{diff_tool_path} '
        f'--source={source_file_path} '
        f'--target={target_file_path} '
        f'--item-path={item_path}'
    )
    qapplication.clipboard.setText(link)
