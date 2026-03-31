<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Smart-Grid Lab: CLOU Simulator</title>
    <style>
        body { font-family: sans-serif; text-align: center; background: #e0e0e0; color: #333; margin: 0; }
        .ui-panel { background: #333; color: white; padding: 15px; border-bottom: 3px solid #ffcc00; }
        .container { position: relative; width: 600px; height: 800px; margin: 20px auto; background: white; border-radius: 8px; border: 3px solid #666; overflow: hidden; }
        canvas { position: absolute; top: 0; left: 0; z-index: 5; cursor: crosshair; }
        /* Гараар зурсан схем */
        .scheme-bg { position: absolute; width: 100%; height: 100%; top: 0; left: 0; z-index: 1; pointer-events: none; opacity: 0.9; }
        /* CLOU тоолуур (Схем дээр тааруулж байрлуулсан) */
        .meter-overlay { position: absolute; width: 330px; top: 180px; left: 135px; z-index: 2; pointer-events: none; }
        .controls { padding: 15px; }
        .btn { padding: 10px 25px; font-size: 18px; cursor: pointer; border: none; border-radius: 5px; margin: 5px; font-weight: bold; }
        .btn-check { background: #2ed573; color: white; }
        .btn-reset { background: #ff4757; color: white; }
    </style>
</head>
<body>
    <div class="ui-panel">
        <h2>⚡ Smart-Grid Lab: CL710K22 Ухаалаг тоолуур</h2>
        <p>Заавар: Зурсан схемийн дагуу А фаз (Шар) болон Тэг N (Цэнхэр) цэгээс чирч тоолуурын контакт руу холбоно уу.</p>
    </div>

    <div class="container">
        <img src="hand_drawn_scheme.jpg" class="scheme-bg" alt="Scheme background">
        <img src="image_0473e1.jpg" class="meter-overlay" alt="CLOU Meter">
        <canvas id="simCanvas" width="600" height="800"></canvas>
    </div>

    <div class="controls">
        <button class="btn btn-check" onclick="checkConnection()">Холболтыг шалгах</button>
        <button class="btn btn-reset" onclick="resetSim()">Шинэчлэх</button>
    </div>

    <script>
        const canvas = document.getElementById('simCanvas');
        const ctx = canvas.getContext('2d');

        // Контакт цэгүүд (Схем болон Тоолуурын зураг дээр тааруулсан)
        const pins = [
            // Эхлэх цэгүүд (Салгуур)
            { id: 'S-L', x: 235, y: 55, color: 'yellow', type: 'start', label: 'L' },
            { id: 'S-N', x: 235, y: 110, color: '#00ccff', type: 'start', label: 'N' },
            // Төгсгөл цэгүүд (CLOU тоолуур - Контактын дагуу)
            { id: 'M-1', x: 255, y: 585, color: 'yellow', type: 'end', connected: null }, // Шон 1 (L-In)
            { id: 'M-3', x: 335, y: 585, color: '#00ccff', type: 'end', connected: null }  // Шон 3 (N-In)
        ];

        let wires = [];
        let drawingWire = null;

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Цэгүүдийг зурах
            pins.forEach(p => {
                ctx.beginPath();
                ctx.arc(p.x, p.y, 10, 0, Math.PI*2);
                ctx.fillStyle = p.type === 'start' ? p.color : '#333';
                ctx.fill();
                ctx.strokeStyle = 'black';
                ctx.lineWidth = 2;
                ctx.stroke();
                ctx.fillStyle = 'black';
                ctx.font = "bold 16px Arial";
                if(p.label) ctx.fillText(p.label, p.x - 20, p.y - 15);
            });

            // Холбогдсон утаснууд
            wires.forEach(w => {
                ctx.beginPath();
                ctx.moveTo(w.from.x, w.from.y);
                ctx.lineTo(w.to.x, w.to.y);
                ctx.strokeStyle = w.color;
                ctx.lineWidth = 6;
                ctx.lineCap = 'round';
                ctx.stroke();
            });

            // Одоо чирч байгаа утас
            if(drawingWire) {
                ctx.beginPath();
                ctx.moveTo(drawingWire.from.x, drawingWire.from.y);
                ctx.lineTo(drawingWire.currX, drawingWire.currY);
                ctx.strokeStyle = drawingWire.color;
                ctx.lineWidth = 4;
                ctx.setLineDash([8, 4]);
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
                if(Math.hypot(p.x-x, p.y-y) < 15 && p.type === 'start') {
                    drawingWire = { from: p, currX: x, currY: y, color: p.color };
                }
            });
        };

        canvas.onmousemove = (e) => {
            if(drawingWire) {
                const r = canvas.getBoundingClientRect();
                drawingWire.currX = e.clientX - r.left;
                drawingWire.currY = e.clientY - r.top;
            }
        };

        canvas.onmouseup = (e) => {
            if(drawingWire) {
                pins.forEach(p => {
                    if(Math.hypot(p.x-drawingWire.currX, p.y-drawingWire.currY) < 15 && p.type === 'end') {
                        // Зөвхөн ижил өнгөтэй утсыг холбох логик
                        if(drawingWire.color === p.color) {
                            wires.push({ from: drawingWire.from, to: p, color: drawingWire.color });
                            p.connected = drawingWire.color;
                        } else {
                            alert("❌ Утасны өнгө болон шонгийн төрөл зөрж байна! Фаз (Шар) болон Тэг (Цэнхэр) утасны шонг дахин шалгана уу.");
                        }
                    }
                });
                drawingWire = null;
            }
        };

        function checkConnection() {
            const m1 = pins.find(p => p.id === 'M-1').connected;
            const m3 = pins.find(p => p.id === 'M-3').connected;
            if(m1 === 'yellow' && m3 === '#00ccff') {
                alert("🎉 ГАЙХАЛТАЙ! CLOU тоолуур зөв холбогдлоо. Насос ажиллаж байна!");
            } else {
                alert("❌ Холболт буруу! Схемийн дагуу Фаз болон Тэгээ дахин шалгана уу.");
            }
        }

        function resetSim() { wires = []; pins.forEach(p => p.connected = null); }
        draw();
    </script>
</body>
</html>
