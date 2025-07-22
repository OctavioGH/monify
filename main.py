import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QGroupBox, QLineEdit, QPushButton
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class StockTradingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stock Trading App")
        self.setGeometry(100, 100, 900, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Top section: Alerts and Portfolio
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.create_alerts_table())
        top_layout.addWidget(self.create_portfolio_table())
        layout.addLayout(top_layout)

        # Bottom section: Trade panel and Graph
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.create_trade_panel())
        bottom_layout.addWidget(self.create_graph_info())
        layout.addLayout(bottom_layout)

    def create_alerts_table(self):
        group = QGroupBox("Trade Alerts")
        layout = QVBoxLayout()
        table = QTableWidget(5, 2)
        table.setHorizontalHeaderLabels(["Symbol", "Alert"])
        data = [
            ("AAPL", "Buy"),
            ("GOOGL", "Sell"),
            ("TSLA", "Buy"),
            ("MSFT", "Sell"),
            ("NFLX", "Sell"),
        ]
        for row, (symbol, alert) in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(symbol))
            alert_item = QTableWidgetItem(alert)
            color = Qt.GlobalColor.green if alert == "Buy" else Qt.GlobalColor.red
            alert_item.setBackground(color)
            table.setItem(row, 1, alert_item)

        layout.addWidget(table)
        group.setLayout(layout)
        return group

    def create_portfolio_table(self):
        group = QGroupBox("Portfolio")
        layout = QVBoxLayout()
        table = QTableWidget(3, 2)
        table.setHorizontalHeaderLabels(["Symbol", "Value"])
        data = [
            ("AAPL", "10,500.00"),
            ("MSFT", "5,350.00"),
            ("TSLA", "2,000.00"),
        ]
        for row, (symbol, value) in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(symbol))
            table.setItem(row, 1, QTableWidgetItem(value))

        layout.addWidget(table)
        group.setLayout(layout)
        return group

    def create_trade_panel(self):
        group = QGroupBox("Place Trade")
        layout = QVBoxLayout()

        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Symbol")

        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Quantity")

        btn_layout = QHBoxLayout()
        buy_btn = QPushButton("Buy")
        sell_btn = QPushButton("Sell")
        btn_layout.addWidget(buy_btn)
        btn_layout.addWidget(sell_btn)

        layout.addWidget(QLabel("Symbol"))
        layout.addWidget(self.symbol_input)
        layout.addWidget(QLabel("Quantity"))
        layout.addWidget(self.quantity_input)
        layout.addLayout(btn_layout)
        group.setLayout(layout)
        return group

    def create_graph_info(self):
        group = QGroupBox("AAPL")
        layout = QVBoxLayout()

        graph_label = QLabel()
        graph_label.setFixedHeight(150)
        graph_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        graph_label.setText("Graph Placeholder")

        price = QLabel("Price: AAPL   $150.25")
        high = QLabel("High: AAPL    $151.80")
        low = QLabel("Day's Low:    $148.50")

        font = QFont()
        font.setPointSize(10)
        for label in (price, high, low):
            label.setFont(font)

        layout.addWidget(graph_label)
        layout.addWidget(price)
        layout.addWidget(high)
        layout.addWidget(low)
        group.setLayout(layout)
        return group


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StockTradingApp()
    window.show()
    sys.exit(app.exec())