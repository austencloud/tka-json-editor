
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView, QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator
from PyQt5.QtGui import QFont, QColor, QBrush
from components.repository import PictographSchema
from components.combo_box_delegate import ComboBoxDelegate


class JsonTree(QTreeWidget):
    def __init__(self, parent=None):
        super(JsonTree, self).__init__(parent)
        self.itemChanged.connect(self.on_item_changed)
        self.itemExpanded.connect(self.on_item_expanded)
        self.json_data = {}
        self.setItemDelegate(ComboBoxDelegate(self))
        self.setEditTriggers(QAbstractItemView.CurrentChanged)  # Start editing on single click
        self.setColumnWidth(1, 50)  # Set the width of the second column to 50 pixels

    def filter_tree(self, search_text, selected_values, item=None):
        print(f"Filtering with: {search_text}, {selected_values}")
        if item is None:
            item = self.invisibleRootItem()

        # If all are empty, show everything
        if search_text == "" and len(selected_values) == 0:
            item.setHidden(False)
            for i in range(item.childCount()):
                child_item = item.child(i)
                self.filter_tree(search_text, selected_values, child_item)
            return True

        child_match = False

        # Check for key and value matches
        value_match = item.text(0).split(": ")[-1] in selected_values

        # Check for search text match
        if isinstance(search_text, list):
            search_match = any(text in item.text(0).lower() for text in search_text)
        else:
            search_match = search_text in item.text(0).lower()
            
        self_match = (value_match or not selected_values) and (search_match or not search_text)

        for i in range(item.childCount()):
            child_item = item.child(i)
            child_match = self.filter_tree(search_text, selected_values, child_item) or child_match

        item.setHidden(not (self_match or child_match))

        if self_match or child_match:
            self.expandItem(item)
        else:
            self.collapseItem(item)

        return self_match or child_match

    def set_json(self, json_data):
        self.json_data = json_data
        self.clear()
        self.add_subnodes(None, json_data)

    def add_subnodes(self, parent, data, path=[]):
        VERTICAL_PADDING = 10  # Vertical padding value
        if isinstance(data, list):
            for idx, group in enumerate(data):
                start_position = group[0]["start_position"].replace("alpha", "α").replace("beta", "β").replace("gamma", "Γ")
                end_position = group[0]["end_position"].replace("alpha", "α").replace("beta", "β").replace("gamma", "Γ")
                item = QTreeWidgetItem([f"{start_position}→{end_position}"])
                item.setData(0, Qt.UserRole, path + [idx])
                if parent is None:
                    self.addTopLevelItem(item)
                else:
                    parent.addChild(item)
                for sub_idx, sub_item in enumerate(group[1:]):
                    sub_key = ["Left", "Right", "Optimal Location"][sub_idx] if sub_idx < 3 else str(sub_idx)
                    child_item = QTreeWidgetItem([sub_key])
                    child_item.setData(0, Qt.UserRole, path + [idx, sub_idx + 1])
                    if sub_key in ["Left", "Right"]:
                        font = QFont()
                        font.setBold(True)
                        child_item.setFont(0, font)
                        color = QColor("blue") if sub_key == "Left" else QColor("red")
                        child_item.setForeground(0, QBrush(color))
                    item.addChild(child_item)  # Moved inside the loop
                    if isinstance(sub_item, dict):
                        self.add_subnodes(child_item, sub_item, path + [idx, sub_idx + 1])

        elif isinstance(data, dict):
            for key, value in data.items():
                if key == "color":  # Skip the "color" attribute
                    continue
                if isinstance(value, (dict, list)):
                    item = QTreeWidgetItem([key])
                    item.setData(0, Qt.UserRole, path + [key])
                    if parent is None:
                        self.addTopLevelItem(item)
                    else:
                        parent.addChild(item)
                    self.add_subnodes(item, value, path + [key])
                else:
                    # Padding for leaf nodes
                    text = f"{key} - {value}"
                    item = QTreeWidgetItem([text])
                    item.setData(0, Qt.UserRole, path + [key])
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    if parent is None:
                        self.addTopLevelItem(item)
                    else:
                        parent.addChild(item)



    def on_item_expanded(self, item):
        item_text = item.text(0)
        if 'α' in item_text or 'β' in item_text or 'Γ' in item_text:
            self.expand_red_blue_nodes(item)

    def expand_red_blue_nodes(self, item):
        for i in range(item.childCount()):
            child = item.child(i)
            child_text = child.text(0)
            if child_text in ["Left", "Right"]:
                self.expandItem(child)
                self.expand_leaf_nodes(child)

    def expand_leaf_nodes(self, item):
        for i in range(item.childCount()):
            child = item.child(i)
            self.expandItem(child)
            self.expand_leaf_nodes(child)

    def get_path_to_item(self, item):
        return item.data(0, Qt.UserRole)

    def on_item_changed(self, item, column):
        if item.childCount() == 0:
            path = item.data(0, Qt.UserRole)
            value = item.text(column)
            self.update_json_data(self.json_data, path, value)

    def update_json_data(self, json_data, path, value):
        key, value = value.split(' - ')  # Extract the value part of the text
        # Create an instance of PictographSchema to access the schema
        schema = PictographSchema().schema
        property_name = path[-1]  # Assuming the last element in the path is the property name

        # Check if the property has an enum attribute in the schema
        if "enum" in schema["properties"].get(property_name, {}):
            valid_values = schema["properties"][property_name]["enum"]

            # Validate the value against the enum
            if value not in valid_values:
                # Handle the invalid value (e.g., show an error message or reject the change)
                print(f"Invalid value for {property_name}: {value}. Must be one of {valid_values}.")
                return

        # Continue with the update if the value is valid
        outer_list = json_data[path[0]]
        inner_list = outer_list[path[1]]
        color_object = inner_list[path[2]]
        color_object[property_name] = value