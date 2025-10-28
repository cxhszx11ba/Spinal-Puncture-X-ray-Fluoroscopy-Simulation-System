import os
import sys
import cv2
import numpy as np
import json
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QPen
from PyQt5.QtWidgets import (
    QApplication, QLabel, QMainWindow, QWidget, QVBoxLayout,
    QGridLayout, QPushButton, QFrame, QMessageBox, QScrollArea
)

class ClickableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.click_callback = None
        self.setStyleSheet("background-color: blue;")
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if self.click_callback:
            self.click_callback(event)

class CameraSelectionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("选择摄像头")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QGridLayout(self.central_widget)

        self.selected_cameras = []
        self.max_selection = 2  # 需要选择两个摄像头

        self.camera_labels = []
        self.camera_timers = []
        self.caps = []

        self.detect_cameras()
        self.show_cameras()
        self.add_instruction_label()  # 添加提示框

    def detect_cameras(self, max_cameras=10):
        self.available_cameras = []
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap is not None and cap.isOpened():
                self.available_cameras.append(i)
                cap.release()

    def show_cameras(self):
        num_cameras = len(self.available_cameras)
        if num_cameras == 0:
            QMessageBox.warning(self, "警告", "未检测到任何摄像头！")
            sys.exit()

        rows = int(np.ceil(num_cameras / 3))
        cols = min(3, num_cameras)

        for index, cam_id in enumerate(self.available_cameras):
            cap = cv2.VideoCapture(cam_id)
            self.caps.append(cap)

            label = ClickableLabel(self)
            label.setFixedSize(200, 150)
            label.click_callback = lambda event, idx=index: self.select_camera(idx)
            self.camera_labels.append(label)

            timer = QTimer(self)
            timer.timeout.connect(lambda idx=index: self.update_frame(idx))
            timer.start(30)
            self.camera_timers.append(timer)

            self.layout.addWidget(label, (index // cols) + 1, index % cols)  # 行号加1，留出提示框位置

    def update_frame(self, idx):
        if idx >= len(self.caps) or not self.caps[idx].isOpened():
            return
            
        ret, frame = self.caps[idx].read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (200, 150))
            image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            if idx < len(self.camera_labels):
                self.camera_labels[idx].setPixmap(QPixmap.fromImage(image))

    def select_camera(self, idx):
        if idx in self.selected_cameras:
            return  # 防止重复选择

        self.selected_cameras.append(self.available_cameras[idx])
        self.camera_labels[idx].setStyleSheet("border: 2px solid red;")

        if len(self.selected_cameras) == self.max_selection:
            self.close()
            self.start_main_window()

    def closeEvent(self, event):
        # 停止所有定时器
        for timer in self.camera_timers:
            timer.stop()
        # 释放所有摄像头
        for cap in self.caps:
            if cap.isOpened():
                cap.release()
        super().closeEvent(event)

    def start_main_window(self):
        self.main_window = VideoWindow(self.selected_cameras)
        self.main_window.show()

    def add_instruction_label(self):
        instruction_label = QLabel("Please select the AP view image and LAT view image in sequence", self)
        instruction_label.setStyleSheet("font-size: 16px; color: blue;")
        instruction_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(instruction_label, 0, 0, 1, 3)  # 占据顶部的三列

class VideoWindow(QMainWindow):
    def __init__(self, selected_cameras):
        super().__init__()
        self.zhengweishexiangtou = selected_cameras[0]
        self.ceweishexiangtou = selected_cameras[1]

        self.setWindowTitle("Dual Camera with Overlay Images")
        self.setGeometry(100, 100, 1000, 800)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        layout = QGridLayout(self.central_widget)

        self.video_label_1 = QLabel(self)
        self.video_label_1.setFixedSize(640, 480)
        self.video_label_2 = QLabel(self)
        self.video_label_2.setFixedSize(640, 480)

        layout.addWidget(self.video_label_1, 0, 0)
        layout.addWidget(self.video_label_2, 0, 1)

        self.display_A1 = ClickableLabel(self)
        self.display_A1.setFixedSize(640, 480)
        self.display_A2 = ClickableLabel(self)
        self.display_A2.setFixedSize(640, 480)

        layout.addWidget(self.display_A1, 1, 0)
        layout.addWidget(self.display_A2, 1, 1)

        # 添加文字注释标签
        self.add_text_overlay(self.video_label_1, "AP view real-time image")
        self.add_text_overlay(self.video_label_2, "LAT view real-time image")
        self.add_text_overlay(self.display_A1, "AP view perspective")
        self.add_text_overlay(self.display_A2, "LAT view perspective")

        self.capture_button = QPushButton("Perspective and simulate puncture trajectory", self)
        self.capture_button.clicked.connect(self.capture_and_simulate)
        layout.addWidget(self.capture_button, 2, 0, 1, 2)

        # 初始化摄像头
        self.cap_1 = None
        self.cap_2 = None
        self.init_cameras()

        base_path = os.path.dirname(os.path.abspath(__file__))
        self.overlay_image_1 = cv2.imread(os.path.join(base_path, "正位片.png"), cv2.IMREAD_UNCHANGED)
        self.overlay_image_2 = cv2.imread(os.path.join(base_path, "侧位片.png"), cv2.IMREAD_UNCHANGED)

        self.overlay_1_x, self.overlay_1_y = 219, 144  # 初始坐标
        self.overlay_1_scale, self.overlay_1_alpha = 0.245, 0.8  # 初始缩放和初始透明度
        self.overlay_1_rotation = 1.9  # 初始旋转
        self.overlay_2_x, self.overlay_2_y = 25, 25  # 初始坐标
        self.overlay_2_scale, self.overlay_2_alpha = 0.5, 1.0  # 初始缩放和初始透明度
        self.overlay_2_rotation = 0  # 初始旋转

        # 使用QTimer代替timerEvent
        self.video_timer = QTimer(self)
        self.video_timer.timeout.connect(self.update_video)
        self.video_timer.start(30)

        self.is_simulating_trajectory = False
        self.points_A1 = []
        self.points_A2 = []
        self.click_count_A1 = 0
        self.click_count_A2 = 0

        self.display_A1.click_callback = lambda event: self.process_click(event.pos(), self.points_A1, self.display_A1, "A1")
        self.display_A2.click_callback = lambda event: self.process_click(event.pos(), self.points_A2, self.display_A2, "A2")

        self.setFocusPolicy(Qt.StrongFocus)

        self.load_overlay_state()

    def init_cameras(self):
        """安全地初始化摄像头"""
        try:
            self.cap_1 = cv2.VideoCapture(self.zhengweishexiangtou)
            self.cap_2 = cv2.VideoCapture(self.ceweishexiangtou)
            
            # 设置缓冲区大小以减少延迟
            if self.cap_1.isOpened():
                self.cap_1.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if self.cap_2.isOpened():
                self.cap_2.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
        except Exception as e:
            print(f"摄像头初始化错误: {e}")

    def update_video(self):
        """更新视频帧"""
        if not self.cap_1 or not self.cap_2:
            return
            
        if not self.cap_1.isOpened() or not self.cap_2.isOpened():
            return

        try:
            ret_1, frame_1 = self.cap_1.read()
            ret_2, frame_2 = self.cap_2.read()

            if not ret_1 or not ret_2:
                return

            frame_1 = cv2.cvtColor(frame_1, cv2.COLOR_BGR2RGB)
            frame_2 = cv2.cvtColor(frame_2, cv2.COLOR_BGR2RGB)

            # 保持长宽比的缩放函数
            def resize_keep_aspect(image, target_size):
                h, w = image.shape[:2]
                target_w, target_h = target_size
                aspect = w / h
                if target_w / target_h > aspect:
                    new_h = target_h
                    new_w = int(new_h * aspect)
                else:
                    new_w = target_w
                    new_h = int(new_w / aspect)
                resized = cv2.resize(image, (new_w, new_h))
                delta_w = target_w - new_w
                delta_h = target_h - new_h
                top, bottom = delta_h // 2, delta_h - (delta_h // 2)
                left, right = delta_w // 2, delta_w - (delta_w // 2)
                padded = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0])
                return padded

            frame_1 = resize_keep_aspect(frame_1, (640, 480))
            frame_2 = resize_keep_aspect(frame_2, (640, 480))

            if self.overlay_image_1 is not None:
                overlay_resized_1 = cv2.resize(self.overlay_image_1, None, fx=self.overlay_1_scale, fy=self.overlay_1_scale)
                overlay_rotated_1 = self.rotate_image(overlay_resized_1, self.overlay_1_rotation)
                self.add_overlay(frame_1, overlay_rotated_1, (self.overlay_1_x, self.overlay_1_y), self.overlay_1_alpha)

            if self.overlay_image_2 is not None:
                overlay_resized_2 = cv2.resize(self.overlay_image_2, None, fx=self.overlay_2_scale, fy=self.overlay_2_scale)
                overlay_rotated_2 = self.rotate_image(overlay_resized_2, self.overlay_2_rotation)
                self.add_overlay(frame_2, overlay_rotated_2, (self.overlay_2_x, self.overlay_2_y), self.overlay_2_alpha)

            image_1 = QImage(frame_1.data, frame_1.shape[1], frame_1.shape[0], QImage.Format_RGB888)
            image_2 = QImage(frame_2.data, frame_2.shape[1], frame_2.shape[0], QImage.Format_RGB888)

            self.video_label_1.setPixmap(QPixmap.fromImage(image_1))
            self.video_label_2.setPixmap(QPixmap.fromImage(image_2))

            # 确保文字注释始终在最顶层
            for child in self.video_label_1.children() + self.video_label_2.children():
                if isinstance(child, QLabel):
                    child.raise_()
                    
        except Exception as e:
            print(f"视频更新错误: {e}")

    def rotate_image(self, image, angle):
        if image is None:
            return None
            
        h, w = image.shape[:2]
        new_w = int(w * np.abs(np.cos(np.radians(angle))) + h * np.abs(np.sin(np.radians(angle))))
        new_h = int(h * np.abs(np.cos(np.radians(angle))) + w * np.abs(np.sin(np.radians(angle))))
        expanded_image = np.zeros((new_h, new_w, 4), dtype=np.uint8)
        center_x, center_y = new_w // 2, new_h // 2
        orig_x, orig_y = w // 2, h // 2
        expanded_image[center_y - orig_y:center_y - orig_y + h, center_x - orig_x:center_x - orig_x + w] = image

        M = cv2.getRotationMatrix2D((center_x, center_y), angle, 1.0)
        rotated = cv2.warpAffine(expanded_image, M, (new_w, new_h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        return rotated

    def add_overlay(self, frame, overlay, position, alpha):
        if overlay is None:
            return
            
        x, y = position
        h, w, _ = overlay.shape

        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if x + w > frame.shape[1]:
            w = frame.shape[1] - x
        if y + h > frame.shape[0]:
            h = frame.shape[0] - y

        if w > 0 and h > 0:
            overlay = overlay[:h, :w]
            frame_section = frame[y:y+h, x:x+w]

            if overlay.shape[2] == 4:
                alpha_mask = (overlay[:, :, 3] / 255.0) * alpha
                for c in range(0, 3):
                    frame_section[:, :, c] = (1. - alpha_mask) * frame_section[:, :, c] + alpha_mask * overlay[:, :, c]
            else:
                alpha_mask = alpha
                for c in range(0, 3):
                    frame_section[:, :, c] = (1. - alpha_mask) * frame_section[:, :, c] + alpha_mask * overlay[:, :, c]

    def capture_and_simulate(self):
        # 直接截图，保留叠加图像
        self.capture_screenshots()
        # 开始轨迹模拟
        self.start_trajectory_simulation()

    def capture_screenshots(self):
        try:
            if self.video_label_1.pixmap() and self.video_label_2.pixmap():
                screenshot_1 = self.video_label_1.pixmap().toImage()
                screenshot_1 = screenshot_1.convertToFormat(QImage.Format_RGBA8888)
                buffer_1 = screenshot_1.bits()
                buffer_1.setsize(screenshot_1.byteCount())
                img_np_1 = np.array(buffer_1).reshape(screenshot_1.height(), screenshot_1.width(), 4)

                screenshot_2 = self.video_label_2.pixmap().toImage()
                screenshot_2 = screenshot_2.convertToFormat(QImage.Format_RGBA8888)
                buffer_2 = screenshot_2.bits()
                buffer_2.setsize(screenshot_2.byteCount())
                img_np_2 = np.array(buffer_2).reshape(screenshot_2.height(), screenshot_2.width(), 4)

                self.display_A1.setPixmap(QPixmap.fromImage(QImage(img_np_1.data, img_np_1.shape[1], img_np_1.shape[0], QImage.Format_RGBA8888)))
                self.display_A2.setPixmap(QPixmap.fromImage(QImage(img_np_2.data, img_np_2.shape[1], img_np_2.shape[0], QImage.Format_RGBA8888)))

                # 确保文字注释始终在最顶层
                for child in self.display_A1.children() + self.display_A2.children():
                    if isinstance(child, QLabel):
                        child.raise_()
        except Exception as e:
            print(f"截图错误: {e}")

    def start_trajectory_simulation(self):
        self.is_simulating_trajectory = True
        self.points_A1 = []
        self.points_A2 = []
        self.click_count_A1 = 0
        self.click_count_A2 = 0
        
        # 设置精确的十字瞄准指针
        self.display_A1.setCursor(Qt.CrossCursor)
        self.display_A2.setCursor(Qt.CrossCursor)

    def process_click(self, pos, points, display, label):
        if not self.is_simulating_trajectory:
            return

        colors = [QColor("red"), QColor("green"), QColor("blue")]
        click_count = getattr(self, f'click_count_{label}')
        click_count += 1

        if click_count <= 3:
            points.append(pos)
            self.draw_point(display, pos, colors[click_count - 1])

            if click_count == 3:
                self.draw_trajectory(display, points)
        elif 4 <= click_count <= 6:
            if click_count == 4:
                points.clear()  # 清除用于下一条线
            points.append(pos)
            self.draw_point(display, pos, colors[click_count - 4])

            if click_count == 6:
                self.draw_trajectory(display, points)
                # 完成所有点击后，恢复默认指针
                display.setCursor(Qt.PointingHandCursor)

        setattr(self, f'click_count_{label}', click_count)

    def draw_point(self, display, pos, color):
        try:
            pixmap = display.pixmap() if display.pixmap() else QPixmap(display.size())
            pixmap = pixmap.copy()
            painter = QPainter(pixmap)
            painter.setPen(QPen(color, 3))
            painter.drawPoint(pos)
            painter.end()
            display.setPixmap(pixmap)
        except Exception as e:
            print(f"绘制点错误: {e}")

    def draw_trajectory(self, display, points):
        try:
            if len(points) < 3:
                return
                
            g, b = points[1], points[2]
            x = np.linalg.norm([b.x() - g.x(), b.y() - g.y()])
            y = np.linalg.norm([g.x() - points[0].x(), g.y() - points[0].y()])
            z = (x * x * x / y / y) + (x * x / y) if y != 0 else 0

            direction = QPoint(b.x() - g.x(), b.y() - g.y())
            if x != 0:
                extension = direction * (z / x)
            else:
                extension = QPoint(0, 0)

            end_point = QPoint(b.x() + extension.x(), b.y() + extension.y())

            pixmap = display.pixmap() if display.pixmap() else QPixmap(display.size())
            pixmap = pixmap.copy()
            painter = QPainter(pixmap)
            # 将线条粗细从5改为2.5（减少50%）
            painter.setPen(QPen(QColor("black"), 2.5))
            painter.drawLine(g, end_point)
            painter.end()
            display.setPixmap(pixmap)
        except Exception as e:
            print(f"绘制轨迹错误: {e}")

    def keyPressEvent(self, event):
        if self.video_label_1.underMouse():
            if event.key() == Qt.Key_Up:
                self.overlay_1_y -= 2
            elif event.key() == Qt.Key_Down:
                self.overlay_1_y += 2
            elif event.key() == Qt.Key_Left:
                self.overlay_1_x -= 2
            elif event.key() == Qt.Key_Right:
                self.overlay_1_x += 2
            elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
                self.overlay_1_scale += 0.002
            elif event.key() == Qt.Key_Minus:
                self.overlay_1_scale = max(0.1, self.overlay_1_scale - 0.002)
            elif event.key() == Qt.Key_W:
                self.overlay_1_alpha = min(self.overlay_1_alpha + 0.02, 1.0)
            elif event.key() == Qt.Key_S:
                self.overlay_1_alpha = max(self.overlay_1_alpha - 0.02, 0.0)
            elif event.key() == Qt.Key_D:
                self.overlay_1_rotation -= 0.1
            elif event.key() == Qt.Key_A:
                self.overlay_1_rotation += 0.1

        elif self.video_label_2.underMouse():
            if event.key() == Qt.Key_Up:
                self.overlay_2_y -= 2
            elif event.key() == Qt.Key_Down:
                self.overlay_2_y += 2
            elif event.key() == Qt.Key_Left:
                self.overlay_2_x -= 2
            elif event.key() == Qt.Key_Right:
                self.overlay_2_x += 2
            elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
                self.overlay_2_scale += 0.01
            elif event.key() == Qt.Key_Minus:
                self.overlay_2_scale = max(0.1, self.overlay_2_scale - 0.01)
            elif event.key() == Qt.Key_W:
                self.overlay_2_alpha = min(self.overlay_2_alpha + 0.02, 1.0)
            elif event.key() == Qt.Key_S:
                self.overlay_2_alpha = max(self.overlay_2_alpha - 0.02, 0.0)
            elif event.key() == Qt.Key_D:
                self.overlay_2_rotation -= 0.1
            elif event.key() == Qt.Key_A:
                self.overlay_2_rotation += 0.1

    def load_overlay_state(self):
        try:
            with open('overlay_state.json', 'r') as f:
                state = json.load(f)
                self.overlay_1_x = state['overlay_1_x']
                self.overlay_1_y = state['overlay_1_y']
                self.overlay_1_scale = state['overlay_1_scale']
                self.overlay_1_alpha = state['overlay_1_alpha']
                self.overlay_1_rotation = state['overlay_1_rotation']
                self.overlay_2_x = state['overlay_2_x']
                self.overlay_2_y = state['overlay_2_y']
                self.overlay_2_scale = state['overlay_2_scale']
                self.overlay_2_alpha = state['overlay_2_alpha']
                self.overlay_2_rotation = state['overlay_2_rotation']
        except FileNotFoundError:
            pass

    def save_overlay_state(self):
        try:
            state = {
                'overlay_1_x': self.overlay_1_x,
                'overlay_1_y': self.overlay_1_y,
                'overlay_1_scale': self.overlay_1_scale,
                'overlay_1_alpha': self.overlay_1_alpha,
                'overlay_1_rotation': self.overlay_1_rotation,
                'overlay_2_x': self.overlay_2_x,
                'overlay_2_y': self.overlay_2_y,
                'overlay_2_scale': self.overlay_2_scale,
                'overlay_2_alpha': self.overlay_2_alpha,
                'overlay_2_rotation': self.overlay_2_rotation
            }
            with open('overlay_state.json', 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"保存状态错误: {e}")

    def closeEvent(self, event):
        try:
            # 停止视频定时器
            if hasattr(self, 'video_timer'):
                self.video_timer.stop()
            
            self.save_overlay_state()
            
            # 安全地释放摄像头
            if self.cap_1 and self.cap_1.isOpened():
                self.cap_1.release()
            if self.cap_2 and self.cap_2.isOpened():
                self.cap_2.release()
                
        except Exception as e:
            print(f"关闭窗口错误: {e}")
        finally:
            super().closeEvent(event)

    def add_text_overlay(self, parent_widget, text):
        text_label = QLabel(text, parent_widget)
        text_label.setStyleSheet("background-color: rgba(0, 0, 0, 128); color: white; padding: 5px;")
        text_label.move(10, 10)
        text_label.raise_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    selection_window = CameraSelectionWindow()
    selection_window.show()
    sys.exit(app.exec_())
