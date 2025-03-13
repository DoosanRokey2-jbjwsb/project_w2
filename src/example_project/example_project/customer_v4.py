import sys
import threading
import queue
import rclpy
import signal
from rclpy.node import Node
from rclpy.qos import QoSProfile
from ament_index_python.packages import get_package_share_directory

import os

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from std_msgs.msg import String
from functools import partial

class CoffeeOrderNode(Node):
    def __init__(self):
        super().__init__('coffee_order_node')
        qos_profile = QoSProfile(depth=5)
        self.order_publisher = self.create_publisher(String, 'coffee_order', qos_profile)
        self.queue = queue.Queue()
        self.timer = self.create_timer(0.1, self.publish_order)

    def publish_order(self):
        while not self.queue.empty():
            order = self.queue.get()
            msg = String()
            msg.data = order
            self.order_publisher.publish(msg)
            self.get_logger().info(f'Published order: {order}')

class MainWindow(QMainWindow):
    def __init__(self, node):
        super().__init__()
        self.node = node
        self.setWindowTitle("커피 주문 시스템")
        self.setGeometry(100, 100, 1200, 800)
        
        # 메인 위젯과 레이아웃
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        
        # 상단 헤더 버튼 생성
        header_layout = QHBoxLayout()
        self.header_buttons = []
        headers = ["인원수 입력", "에스프레소 주문", "선물 보내기"]
        
        for text in headers:
            button = QPushButton(text)
            button.setStyleSheet("""
                QPushButton {
                    background-color: gray;
                    color: white;
                    padding: 10px;
                    border: none;
                    font-size: 14px;
                }
            """)
            self.header_buttons.append(button)
            header_layout.addWidget(button)
        
        main_layout.addLayout(header_layout)
        
        # 스택 위젯 생성
        self.stack_widget = QStackedWidget()
        
        # 페이지 생성
        self.stack_widget.addWidget(self.create_people_page())
        self.stack_widget.addWidget(self.create_order_page())
        self.stack_widget.addWidget(self.create_gift_page())
        
        main_layout.addWidget(self.stack_widget)
        main_widget.setLayout(main_layout)

        # 헤더 버튼 연결
        for i, button in enumerate(self.header_buttons):
            button.clicked.connect(lambda checked, index=i: self.change_page(index))

    def create_people_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        # 중앙 정렬을 위한 레이아웃
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignCenter)
        
        # 안내 텍스트
        label = QLabel("인원수를 입력해주세요")
        label.setStyleSheet("font-size: 20px;")
        center_layout.addWidget(label)
        
        # 스핀박스로 숫자 입력
        self.people_spinbox = QSpinBox()
        self.people_spinbox.setMinimum(1)
        self.people_spinbox.setMaximum(10)
        self.people_spinbox.setValue(1)
        self.people_spinbox.setFixedWidth(200)
        self.people_spinbox.setStyleSheet("""
            QSpinBox {
                font-size: 16px;
                padding: 5px;
            }
        """)
        center_layout.addWidget(self.people_spinbox)
        
        # 입력 버튼
        submit_btn = QPushButton("입력하기")
        submit_btn.setFixedWidth(200)
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: gray;
                color: white;
                padding: 10px;
                font-size: 16px;
            }
        """)
        center_layout.addWidget(submit_btn)
        
        layout.addLayout(center_layout)
        page.setLayout(layout)
        return page

    def create_order_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        # 커피 선택 영역
        coffee_layout = QHBoxLayout()
        coffee_types = ["과테말라 안티구아", "콜롬비아 수프리모", "케냐 AA", "코스타리카 따라주"]
        
        for coffee in coffee_types:
            coffee_widget = QWidget()
            coffee_v_layout = QVBoxLayout()
            
            # 커피 이미지
            image_label = QLabel()
            pixmap = QPixmap("coffee.png")
            if pixmap.isNull():
                image_label.setText("이미지 없음")
            else:
                image_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
            coffee_v_layout.addWidget(image_label)
            
            # 커피 이름 버튼
            coffee_btn = QPushButton(coffee)
            coffee_btn.setStyleSheet("""
                QPushButton {
                    background-color: gray;
                    color: white;
                    padding: 10px;
                }
            """)
            coffee_v_layout.addWidget(coffee_btn)
            
            coffee_widget.setLayout(coffee_v_layout)
            coffee_layout.addWidget(coffee_widget)

        layout.addLayout(coffee_layout)

        # 주문 내역 및 버튼
        order_layout = QVBoxLayout()
        self.order_text = QTextEdit()
        self.order_text.setReadOnly(True)
        order_layout.addWidget(self.order_text)

        # 합계 표시
        self.total_label = QLabel("합계: 0원")
        order_layout.addWidget(self.total_label)

        # 버튼 영역
        button_layout = QHBoxLayout()
        reset_btn = QPushButton("초기화")
        order_btn = QPushButton("주문하기")
        button_layout.addWidget(reset_btn)
        button_layout.addWidget(order_btn)
        order_layout.addLayout(button_layout)

        layout.addLayout(order_layout)
        page.setLayout(layout)
        return page

    def create_gift_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        # 중앙 정렬을 위한 레이아웃
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignCenter)
        
        # 안내 텍스트
        label = QLabel("선물을 보낼 테이블\n번호를 입력해주세요")
        label.setStyleSheet("font-size: 20px;")
        label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(label)
        
        # 스핀박스로 테이블 번호 입력
        self.table_spinbox = QSpinBox()
        self.table_spinbox.setMinimum(1)
        self.table_spinbox.setMaximum(10)
        self.table_spinbox.setValue(1)
        self.table_spinbox.setFixedWidth(200)
        self.table_spinbox.setStyleSheet("""
            QSpinBox {
                font-size: 16px;
                padding: 5px;
            }
        """)
        center_layout.addWidget(self.table_spinbox)
        
        # 입력 버튼
        submit_btn = QPushButton("입력하기")
        submit_btn.setFixedWidth(200)
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: gray;
                color: white;
                padding: 10px;
                font-size: 16px;
            }
        """)
        center_layout.addWidget(submit_btn)
        
        layout.addLayout(center_layout)
        page.setLayout(layout)
        return page

    def change_page(self, index):
        self.stack_widget.setCurrentIndex(index)
        
        # 선택된 버튼 스타일 변경
        for i, button in enumerate(self.header_buttons):
            if i == index:
                button.setStyleSheet("""
                    QPushButton {
                        background-color: darkgray;
                        color: white;
                        padding: 10px;
                        border: none;
                        font-size: 14px;
                    }
                """)
            else:
                button.setStyleSheet("""
                    QPushButton {
                        background-color: gray;
                        color: white;
                        padding: 10px;
                        border: none;
                        font-size: 14px;
                    }
                """)

def main(args=None):
    rclpy.init(args=args)
    node = CoffeeOrderNode()
    ros_thread = threading.Thread(target=lambda: rclpy.spin(node), daemon=True)
    ros_thread.start()

    app = QApplication(sys.argv)
    window = MainWindow(node)
    window.show()

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
