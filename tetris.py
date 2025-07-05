import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QApplication
import socket, time
import random

class Tetris(QMainWindow):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.tboard = None

    def initUI(self):
        self.setFixedSize(360, 760)
        self.setWindowTitle('Tetris')

        self.button1 = QtWidgets.QPushButton(self)
        self.button1.setText('Начать')
        self.button1.setFixedSize(100, 50)
        self.button1.move(130, 450)
        self.button1.clicked.connect(self.start_game)
        self.button1.show()

        self.label1 = QtWidgets.QLabel(self)
        self.label1.setText('Нажмите кнопку снизу чтобы начать')
        self.label1.setFixedSize(250, 50)
        self.label1.setAlignment(QtCore.Qt.AlignCenter)
        self.label1.move(55, 200)
        self.label1.show()
        arrow_font = QtGui.QFont('arial', 70, QtGui.QFont.Bold)

        self.label_arrow = QtWidgets.QLabel(self)
        self.label_arrow.setText('↓')
        self.label_arrow.setAlignment(QtCore.Qt.AlignCenter)
        self.label_arrow.setFixedSize(250, 120)
        self.label_arrow.move(55, 270)
        self.label_arrow.setFont(arrow_font)
        self.label_arrow.show()

        self.show()

    def start_game(self):
        self.tetris = Tetris(self)
        stylesheet = '''
        QMainWindow{
        background-image: url("wallpaper.jpg");
        background-repeat: no-repeat;
        background-position: center;
        }
        '''
        self.tetris.setStyleSheet(stylesheet)
        self.tetris.setFixedSize(360, 760)
        self.tetris.setWindowTitle('Tetris')
        self.close()
        self.Bord = Border(self)
        self.tetris.setCentralWidget(self.Bord)
        self.tetris.show()

