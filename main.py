import sys
from math import sqrt

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QHBoxLayout, QVBoxLayout, QMainWindow, QAction, qApp, QSpinBox,
    QPushButton, QGroupBox, QLineEdit, QGraphicsView, QGraphicsScene, QMessageBox
)
from PyQt5.QtCore import QSize, Qt, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QDoubleValidator, QPainterPath


MAXIMUM_INPUT_SIZE = 15
POINTS_COUNT = 1000
CAPACITORS_SHIFT = 150


def calc_charge_path(m, q, u, d, v):
    a = +9.8 + q * u / (m * d)
    print(f"a = {a}")
    last_x = v * sqrt(abs(d / a))
    delta_x = last_x / POINTS_COUNT
    x = 0
    res = []
    for i in range(POINTS_COUNT + 1):
        t = x / v
        res.append((x, (a * t**2) / 2))
        x += delta_x
    return res


class GraphicsPanel(QGraphicsView):

    last_x_calculated = QtCore.pyqtSignal(float, float)

    def __init__(self, parent):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self._last_points = []
        self._last_scale = None

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        self.redraw()

    def redraw(self):
        self.setSceneRect(0, 0, self.width(), self.height())
        self.scene.setBackgroundBrush(QColor(255, 255, 255))
        self._draw_capacitors()

    def _draw_capacitors(self):
        self.scene.clear()
        w = self.sceneRect().width()
        h = self.sceneRect().height()
        print(-w/2, w/2)
        self.scene.addLine(0, h/2 - CAPACITORS_SHIFT, w, h/2 - CAPACITORS_SHIFT, QPen(Qt.black, 2))
        self.scene.addLine(0, h/2 + CAPACITORS_SHIFT, w, h/2 + CAPACITORS_SHIFT, QPen(Qt.black, 2))

    def draw_path(self, m, q, u, d, v, s):
        w = self.sceneRect().width()
        h = self.sceneRect().height()

        if self._last_scale != s:
            self.redraw()

        self._last_scale = s
        self._last_points = points = calc_charge_path(m, q, u, d, v)

        ky = CAPACITORS_SHIFT / abs(points[-1][1])
        path = QPainterPath(QPointF(points[0][0] * s, points[0][1] * ky + h / 2))
        for x, y in points[1:]:
            x *= s
            y *= ky
            y += h / 2
            path.lineTo(x, y)

        self.scene.addPath(path, QPen(QColor(100, 100, 100), 1))
        self.last_x_calculated.emit(points[-1][0], points[-1][0] / v)


