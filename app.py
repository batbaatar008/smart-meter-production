<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Smart-Grid Lab: CLOU Simulator</title>
    <style>
        body { font-family: sans-serif; text-align: center; background: #1e272e; color: white; margin: 0; }
        .container { position: relative; width: 600px; height: 850px; margin: 20px auto; background: #f1f2f6; border-radius: 10px; border: 4px solid #ffa502; overflow: hidden; }
        canvas { position: absolute; top: 0; left: 0; z-index: 5; cursor: crosshair; }
        .meter-bg { position: absolute; width: 450px; top: 180px; left: 75px; z-index: 1; pointer-events: none; }
        .ui-panel { background: #2f3542; padding: 15px; border-bottom: 3px solid #ffa502; }
        .controls { padding: 15px; }
        .btn { padding: 10px 25px; font-size: 18px; cursor: pointer; border: none; border-radius: 5px; margin: 5px; font-weight: bold; }
        .btn-check { background: #2ed573; color: white; }
        .btn-reset { background: #ff4757; color: white; }
    </style>
</head>
<body>
    <div class="ui-panel">
        <h2>⚡ Smart-Grid Lab: CL710K22 Ухаалаг тоолуур</h2>
        <p>Заавар: Дээд талын фаз (Шар), тэг (Цэнхэр) цэгээс чирч тоолуурын контакт руу холбоно уу.</p>
    </div>

    <div class="container">
        <img src="image_0473e1.jpg" class="meter-bg" id="meterImg">
        <canvas id="simCanvas" width="600" height="850"></canvas>
    </div>

    <div class="controls">
        <button class="btn btn-check" onclick="checkConnection()">Холболтыг шалгах</button>
        <button class="btn btn-reset" onclick="resetSim()">Шинэчлэх</button>
    </div>

    <script>
        const canvas = document.getElementById('simCanvas');
        const ctx = canvas.getContext('2d');

        // Контакт цэгүүд (Зураг дээрх контактууд дээр тааруулсан)
        const pins = [
            { id: 'S-L', x: 200, y: 50, color: 'yellow', type: 'start', label: 'Фаз (L)' },
            { id: 'S-N', x: 400, y: 50, color: '#00a8ff', type: 'start', label: 'Тэг (N)' },
            { id: 'M-1', x: 235, y: 745, targetColor: 'yellow', type: 'end', connected: null }, // Шон 1
            { id: 'M-3', x: 345, y: 745, targetColor: '#00a8ff', type: 'end', connected: null }  // Шон 3
        ];

        let wires = [];
        let drawingWire = null;

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Цэгүүдийг зурах
            pins.forEach(p => {
                ctx.beginPath();
                ctx.arc(p.x, p.y, 12, 0, Math.PI*2);
                ctx.fillStyle = p.type === 'start' ? p.color : '#2f3542';
                ctx.fill();
                ctx.strokeStyle = 'white';
                ctx.lineWidth = 3;
                ctx.stroke();
                ctx.fillStyle = 'white';
                ctx.font = "bold 14px Arial";
                if(p.label) ctx.fillText(p.label, p.x - 25, p.y - 25);
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
                if(Math.hypot(p.x-x, p.y-y) < 20 && p.type === 'start') {
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
                    if(Math.hypot(p.x-drawingWire.currX, p.y-drawingWire.currY) < 25 && p.type === 'end') {
                        wires.push({ from: drawingWire.from, to: p, color: drawingWire.color });
                        p.connected = drawingWire.color;
                    }
                });
                drawingWire = null;
            }
        };

        function checkConnection() {
            const m1 = pins.find(p => p.id === 'M-1').connected;
            const m3 = pins.find(p => p.id === 'M-3').connected;
            if(m1 === 'yellow' && m3 === '#00a8ff') {
                alert("🎉 ГАЙХАЛТАЙ! CLOU тоолуур зөв холбогдлоо. Насос ажиллаж байна!");
            } else {
                alert("❌ Холболт буруу! Фаз (Шар) болон Тэг (Цэнхэр) утасны шонг дахин шалгана уу.");
            }
        }

        function resetSim() { wires = []; pins.forEach(p => p.connected = null); }
        draw();
    </script>
</body>
</html>
