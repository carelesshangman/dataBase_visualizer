import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pymysql
import random
from PyQt5.QtWidgets import QCheckBox, QScrollArea
import pandas as pd
from PyQt5.QtWidgets import QPushButton

class DatabaseManager:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.conn = None

    def connect(self):
        try:
            self.conn = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
        except pymysql.DatabaseError as e:
            print(f"Error connecting to database: {e}")
            sys.exit(1)

    def get_departments(self):
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT dept_no FROM departments")
        results = cursor.fetchall()
        cursor.close()
        self.conn.close()
        return [row[0] for row in results]

    def get_department_data(self, department):
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT YEAR(from_date), MONTH(from_date), COUNT(*) FROM dept_emp WHERE dept_no = '{department}' GROUP BY YEAR(from_date), MONTH(from_date)")
        results = cursor.fetchall()
        cursor.close()
        self.conn.close()
        return [{'year': row[0], 'month': row[1], 'no_employed': row[2]} for row in results]


class MainWindow(QMainWindow):
    def __init__(self, dbManager):
        super().__init__()
        self.dbManager = dbManager
        self.setWindowTitle('Tower Graph maker thingy')
        self.setGeometry(100, 100, 800, 600)

        main_widget = QWidget(self)
        layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        export_data_button = QPushButton('Export Data')
        export_data_button.clicked.connect(self.export_data)
        layout.addWidget(export_data_button)

        departments = self.dbManager.get_departments()

        # Generate a random color for each department
        self.department_colors = {department: (random.random(), random.random(), random.random()) for department in departments}

        # Create a dictionary to keep track of which departments are selected
        self.selected_departments = {}

        # Add checkboxes for department selection
        scroll = QScrollArea(main_widget)
        scroll.setWidgetResizable(True)
        scrollContent = QWidget(scroll)
        scrollLayout = QVBoxLayout(scrollContent)
        scroll.setWidget(scrollContent)
        layout.addWidget(scroll)

        for department in departments:
            checkbox = QCheckBox(department)
            checkbox.stateChanged.connect(self.update_graph)
            scrollLayout.addWidget(checkbox)

        self.canvas = FigureCanvas(Figure(figsize=(8, 6)))
        layout.addWidget(self.canvas)

        self.ax = None

    def export_data(self):
        for department, selected in self.selected_departments.items():
            if selected:
                department_data = self.dbManager.get_department_data(department)
                df = pd.DataFrame(department_data)
                df.to_csv(f'{department}_data.csv', index=False)

    def update_graph(self, state):
        department = self.sender().text()
        self.selected_departments[department] = bool(state)
        self.draw_graph()

    def draw_graph(self):
        if self.ax is not None:
            self.ax.clear()
        else:
            self.ax = self.canvas.figure.add_subplot(111, projection='3d')

        for department, selected in self.selected_departments.items():
            if selected:
                department_data = self.dbManager.get_department_data(department)
                x = [data['year'] for data in department_data]
                y = [data['month'] for data in department_data]
                z = [data['no_employed'] for data in department_data]

                # Use the department's color when drawing the bars
                self.ax.bar3d(x, y, [0] * len(x), 0.8, 0.8, z, color=self.department_colors[department], shade=True)

        self.ax.set_xlabel('Year')
        self.ax.set_ylabel('Month')
        self.ax.set_zlabel('No. Employed')
        self.canvas.draw()

if __name__ == '__main__':
    dbManager = DatabaseManager("localhost", "root", "", "employees")
    app = QApplication(sys.argv)
    window = MainWindow(dbManager)
    window.show()
    sys.exit(app.exec_())
