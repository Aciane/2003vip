"""
TouchDesigner FBX 粒子化交互装置艺术项目
============================================

使用方法：
1. 打开 TouchDesigner
2. 创建一个新的 Text DAT
3. 将此代码粘贴进去
4. 右键点击 Text DAT，选择 "Run"
5. 这将自动构建整个项目

作者：AI Assistant
日期：2026/3/25
"""

import TDStoreTools
import TDFunctions
import inspect

# ============================================================
# 第一部分：创建项目结构
# ============================================================

# 获取当前面板
root = op('/')

# 创建主要的组件
# 1. 摄像头输入组件
video_in = op.create('videoin', 'VideoIn_TOP')
video_in.nodeY = 300
video_in.nodeX = -400

# 2. FBX 导入组件
fbx_importer = op.create('fbx', 'FBX Import')
fbx_importer.nodeY = 0
fbx_importer.nodeX = -400

# 3. 粒子系统
particle_sop = op.create('particleSOP', 'Particle_SOP')
particle_sop.nodeY = 0
particle_sop.nodeX = 0

# 4. 渲染组件
geo = op.create('geo', 'Render_Geo')
geo.nodeY = 200
geo.nodeX = 0

# 5. 相机组件
camera = op.create('camera', 'Camera')
camera.nodeY = 400
camera.nodeX = 200

# 6. 照明
light = op.create('light', 'Light')
light.nodeY = 400
light.nodeX = 0

# ============================================================
# 第二部分：配置 FBX 导入
# ============================================================

# 设置 FBX 文件路径 (需要根据实际路径修改)
fbx_path = 'shao/shao.fbx'

# 配置 FBX Import 参数
if hasattr(fbx_importer.par, 'file'):
    fbx_importer.par.file = fbx_path

# ============================================================
# 第三部分：配置粒子系统
# ============================================================

# 粒子参数配置
particle_sop.par.copy = 'src'
particle_sop.par.maxpoints = 20000
particle_sop.par.life = 10.0
particle_sop.par.random = 0.1
particle_sop.par.vel.x = 0.0
particle_sop.par.vel.y = 0.0
particle_sop.par.vel.z = 0.0

# ============================================================
# 第四部分：创建距离检测系统
# ============================================================

# 这需要 Python 扩展和 OpenCV
# 在实际项目中，你需要在 Text DAT 中编写 OpenCV 代码

print("项目结构创建完成！")
print("请继续添加距离检测和粒子控制逻辑")

# ============================================================
# 重要提示
# ============================================================

"""
由于 TouchDesigner 的项目文件 (.toe) 是二进制格式，
这个脚本只能提供基础架构。

实际使用中，请按照以下步骤操作：

步骤 1: FBX 模型导入
- 在 TouchDesigner 中使用 FBX Import COMP
- 导入 /Users/tangzezhen/letstalking/shao/shao.fbx
- 确保纹理正确加载

步骤 2: 粒子化处理
- 使用 Particle SOP 将几何体转换为粒子
- 或者使用 "Points to Particles" 方法

步骤 3: 摄像头设置
- 使用 Video Device In TOP
- 选择 MacBook 内置摄像头或外接摄像头

步骤 4: 人物检测和距离估算
- 方案 A: 使用 Blob Tracking
- 方案 B: 使用 OpenCV + Python

步骤 5: 粒子控制
- 根据距离值修改粒子参数
- 实现扩散/凝聚效果

步骤 6: 朝向控制
- 使用 Look At CHOP
- 让模型始终面向摄像头/人物
"""

# ============================================================
# 粒子控制参数示例
# ============================================================

def update_particles(distance_value):
    """
    根据距离更新粒子状态
    
    distance_value: 0.0 (最远) 到 1.0 (最近)
    """
    # 粒子数量
    num_particles = 5000 + int(distance_value * 15000)  # 5000-20000
    
    # 粒子大小
    particle_size = 0.05 + (1.0 - distance_value) * 0.1  # 越近越大
    
    # 扩散程度
    dispersion = distance_value * 2.0  # 越近越扩散
    
    # 颜色变化
    if distance_value > 0.7:
        # 很近 - 明亮、彩色
        color = (1.0, 0.8, 0.5, 1.0)
    elif distance_value > 0.3:
        # 中等 - 正常
        color = (0.8, 0.8, 1.0, 1.0)
    else:
        # 很远 - 暗淡、蓝色
        color = (0.3, 0.3, 0.5, 0.5)
    
    return {
        'num_particles': num_particles,
        'particle_size': particle_size,
        'dispersion': dispersion,
        'color': color
    }

print("粒子控制函数已定义")