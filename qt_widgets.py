from itertools import chain

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from game_logic import GameField
from resources import Sounds


class Percent:
    def __init__(self, base_val: int):
        self._base = base_val
        self.scaler = base_val * 0.01

    def __call__(self, percents):
        return percents * self.scaler


class QLabelNumber(QLabel):
    def __init__(self, *args, number: int = 0, **kwargs):
        super(QLabelNumber, self).__init__(*args, **kwargs)
        font = QFont("Segoe Script", 13)
        self.setFont(font)
        self.display(number)
        min_width = self.fontMetrics().boundingRect("00000").width()
        self.setMinimumWidth(min_width)

    def display(self, number: int):
        self.setText(str(number))


class FieldItemWidget(QPushButton):
    changed = pyqtSignal(QObject)
    leftButtonPressed = pyqtSignal(QObject)
    rightButtonPressed = pyqtSignal(QObject)

    def __init__(self, y, x, *args, **kwargs):
        super(FieldItemWidget, self).__init__(*args, **kwargs)
        self._y = y
        self._x = x
        size_policy = QSizePolicy.Expanding
        policy = QSizePolicy()
        policy.setHorizontalPolicy(size_policy)
        policy.setVerticalPolicy(size_policy)
        policy.setWidthForHeight(True)
        self.setSizePolicy(policy)

        self.logic_source = self.parent().logic_source.items[y, x]
        self.logic_source.changed.connect(self.changed)

        self.gradient = None
        self.construct_gradient(QColor(self.logic_source.item.color))

        self.active_size_toggled = False
        self.self_size_modifier = 1
        self.update()

    def construct_gradient(self, color: QColor = QColor("magenta")):
        gr = QRadialGradient()
        gr.setCoordinateMode(QGradient.StretchToDeviceMode)
        c1 = color.lighter(150)
        c2 = color.darker(450)

        gr.setColorAt(0.05, c1)
        gr.setColorAt(0.49, color)
        gr.setColorAt(1.0, c2)
        gr.setCenter(QPointF(0.7, 0.3))

        gr.setFocalPoint(QPointF(0.7, 0.3))
        self.gradient = gr

    def changed(self):
        if self.logic_source.item:
            self.construct_gradient(QColor(self.logic_source.item.color))
        self.update()

    def resizeEvent(self, e: QResizeEvent):
        super().resizeEvent(e)
        self.pct = Percent(self.rect().width())

    def paintEvent(self, e: QPaintEvent):
        # super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        painter.setPen(Qt.NoPen)

        pct = self.pct
        if self.logic_source.item is not None:
            rect = QRectF(self.rect()).marginsAdded(QMarginsF() - (pct(2)))
            shadow_rect = QRectF(rect)
            shadow_rect.translate(QPoint(pct(-1), pct(1)))
            shadow_rect.adjust(pct(-2), pct(2), pct(0), pct(2))

            shadow_color = QColor("#000000")
            shadow_color.setAlpha(100)

            painter.setBrush(shadow_color)
            painter.drawEllipse(shadow_rect)

            painter.setBrush(self.gradient)
            painter.drawEllipse(rect)

        painter.end()

    def sizeHint(self):
        return QSize(50, 50)

    def minimumSizeHint(self):
        return QSize(self.sizeHint().width() // 2, self.sizeHint().height() // 2)

    def __repr__(self):
        return f"FieldItemWidget({self._y}, {self._x})"

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self.leftButtonPressed.emit(self)
        elif e.button() == Qt.RightButton:
            self.rightButtonPressed.emit(self)
        else:
            pass


class GameFieldWidget(QWidget):
    def __init__(self, logic_source, *args, **kwargs):
        super(GameFieldWidget, self).__init__(*args, **kwargs)

        self.logic_source = logic_source

        self.logic_source.items_were_spawned.connect(self.parent().sounds.tick2.play)
        bubble_sounds = self.parent().sounds
        self.logic_source.cells_cleared.connect(bubble_sounds.bubbles_play)

        layout = QGridLayout()
        self.setLayout(layout)
        layout.setSpacing(0)
        layout.heightForWidth(True)
        self.fieldItems2D = []
        height, width = logic_source.items._container.shape

        for y in range(height):
            self.fieldItems2D.append([])
            for x in range(width):
                item = FieldItemWidget(y, x, parent=self)
                self.fieldItems2D[y].append(item)
                layout.addWidget(item, y, x)
                item.leftButtonPressed.connect(self.item_clicked)
                item.rightButtonPressed.connect(self.item_clicked)

        self.fieldItems = list(chain.from_iterable(self.fieldItems2D))

        self.ratio = width / height
        self.adjusted_to_size = (-1, -1)
        # self.setSizePolicy(QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored))

    def paintEvent(self, e: QPaintEvent):
        painter = QPainter(self)
        # color = QColor("peachpuff")
        # color.setAlpha(60)
        color = QColor("darkgreen")
        color.setAlpha(30)
        brush = QBrush(color)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect() + (QMargins() - 1), 20, 20)
        # painter.fillRect(self.rect(), brush)

    def resizeEvent(self, event):
        # https://stackoverflow.com/a/61589941/13537384
        size = event.size()
        if size == self.adjusted_to_size:
            # Avoid infinite recursion. I suspect Qt does this for you,
            # but it's best to be safe.
            return
        self.adjusted_to_size = size

        full_width = size.width()
        full_height = size.height()
        width = min(full_width, full_height * self.ratio)
        height = min(full_height, full_width / self.ratio)

        h_margin = round((full_width - width) / 2)
        v_margin = round((full_height - height) / 2)

        self.setContentsMargins(h_margin, v_margin, h_margin, v_margin)

    def item_clicked(self, item):
        self.logic_source.cell_clicked(item.logic_source)


