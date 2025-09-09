import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout,
    QHBoxLayout, QComboBox, QTextEdit, QGroupBox
)
from PyQt5.QtCore import Qt

# 기존 코드에서 run_motor, run_actuator, DEF_* 등 그대로 import 가능

class MotorActuatorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Motor & Actuator Control")
        self.setGeometry(100, 100, 650, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # === ACT GROUP ===
        act_group = QGroupBox("Actuator Control")
        act_layout = QHBoxLayout()

        self.act_speed = QLineEdit()
        self.act_time = QLineEdit()
        act_e_btn = QPushButton("Extend (E)")
        act_r_btn = QPushButton("Retract (R)")

        act_e_btn.clicked.connect(lambda: self.run_act_clicked('e'))
        act_r_btn.clicked.connect(lambda: self.run_act_clicked('r'))

        act_layout.addWidget(QLabel("Speed:"))
        act_layout.addWidget(self.act_speed)
        act_layout.addWidget(QLabel("Hold Time:"))
        act_layout.addWidget(self.act_time)
        act_layout.addWidget(act_e_btn)
        act_layout.addWidget(act_r_btn)
        act_group.setLayout(act_layout)
        layout.addWidget(act_group)

        # === MOTOR GROUP ===
        motor_group = QGroupBox("Motor Control")
        motor_layout = QHBoxLayout()

        self.motor_select = QComboBox()
        self.motor_select.addItems(["1", "2"])
        self.motor_steps = QLineEdit()
        self.motor_accel = QLineEdit()

        motor_f_btn = QPushButton("Run F")
        motor_b_btn = QPushButton("Run B")
        motor_f_btn.clicked.connect(lambda: self.run_motor_clicked('f'))
        motor_b_btn.clicked.connect(lambda: self.run_motor_clicked('b'))

        motor_layout.addWidget(QLabel("Motor:"))
        motor_layout.addWidget(self.motor_select)
        motor_layout.addWidget(QLabel("Steps:"))
        motor_layout.addWidget(self.motor_steps)
        motor_layout.addWidget(QLabel("Accel:"))
        motor_layout.addWidget(self.motor_accel)
        motor_layout.addWidget(motor_f_btn)
        motor_layout.addWidget(motor_b_btn)
        motor_group.setLayout(motor_layout)
        layout.addWidget(motor_group)

        # === OUTPUT TEXT ===
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        self.setLayout(layout)

    def print_output(self, msg):
        self.output_text.append(msg)
        self.output_text.verticalScrollBar().setValue(self.output_text.verticalScrollBar().maximum())

    # === ACT BUTTON FUNCTION ===
    def run_act_clicked(self, cmd):
        try:
            spd = float(self.act_speed.text()) if self.act_speed.text() else DEF_ACT_SPEED
        except:
            spd = DEF_ACT_SPEED
        try:
            sec = float(self.act_time.text()) if self.act_time.text() else DEF_ACT_TIME
        except:
            sec = DEF_ACT_TIME

        self.print_output(f"[ACT] Running {cmd}: speed={spd}, time={sec}")
        run_actuator(cmd, spd, sec)
        self.print_output(f"[ACT] {cmd} Done")

    # === MOTOR BUTTON FUNCTION ===
    def run_motor_clicked(self, direction):
        try:
            m = int(self.motor_select.currentText())
        except:
            m = 1

        d = direction  # 버튼에서 전달된 f 또는 b

        # Steps 입력 없으면 기본값 사용
        try:
            s_text = self.motor_steps.text()
            s = int(s_text) if s_text else (DEF_STEPS1 if m == 1 else DEF_STEPS2)
        except:
            s = DEF_STEPS1 if m == 1 else DEF_STEPS2

        # Accel 입력 없으면 기본값 사용
        try:
            a_text = self.motor_accel.text()
            a = float(a_text) if a_text else DEF_ACCEL
        except:
            a = DEF_ACCEL

        self.print_output(f"[MOTOR] Running motor{m}: dir={d}, steps={s}, accel={a}")
        run_motor(m, d, s, a)
        self.print_output("[MOTOR] Done")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = MotorActuatorGUI()
    gui.show()
    sys.exit(app.exec_())