class RightMenu(QVBoxLayout):

    run_clicked = QtCore.pyqtSignal(float, float, float, float, float, float)
    reset_clicked = QtCore.pyqtSignal()
    scale_changed = QtCore.pyqtSignal(float)

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent)
        self.mass_input = None
        self.mass_spinbox = None
        self.charge_input = None
        self.charge_spinbox = None
        self.voltage_input = None
        self.voltage_spinbox = None
        self.dist_input = None
        self.dist_spinbox = None
        self.velocity_input = None
        self.velocity_spinbox = None
        self.run_button = None
        self.reset_button = None
        self.dist_result = None
        self.scale_input = None
        self.scale_spinbox = None
        self.time_result = None
        self.addWidget(self._create_input_panel(parent), 5)
        self.addWidget(self._create_run_reset_panel(parent), 1)
        self.addWidget(self._create_results_panel(parent), 1)
        self.run_button.clicked.connect(self.run)
        self.reset_button.clicked.connect(self.reset)
        self.scale_input.textEdited.connect(lambda _: self.run())
        self._set_default()

    def _set_default(self):
        self.mass_input.setText("1")
        self.mass_spinbox.setValue(-11)
        self.charge_input.setText("-1,8")
        self.charge_spinbox.setValue(-14)
        self.voltage_input.setText("5000")
        self.dist_input.setText("2,32")
        self.dist_spinbox.setValue(-2)
        self.velocity_input.setText("3")
        self.scale_input.setText("1000")

    def run(self):
        try:
            m = float(self.mass_input.text().replace(',', '.')) * 10 ** int(self.mass_spinbox.text())
            q = float(self.charge_input.text().replace(',', '.')) * 10 ** int(self.charge_spinbox.text())
            u = float(self.voltage_input.text().replace(',', '.')) * 10 ** int(self.voltage_spinbox.text())
            d = float(self.dist_input.text().replace(',', '.')) * 10 ** int(self.dist_spinbox.text())
            v = float(self.velocity_input.text().replace(',', '.')) * 10 ** int(self.velocity_spinbox.text())
            s = float(self.scale_input.text().replace(',', '.')) * 10 ** int(self.scale_spinbox.text())
        except ValueError:
            box = QMessageBox()
            box.setText("Введите данные")
            box.exec()
            return False
        else:
            self.run_clicked.emit(m, q, u, d, v, s)

    def reset(self):
        self.mass_input.setText("")
        self.charge_input.setText("")
        self.voltage_input.setText("")
        self.dist_input.setText("")
        self.dist_result.setText("")
        self.velocity_input.setText("")
        self.reset_clicked.emit()

    def set_results(self, x, t):
        self.dist_result.setText(str(x)[:10])
        self.time_result.setText(str(t)[:10])

    def _create_run_reset_panel(self, parent):
        group = QGroupBox(parent)
        layout = QHBoxLayout(group)
        group.setLayout(layout)
        self.run_button = b1 = QPushButton("▶︎")
        self.reset_button = b2 = QPushButton("↺")
        layout.addWidget(b1)
        layout.addWidget(b2)
        return group

    def _create_results_panel(self, parent):
        group = QGroupBox(parent)
        layout = QVBoxLayout(parent)
        group.setLayout(layout)

        dist_layout = QHBoxLayout(group)
        dist_layout.addWidget(QLabel("Δx: ", group), 1)
        self.dist_result = QLabel("", group)
        dist_layout.addWidget(self.dist_result, 3)
        layout.addLayout(dist_layout)

        time_layout = QHBoxLayout(group)
        time_layout.addWidget(QLabel("Δt: ", group), 1)
        self.time_result = QLabel("", group)
        time_layout.addWidget(self.time_result, 3)
        layout.addLayout(time_layout)

        return group

    def _create_input_panel(self, parent):
        group = QGroupBox(parent)
        layout = QVBoxLayout(group)
        layout.setAlignment(QtCore.Qt.AlignTop)
        group.setLayout(layout)

        # generate mass input layout
        mass_input, mass_spinbox, mass_layout = self._create_layout("m:", group)
        self.mass_input = mass_input
        self.mass_spinbox = mass_spinbox
        layout.addLayout(mass_layout)

        # generate charge input layout
        charge_input, charge_spinbox, charge_layout = self._create_layout("q:", group)
        self.charge_input = charge_input
        self.charge_spinbox = charge_spinbox
        layout.addLayout(charge_layout)

        # generate voltage input layout
        voltage_input, voltage_spinbox, voltage_layout = self._create_layout("U:", group)
        self.voltage_input = voltage_input
        self.voltage_spinbox = voltage_spinbox
        layout.addLayout(voltage_layout)

        # generate dist input layout
        dist_input, dist_spinbox, dist_layout = self._create_layout("d:", group)
        self.dist_input = dist_input
        self.dist_spinbox = dist_spinbox
        layout.addLayout(dist_layout)

        # generate velocity input layout
        velocity_input, velocity_spinbox, velocity_layout = self._create_layout("v:", group)
        self.velocity_input = velocity_input
        self.velocity_spinbox = velocity_spinbox
        layout.addLayout(velocity_layout)

        # generate velocity input layout
        scale_input, scale_spinbox, scale_layout = self._create_layout("scale:", group)
        self.scale_input = scale_input
        self.scale_spinbox = scale_spinbox
        layout.addLayout(scale_layout)

        return group

    @staticmethod
    def _create_layout(text, group):
        line_input = QLineEdit(group)
        line_input.setMaxLength(MAXIMUM_INPUT_SIZE)
        line_input.setValidator(QDoubleValidator())
        layout = QHBoxLayout(group)
        layout.addWidget(QLabel(text), 1)
        layout.addWidget(line_input, 5)
        spinbox = QSpinBox(group)
        spinbox.setMinimum(-40)
        spinbox.setMaximum(40)
        layout.addWidget(spinbox, 1)
        return line_input, spinbox, layout


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setMinimumSize(QSize(1000, 600))
        self.setWindowTitle("sim2")
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        horizontal_layout = QHBoxLayout(self)
        right_menu = RightMenu(self)
        graphics_panel = GraphicsPanel(self)
        central_widget.setLayout(horizontal_layout)
        horizontal_layout.addWidget(graphics_panel, 3)
        horizontal_layout.addLayout(right_menu, 1)

        right_menu.run_clicked.connect(graphics_panel.draw_path)
        right_menu.reset_clicked.connect(graphics_panel.redraw)
        graphics_panel.last_x_calculated.connect(right_menu.set_results)

        exit_action = QAction("&Exit", self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(qApp.quit)


def main():
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