class InformationBar(QWidget):
    def __init__(self, logic_source, *args, **kwargs):
        super(InformationBar, self).__init__(*args, **kwargs)
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.setFixedHeight(50)

        self.logic_source = logic_source
        self.parent().current_scores.connect(self.update_counter)

        layout.addStretch()
        label = QLabel("Scores:")
        font = QFont("Segoe Script", 13)
        label.setFont(font)
        layout.addWidget(label)
        self.scores_counter = QLabelNumber(self)
        layout.addWidget(self.scores_counter, alignment=Qt.AlignLeft)

    def reset(self):
        self.scores_counter.display(0)

    def update_counter(self, value):
        self.scores_counter.display(value)

    def paintEvent(self, e: QPaintEvent):
        painter = QPainter(self)
        color = QColor("white")
        color.setAlpha(60)
        brush = QBrush(color)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect() + (QMargins() - 1), 10, 10)


class GameActions(QObject):
    def __init__(self, *args, **kwargs):
        super(GameActions, self).__init__(*args, **kwargs)
        self.resetAction = QAction("Reset", self)
        self.resetAction.triggered.connect(self.parent().logic_source.reset)

        self.spawnAction = QAction("Spawn", self)
        self.spawnAction.triggered.connect(self.parent().logic_source.spawn_items)

        self.toggleSound = QAction("Sound", self)
        self.toggleSound.triggered.connect(self.parent().sounds.toggle_sound)
        self.toggleSound.setCheckable(True)
        self.toggleSound.setChecked(True)


class GameMenu(QMenuBar):
    def __init__(self, *args, **kwargs):
        super(GameMenu, self).__init__(*args, **kwargs)

        file_menu = self.addMenu("File")
        file_menu.addAction(self.parent().game_actions.resetAction)
        file_menu.addAction(self.parent().game_actions.spawnAction)
        file_menu.addAction(self.parent().game_actions.toggleSound)


class MainWindow(QMainWindow):
    current_scores = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Bubble trouble")
        self.setWindowIcon(QIcon("FILE.ico"))
        self.sounds = Sounds()
        # self.menuBar().show()

        self.logic_source = GameField(height=10, width=10, colors=5)

        self.mainWidget = QWidget(self)
        self.setCentralWidget(self.mainWidget)

        layout = QVBoxLayout()
        self.mainWidget.setLayout(layout)

        self.status_bar = InformationBar(logic_source=self.logic_source, parent=self)
        layout.addWidget(self.status_bar)

        layout.addWidget(GameFieldWidget(logic_source=self.logic_source, parent=self))

        self.scores = 0

        self.game_actions = GameActions(self)

        self.menu = GameMenu(self)
        self.setMenuBar(self.menu)

        self.logic_source.cells_cleared.connect(self.add_scores)
        self.logic_source.field_was_reset.connect(self.reset_scores)

        size_policy = QSizePolicy.Minimum
        policy = QSizePolicy()
        policy.setHorizontalPolicy(size_policy)
        policy.setVerticalPolicy(size_policy)
        self.setSizePolicy(policy)
        # self.logic_source.spawn_items()
        self.show()

    def reset_scores(self):
        self.scores = 0
        self.current_scores.emit(self.scores)
        self.sounds.restart.play()

    def add_scores(self, cells_cleared):
        self.scores += cells_cleared * cells_cleared
        self.current_scores.emit(self.scores)

    def paintEvent(self, e: QPaintEvent):
        painter = QPainter(self)
        brush = QBrush(QColor("cornsilk"))
        painter.fillRect(self.rect(), brush)
