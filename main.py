import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QLabel, QPushButton, QDateEdit, QComboBox,
                             QMessageBox)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pymysql
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.canvas = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Graph of number of employees")
        self.setGeometry(50, 50, 1920, 1080)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Filter widgets
        filter_layout = QHBoxLayout()
        layout.addLayout(filter_layout)

        filter_layout.addWidget(QLabel("Start Date:"))
        self.start_date = QDateEdit()
        filter_layout.addWidget(self.start_date)

        filter_layout.addWidget(QLabel("End Date:"))
        self.end_date = QDateEdit()
        filter_layout.addWidget(self.end_date)

        filter_layout.addWidget(QLabel("Department:"))
        self.department = QComboBox()
        self.fill_departments()
        filter_layout.addWidget(self.department)

        filter_button = QPushButton("Apply Filters")
        filter_button.clicked.connect(self.update_graph)
        filter_layout.addWidget(filter_button)

        self.view_button = QPushButton("Switch View")
        self.view_button.clicked.connect(self.switch_view)
        filter_layout.addWidget(self.view_button)

        self.view_3d = False  # Initially in 2D view

        # Graf
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.canvas_layout = QVBoxLayout()
        layout.addLayout(self.canvas_layout)

        self.update_graph()

    def switch_view(self):
        self.view_3d = not self.view_3d
        self.update_graph()

    def fill_departments(self):
        conn = pymysql.connect(host='localhost', user='root', password='', db='employees')
        sql_query = "SELECT dept_no, dept_name FROM departments ORDER BY dept_no;"
        df = pd.read_sql_query(sql_query, conn)
        conn.close()

        self.department.addItem("All", None)
        for index, row in df.iterrows():
            self.department.addItem(row["dept_name"], row["dept_no"])

    def update_graph(self):
        if self.canvas:
            self.canvas_layout.removeWidget(self.canvas)  # Remove the old canvas
            self.canvas.deleteLater()
            self.fig.clear()

        self.fig = Figure(figsize=(5, 4), dpi=100)

        if not self.view_3d:
            ax = self.fig.add_subplot(111)
        else:
            ax = self.fig.add_subplot(111, projection='3d')

        self.canvas = FigureCanvas(self.fig)
        self.canvas_layout.addWidget(self.canvas)  # Add the new canvas

        self.fig.clear()

        if not self.view_3d:
            ax = self.fig.add_subplot(111)
        else:
            ax = self.fig.add_subplot(111, projection='3d')

        df = self.get_data()

        if df is None:
            QMessageBox.warning(self, "Invalid Filter", "Please check your filter settings and try again.")
            return

        if not self.view_3d:
            for dept_name, dept_df in df.groupby("dept_name"):
                dept_df = dept_df.sort_values(["year", "month"])
                ax.plot(dept_df["year"].astype(str) + "-" + dept_df["month"].astype(str), dept_df["num_employees"],
                        label=dept_name)
        else:
            for dept_name, dept_df in df.groupby("dept_name"):
                dept_df = dept_df.sort_values(["year", "month"])
                ax.bar3d(dept_df["year"], dept_df["month"], 0, 1, 1, dept_df["num_employees"],
                         label=dept_name)

        ax.legend()
        if not self.view_3d:
            ax.set_xlabel("Year - Month")
        else:
            ax.set_xlabel("Year")
            ax.set_ylabel("Month")
        ax.set_ylabel("Number of employees")
        ax.set_title("Number of employees per department, year and month")
        self.canvas.draw()

    def get_data(self):
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        selected_department = self.department.currentData()

        if start_date > end_date:
            return None

        conn = pymysql.connect(host='localhost', user='root', password='', db='employees')

        sql_query = f"""
            SELECT de.dept_no, d.dept_name, YEAR(de.from_date) as year, MONTH(de.from_date) as month, COUNT(de.emp_no) as num_employees
        FROM dept_emp de
        JOIN departments d ON de.dept_no = d.dept_no
        WHERE de.to_date > NOW()
        AND de.from_date >= '{start_date}'
        AND de.from_date <= '{end_date}'
        {"AND de.dept_no = '" + selected_department + "'" if selected_department else ""}
        GROUP BY de.dept_no, year, month
        ORDER BY de.dept_no, year, month;
        """
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_app = MyApp()
    main_app.show()
    sys.exit(app.exec_())