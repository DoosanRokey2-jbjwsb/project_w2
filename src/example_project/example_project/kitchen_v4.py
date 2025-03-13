import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from example_interfaces.srv import Trigger
import threading
import signal
from datetime import datetime
import sqlite3

COFFEE_BEANS = [
    "과테말라 안티구아",
    "콜롬비아 수프리모",
    "케냐 AA",
    "코스타리카 따라주"
]
COFFEE_PRICE = 3000

class OrderServiceNode(Node):
    def __init__(self):
        super().__init__('order_service_node')
        self.srv = self.create_service(Trigger, 'order_service', self.order_callback)
        self.emit_signal = None

    def order_callback(self, request, response):
        if self.emit_signal is not None:
            self.emit_signal(request.data)
            response.success = True
            response.message = 'Order received successfully'
        else:
            response.success = False
            response.message = 'GUI not connected'
        return response

    def set_emit_signal(self, emit_func):
        self.emit_signal = emit_func

class MainWindow(QMainWindow):
    order_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("주문 목록 화면")
        self.setGeometry(100, 100, 1200, 800)
        
        self.connect_database()
        self.setup_ui()
        self.order_signal.connect(self.update_order)

    def setup_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        
        self.list_widget = QListWidget()
        self.list_widget.addItems(["테이블 당 주문 내역", "로봇 제어"])
        self.list_widget.setStyleSheet("QListWidget::item { padding: 20px; }")
        self.list_widget.currentRowChanged.connect(self.display_page)
        
        self.stack_widget = QStackedWidget()
        
        order_page = QWidget()
        order_layout = QVBoxLayout()

        tables_layout = QHBoxLayout()
        self.text_browsers = []
        for i in range(1, 5):
            table_widget = QWidget()
            table_layout = QVBoxLayout()
            table_layout.addWidget(QLabel(f"테이블 {i}"))
            
            text_browser = QTextBrowser()
            self.text_browsers.append(text_browser)
            table_layout.addWidget(text_browser)
            
            btn_layout = QVBoxLayout()
            confirm_btn = QPushButton("주문확인")
            serving_btn = QPushButton("서빙완료")
            btn_layout.addWidget(confirm_btn)
            btn_layout.addWidget(serving_btn)
            table_layout.addLayout(btn_layout)
            
            table_widget.setLayout(table_layout)
            tables_layout.addWidget(table_widget)
            
        order_layout.addLayout(tables_layout)
        
        bottom_layout = QHBoxLayout()
        daily_sales_btn = QPushButton("일일매출")
        daily_sales_btn.clicked.connect(self.show_daily_revenue)
        menu_sales_btn = QPushButton("메뉴별매출")
        select_menu_btn = QPushButton("선호 메뉴")
        bottom_layout.addWidget(daily_sales_btn)
        bottom_layout.addWidget(menu_sales_btn)
        bottom_layout.addWidget(select_menu_btn)
        order_layout.addLayout(bottom_layout)
        
        order_page.setLayout(order_layout)
        
        robot_page = QWidget()
        robot_layout = QVBoxLayout()
        
        robot_header_layout = QHBoxLayout()
        order_header = QLabel("주문 목록")
        serving_header = QLabel("서빙 로봇")
        robot_header_layout.addWidget(order_header)
        robot_header_layout.addWidget(serving_header)
        
        table_button_layout = QHBoxLayout()
        self.table_buttons = []
        for i in range(1, 5):
            button = QPushButton(f"테이블 {i}")
            button.clicked.connect(lambda _, table=i: self.send_robot_to_table(table))
            self.table_buttons.append(button)
            table_button_layout.addWidget(button)

        description_label = QLabel("테이블 버튼\n버튼 클릭시 서빙 로봇을 해당하는 테이블로 이동하는 명령을 보냅니다.")
        description_label.setStyleSheet("QLabel { background-color: lightgray; padding: 10px; }")

        robot_layout.addLayout(robot_header_layout)
        robot_layout.addLayout(table_button_layout)
        robot_layout.addWidget(description_label)
        robot_page.setLayout(robot_layout)
        
        self.stack_widget.addWidget(order_page)
        self.stack_widget.addWidget(robot_page)
        
        main_layout.addWidget(self.list_widget, 1)
        main_layout.addWidget(self.stack_widget, 3)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def display_page(self, index):
        self.stack_widget.setCurrentIndex(index)

    def send_robot_to_table(self, table):
        print(f"로봇이 테이블 {table}로 이동합니다.")

    def update_order(self, order_data):
        try:
            table_id, order_info = order_data.split(',', 1)
            table_num = int(table_id.replace('table', ''))
            if 1 <= table_num <= len(self.text_browsers):
                self.text_browsers[table_num-1].append(f"{order_info}\n")
                self.insert_data(table_num, order_info)
        except Exception as e:
            print(f"Error updating order: {e}")

    def connect_database(self):
        self.conn = sqlite3.connect('database.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_number INTEGER NOT NULL,
            coffee_bean TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        self.conn.commit()

    def insert_data(self, table_num, order_info):
        try:
            coffee_bean, quantity = order_info.split('x')
            coffee_bean = coffee_bean.strip()
            quantity = int(quantity.strip())
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.cursor.execute(
                "INSERT INTO orders (table_number, coffee_bean, quantity, time) VALUES (?, ?, ?, ?)",
                (table_num, coffee_bean, quantity, current_time)
            )
            self.conn.commit()
        except Exception as e:
            print(f"Error inserting data: {e}")

    def show_daily_revenue(self):
        try:
            self.cursor.execute("""
                SELECT coffee_bean, SUM(quantity)
                FROM orders
                WHERE date(time) = date('now')
                GROUP BY coffee_bean
            """)
            rows = self.cursor.fetchall()
            total_revenue = sum(COFFEE_PRICE * quantity for _, quantity in rows)
            
            msg = QMessageBox()
            msg.setWindowTitle("일일 매출")
            msg.setText(f"오늘의 총 매출: {total_revenue:,}원")
            msg.exec_()
        except Exception as e:
            print(f"Error calculating revenue: {e}")

def main():
    rclpy.init()
    service_node = OrderServiceNode()
    app = QApplication(sys.argv)
    window = MainWindow()
    service_node.set_emit_signal(window.order_signal.emit)
    ros_thread = threading.Thread(target=lambda: rclpy.spin(service_node), daemon=True)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    ros_thread.start()
    window.show()
    
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        pass
    finally:
        service_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
