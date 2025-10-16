import sqlite3
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, OneLineAvatarIconListItem
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.list import IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("maeltodo.db")
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Create lists table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        ''')

        # Create tasks table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                is_checked INTEGER DEFAULT 0,
                FOREIGN KEY (list_id) REFERENCES lists (id) ON DELETE CASCADE
            )
        ''')
        self.conn.commit()

    def add_list(self, name):
        self.cursor.execute("INSERT INTO lists (name) VALUES (?)", (name,))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_lists(self):
        self.cursor.execute("SELECT id, name FROM lists")
        return self.cursor.fetchall()

    def delete_list(self, list_id):
        self.cursor.execute("DELETE FROM lists WHERE id = ?", (list_id,))
        self.conn.commit()

    def add_task(self, list_id, text):
        self.cursor.execute("INSERT INTO tasks (list_id, text, is_checked) VALUES (?, ?, 0)", (list_id, text))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_tasks(self, list_id):
        self.cursor.execute("SELECT id, text, is_checked FROM tasks WHERE list_id = ?", (list_id, ))
        return self.cursor.fetchall()

    def update_task(self, task_id, text, is_checked):
        self.cursor.execute("UPDATE tasks SET text = ?, is_checked = ? WHERE id = ?", (text, is_checked, task_id))
        self.conn.commit()

    def delete_task(self, task_id):
        self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()

    def rename_list(self, list_id, new_name):
        self.cursor.execute("UPDATE lists SET name = ? WHERE id = ?", (new_name, list_id))
        self.conn.commit()

    def close(self):
        self.conn.close()




class TaskItem(OneLineAvatarIconListItem):
    def __init__(self, task_id, task_text, is_checked, update_callback, **kwargs):
        super().__init__(**kwargs)
        self.task_id = task_id
        self.text = task_text
        self.is_checked = is_checked
        self.original_text = task_text  # Store original text without markup
        self.update_callback = update_callback

        # Checkbox on the left
        self.check_icon = MDIconButton(
            icon="checkbox-marked-circle" if is_checked else "checkbox-blank-circle-outline",
            theme_text_color="Custom",
            text_color=self.theme_cls.primary_color if is_checked else self.theme_cls.disabled_hint_text_color,
            on_release=self.toggle_check
        )
        self.add_widget(IconLeftWidget(self.check_icon))

        # Apply strikethrough if checked
        if is_checked:
            self.text = f"[s]{self.original_text}[/s]"

        # Bind click event to edit task
        self.bind(on_release=self.edit_task)

    def toggle_check(self, instance):
        self.is_checked = not self.is_checked

        if self.is_checked:
            self.check_icon.icon = "checkbox-marked-circle"
            self.check_icon.text_color = self.theme_cls.primary_color
            self.text = f"[s]{self.original_text}[/s]"
        else:
            self.check_icon.icon = "checkbox-blank-circle-outline"
            self.check_icon.text_color = self.theme_cls.disabled_hint_text_color
            self.text = self.original_text

        self.update_callback(self.task_id, self.original_text, self.is_checked)

    def edit_task(self, instance):
        self.dialog_text_field = MDTextField(
            text=self.original_text,
            hint_text = "Edit task"
        )

        self.dialog = MDDialog(
            title="Edit Task",
            type="custom",
            content_cls=self.dialog_text_field,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=self.close_dialog),
                MDFlatButton(text="SAVE", on_release=self.save_edit)
            ]
        )

        self.dialog_text_field = MDTextField(
            text=self.original_text,
            hint_text="Edit task"
        )

        self.dialog = MDDialog(
            title="Edit Task",
            type="custom",
            content_cls=self.dialog_text_field,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=self.close_dialog),
                MDFlatButton(text="SAVE", on_release=self.save_edit)
            ]
        )
        self.dialog.open()

    def save_edit(self, instance):
        new_text = self.dialog_text_field.text.strip()
        if new_text:
            self.original_text = new_text
            if self.is_checked:
                self.text = f"[s]{new_text}[/s]"
            else:
                self.text = new_text
            self.update_callback(self.task_id, new_text, self.is_checked)
        self.dialog.dismiss()

    def close_dialog(self, instance):
        self.dialog.dismiss()

class MaelToDoApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_pallete = "Amber"


        self.db = Database()
        self.current_list_id = None

        # Create the main screen
        screen = MDScreen()

        # Vertical layout to stack widgets
        layout = MDBoxLayout(orientation="vertical", padding=20, spacing=10)

        # List selection dropdown
        list_button_layout = MDBoxLayout(size_hint_y=None, height=50, spacing=10)



        self.list_button = MDRaisedButton(
            text="Select List",
            size_hint_x=0.7,
            on_release=self.show_list_menu
        )

        add_list_button = MDIconButton(
            icon="plus",
            on_release=self.add_new_list
        )

        rename_list_button = MDIconButton(
            icon="pencil",
            on_release=self.rename_list
        )

        delete_list_button = MDIconButton(
            icon="delete",
            on_release=self.delete_list
        )

        list_button_layout.add_widget(self.list_button)
        list_button_layout.add_widget(add_list_button)
        list_button_layout.add_widget(rename_list_button)
        list_button_layout.add_widget(delete_list_button)

        # Text input for new tasks
        self.task_input = MDTextField(
            hint_text="Enter a new task...",
            size_hint_y=None,
            height=50
        )

        # Horizontal layout for add button and delete button
        button_layout = MDBoxLayout(size_hint_y=None, height=50, spacing=10)

        # Button to add tasks
        add_button = MDRaisedButton(
            text="Add Task",
            size_hint_y=None,
            height=50,
            on_release=self.add_task
        )

        # Button to check/uncheck all tasks
        toggle_all_button = MDIconButton(
            icon="checkbox-multiple-marked",
            on_release=self.toggle_all_tasks
        )

        # Button to delete checked tasks
        delete_button = MDIconButton(
            icon="delete",
            on_release=self.delete_checked_tasks
        )

        button_layout.add_widget(add_button)
        button_layout.add_widget(toggle_all_button)
        button_layout.add_widget(delete_button)

        # Scrollable list to display tasks
        scroll = MDScrollView()
        self.task_list = MDList()
        scroll.add_widget(self.task_list)

        # Add everything to layout
        layout.add_widget(list_button_layout)
        layout.add_widget(self.task_input)
        layout.add_widget(button_layout)
        layout.add_widget(scroll)
        screen.add_widget(layout)

        # Load lists adn select first one if available
        self.load_lists()

        return screen

    def load_lists(self):
        lists = self.db.get_lists()
        if lists:
            self.current_list_id = lists[0][0]
            self.list_button.text = lists[0][1]
            self.load_tasks()
        else:
            # Create default list
            self.current_list_id = self.db.add_list("My Tasks")
            self.list_button.text = "My Tasks"

    def show_list_menu(self, instance):
        lists = self.db.get_lists()
        menu_item = [
            {
                "text": name,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=list_id, n=name: self.select_list(x, n)
            }
            for list_id, name in lists
        ]

        self.menu = MDDropdownMenu(
            caller=instance,
            items=menu_item,
            width_mult=4
        )
        self.menu.open()

    def select_list(self, list_id, list_name):
        self.current_list_id = list_id
        self.list_button.text = list_name
        self.load_tasks()
        self.menu.dismiss()

    def add_new_list(self, instance):
        self.dialog_list_field = MDTextField(
            hint_text="List name"
        )

        self.dialog = MDDialog(
            title="Create New List",
            type="custom",
            content_cls=self.dialog_list_field,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="CREATE", on_release=self.save_new_list)
            ]
        )
        self.dialog.open()

    def save_new_list(self, instance):
        list_name = self.dialog_list_field.text.strip()
        if list_name:
            list_id = self.db.add_list(list_name)
            self.current_list_id = list_id
            self.list_button.text = list_name
            self.load_tasks()
        self.dialog.dismiss()

    def load_tasks(self):
        self.task_list.clear_widgets()
        if self.current_list_id:
            tasks = self.db.get_tasks(self.current_list_id)
            for task_id, text, is_checked in tasks:
                task_item = TaskItem(
                    task_id=task_id,
                    task_text=text,
                    is_checked=bool(is_checked),
                    update_callback=self.update_task
                )
                self.task_list.add_widget(task_item)

    def add_task(self, instance):
        if not self.current_list_id:
            return

        # Get the text from input
        task_text = self.task_input.text.strip()

        # Only add if not empty
        if task_text:
            task_id = self.db.add_task(self.current_list_id, task_text)
            task_item = TaskItem(
                task_id=task_id,
                task_text=task_text,
                is_checked=False,
                update_callback=self.update_task
            )
            self.task_list.add_widget(task_item)
            self.task_input.text = ""

    def update_task(self, task_id, text, is_checked):
        self.db.update_task(task_id, text, int(is_checked))

    def delete_checked_tasks(self, instance):
        # Get all checked tasks
        checked_tasks = [task for task in self.task_list.children if hasattr(task, "is_checked") and task.is_checked]
        # Remove them
        for task in checked_tasks:
            self.db.delete_task(task.task_id)
            self.task_list.remove_widget(task)

    def toggle_all_tasks(self, instance):
        # Check if any task is unchecked
        has_unchecked = any(not task.is_checked for task in self.task_list.children if hasattr(task, "is_checked"))

        # If any unchecked, check all; otherwise uncheck all
        for task in self.task_list.children:
            if hasattr(task, "check_icon"):
                if has_unchecked and not task.is_checked:
                    task.toggle_check(task.check_icon)
                elif not has_unchecked and task.is_checked:
                    task.toggle_check(task.check_icon)

    def rename_list(self, instance):
        if not self.current_list_id:
            return

        self.dialog_rename_field = MDTextField(
            text=self.list_button.text,
            hint_text="List name"
        )

        self.dialog = MDDialog(
            title="Rename List",
            type="custom",
            content_cls=self.dialog_rename_field,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="RENAME", on_release=self.save_rename_list)
            ]
        )
        self.dialog.open()

    def save_rename_list(self, instance):
        new_name = self.dialog_rename_field.text.strip()
        if new_name:
            self.db.rename_list(self.current_list_id, new_name)
            self.list_button.text = new_name
        self.dialog.dismiss()

    def delete_list(self, instance):
        if not self.current_list_id:
            return

        self.dialog = MDDialog(
            title="Delete List",
            text=f"Are you sure you want to delete '{self.list_button.text}' and all its tasks?",
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x:self.dialog.dismiss()),
                MDFlatButton(text="DELETE", on_release=self.confirm_delete_list)
            ]
        )
        self.dialog.open()

    def confirm_delete_list(self, instance):
        self.db.delete_list(self.current_list_id)
        self.dialog.dismiss()

        # Load remaining lists or create default
        lists = self.db.get_lists()
        if lists:
            self.current_list_id = lists[0][0]
            self.list_button.text = lists[0][1]
            self.load_tasks()
        else:
            # Create default list if none remain
            self.current_list_id = self.db.add_list("My Tasks")
            self.list_button.text = "My Tasks"
            self.load_tasks()

    def on_stop(self):
        self.db.close()


if __name__ == "__main__":
    MaelToDoApp().run()