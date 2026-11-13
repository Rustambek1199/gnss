document.addEventListener('DOMContentLoaded', () => {

    // ===== Sidebar scroll to section =====
    window.scrollToSection = function(id) {
        document.querySelectorAll('.nav-links li').forEach(li => li.classList.remove('active'));
        const el = document.getElementById(id);
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    // ===== Bugungi sana =====
    const now = new Date();
    const todayYear  = now.getFullYear();
    const todayMonth = now.getMonth() + 1; // 1-12
    const todayDay   = now.getDate();

    // Yil selectni bugungi yilga o'rnating
    const yearSel = document.getElementById('sel-year');
    if (yearSel) {
        const matchY = [...yearSel.options].find(o => o.value == todayYear);
        if (matchY) yearSel.value = String(todayYear);
        else yearSel.selectedIndex = yearSel.options.length - 1;
    }

    // Oy selectni bugungi oyga o'rnating
    const monthSel = document.getElementById('sel-month');
    if (monthSel) monthSel.value = String(todayMonth);

    // ===== Populate Day dropdown =====
    const daySelect = document.getElementById('sel-day');
    for (let i = 1; i <= 31; i++) {
        const opt = document.createElement('option');
        opt.value = i; opt.textContent = i + '-kun';
        daySelect.appendChild(opt);
    }
    // Bugungi kunni tanlang
    daySelect.value = String(todayDay);

    // ===== Populate Start/End date dropdowns with date ranges =====
    const nowYear = now.getFullYear();
    const startSel = document.getElementById('sel-startdate');
    const endSel = document.getElementById('sel-enddate');
    for (let y = 2021; y <= 2026; y++) {
        for (let m = 1; m <= 12; m++) {
            if (y === nowYear && m > now.getMonth() + 1) break;
            const val = `${y}-${String(m).padStart(2,'0')}-01`;
            const label = `${y}-${String(m).padStart(2,'0')}`;
            const o1 = new Option(label, val);
            const o2 = new Option(label, val);
            startSel.appendChild(o1);
            endSel.appendChild(o2.cloneNode(true));
        }
    }

    // ===== Plotly shared layout =====
    const layoutBase = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#a0aec0', family: 'Inter' },
        margin: { t: 30, r: 20, l: 50, b: 50 }
    };

    // ===== 3D Globe & 2D Leaflet Map =====
    let indexGlobe = null;
    let indexMap = null;
    let mapCircles = [];
    let lastIndexMapData = [];
    let isIndexRotating = true;

    function initIndexLeafletMap() {
        if (indexMap) return;
        indexMap = L.map('map', { zoomControl: true }).setView([41.0, 64.0], 7);
        window.mapObj = indexMap;
        const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap'
        }).addTo(indexMap);
        const sat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: '&copy; Esri'
        });
        L.control.layers({ "🗺️ OpenStreetMap": osm, "🛰️ Sun'iy yo'ldosh": sat }).addTo(indexMap);
    }

    function initIndexGlobe() {
        const container = document.getElementById('globe');
        if (!container || indexGlobe || typeof Globe === 'undefined') return;

        try {
            indexGlobe = Globe()(container)
                .globeImageUrl('/static/img/earth-night.jpg')
                .backgroundImageUrl('/static/img/night-sky.png')
                .showAtmosphere(true)
                .atmosphereColor('#3b82f6')
                .atmosphereAltitude(0.22)
                .pointOfView({ lat: 40.8, lng: 64.5, altitude: 1.7 }, 1200);

            const controls = indexGlobe.controls();
            if (controls) {
                controls.autoRotate = true;
                controls.autoRotateSpeed = 0.5;
                controls.enableDamping = true;
            }

            const ro = new ResizeObserver(entries => {
                for (let entry of entries) {
                    const { width, height } = entry.contentRect;
                    if (width > 0 && height > 0 && indexGlobe) {
                        indexGlobe.width(width).height(height);
                    }
                }
            });
            ro.observe(container);
            indexGlobe.width(container.clientWidth || 800).height(container.clientHeight || 480);
        } catch (e) {
            console.error("Index Globe init xatosi:", e);
        }
    }

    window.switchIndexMapView = function(mode) {
        const globeEl = document.getElementById('globe');
        const mapEl = document.getElementById('map');
        const btn3D = document.getElementById('btnView3D_idx');
        const btn2D = document.getElementById('btnView2D_idx');

        if (mode === '3d') {
            globeEl.style.display = 'block';
            mapEl.style.display = 'none';
            btn3D.style.background = 'linear-gradient(135deg,#3b82f6,#1d4ed8)';
            btn3D.style.color = '#fff';
            btn2D.style.background = 'transparent';
            btn2D.style.color = '#94a3b8';
            if (!indexGlobe) {
                initIndexGlobe();
                if (lastIndexMapData.length) updateMap(lastIndexMapData);
            } else {
                indexGlobe.width(globeEl.clientWidth).height(globeEl.clientHeight);
            }
        } else {
            globeEl.style.display = 'none';
            mapEl.style.display = 'block';
            btn2D.style.background = 'linear-gradient(135deg,#3b82f6,#1d4ed8)';
            btn2D.style.color = '#fff';
            btn3D.style.background = 'transparent';
            btn3D.style.color = '#94a3b8';
            initIndexLeafletMap();
            if (indexMap) {
                setTimeout(() => {
                    indexMap.invalidateSize();
                    if (lastIndexMapData.length) renderLeafletCircles(lastIndexMapData);
                }, 80);
            }
        }
    };

    window.resetIndexGlobeFocus = function() {
        if (indexGlobe) {
            indexGlobe.pointOfView({ lat: 40.8, lng: 64.5, altitude: 1.7 }, 1000);
        }
    };

    window.toggleIndexGlobeRotation = function() {
        if (!indexGlobe) return;
        const c = indexGlobe.controls();
        if (!c) return;
        isIndexRotating = !isIndexRotating;
        c.autoRotate = isIndexRotating;
        const txt = document.getElementById('rotateStatus_idx');
        if (txt) txt.textContent = isIndexRotating ? "Yoqiq" : "O'chiq";
    };

    function renderLeafletCircles(mapData) {
        if (!indexMap) return;
        mapCircles.forEach(c => indexMap.removeLayer(c));
        mapCircles = [];
        mapData.forEach(pt => {
            const color = pt.risk > 70 ? '#ff4444' : (pt.risk > 40 ? '#ffa500' : '#00cc66');
            const circle = L.circle([pt.lat, pt.lon], {
                color: color, fillColor: color, fillOpacity: 0.45,
                radius: pt.risk * 180 + 2000, weight: 1.5
            }).addTo(indexMap);
            circle.bindPopup(`<b>${pt.name || ''}</b><br>Xavf darajasi: <b style="color:${color}">${pt.risk.toFixed(1)}%</b>`);
            mapCircles.push(circle);
        });
    }

    function updateMap(mapData) {
        lastIndexMapData = mapData || [];
        if (indexMap) {
            renderLeafletCircles(lastIndexMapData);
        }

        // 3D Globe yangilash
        if (indexGlobe && mapData && mapData.length) {
            const items = mapData.map(pt => ({
                ...pt,
                color: pt.risk > 70 ? '#ef4444' : (pt.risk > 40 ? '#f59e0b' : '#10b981')
            }));

            // HTML belgilar
            indexGlobe.htmlElementsData(items)
                .htmlLat(d => d.lat)
                .htmlLng(d => d.lon)
                .htmlAltitude(0.015)
                .htmlElement(d => {
                    const el = document.createElement('div');
                    el.style.background = 'rgba(15,23,42,0.92)';
                    el.style.border = `1.5px solid ${d.color}`;
                    el.style.borderRadius = '6px';
                    el.style.padding = '3px 6px';
                    el.style.color = '#fff';
                    el.style.fontSize = '11px';
                    el.style.fontWeight = '600';
                    el.style.whiteSpace = 'nowrap';
                    el.style.boxShadow = `0 0 10px ${d.color}66`;
                    el.style.cursor = 'pointer';
                    el.innerHTML = `<span>⚠️ ${d.name || ''}: <b style="color:${d.color}">${d.risk.toFixed(0)}%</b></span>`;
                    el.onclick = () => {
                        indexGlobe.pointOfView({ lat: d.lat, lng: d.lon, altitude: 1.1 }, 1000);
                    };
                    return el;
                });

            // Doiralar
            indexGlobe.ringsData(items)
                .ringLat(d => d.lat)
                .ringLng(d => d.lon)
                .ringAltitude(0.005)
                .ringColor(d => d.color)
                .ringMaxRadius(d => 1.2 + (d.risk / 50))
                .ringPropagationSpeed(1.2)
                .ringRepeatPeriod(1200);
        }
    }

    initIndexGlobe();

    // ===== Main fetch function =====
    window.fetchData = function() {
        const region = document.getElementById('sel-region').value;
        const year = document.getElementById('sel-year').value;
        const month = document.getElementById('sel-month').value;
        const day = document.getElementById('sel-day').value;
        const startDate = document.getElementById('sel-startdate').value;
        const endDate = document.getElementById('sel-enddate').value;

        // Build URL
        let url = `/api/data?region=${region}`;
        if (year) url += `&year=${year}`;
        if (month) url += `&month=${month}`;
        if (day) url += `&day=${day}`;
        if (startDate) url += `&start_date=${startDate}`;
        if (endDate) url += `&end_date=${endDate}`;

        // Update filter label
        const monthNames = ['','Yanvar','Fevral','Mart','Aprel','May','Iyun','Iyul','Avgust','Sentabr','Oktabr','Noyabr','Dekabr'];
        let label = `📍 Hudud: ${region}`;
        if (year) label += ` | 📅 ${year}`;
        if (month) label += ` — ${monthNames[parseInt(month)]}`;
        if (day) label += ` ${day}-kun`;
        document.getElementById('current-filter-label').textContent = label;

        // Show loading
        document.getElementById('loadingOverlay').classList.add('active');
        document.getElementById('btn-analyze').disabled = true;
        document.getElementById('analyzeSpinner').style.display = 'inline';

        fetch(url)
            .then(res => res.json())
            .then(data => {
                // ----- Metrics -----
                const risk = parseFloat(data.metrics.risk_index);
                const wind = parseFloat(data.metrics.wind_speed);
                const soil = parseFloat(data.metrics.soil_moisture);
                const ndvi = parseFloat(data.metrics.ndvi);

                document.getElementById('val-wind').textContent = wind.toFixed(1) + ' m/s';
                document.getElementById('val-soil').textContent = soil.toFixed(1) + ' %';
                document.getElementById('val-ndvi').textContent = ndvi.toFixed(2);
                document.getElementById('val-risk').textContent = risk.toFixed(0);

                // Color risk
                const riskCard = document.getElementById('val-risk').closest('.metric-card');
                riskCard.style.borderColor = risk > 70 ? '#ef4444' : risk > 40 ? '#f59e0b' : '#10b981';
                document.getElementById('delta-risk').textContent = risk > 70 ? '🔴 Yuqori xavf' : risk > 40 ? '🟡 O\'rtacha xavf' : '🟢 Past xavf';
                document.getElementById('delta-risk').style.color = risk > 70 ? '#ef4444' : risk > 40 ? '#f59e0b' : '#10b981';
                document.getElementById('delta-ndvi').textContent = ndvi < 0.2 ? '🔴 Degradatsiya' : ndvi < 0.35 ? '🟡 O\'rtacha' : '🟢 Yaxshi';
                document.getElementById('delta-wind').textContent = wind > 6 ? '⚠️ Kuchli shamol' : 'Normal';

                // ----- Timeseries -----
                Plotly.newPlot('chart-timeseries', [
                    { x: data.timeseries.dates, y: data.timeseries.ndvi, name: 'NDVI', type: 'scatter',
                      line: {color: '#00ffcc', width: 2.5}, fill: 'tozeroy', fillcolor: 'rgba(0,255,204,0.1)' },
                    { x: data.timeseries.dates, y: data.timeseries.swvl1, name: 'Tuproq Namligi', type: 'scatter',
                      line: {color: '#3399ff', width: 2.5} }
                ], { ...layoutBase, hovermode: 'x unified',
                     xaxis: { title: 'Sana', gridcolor: 'rgba(255,255,255,0.05)' },
                     yaxis: { title: 'Qiymat', gridcolor: 'rgba(255,255,255,0.05)' } });

                Plotly.newPlot('chart-risk', [
                    { x: data.timeseries.dates, y: data.timeseries.risk_index, name: 'Xavf Indeksi', type: 'scatter',
                      line: {color: '#ff4d4d', width: 2.5}, fill: 'tozeroy', fillcolor: 'rgba(255,77,77,0.15)' }
                ], { ...layoutBase, hovermode: 'x unified',
                     xaxis: { title: 'Sana', gridcolor: 'rgba(255,255,255,0.05)' },
                     yaxis: { title: 'Risk (0-100)', range: [0, 100], gridcolor: 'rgba(255,255,255,0.05)' } });

                // ----- Danger months -----
                const monthLabels = ['Yan','Fev','Mar','Apr','May','Iyn','Iyl','Avg','Sen','Okt','Noy','Dek'];
                const monthColors = data.dangerous_months.counts.map(v =>
                    v > 15 ? '#ef4444' : v > 8 ? '#f59e0b' : '#10b981'
                );
                Plotly.newPlot('chart-danger-months', [{
                    x: data.dangerous_months.months.map(m => monthLabels[m-1]),
                    y: data.dangerous_months.counts,
                    type: 'bar',
                    marker: { color: monthColors, line: { color: 'rgba(255,255,255,0.1)', width: 1 } },
                    text: data.dangerous_months.counts.map(v => v > 0 ? v + ' kun' : ''),
                    textposition: 'outside',
                    textfont: { color: '#e2e8f0', size: 11 }
                }], { ...layoutBase,
                      xaxis: { title: 'Oy', gridcolor: 'rgba(255,255,255,0.05)' },
                      yaxis: { title: 'Xavfli kunlar soni', gridcolor: 'rgba(255,255,255,0.05)' } });

                // ----- Wind Rose -----
                Plotly.newPlot('chart-wind-rose', [{
                    r: data.wind_rose.frequencies,
                    theta: data.wind_rose.directions,
                    type: 'barpolar',
                    name: 'Shamol takroriyligi',
                    marker: {
                        color: data.wind_rose.avg_speeds,
                        colorscale: 'Viridis',
                        colorbar: { title: 'm/s', titlefont: {color:'#a0aec0'}, tickfont: {color:'#a0aec0'} },
                        showscale: true
                    }
                }], { ...layoutBase,
                      polar: {
                          radialaxis: { visible: true, ticksuffix: '%', gridcolor: 'rgba(255,255,255,0.1)', tickfont: {color:'#a0aec0'} },
                          angularaxis: { direction: 'clockwise', gridcolor: 'rgba(255,255,255,0.1)', tickfont: {color:'#a0aec0'} },
                          bgcolor: 'rgba(0,0,0,0)'
                      } });

                // ----- Feature Importance -----
                Plotly.newPlot('chart-importance', [{
                    x: data.feature_importance.importances,
                    y: data.feature_importance.features,
                    type: 'bar', orientation: 'h',
                    marker: { color: data.feature_importance.importances, colorscale: 'Magma' }
                }], { ...layoutBase, margin: {l: 90, r: 20, t: 20, b: 40},
                      xaxis: { title: 'Ahamiyat', gridcolor: 'rgba(255,255,255,0.05)' } });

                // ----- Map -----
                updateMap(data.map_data);

                // ----- Initial Prediction -----
                triggerPrediction();

                // Hide loading
                document.getElementById('loadingOverlay').classList.remove('active');
                document.getElementById('btn-analyze').disabled = false;
                document.getElementById('analyzeSpinner').style.display = 'none';
            })
            .catch(err => {
                console.error('Xato:', err);
                document.getElementById('loadingOverlay').classList.remove('active');
                document.getElementById('btn-analyze').disabled = false;
                document.getElementById('analyzeSpinner').style.display = 'none';
            });
    };

    // ===== Sliders sync =====
    ['ws','wd','sm','pwv','ztd'].forEach(id => {
        const inp = document.getElementById(`inp-${id}`);
        const lbl = document.getElementById(`lbl-${id}`);
        if (inp && lbl) inp.addEventListener('input', () => { lbl.textContent = inp.value; });
    });

    // ===== ML Prediction =====
    document.getElementById('btn-predict').addEventListener('click', triggerPrediction);

    function triggerPrediction() {
        const payload = {
            wind_speed: parseFloat(document.getElementById('inp-ws').value),
            wind_dir: parseFloat(document.getElementById('inp-wd').value),
            swvl1: parseFloat(document.getElementById('inp-sm').value),
            pwv: parseFloat(document.getElementById('inp-pwv').value),
            ztd: parseFloat(document.getElementById('inp-ztd').value)
        };
        fetch('/api/predict', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        }).then(r => r.json()).then(data => {
            const title = document.getElementById('pred-title');
            if (data.prediction === 1) {
                title.innerHTML = `🚨 DIQQAT! Chang bo'roni xavfi: ${(data.probability*100).toFixed(1)}%`;
                title.style.color = '#ef4444';
            } else {
                title.innerHTML = `✅ Barqaror holat. Xavf: ${(data.probability*100).toFixed(1)}%`;
                title.style.color = '#10b981';
            }
            Plotly.newPlot('chart-gauge', [{
                type: 'indicator', mode: 'gauge+number',
                value: data.probability * 100,
                number: { font: {color:'#fff', family:'Inter', size:36}, suffix:'%' },
                gauge: {
                    axis: { range: [null,100], tickcolor:'#a0aec0' },
                    bar: { color: 'rgba(255,255,255,0.8)' },
                    bgcolor: 'rgba(255,255,255,0.03)',
                    bordercolor: 'rgba(255,255,255,0.1)',
                    steps: [
                        {range:[0,30], color:'rgba(16,185,129,0.4)'},
                        {range:[30,70], color:'rgba(245,158,11,0.4)'},
                        {range:[70,100], color:'rgba(239,68,68,0.4)'}
                    ]
                }
            }], { ...layoutBase, height:200, margin:{t:20,b:20,l:20,r:20} });
        });
    }

    // ===== Simulation =====
    function runSimulation() {
        const loader = document.getElementById('sim-loading');
        const img = document.getElementById('sim-image');
        const btn = document.getElementById('btn-simulate');
        if (loader) loader.style.display = 'block';
        if (btn) { btn.disabled = true; btn.textContent = '⏳ Hisoblanmoqda...'; }

        fetch('/api/simulate', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                if (data.image) img.src = data.image;
                if (loader) loader.style.display = 'none';
                if (btn) { btn.disabled = false; btn.textContent = '🔄 Qayta hisoblash'; }
            })
            .catch(err => {
                console.error("Simulation error:", err);
                if (loader) loader.style.display = 'none';
                if (btn) { btn.disabled = false; btn.textContent = '🔄 Qayta hisoblash'; }
            });
    }
    const simBtn = document.getElementById('btn-simulate');
    if (simBtn) simBtn.addEventListener('click', runSimulation);

    // ===== Initial load =====
    fetchData();
    // Eslatma: Simulyatsiya rasmi allaqachon tayyor holda yuklanadi, qayta hisoblab o'tirmaydi
});