class Border(QtWidgets.QFrame):
    board_height = 22
    board_width = 10
    DROP_SPEED = 300
    
    def __init__(self, parent):
        super().__init__(parent)
        self.init_board()
    
    def init_board(self):
        self.timer = QtCore.QBasicTimer()
        self.dropped = False
        self.corr_x = 0
        self.corr_y = 0
        self.score = 0
        self.field = [FigureShape() for _ in range(Border.board_width * Border.board_height)]
        self.setFocusPolicy(Qt.StrongFocus)
        self.active = False
        self.awaitLine = False
        self.paused = False
        self.curPiece = FigureShape()
        self.new_Piece()
        self.timer.start(Border.DROP_SPEED, self)  # Запуск таймера
        #self.paintEvent()
    
    def keyPressEvent(self, event):
        if self.curPiece.currentShape == Figure.no_figure or not self.active:
            super(Border, self).keyPressEvent(event)
            return
        key = event.key()
        if key == Qt.Key.Key_P:
            self.paused = not self.paused
            if self.paused:
                self.timer.stop()
            else:
                self.timer.start(Border.DROP_SPEED, self)
            self.update()  # Перерисуем экран (для отображения надписи "Пауза")
            return
        if self.paused:
            return  # Никакие действия не выполняются в паузе
        
        if key == Qt.Key.Key_Left:
            self.moveFigure(self.curPiece, self.corr_x-1, self.corr_y)
        elif key == Qt.Key.Key_Right:
            self.moveFigure(self.curPiece, self.corr_x+1, self.corr_y)
        elif key == Qt.Key.Key_Up:
            self.moveFigure(self.curPiece.rotateLeft(), self.corr_x, self.corr_y)
        elif key == Qt.Key.Key_Down:
            self.moveFigure(self.curPiece.rotateRight(), self.corr_x, self.corr_y)
        elif key == Qt.Key.Key_Space:
            self.dropDown()
        else:
            super(Border, self).keyPressEvent(event)
        
    def dropDown(self):
        """Сбрасывает фигуру до самого низа и фиксирует её"""
        new_y = self.corr_y
        # Пробуем опускать фигуру, пока это возможно
        while self.moveFigure(self.curPiece, self.corr_x, new_y - 1):
            new_y -= 1
        # Фиксируем фигуру на поле
        self.fix_to_field()
    
    def new_Piece(self):
        self.curPiece = FigureShape()
        self.curPiece.get_shape()
        self.corr_x = Border.board_width // 2
        self.corr_y = Border.board_height - 3  # Самый верх
        self.active = True  # Активируем фигуру для управления
        if not self.moveFigure(self.curPiece, self.corr_x, self.corr_y):
            #self.curPiece.set_shape(Figure.no_figure)
            self.timer.stop()
            print("Game Over: Cannot place new piece")
            self.bests = Results(self.score)
            self.parent().close()
            
        self.update()
        return
    
    def moveFigure(self, new_piece, new_x, new_y):
        for i in range(4):
            x = new_x + new_piece.get_x(i)
            y = new_y - new_piece.get_y(i)

            # Проверяем границы поля
            if x < 0 or x >= Border.board_width or y < 0 or y >= Border.board_height:
                return False

            # Проверяем, занята ли клетка
            #print(self.field)
            if self.get_figure(x, y).currentShape != Figure.no_figure:
                return False

        # Если все проверки прошли — двигаем фигуру
        self.curPiece = new_piece
        self.corr_x = new_x
        self.corr_y = new_y
        self.update()
        return True

    
    def timerEvent(self, event):
        if event.timerId() == self.timer.timerId():
            if self.awaitLine:
                self.awaitLine = False
                self.new_Piece()
            else:
                self.lineDown()
        super(Border, self).timerEvent(event)

    def clear_board(self):
        for i in range(Border.board_height*Border.board_width):
            self.field.append(FigureShape())
    
    def clear_line(self):
        count_line_to_remove = 0
        rows_to_remove = []
        for y in range(22):
            count = 0
            for x in range(10):
                # print(self.get_figure(x,y).currentShape)
                if self.get_figure(x, y).currentShape:
                    count += 1
            print(count)
            if count == 10:
                rows_to_remove.append(y)
                count_line_to_remove += 1
        # print(self.field)
        rows_to_remove.reverse()
        print(rows_to_remove)
        for line in rows_to_remove:
            for x in range(10):
                self.init_figure(x, line, FigureShape())
            for y in range(line, 21):
                for x in range(10):
                    self.init_figure(x,y, self.get_figure(x,y+1))
        if count_line_to_remove:
            self.score += count_line_to_remove
            self.awaitLine = True
            #self.curPiece = Figure.no_figure
        self.update()

    def init_figure(self, x, y, figure): # заполяет фигуру
        # print(x,y)
        if y > 21:
            return
        self.field[(y*Border.board_width)+x] = figure
    
    def get_figure(self, x, y): #получает фигуру
        return self.field[(y*Border.board_width)+x]
    
    def square_width(self):
        return self.contentsRect().width()//Border.board_width
    
    def square_height(self):
        return self.contentsRect().height() // Border.board_height

    def drawSquare(self, painter: QtGui.QPainter, x, y, shape):
        color_table = [
            QColor(0, 0, 0),         # no_figure
            QColor(255, 0, 0),       # square (красный)
            QColor(0, 255, 0),       # left_gun (зелёный)
            QColor(0, 0, 255),       # right_gun (синий)
            QColor(255, 255, 0),     # left_snake (жёлтый)
            QColor(255, 0, 255),     # right_snake (фиолетовый)
            QColor(0, 255, 255),     # line (голубой)
            QColor(255, 165, 0)      # letter_T (оранжевый)
        ]

        color = color_table[shape]
        painter.fillRect(x + 1, y + 1, self.square_width() - 2, self.square_height() - 2, color)  # Заливка

        painter.setPen(Qt.black)  # Чёрная рамка
        painter.drawRect(x, y, self.square_width(), self.square_height())  # Обводка

    
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        rect = self.contentsRect()
        board_top = rect.bottom() - Border.board_height * self.square_height()
        for i in range(Border.board_height):
            for g in range(Border.board_width):
                shape_obj = self.get_figure(g, Border.board_height - i - 1)
                if shape_obj.currentShape != Figure.no_figure:
                    self.drawSquare(painter,
                        rect.left() + g * self.square_width(),
                        board_top + i * self.square_height(),
                        shape_obj.currentShape
                    )

        painter.setPen(QColor(200, 200, 200))  # Светло-серый цвет линий
        for x in range(Border.board_width + 1):
            painter.drawLine(
                rect.left() + x * self.square_width(),
                board_top,
                rect.left() + x * self.square_width(),
                board_top + Border.board_height * self.square_height()
            )
        for y in range(Border.board_height + 1):
            painter.drawLine(
                rect.left(),
                board_top + y * self.square_height(),
                rect.left() + Border.board_width * self.square_width(),
                board_top + y * self.square_height()
            )

        if self.curPiece.currentShape != Figure.no_figure:
            for i in range(4):
                x = self.corr_x + self.curPiece.get_x(i)
                y = self.corr_y - self.curPiece.get_y(i)
                self.drawSquare(painter,
                    rect.left() + x * self.square_width(),
                    board_top + (self.board_height - y - 1) * self.square_height(),
                    self.curPiece.currentShape
                )
        BrushPaint = QtGui.QBrush(QColor('white'), Qt.SolidPattern)
        painter.setBrush(BrushPaint)
        painter.drawRect(0, 0, 360, 45)
        
        painter.setPen(QColor('black'))
        painter.setFont(QFont('Montserrat SemiBold', 20))
        painter.drawText(QtCore.QRect(0, 0, 360, 45), Qt.AlignCenter, f'Счёт: {self.score}')
        
    def lineDown(self):
        if not self.moveFigure(self.curPiece, self.corr_x, self.corr_y - 1):
            self.fix_to_field()
    
    def fix_to_field(self):
        for i in range(4):
            x = self.corr_x + self.curPiece.get_x(i)
            y = self.corr_y - self.curPiece.get_y(i)
            self.init_figure(x, y, self.curPiece)  # Записываем фигуру в поле
        self.active = False
        self.clear_line()
        self.new_Piece()

