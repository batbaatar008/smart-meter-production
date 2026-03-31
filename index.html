<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Smart-Grid Lab: CLOU Simulator</title>
    <style>
        body { font-family: sans-serif; text-align: center; background: #f4f4f4; margin: 0; }
        .ui-panel { background: #2c3e50; color: white; padding: 20px; border-bottom: 4px solid #f1c40f; }
        .container { position: relative; width: 600px; height: 800px; margin: 20px auto; background: white; border: 2px solid #bdc3c7; box-shadow: 0 0 20px rgba(0,0,0,0.1); }
        canvas { position: absolute; top: 0; left: 0; z-index: 10; cursor: crosshair; }
        /* Гараар зурсан схем */
        .scheme-bg { position: absolute; width: 100%; height: 100%; top: 0; left: 0; z-index: 1; opacity: 0.8; object-fit: contain; }
        /* CLOU тоолуур */
        .meter-overlay { position: absolute; width: 320px; top: 190px; left: 140px; z-index: 2; pointer-events: none; }
        .controls { margin-bottom: 30px; }
        .btn { padding: 12px 30px; font-size: 18px; cursor: pointer; border: none; border-radius: 5px; margin: 10px; font-weight: bold; transition: 0.3s; }
        .btn-check { background: #27ae60; color: white; }
        .btn-reset { background: #e74c3c; color: white; }
        .btn:hover { opacity: 0.8; transform: translateY(-2px); }
    </style>
</head>
<body>
    <div class="ui-panel">
        <h2>⚡ Smart-Grid Lab: Бодит Холболтын Симулятор</h2>
        <p>Заавар: Дээд талын салгуурын цэгүүдээс чирч, тоолуурын 1 болон 3-р шонд холбоно уу.</p>
    </div>

    <div class="container">
        <img src="https://raw.githubusercontent.com/batbaatar008/smart-meter-simulator/main/image_054a18.jpg" class="scheme-bg">
        <img src="https://raw.githubusercontent.com/batbaatar008/smart-meter-simulator/main/image_0473e1.jpg" class="meter-overlay">
        <canvas id="simCanvas" width="600" height="800"></canvas>
    </div>

    <div class="controls">
        <button class="btn btn-check" onclick="check()">Холболтыг шалгах</button>
        <button class="btn btn-reset" onclick="reset()">Шинэчлэх</button>
    </div>

    <script>
        const canvas = document.getElementById('simCanvas');
        const ctx = canvas.getContext('2d');

        // Цэгүүдийн байршил (Зураг дээрх салгуур болон тоолуурын шонд тааруулсан)
        const pins = [
            { id: 'S-L', x: 235, y: 55, color: 'yellow', type: 'start' }, // Салгуур Фаз
            { id: 'S-N', x: 235, y: 115, color: '#00ccff', type: 'start' }, // Салгуур Тэг
            { id: 'M-1', x: 260, y: 595, color: 'yellow', type: 'end', connected: null }, // Тоолуур 1-р шон
            { id: 'M-3', x: 340, y: 595, color: '#00ccff', type: 'end', connected: null }  // Тоолуур 3-р шон
        ];

        let wires = [];
        let drawing = null;

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            pins.forEach(p => {
                ctx.beginPath();
                ctx.arc(p.x, p.y, 12, 0, Math.PI*2);
                ctx.fillStyle = p.type === 'start' ? p.color : 'rgba(0,0,0,0.1)';
                ctx.fill();
                ctx.strokeStyle = '#2c3e50';
                ctx.lineWidth = 2;
                ctx.stroke();
            });

            wires.forEach(w => {
                ctx.beginPath();
                ctx.moveTo(w.from.x, w.from.y);
                ctx.lineTo(w.to.x, w.to.y);
                ctx.strokeStyle = w.color;
                ctx.lineWidth = 6;
                ctx.lineCap = 'round';
                ctx.stroke();
            });

            if(drawing) {
                ctx.beginPath();
                ctx.moveTo(drawing.from.x, drawing.from.y);
                ctx.lineTo(drawing.x, drawing.y);
                ctx.strokeStyle = drawing.color;
                ctx.lineWidth = 4;
                ctx.setLineDash([10, 5]);
                ctx.stroke();
                ctx.setLineDash([]);
            }
            requestAnimationFrame(draw);
        }

        canvas.onmousedown = (e) => {
            const r = canvas.getBoundingClientRect();
            const x = e.clientX - r.left;
            const y = e.clientY - r.top;
            pins.forEach(p => {
                if(Math.hypot(p.x-x, p.y-y) < 20 && p.type === 'start') {
                    drawing = { from: p, x: x, y: y, color: p.color };
                }
            });
        };

        canvas.onmousemove = (e) => {
            if(drawing) {
                const r = canvas.getBoundingClientRect();
                drawing.x = e.clientX - r.left;
                drawing.y = e.clientY - r.top;
            }
        };

        canvas.onmouseup = (e) => {
            if(drawing) {
                pins.forEach(p => {
                    if(Math.hypot(p.x-drawing.x, p.y-drawing.y) < 20 && p.type === 'end') {
                        if(drawing.color === p.color) {
                            wires.push({ from: drawing.from, to: p, color: drawing.color });
                            p.connected = drawing.color;
                        } else {
                            alert("❌ Буруу шон! Фаз (Шар) болон Тэг (Цэнхэр) утсыг өнгөөр нь ялгаж холбоно уу.");
                        }
                    }
                });
                drawing = null;
            }
        };

        function check() {
            const l = pins.find(p => p.id === 'M-1').connected;
            const n = pins.find(p => p.id === 'M-3').connected;
            if(l && n) {
                alert("🎉 БАЯР ХҮРГЭЕ! Чи схемийн дагуу CLOU тоолуурыг амжилттай холболоо.");
            } else {
                alert("❌ Холболт дутуу байна. Салгуураас тоолуурын шон руу утсаа чирч холбоно уу.");
            }
        }

        function reset() { wires = []; pins.forEach(p => p.connected = null); }
        draw();
    </script>
</body>
</html>
