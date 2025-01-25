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
            label_style=ft.TextStyle(size=13),
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
            style=ft.TextStyle(color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD, size=14),
            value="Daily target",
        )
                
        self.bt_register = ft.ElevatedButton(
            " YOMOU ",
            on_click=self.register_book
        )

        # Initialize the DatePicker button
        self.target_date_button = ft.TextButton(
            content=ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.EDIT_CALENDAR),
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
                    spacing=0,
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
        self.value_dict["title"] = e.control.value if e.control.value else None

    def total_pages_entered(self, e):
        if e.control.value:
            try:
                self.value_dict["total_pages"] = int(e.control.value)
                self.calc_daily_target()
            except ValueError:
                print("Invalid number of total pages.")
                self.value_dict["total_pages"] = None
        else:
            self.value_dict["total_pages"] = None
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
        # self.page.overlay.clear()
        self.page.update()

    def date_dismissed(self, e):
        # Close the DatePicker when dismissed
        self.page.overlay.clear()
        self.page.update()

    def register_book(self, e):
        # Validate that the book title and total pages are not blank
        if not self.value_dict["title"] or self.value_dict["total_pages"] is None:
            error_message = "Both 'Book title' and 'Total pages' are required."
            print(error_message)
            self.page.snack_bar = ft.SnackBar(ft.Text(error_message), bgcolor=ft.Colors.ON_PRIMARY_CONTAINER)
            self.page.snack_bar.open = True
            self.page.update()
            return

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
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Book registered successfully!"),
                duration=1000)
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
            style=ft.TextStyle(color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD, size=14),
            expand=True
        )

class HeaderIcon(ft.Icon):
    def __init__(self, icon_name, value):
        super().__init__(
            name=icon_name,
            size=20,
            tooltip=value,
        )
        
class SortIcon(ft.IconButton):
    def __init__(self, icon_name, on_click):
        super().__init__(
            icon=icon_name,
            icon_size=25,
            tooltip="Sort",
            on_click=on_click
        )    
        
class ListText(ft.Text):
    def __init__(self, value, color=ft.Colors.SECONDARY, weight=ft.FontWeight.NORMAL, size=13):
        super().__init__(
            value=value,
            style=ft.TextStyle(color=color, weight=weight, size=size),
            expand=True
        )

class DeleteConfirmationDialog(ft.AlertDialog):
    def __init__(self, page, book, on_confirm):
        super().__init__(
            title=ft.Text("Delete Book"),
            content=ft.Text("Do you want to delete this book?"),
            actions=[
                ft.TextButton("Cancel", on_click=self.close_dialog),
                ft.ElevatedButton("Confirm", on_click=lambda e: self.confirm_and_close(on_confirm)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page = page

    def close_dialog(self, e):
        self.page.close(self)
        self.page.update()

    def confirm_and_close(self, on_confirm):
        on_confirm()
        self.page.close(self)
        self.page.update()
        self.close_dialog(None)

# Dialog to edit or delete a book
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
        self.target_date = datetime.datetime.strptime(book["target_date"], "%Y-%m-%d").date()
        self.target_date_button = ft.TextButton(
            content=ft.Row(
                spacing=0,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.EDIT_CALENDAR,
                    ),
                    ft.Text(f"Target Date: {self.target_date.strftime('%Y-%m-%d')}"),
                ]
            ),
            on_click=self.open_date_picker,
        )

        self.confirmation_dialog = DeleteConfirmationDialog(
            self.page,
            self.book,
            on_confirm=lambda: self.delete_book(),
        )

        self.content = ft.Column(
            height=380,
            spacing=15,
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            on_click=self.close_dialog,
                            icon_color=ft.Colors.PRIMARY,
                            tooltip="Close menu",
                        )
                    ],
                    alignment=ft.MainAxisAlignment.END
                ),
                self.title_input,
                self.total_pages_input,
                self.read_pages_input,
                self.target_date_button,
                ft.Row(
                    controls=[
                        ft.Container(),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_FOREVER_ROUNDED,
                            tooltip="Delete book",
                            on_click=lambda e: page.open(self.confirmation_dialog),
                            icon_color=ft.Colors.TERTIARY,
                        ),
                        ft.ElevatedButton("Update", tooltip="Update book", on_click=self.update_book),
                        ft.Container(),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                )
            ]
        )

    # DatePicker for setting the new target date
    def open_date_picker(self, e):
        date_picker = ft.DatePicker(
            first_date=datetime.date.today(),
            last_date=datetime.date(2030, 12, 31),
            on_change=self.date_changed,
            on_dismiss=self.date_dismissed,
        )
        self.page.overlay.append(date_picker)
        # date_picker.pick_date()
        date_picker.open = True
        self.page.update()
        
    def date_changed(self, e):
        target_date = e.control.value.date()
        self.target_date = target_date.strftime('%Y-%m-%d')
        self.target_date_button.content.controls[1].value = f"Target Date: {self.target_date}"
        self.update()
        
    def date_dismissed(self, e):
        self.page.overlay.clear()
        self.update()


    def update_book(self, e):
        self.book["title"] = self.title_input.value
        self.book["total_pages"] = int(self.total_pages_input.value)
        self.book["read_pages"] = int(self.read_pages_input.value)
        self.book["target_date"] = self.target_date
        self.on_update(self.book)
        self.close_dialog(e)

    def delete_book(self):
        self.on_delete(self.book)
        self.close_dialog(self)

    def close_dialog(self, e):
        self.page.close(self)


