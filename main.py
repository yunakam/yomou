import flet as ft
import datetime
import math
import sqlite3
import os

### DATABASE FUNCTIONS ###

def connect_to_database(db_path):
    return sqlite3.connect(db_path)

def create_book_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS book (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            total_pages INTEGER NOT NULL,
            read_pages INTEGER NOT NULL,
            registered_date DATE NOT NULL,
            target_date DATE NOT NULL,
            finished BOOLEAN NOT NULL
        )
    """)
    conn.commit()

def get_data(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [column[0] for column in cursor.description]
    data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return data


### APP CLASS ###

## Register Books

class Input(ft.Row):
    def __init__(self, label, suffix_text=None, on_blur=None, width=None):
        super().__init__()
        
        self.text_field = ft.TextField(
            content_padding=ft.padding.symmetric(horizontal=7, vertical=0),
            text_size=13,
            label=label,
            label_style=ft.TextStyle(size=11, weight=ft.FontWeight.BOLD),
            suffix_text=suffix_text,
            suffix_style=ft.TextStyle(size=11),
            width=width,
            on_blur=on_blur
        )
       
        self.controls.append(self.text_field)

class Register(ft.Container):
    def __init__(self, app):
        super().__init__(
            bgcolor="white",
            padding=20,
            border_radius=10,
        )
        
        self.app = app
        self.page = app.page
        self.value_dict = {"title": None, "total_pages": None, "read_pages": 0, "target_date": None}

        self.title = Input("Book title", on_blur=self.title_entered)
        self.total_pages = Input("Total pages", suffix_text="pages", on_blur=self.total_pages_entered, width=90)
        
        self.daily_target = ft.Text(
            width=100,
            style=ft.TextStyle(color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD, size=13),
            value="Daily target",
        )
                
        self.bt_register = ft.ElevatedButton(
            " Add Book ",
            on_click=self.register_book
        )

        # Initialize the DatePicker button
        self.target_date_button = ft.TextButton(
            content=ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CALENDAR_MONTH),
                        ft.Text(value="Target date to finish the book", size=13)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=5,
                ),
                padding=ft.padding.all(10),
            ),
            style=ft.ButtonStyle(padding=0),
            on_click=self.open_date_picker,
        )
                    
        self.content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.START,
            controls=[
                self.title,
                ft.Row(
                    controls=[
                        self.total_pages,
                        self.target_date_button,
                    ]
                ),
                ft.Row(),                 
                ft.Row(
                    controls=[
                        ft.Container(),
                        ft.Icon(ft.Icons.DOUBLE_ARROW),
                        self.daily_target,
                    ]
                ),                
                ft.Container(
                    alignment=ft.alignment.center, 
                    margin=ft.margin.only(top=10),
                    content=self.bt_register,
                )
            ],
            alignment=ft.MainAxisAlignment.START
        )

    def calc_daily_target(self):
        total_pages = self.value_dict["total_pages"]
        read_pages = self.value_dict["read_pages"]
        target_date = self.value_dict["target_date"]
        
        if total_pages is not None and target_date is not None:
            days_to_target = (target_date - datetime.date.today()).days
            if days_to_target > 0:
                daily_target = math.ceil((total_pages - read_pages) / days_to_target)
                self.daily_target.value = f"{daily_target} pages/day"                
            else:
                print("Target date is today or in the past.")
        else:
            print("Total pages or target date not set.")
           
    def title_entered(self, e):
        if e.control.value:
            self.value_dict["title"] = e.control.value

    def total_pages_entered(self, e):
        if e.control.value:
            try:
                self.value_dict["total_pages"] = int(e.control.value)
                print(f"Total pages entered: {self.value_dict['total_pages']}")
                self.calc_daily_target()
            except ValueError:
                print("Invalid number of total pages.")
        self.page.update()
                                    
    def open_date_picker(self, e):
        # Open the DatePicker
        date_picker = ft.DatePicker(
            first_date=datetime.date.today(),
            last_date=datetime.date(2030, 12, 31),
            on_change=self.date_changed,
            on_dismiss=self.date_dismissed,
        )
        self.page.overlay.append(date_picker)
        date_picker.open = True
        self.page.update()

    def date_changed(self, e):
        # Update the dictionary with the selected date from the DatePicker
        target_date = e.control.value.date()  # Directly use the datetime object
        self.value_dict["target_date"] = target_date

        print(f"Target date value entered: {target_date}, days to the target date: {(target_date - datetime.date.today()).days}")
        self.calc_daily_target()

        self.target_date_button.content.content.controls[1].value = f"Finish by: {target_date.strftime('%Y-%m-%d')}"
        self.page.overlay.clear()
        self.page.update()

    def date_dismissed(self, e):
        # Close the DatePicker when dismissed
        self.page.overlay.clear()
        self.page.update()

    def register_book(self, e):
        # Construct the path to the database file
        db_path = os.path.join(os.path.dirname(__file__), 'db', 'books.db')

        # Connect to the database
        conn = connect_to_database(db_path)

        # Insert the book data into the database
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO book (title, total_pages, read_pages, registered_date, target_date, finished)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    self.value_dict["title"],
                    self.value_dict["total_pages"],
                    self.value_dict["read_pages"],
                    datetime.date.today(),
                    self.value_dict["target_date"],
                    False  # Initial finished status is False
                )
            )
            conn.commit()
            print("Book registered successfully.")
            # Optionally, provide user feedback
            self.page.snack_bar = ft.SnackBar(ft.Text("Book registered successfully!"))
            self.page.snack_bar.open = True
            # Refresh the book list
            self.app.book_list.update_book_list()
        except Exception as e:
            print(f"Error registering book: {e}")
            # Optionally, provide user feedback
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error registering book: {e}"), bgcolor=ft.Colors.RED)
            self.page.snack_bar.open = True
        finally:
            conn.close()
        self.page.update()


## Book list - view, edit and delete
class HeaderText(ft.Text):
    def __init__(self, value):
        super().__init__(
            value=value,
            style=ft.TextStyle(color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD, size=12),
            expand=True
        )

class ListText(ft.Text):
    def __init__(self, value):
        super().__init__(
            value=value,
            style=ft.TextStyle(color=ft.Colors.SECONDARY, weight=ft.FontWeight.BOLD, size=12),
            expand=True
        )

class EditBookDialog(ft.AlertDialog):
    def __init__(self, page, book, on_update, on_delete):
        super().__init__(
            content_padding=ft.padding.symmetric(vertical=5, horizontal=15)
        )
        self.page = page
        self.book = book
        self.on_update = on_update
        self.on_delete = on_delete

        self.title_input = ft.TextField(label="Title", value=book["title"])
        self.total_pages_input = ft.TextField(label="Total Pages", value=str(book["total_pages"]), keyboard_type=ft.KeyboardType.NUMBER)        
        self.read_pages_input = ft.TextField(label="Read Pages", value=str(book["read_pages"]), keyboard_type=ft.KeyboardType.NUMBER)
        self.target_date_input = ft.TextField(label="Target Date", value=book["target_date"])

        self.content = ft.Column(
            spacing=15,
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            on_click=self.close_dialog,
                            icon_color=ft.Colors.PRIMARY
                        )
                    ],
                    alignment=ft.MainAxisAlignment.END
                ),
                self.title_input,
                self.total_pages_input,
                self.read_pages_input,
                self.target_date_input,
                ft.Row(
                    controls=[
                        ft.ElevatedButton("Update", on_click=self.update_book),
                        ft.ElevatedButton("Delete", on_click=self.delete_book, color=ft.Colors.ON_TERTIARY, bgcolor=ft.Colors.TERTIARY)
                    ],
                    alignment=ft.MainAxisAlignment.END,
                )
            ]
        )

    def update_book(self, e):
        self.book["title"] = self.title_input.value
        self.book["read_pages"] = int(self.read_pages_input.value)
        self.book["target_date"] = self.target_date_input.value
        self.on_update(self.book)
        self.close_dialog(e)

    def delete_book(self, e):
        self.on_delete(self.book)
        self.close_dialog(e)

    def close_dialog(self, e):
        self.page.close(self)

        
class BookList(ft.Column):
    def __init__(self, page):
        super().__init__()

        self.page = page
        self.book_list = ft.Column(spacing=0)
        # Add headers
        headers = ft.Row(
            controls=[
                HeaderText("Title"),
                HeaderText("Remaining pages"),
                HeaderText("Target date"),
                HeaderText("Daily target"),
                ft.Container(width=50),
            ],
        )
        self.controls.append(headers)
        self.controls.append(self.book_list)

        self.update_book_list()

    def update_book_list(self):
        # Clear the current list
        self.book_list.controls.clear()

        db_path = os.path.join(os.path.dirname(__file__), 'db', 'books.db')
        conn = connect_to_database(db_path)
        books = get_data(conn, "book")

        for book in books:
            remaining_pages = book["total_pages"] - book["read_pages"]
            
            # Convert the target_date string to a datetime.date object
            target_date = datetime.datetime.strptime(book["target_date"], "%Y-%m-%d").date()
            days_to_target = (target_date - datetime.date.today()).days
            
            if days_to_target > 0:
                daily_target = math.ceil(remaining_pages / days_to_target)
                daily_target_text = f"{daily_target} pages/day"
            else:
                daily_target_text = "Target date passed"

            book_entry = ft.Row(
                controls=[
                    ListText(book["title"]),
                    ListText(f'{remaining_pages} pages'),
                    ListText(book["target_date"]),
                    ListText(daily_target_text),
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        icon_size=17,
                        padding=ft.padding.all(0),
                        tooltip="Edit or Delete Book",
                        on_click=lambda e, book=book: self.open_edit_dialog(book)
                    ),
                ]
            )
            self.book_list.controls.append(book_entry)

        # Close the database connection
        conn.close()

        # Update the page
        self.page.update()

    def open_edit_dialog(self, book):
        def on_update(updated_book):
            # Construct the path to the database file
            db_path = os.path.join(os.path.dirname(__file__), 'db', 'books.db')

            # Connect to the database
            conn = connect_to_database(db_path)

            # Update the book data in the database
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE book
                SET title = ?, total_pages = ?, read_pages = ?, target_date = ?
                WHERE id = ?
            """, (updated_book["title"], updated_book["total_pages"], updated_book["read_pages"], updated_book["target_date"], updated_book["id"]))
            conn.commit()
            conn.close()

            # Refresh the book list
            self.update_book_list()

        def on_delete(book_to_delete):
            # Construct the path to the database file
            db_path = os.path.join(os.path.dirname(__file__), 'db', 'books.db')

            # Connect to the database
            conn = connect_to_database(db_path)

            # Delete the book data from the database
            cursor = conn.cursor()
            cursor.execute("DELETE FROM book WHERE id = ?", (book_to_delete["id"],))
            conn.commit()
            conn.close()

            # Refresh the book list
            self.update_book_list()

        dialog = EditBookDialog(self.page, book, on_update, on_delete)
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()


## Yomou              
class Yomou(ft.Column):
    def __init__(self, page):
        super().__init__(
            expand=True,
        )
        
        self.page = page
        self.register = Register(self)
        self.book_list = BookList(page)
        
        self.controls = [
            self.register,
            self.book_list,
        ]

        
### MAIN ###
def main(page: ft.Page):
    page.window.width = 600
    page.window.height = 800
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme = ft.Theme(color_scheme_seed="light_blue")
    page.padding = 20

    db_path = os.path.join(os.path.dirname(__file__), 'db', 'books.db')
    conn = connect_to_database(db_path)
    create_book_table(conn)
    conn.close()

    app = Yomou(page)
    page.add(app)

ft.app(main)
