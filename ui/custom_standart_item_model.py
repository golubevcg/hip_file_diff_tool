import os
import copy

from hutil.Qt.QtGui import QPixmap, QIcon, QStandardItemModel, QStandardItem
from hutil.Qt.QtCore import Qt


ICONS_PATH = os.path.dirname(os.path.abspath(__file__))
ICONS_PATH = os.path.join(ICONS_PATH, "icons")

ICONS_MAPPING_PATH = os.path.join(ICONS_PATH, 'IconMapping')
ICONS_ZIP_PATH = os.path.join(ICONS_PATH, 'icons.zip')

ICON_MAPPINGS = {}
with open(ICONS_MAPPING_PATH, 'r') as file:
    for line in file:
        if line.startswith("#") or ":=" not in line:
            continue

        key, value = line.split(":=")
        key = key.strip()
        value = value.strip().rstrip(";")
        ICON_MAPPINGS[key] = value.replace("_", "/", 1)


class CustomStandardItemModel(QStandardItemModel):
    def __init__(self, *args, **kwargs):
        super(CustomStandardItemModel, self).__init__(*args, **kwargs)
        self.item_dictionary = {}
        self.path_role = Qt.UserRole + 1
        self.data_role = Qt.UserRole + 2

    def add_item_with_path(
            self, 
            item_text, 
            path, 
            data, 
            icons_zip,
            parent=None,
        ):
        """Adds an item to the model with a unique identifier."""
        item = QStandardItem(item_text)
        item.setData(path, self.path_role)
        item.setData(data, self.data_role)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)

        self.item_dictionary[path] = item

        icon_path = data.icon
        if icon_path in ICON_MAPPINGS:
            icon_path = ICON_MAPPINGS[icon_path]
        elif icon_path:
            icon_path = icon_path.replace("_", "/", 1)

        icon_path_inside_zip = icon_path + ".svg"
        try:
            with icons_zip.open(icon_path_inside_zip) as file:
                icon_data = file.read()
                pixmap = QPixmap()
                pixmap.loadFromData(icon_data)
                qicon = QIcon(pixmap)
                item.setIcon(qicon)
        except Exception as e:
            pass
        
        if parent:
            parent.appendRow(item)
        else:
            self.appendRow(item)

        for parm_name in data.parms:
            parm = data.get_parm_by_name(parm_name)
            parm_path = path + "/{0}".format(parm_name)
            if parm.tag != "edited":
                continue

            value = parm.value
            parm_item = QStandardItem(parm.name)
            parm_item.setData(parm, self.data_role)
            parm_item.setData(parm_path, self.path_role)
            self.item_dictionary[parm_path] = parm_item

            parm_item.setFlags(parm_item.flags() & ~Qt.ItemIsEditable)
            try:
                with icons_zip.open("VOP/parameter.svg") as file:
                    parm_icon_data = file.read()
                    pixmap = QPixmap()
                    pixmap.loadFromData(parm_icon_data)
                    qicon = QIcon(pixmap)
                    parm_item.setIcon(qicon)
            except Exception as e:
                pass

            item.appendRow(parm_item)

            value = parm.value
            value_path = parm_path + "/value"
            value_item = QStandardItem(str(value))
            value_item.setFlags(parm_item.flags() & ~Qt.ItemIsEditable)
            value_data = copy.copy(parm)
            value_data.tag = 'value'
            value_item.setData(value_data, self.data_role)
            value_item.setData(value_path, self.path_role)
            self.item_dictionary[value_path] = value_item

            parm_item.appendRow(value_item)

    def get_item_by_path(self, path):
        """Retrieve an item based on its unique identifier."""
        return self.item_dictionary.get(path)
   