# Main book list component
class BookList(ft.Column):
    def __init__(self, page):
        super().__init__(
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

        self.page = page
        self.book_list = ft.Column(spacing=0)
        self.sort_by = "read_percentage"  # Default sorting criteria
        self.sort_order = True  # True for ascending, False for descending

        headers = ft.Row(
            controls=[
                ft.Container(expand=5),                
                # ft.Container(expand=5, content=HeaderText("Title")),
                ft.Row(spacing=0, expand=2, controls=[
                    ft.Container(width=8, content=HeaderIcon(ft.Icons.INCOMPLETE_CIRCLE, "Read")),
                    SortIcon(ft.Icons.ARROW_DROP_DOWN, on_click=self.sort_by_read_percentage),
                ]),
                ft.Row(spacing=0, expand=3, controls=[
                    ft.Container(width=8, content=HeaderIcon(ft.Icons.CALENDAR_MONTH, "Target date")),
                    SortIcon(ft.Icons.ARROW_DROP_DOWN, on_click=self.sort_by_target_date),
                ]),
                ft.Container(expand=4, alignment=ft.alignment.center_left, content=HeaderIcon(ft.Icons.MENU_BOOK, "Daily target")),
                ft.Container(width=15),
            ],
        )
        self.controls.append(headers)
        self.controls.append(self.book_list)

        self.update_book_list()

    def update_book_list(self):
        self.book_list.controls.clear()

        db_path = os.path.join(os.path.dirname(__file__), 'db', 'books.db')
        conn = connect_to_database(db_path)
        books = get_data(conn, "book")

        if self.sort_by == "read_percentage":
            books.sort(key=lambda book: (book["read_pages"] / book["total_pages"]) * 100,
                       reverse=not self.sort_order)
        elif self.sort_by == "target_date":
            books.sort(key=lambda book: datetime.datetime.strptime(book["target_date"], "%Y-%m-%d").date(),
                       reverse=not self.sort_order)

        for book in books:
            remaining_pages = book["total_pages"] - book["read_pages"]
            read_percentage = round((book["read_pages"] / book["total_pages"]) * 100)

            target_date = datetime.datetime.strptime(book["target_date"], "%Y-%m-%d").date()
            days_to_target = (target_date - datetime.date.today()).days

            if days_to_target > 0:
                daily_target = math.ceil(remaining_pages / days_to_target)
                daily_target_text = f"{daily_target} pages/day"
                daily_target_color = ft.Colors.SECONDARY
                daily_target_weight = ft.FontWeight.NORMAL
            else:
                daily_target_text = "Target date passed"
                daily_target_color = ft.Colors.TERTIARY
                daily_target_weight = ft.FontWeight.BOLD

            book_entry = ft.Row(
                controls=[
                    ft.Container(expand=5, content=ListText(book["title"], weight=ft.FontWeight.BOLD, size=14)),
                    ft.Container(expand=2, content=ListText(f'{read_percentage} %')),
                    ft.Container(expand=3, content=ListText(target_date)),
                    ft.Container(expand=4, content=ListText(daily_target_text, daily_target_color, daily_target_weight)),
                    ft.Container(width=15, content=ft.IconButton(
                        icon=ft.Icons.EDIT,
                        icon_size=17,
                        padding=ft.padding.all(0),
                        tooltip="Edit or Delete Book",
                        on_click=lambda e, book=book: self.open_edit_dialog(book)
                    )),
                ]
            )
            self.book_list.controls.append(book_entry)

        conn.close()
        self.page.update()

    def sort_by_read_percentage(self, e):
        self.sort_by = "read_percentage"
        self.sort_order = not self.sort_order
        self.update_book_list()

    def sort_by_target_date(self, e):
        self.sort_by = "target_date"
        self.sort_order = not self.sort_order
        self.update_book_list()

    def open_edit_dialog(self, book):
        def on_update(updated_book):
            db_path = os.path.join(os.path.dirname(__file__), 'db', 'books.db')
            conn = connect_to_database(db_path)

            cursor = conn.cursor()
            cursor.execute("""
                UPDATE book
                SET title = ?, total_pages = ?, read_pages = ?, target_date = ?
                WHERE id = ?
            """, (updated_book["title"], updated_book["total_pages"], updated_book["read_pages"], updated_book["target_date"], updated_book["id"]))
            conn.commit()
            conn.close()

            self.update_book_list()

        def on_delete(book_to_delete):
            db_path = os.path.join(os.path.dirname(__file__), 'db', 'books.db')
            conn = connect_to_database(db_path)

            cursor = conn.cursor()
            cursor.execute("DELETE FROM book WHERE id = ?", (book_to_delete["id"],))
            conn.commit()
            conn.close()

            self.update_book_list()

            self.page.snack_bar = ft.SnackBar(ft.Text(f"Deleted book: '{book_to_delete['title']}'"), bgcolor=ft.Colors.ON_PRIMARY_CONTAINER)
            self.page.snack_bar.open = True
            self.page.update()

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
    page.add(ft.SafeArea(app))

ft.app(main)