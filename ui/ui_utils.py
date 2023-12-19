import os
import sys
from hutil.Qt.QtWidgets import QMessageBox


def generate_link_to_clipboard(qapplication, item_path) -> None:
    source_file_path = qapplication.source_file_line_edit.text()
    target_file_path = qapplication.target_file_line_edit.text()
    if not source_file_path or not target_file_path:
        QMessageBox.warning(
            qapplication,
            "Invalid Paths",
            "Source file or target files are empty, cannot generate link",
        )
        return
            
    hython_executable_path = os.environ.get('HOUDINI_HYTHON')
    if not hython_executable_path:
        hython_executable_path = sys.executable

    diff_tool_path = os.environ.get('HOUDINI_AGOL_DIFF_TOOL')
    if not diff_tool_path:
        diff_tool_path = qapplication.main_path
    
    link = (
        f'& "{hython_executable_path}" '
        f'{diff_tool_path} '
        f'--source={source_file_path} '
        f'--target={target_file_path} '
        f'--item-path={item_path}'
    )
    qapplication.clipboard.setText(link)