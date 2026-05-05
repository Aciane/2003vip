import os

def generate_galaxy_html(filename="galaxy_spiral.html"):
    """
    生成一个基于密度波理论的银河系WebGL模型。
    """
    
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Density Wave Galaxy Simulation</title>
    <style>
        body { margin: 0; overflow: hidden; background-color: #050505; }
        canvas { display: block; }
        #info {
            position: absolute;
            top: 10px;
            left: 10px;
            color: #aaa;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            pointer-events: none;
            background: rgba(0, 0, 0, 0.7);
            padding: 15px;
            border-left: 3px solid #66ccff;
        }
        h1 { margin: 0 0 5px 0; font-size: 14px; color: #fff; text-transform: uppercase; letter-spacing: 2px;}
        p { margin: 0; font-size: 12px; }
    </style>
</head>
<body>
    <div id="info">
        <h1>Milky Way Structure</h1>
        <p>Model: Logarithmic Spiral Density Wave</p>
        <p>Particles: 80,000 (Interactive)</p>
        <p>Tech: Three.js / BufferGeometry</p>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>

    <script>
        // 配置参数：你可以调整这些参数改变星系形态
        const GALAXY_CONFIG = {
            count: 80000,           // 星星数量
            size: 0.015,            // 星星基础大小
            radius: 5,              // 星系半径
            branches: 3,            // 旋臂数量 (银河系通常模拟为3-4条主臂)
            spin: 1,                // 旋臂弯曲程度
            randomness: 0.2,        // 散射随机性
            randomnessPower: 3,     // 随机性幂次 (控制核心聚集度)
            insideColor: '#ff6030', // 核心颜色 (老恒星)
            outsideColor: '#1b3984' // 边缘颜色 (年轻恒星)
        };

        let camera, scene, renderer, galaxyPoints;

        init();
        animate();

        function init() {
            scene = new THREE.Scene();
            
            // 添加一些环境雾，模拟深空尘埃
            scene.fog = new THREE.FogExp2(0x050505, 0.1);

            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 100);
            camera.position.x = 3;
            camera.position.y = 3;
            camera.position.z = 5;
            camera.lookAt(scene.position);

            renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // 限制DPI以保证性能
            document.body.appendChild(renderer.domElement);

            generateGalaxy();

            window.addEventListener('resize', onWindowResize);
        }

        function generateGalaxy() {
            if(galaxyPoints !== undefined) {
                scene.remove(galaxyPoints);
                galaxyPoints.geometry.dispose();
                galaxyPoints.material.dispose();
            }

            const geometry = new THREE.BufferGeometry();
            const positions = new Float32Array(GALAXY_CONFIG.count * 3);
            const colors = new Float32Array(GALAXY_CONFIG.count * 3);

            const colorInside = new THREE.Color(GALAXY_CONFIG.insideColor);
            const colorOutside = new THREE.Color(GALAXY_CONFIG.outsideColor);

            for(let i = 0; i < GALAXY_CONFIG.count; i++) {
                const i3 = i * 3;

                // 核心算法：对数螺线生成
                // radius: 0 -> 1 (距离中心的归一化距离)
                const radius = Math.random() * GALAXY_CONFIG.radius;
                
                // 旋臂角度
                // (i % branches) / branches * 2PI -> 将粒子分配到不同的臂上
                const spinAngle = radius * GALAXY_CONFIG.spin;
                const branchAngle = (i % GALAXY_CONFIG.branches) / GALAXY_CONFIG.branches * Math.PI * 2;

                // 随机散射 (高斯分布近似)
                // 使用 power 使得随机值更靠近0，从而让旋臂更清晰
                const randomX = Math.pow(Math.random(), GALAXY_CONFIG.randomnessPower) * (Math.random() < 0.5 ? 1 : -1) * GALAXY_CONFIG.randomness * radius;
                const randomY = Math.pow(Math.random(), GALAXY_CONFIG.randomnessPower) * (Math.random() < 0.5 ? 1 : -1) * GALAXY_CONFIG.randomness * radius;
                const randomZ = Math.pow(Math.random(), GALAXY_CONFIG.randomnessPower) * (Math.random() < 0.5 ? 1 : -1) * GALAXY_CONFIG.randomness * radius;

                // 极坐标转笛卡尔坐标
                positions[i3    ] = Math.cos(branchAngle + spinAngle) * radius + randomX;
                positions[i3 + 1] = randomY * 0.5; // 压扁Y轴，形成盘状
                positions[i3 + 2] = Math.sin(branchAngle + spinAngle) * radius + randomZ;

                // 颜色混合
                const mixedColor = colorInside.clone();
                mixedColor.lerp(colorOutside, radius / GALAXY_CONFIG.radius);

                colors[i3    ] = mixedColor.r;
                colors[i3 + 1] = mixedColor.g;
                colors[i3 + 2] = mixedColor.b;
            }

            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

            const material = new THREE.PointsMaterial({
                size: GALAXY_CONFIG.size,
                sizeAttenuation: true,
                depthWrite: false, // 关闭深度写入，允许粒子前后叠加
                blending: THREE.AdditiveBlending, // 加法混合，核心发光关键
                vertexColors: true
            });

            galaxyPoints = new THREE.Points(geometry, material);
            scene.add(galaxyPoints);
        }

        function onWindowResize() {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }

        function animate() {
            requestAnimationFrame(animate);

            // 整体旋转
            galaxyPoints.rotation.y += 0.0005;

            // 缓慢的摄像机轨道运动
            const time = Date.now() * 0.0001;
            camera.position.x = Math.cos(time) * 4;
            camera.position.z = Math.sin(time) * 4;
            camera.lookAt(new THREE.Vector3(0,0,0));

            renderer.render(scene, camera);
        }
    </script>
</body>
</html>
    """
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"File generated: {os.path.abspath(filename)}")

if __name__ == "__main__":
    generate_galaxy_html()