from PyQt5.QtWidgets import QLabel, QMainWindow, QWidget, QApplication, QAction, QMenuBar, QFileDialog, QGridLayout
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import QTimer, Qt
from components.context_menu import ContextMenu, ContextMenuItem
from components.json_tree import JsonTree
from components.code_editor import CodeEditor
from components.split_panel import SplitPanel
from PyQt5.QtWidgets import QGroupBox, QCheckBox, QVBoxLayout, QLineEdit
from PyQt5.QtWidgets import QMessageBox
import json
from itertools import zip_longest  # Add this import at the top of your file


class JsonEditor(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(2800, 2000)
        self.current_file_path = None 
        self.json_data = {}

        self.json_tree = JsonTree()
        self.code_editor = CodeEditor()
        self.save_status_label = QLabel("")
        self.search_bar = QLineEdit()
        self.split_panel = SplitPanel(self.json_tree, self.code_editor)
        self.save_button = QPushButton("Save Changes")
        
        self.value_group = QGroupBox("Select Values")
        master_layout = QHBoxLayout()
        self.checkbox_layout = QHBoxLayout()
        self.value_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        
        self.value_group.setLayout(self.value_layout)
        
        self.save_status_label.setMaximumHeight(20)
        self.save_status_label.setStyleSheet("font: 12pt")
        self.save_status_label.setAlignment(Qt.AlignCenter)

        self.split_panel.set_sizes([800, 800])

        self.search_bar.textChanged.connect(self.filter_json_tree)
        self.save_button.clicked.connect(self.save_json_file)

        self.create_menu_bar()
        self.connect_signals()
        self.load_default_file()

        # LAYOUTS #

        self.checkbox_layout.addWidget(self.value_group)
        self.value_group.setMinimumWidth(600)
        
        self.checkbox_layout.addLayout(self.value_layout) 
        
        right_layout.addWidget(self.search_bar)
        right_layout.addWidget(self.save_status_label)
        right_layout.addWidget(self.split_panel)
        right_layout.addWidget(self.save_button)

        master_layout.addLayout(self.checkbox_layout)
        master_layout.addLayout(right_layout)

        container = QWidget()
        container.setLayout(master_layout)
        self.setCentralWidget(container)

        # Inside __init__ method after loading the default JSON file
        key_value_dict = {}
        self.collect_lowest_keys_values(self.json_data, key_value_dict, depth=1)  # Start with depth=1
        self.create_checkboxes(key_value_dict)

    def create_checkboxes(self, key_value_dict):
        self.key_checkboxes = []
        self.value_checkboxes = []

        for key, values in key_value_dict.items():
            key_group = QGroupBox(key.capitalize())  # Create a group box for each key
            grid_layout = QGridLayout()  # Create a grid layout for the group box

            row = 0
            col = 0

            for value in sorted(map(str, values)):  # Convert all values to strings and sort them
                if isinstance(value, str):  # Only add string values
                    base_value = value
                    value_checkbox = QCheckBox(base_value)
                    value_checkbox.stateChanged.connect(self.filter_json_tree)  # Connect to slot
                    self.value_checkboxes.append(value_checkbox)

                    grid_layout.addWidget(value_checkbox, row, col)  # Add checkbox to the grid layout

                    col += 1
                    if col > 1:  # Reset column and move to next row
                        col = 0
                        row += 1

            key_group.setLayout(grid_layout)  # Set the grid layout to the group box
            self.value_layout.addWidget(key_group) 

    def load_default_file(self):
        self.current_file_path = 'pictographs.json'  # Set the path of the default file
        try:
            with open('pictographs.json', 'r') as file:
                self.json_data = json.load(file)  # Update this line
                self.json_tree.set_json(self.json_data)
                self.code_editor.set_code(json.dumps(self.json_data, indent=4))
        except Exception as e:
            print(f"Failed to load default file: {e}")

    def create_menu_bar(self):
        menu_bar = QMenuBar()
        file_menu = menu_bar.addMenu("File")
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_json_file)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_json_file)
        file_menu.addAction(save_action)

        self.setMenuBar(menu_bar)

    def connect_signals(self):
        self.json_tree.itemChanged.connect(self.on_json_tree_item_changed)

    def on_json_tree_item_changed(self, item, column):
        path = self.json_tree.get_path_to_item(item)
        value = item.text(column)
        self.json_tree.update_json_data(self.json_data, path, value)
        self.code_editor.set_code(json.dumps(self.json_data, indent=4))
        
    def collect_lowest_keys_values(self, data, key_value_dict, depth=0):
        print(f"Depth: {depth}, Data: {data}")  # Debug print
        if depth > 0:  # Only collect keys and values if not at the top level
            if isinstance(data, list):
                for item in data:
                    self.collect_lowest_keys_values(item, key_value_dict, depth + 1)
            elif isinstance(data, dict):
                for key, value in data.items():
                    if key not in key_value_dict:
                        key_value_dict[key] = set()
                    if isinstance(value, (list, dict)):
                        self.collect_lowest_keys_values(value, key_value_dict, depth + 1)
                    else:
                        key_value_dict[key].add(value)
        print(f"key_value_dict after depth {depth}: {key_value_dict}")  # Debug print


    # Add this method to filter the JSON tree
    def filter_json_tree(self):
        search_text = self.search_bar.text().lower()
        selected_values = [checkbox.text().split(": ")[1] for checkbox in self.value_checkboxes if checkbox.isChecked()]
        self.json_tree.filter_tree(search_text, selected_values)


    def open_json_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_path:
            with open(file_path, 'r') as file:
                self.json_data = json.load(file)
                self.current_file_path = file_path  
                self.json_tree.set_json(self.json_data)  # Update this line
                self.code_editor.set_code(json.dumps(self.json_data, indent=4))
        
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Save Changes',
                                    'Do you want to save changes?', QMessageBox.Yes | 
                                    QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.save_json_file()
        event.accept()

    def save_json_file(self):
        if self.current_file_path:
            with open(self.current_file_path, 'w') as file:
                json.dump(self.json_data, file, indent=4)
            self.save_status_label.setText("File Saved!")
            QTimer.singleShot(5000, lambda: self.save_status_label.setText(""))  # Clear message after 5 seconds
