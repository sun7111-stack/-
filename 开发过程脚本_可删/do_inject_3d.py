# -*- coding: utf-8 -*-
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_content = content
if 'id="benchmarkCompareBox"' in content and '<div id="factory3dContainer"' not in content:
    idx_start = content.find('id="benchmarkCompareBox"')
    idx_1 = content.find('</div>', idx_start)
    idx_2 = content.find('</div>', idx_1 + 1)
    idx_3 = content.find('</div>', idx_2 + 1)
    idx_end = idx_3 + 6
    
    pre = content[:idx_end]
    post = content[idx_end:]
    
    new_content = pre + '''
                              <!-- 3D Digital Twin Card -->
                              <div class="col-12 mt-3">
                                  <div class="card shadow-lg border-0 overflow-hidden">
                                      <div class="card-header bg-dark text-info fw-bold border-0 d-flex justify-content-between align-items-center">
                                          <span><i class="fas fa-cubes me-2"></i>车间 3D 碳排放数字孪生 (WebGL 实时渲染) <span class="badge bg-danger ms-2 fade-anim">LIVE</span></span>
                                          <span class="badge bg-secondary text-light" style="font-family: monospace;">ENG: THREE.JS v135</span>
                                      </div>
                                      <div class="card-body p-0 position-relative">
                                          <div id="factory3dContainer" style="width: 100%; height: 400px; background: #050510;"></div>

                                          <div class="position-absolute top-0 start-0 m-3 text-white" style="pointer-events: none; z-index: 10;">
                                              <div class="p-2 rounded twin-sensor" style="background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); font-family: monospace; font-size: 13px; border-left: 3px solid #0dcaf0;">
                                                  <p class="mb-1 text-info"><i class="fas fa-satellite-dish me-2"></i>实时传感采集点簇(IOT)</p>
                                                  <p class="mb-1">STATUS: <span class="text-success flash-status">ONLINE 联机</span></p>
                                                  <p class="mb-1">RATE: <span id="twinEmissionsRate" class="text-warning fw-bold fs-5">0.00</span> <span class="text-muted">kgCO2/sec</span></p>
                                                  <p class="mb-0">TEMP: <span class="text-danger">85.4°C</span> | LOAD: <span class="text-primary">92%</span></p>
                                              </div>
                                          </div>
                                      </div>
                                  </div>
                              </div>''' + post
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Script successfully added 3D container!')
else:
    print('Target not found or already injected')

if 'twin3d.js' not in new_content:
    new_content = new_content.replace('<script src="demo-flow.js"></script>', '<script src="demo-flow.js"></script>\n    <script src="twin3d.js"></script>')
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
