"""
人物距离检测 Python 模块
=========================

这个模块使用 OpenCV 进行人物检测和距离估算
配合 TouchDesigner 使用

安装依赖：
    pip install opencv-python numpy

使用方法：
    在 TouchDesigner 的 Python DAT 中导入此模块
    或者直接运行此脚本测试
"""

import cv2
import numpy as np
from collections import deque
import time

class PersonDistanceDetector:
    """基于普通RGB摄像头的人物距离检测器"""
    
    def __init__(self, camera_index=0, width=640, height=480):
        self.cap = None
        self.camera_index = camera_index
        self.width = width
        self.height = height
        
        # 历史数据用于平滑
        self.history = deque(maxlen=10)
        
        # 背景模型
        self.bg_subtractor = None
        self.fg_mask = None
        self.background = None
        
        # 距离估算参数
        self.known_person_height = 170  # 假设人物高度170cm
        self.focal_length = None  # 将在校准中确定
        
        # 初始化背景减除
        self._init_bg_subtractor()
        
    def _init_bg_subtractor(self):
        """初始化背景减除算法"""
        # 使用MOG2算法，能更好地处理光线变化
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True,
            history=50,
            varThreshold=16
        )
    
    def open(self):
        """打开摄像头"""
        self.cap = cv2.VideoCapture(self.camera_index)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            print(f"摄像头已打开: {self.width}x{self.height}")
            return True
        else:
            print("无法打开摄像头")
            return False
    
    def close(self):
        """关闭摄像头"""
        if self.cap:
            self.cap.release()
            cv2.destroyAllWindows()
    
    def detect_person(self, frame):
        """
        检测人物并估算距离
        
        返回:
            dict: {
                'detected': bool,    # 是否检测到人物
                'distance': float,   # 距离值 (0.0-1.0, 越近越大)
                'area': int,         # 人物区域面积
                'bounding_box': tuple,  # (x, y, w, h)
                'center': tuple      # 中心点 (cx, cy)
            }
        """
        if frame is None:
            return {'detected': False, 'distance': 0.0}
        
        # 应用背景减除
        fg_mask = self.bg_subtractor.apply(frame)
        
        # 形态学操作：去噪
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        
        # 去除阴影 (MOG2会将阴影标记为灰色)
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
        
        # 查找轮廓
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {'detected': False, 'distance': 0.0}
        
        # 找最大的轮廓（应该是人物）
        max_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(max_contour)
        
        # 过滤太小的区域（噪声）
        if area < 3000:
            return {'detected': False, 'distance': 0.0}
        
        # 获取边界框
        x, y, w, h = cv2.boundingRect(max_contour)
        cx, cy = x + w // 2, y + h // 2
        
        # 计算距离 (基于区域面积)
        # 这是一个简化模型，实际需要根据实验校准
        # 假设: 距离2米时，人物面积约50000像素
        #       距离0.5米时，人物面积约200000像素
        max_area = 200000
        min_area = 10000
        
        # 归一化距离 (0.0 = 最远, 1.0 = 最近)
        normalized_distance = np.clip((area - min_area) / (max_area - min_area), 0, 1)
        
        # 平滑处理
        self.history.append(normalized_distance)
        smoothed_distance = np.mean(self.history)
        
        return {
            'detected': True,
            'distance': float(smoothed_distance),
            'area': area,
            'bounding_box': (x, y, w, h),
            'center': (cx, cy),
            'raw_area': area
        }
    
    def process_frame(self):
        """处理单帧并返回结果"""
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        # 转换为RGB (OpenCV是BGR)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 检测人物
        result = self.detect_person(frame)
        result['frame'] = frame
        
        return result
    
    def run(self, display=True):
        """运行检测循环"""
        if not self.open():
            return
        
        print("按 'q' 退出")
        
        try:
            while True:
                result = self.process_frame()
                
                if result and display:
                    frame = result['frame']
                    
                    # 绘制边界框
                    if result['detected']:
                        x, y, w, h = result['bounding_box']
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        
                        # 显示距离
                        text = f"Distance: {result['distance']:.2f}"
                        cv2.putText(frame, text, (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        
                        # 显示面积
                        area_text = f"Area: {result['area']}"
                        cv2.putText(frame, area_text, (10, 70),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                if display:
                    cv2.imshow('Person Detection', frame if result else np.zeros((480, 640, 3)))
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        finally:
            self.close()


# ============================================================
# TouchDesigner 专用函数
# ============================================================

def get_distance_value():
    """
    用于 TouchDesigner Python DAT 的函数
    返回当前的归一化距离值
    """
    detector = PersonDistanceDetector(camera_index=0)
    result = detector.process_frame()
    detector.close()
    
    if result and result['detected']:
        return result['distance']
    return 0.0


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("人物距离检测器测试")
    print("=" * 50)
    
    detector = PersonDistanceDetector()
    detector.run(display=True)