class Results(QMainWindow):
    def __init__(self,score):
        super().__init__()
        self.score = score
        self.initUI()

    def initUI(self):
        self.setFixedSize(400, 400)
        self.setWindowTitle('Tetris: Results')

        self.client_part = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_part.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.client_part.connect(('localhost', 4365))
        client_receive = self.client_part.recv(1024).decode()
        print(client_receive)
        result_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel(text=client_receive)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        result_widget.setLayout(layout)
        self.setCentralWidget(result_widget)
        
        #input_name
        self.input_name = QtWidgets.QLineEdit(self)
        layout.addWidget(self.input_name)
        
        #button
        self.button1 = QtWidgets.QPushButton(self)
        self.button1.setText('Отправить результат')
        self.button1.setFixedSize(130, 50)
        self.button1.move(130, 450)
        self.button1.clicked.connect(self.send_results)
        layout.addWidget(self.button1)
        
        self.show()
    
    def send_results(self):
        text_to_send = self.input_name.text()
        if text_to_send:
            self.client_part.send((text_to_send+'\n'+str(self.score)).encode())
            exit()
        

class Figure(object):
    no_figure = 0 # нет фигуры
    square = 1 #Квадрат 2x2
    left_gun = 2 #Буква Г влево
    right_gun = 3 #Буква Г
    left_snake = 4 #Змейка влево
    right_snake = 5 #Змейка вправо
    line = 6 #Прямая вертикальная линия
    letter_T = 7 #Буква Т
    
    figures = []

class FigureShape(object):
    shape = (((0,0),(0,0), (0,0), (0,0)), # No square
        ((0, 0), (1, 0), (0, -1), (1, -1)),   # square
        ((0, 0), (0, 1), (0, -1), (-1, -1)),  # left_gun
        ((0, 0), (0, 1), (0, -1), (1, -1)),   # right_gun
        ((0, 0), (1, 0), (0, -1), (-1, -1)),  # left_snake
        ((0, 0), (-1, 0), (0, -1), (1, -1)),  # right_snake
        ((0, 0), (0, -1), (0, -2), (0, 1)),   # line
        ((0, 0), (-1, 0), (1, 0), (0, -1)),   # letter_T (шапка сверху)
        )    
    def __init__(self):
        self.coords = [[0,0],[0,0],[0,0],[0,0]]
        self.currentShape = Figure.no_figure
    def set_shape(self, shape):
        cur_s = FigureShape.shape[shape]
        for i in range(4):
            self.coords[i][0] = cur_s[i][0]
            self.coords[i][1] = cur_s[i][1]
        self.currentShape = shape
        
    def get_shape(self):
        self.set_shape(random.randint(1, 7))
    
    def get_x(self, index):
        return self.coords[index][0]
        
    def get_y(self, index):
        return self.coords[index][1]


    def setx(self, index, x):
        self.coords[index][0] = x
    
    def sety(self, index, y):
        self.coords[index][1] = y
    
    def minx(self):
        min = self.coords[0][0]
        for i in range(4):
            if min <= self.coords[i][0]:
                min = self.coords[i][0]
        return min
    
    def miny(self):
        min = self.coords[0][1]
        for i in range(4):
            if min <= self.coords[i][1]:
                min = self.coords[i][1]
        return min
    
    def max_x(self):
        max = self.coords[0][0]
        for i in range(4):
            if max >= self.coords[i][0]:
                max = self.coords[i][0]
        return max

    def max_y(self):
        max = self.coords[0][1]
        for i in range(4):
            if max >= self.coords[i][1]:
                max = self.coords[i][1]
        return max
    
    def rotateLeft(self):
        # print(self.coords)
        if self.currentShape == Figure.square:
            return self
        copy = FigureShape()
        copy.set_shape(self.currentShape)
        for piece in range(4):
            copy.setx(piece, self.get_y(piece))
            copy.sety(piece, -self.get_x(piece))
        return copy
    
    def rotateRight(self):
        if self.currentShape == Figure.square:
            return self
        copy = FigureShape()
        copy.set_shape(self.currentShape)
        for piece in range(4):
            copy.setx(piece, -self.get_y(piece))
            copy.sety(piece, self.get_x(piece))
        return copy
    


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Tetris('Tetris')
    # QFontDb = QtGui.QFontDatabase()
    # print(QFontDb.families())
    ex.initUI()
    sys.exit(app.exec_())