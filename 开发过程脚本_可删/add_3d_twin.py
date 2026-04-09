import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add the 3D twin UI inside carbonResultBox
new_ui = """                              <div class="col-md-6 mb-3">
                                  <div class="card shadow-sm h-100 border-0">
                                      <div class="card-header bg-light fw-bold">行业基准对比 Benchmark</div>
                                      <div class="card-body" id="benchmarkCompareBox" style="min-height: 250px;"></div>
                                  </div>
                              </div>
                              
                              <!-- 3D Digital Twin Card -->
                              <div class="col-12 mt-3">
                                  <div class="card shadow-lg border-0 overflow-hidden">
                                      <div class="card-header bg-dark text-info fw-bold border-0 d-flex justify-content-between align-items-center">
                                          <span><i class="fas fa-cubes me-2"></i>车间 3D 碳排放数字孪生 (WebGL 实时渲染) <span class="badge bg-danger ms-2 fade-anim">LIVE</span></span>
                                          <span class="badge bg-secondary text-light" style="font-family: monospace;">ENG: THREE.JS v135</span>
                                      </div>
                                      <div class="card-body p-0 position-relative">
                                          <div id="factory3dContainer" style="width: 100%; height: 350px; background: #050510;"></div>
                                          
                                          <div class="position-absolute top-0 start-0 m-3 text-white" style="pointer-events: none; z-index: 10;">
                                              <div class="p-2 rounded" style="background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); font-family: monospace; font-size: 13px; border-left: 3px solid #0dcaf0;">
                                                  <p class="mb-1 text-info"><i class="fas fa-satellite-dish me-2"></i>实时传感采集点簇(IOT)</p>
                                                  <p class="mb-1">STATUS: <span class="text-success flash-status">ONLINE 联机</span></p>
                                                  <p class="mb-1">RATE: <span id="twinEmissionsRate" class="text-warning fw-bold fs-5">0.00</span> <span class="text-muted">kgCO₂/sec</span></p>
                                                  <p class="mb-0">TEMP: <span class="text-danger">85.4°C</span> | LOAD: <span class="text-primary">92%</span></p>
                                              </div>
                                          </div>
                                      </div>
                                  </div>
                              </div>
"""

html = html.replace('''                              <div class="col-md-6 mb-3">
                                  <div class="card shadow-sm h-100 border-0">
                                      <div class="card-header bg-light fw-bold">行业基准对比 Benchmark</div>
                                      <div class="card-body" id="benchmarkCompareBox" style="min-height: 250px;"></div>
                                  </div>
                              </div>''', new_ui)

# 2. Add twin3d.js to scripts
script_insert = '<script src="demo-flow.js"></script>\n             <script src="twin3d.js"></script>'
html = html.replace('<script src="demo-flow.js"></script>', script_insert)

# 3. Add glowing CSS
style_insert = '''    <style>
        .fade-anim { animation: fadeInOut 2s infinite; }
        @keyframes fadeInOut { 0%, 100% { opacity: 0.4; } 50% { opacity: 1; box-shadow: 0 0 10px red; } }
        .flash-status { animation: flashText 1s infinite alternate; }
        @keyframes flashText { from { opacity: 1; } to { opacity: 0.5; } }
'''
if '<style>' in html:
    html = html.replace('<style>', style_insert)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
