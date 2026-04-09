import re
with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Regex to find demo-carbon
pattern = r'(<section id="demo-carbon" class="page-section" style="display:none;">)(.*?)(</section>)'
match = re.search(pattern, content, re.DOTALL)

if match:
    new_section = r'''<section id="demo-carbon" class="page-section" style="display:none;">
                      <div class="container py-4">
                          <h3 class="mb-2"><i class="fas fa-leaf text-success me-2"></i>自动化碳核算与数字孪生分析</h3>
                          <p class="text-muted mb-4 small">基于票据识别与业务活动数据，自动完成碳排放核算、结构分析与可视化监测。</p>
                          
                          <div class="mb-4">
                              <button id="carbonBtn" class="btn btn-success me-2"><i class="fas fa-calculator me-2"></i>开始核算</button>
                              <button class="btn btn-outline-secondary me-2"><i class="fas fa-database me-2"></i>查看示例数据</button>
                              <button class="btn btn-outline-primary"><i class="fas fa-download me-2"></i>导出分析结果</button>
                          </div>

                          <!-- 顶部 4 张核心指标卡 -->
                          <div id="carbonTotalCard" class="row g-3 mb-4" style="display:none;">
                              <div class="col-md-3">
                                  <div class="card border-0 shadow-sm h-100 position-relative border-start border-success border-4">
                                      <div class="card-body">
                                          <div class="text-muted small fw-bold mb-1">本期总碳排放量 <span class="badge bg-light text-dark float-end">月度核算</span></div>
                                          <h2 class="text-success mb-0 fw-bold"><span id="totalCarbonValue">--</span> <small class="fs-6 text-muted">tCO₂e</small></h2>
                                          <div class="mt-2 small text-danger"><i class="fas fa-arrow-up me-1"></i>较上期 +8.4%</div>
                                      </div>
                                  </div>
                              </div>
                              <div class="col-md-3">
                                  <div class="card border-0 shadow-sm h-100 position-relative border-start border-warning border-4">
                                      <div class="card-body">
                                          <div class="text-muted small fw-bold mb-1">主要排放源 <span class="badge bg-light text-dark float-end">主要贡献项</span></div>
                                          <h2 class="text-dark mb-0 fw-bold">电力消耗</h2>
                                          <div class="mt-2 small text-muted">占总排放 <span class="fw-bold text-dark">46%</span></div>
                                      </div>
                                  </div>
                              </div>
                              <div class="col-md-3">
                                  <div class="card border-0 shadow-sm h-100 position-relative border-start border-info border-4">
                                      <div class="card-body">
                                          <div class="text-muted small fw-bold mb-1">行业偏离度 <span class="badge bg-light text-dark float-end">基准对比</span></div>
                                          <h2 class="text-info mb-0 fw-bold">+12.3%</h2>
                                          <div class="mt-2 small text-muted">高于行业平均</div>
                                      </div>
                                  </div>
                              </div>
                              <div class="col-md-3">
                                  <div class="card border-0 shadow-sm h-100 position-relative border-start border-danger border-4">
                                      <div class="card-body">
                                          <div class="text-muted small fw-bold mb-1">风险等级 <span class="badge bg-light text-dark float-end">动态预警</span></div>
                                          <h2 class="text-danger mb-0 fw-bold">中风险</h2>
                                          <div class="mt-2 small text-muted">运输数据需进一步核验</div>
                                      </div>
                                  </div>
                              </div>
                          </div>

                          <!-- 核心图表分析区 -->
                          <div id="carbonResultBox" class="row g-3" style="display:none;">
                              <!-- Left Chart -->
                              <div class="col-md-6 mb-3">
                                  <div class="card shadow-sm h-100 border-0">
                                      <div class="card-header bg-light border-0 d-flex justify-content-between align-items-center">
                                          <span class="fw-bold">核算明细 Breakdown</span>
                                          <div class="btn-group btn-group-sm">
                                              <button class="btn btn-outline-secondary active">占比视图</button>
                                              <button class="btn btn-outline-secondary">数值视图</button>
                                          </div>
                                      </div>
                                      <div class="card-body px-4 pb-0 pt-2 d-flex flex-column">
                                          <p class="text-muted small mb-0">展示本期碳排放的来源结构与占比分布</p>
                                          <div id="carbonBreakdownList" style="display:none;"></div>
                                          <div id="pieChartBox" style="flex-grow: 1; min-height: 250px;"></div>
                                          <p class="text-muted small mb-3 border-top pt-2 mt-2"><strong>当前排放主要集中于电力使用与燃料消耗环节，两者合计占比超过68%。</strong></p>
                                      </div>
                                  </div>
                              </div>
                              
                              <!-- Right Chart -->
                              <div class="col-md-6 mb-3">
                                  <div class="card shadow-sm h-100 border-0">
                                      <div class="card-header bg-light border-0 d-flex justify-content-between align-items-center">
                                          <span class="fw-bold">行业基准对比 Benchmark</span>
                                          <div class="btn-group btn-group-sm">
                                              <button class="btn btn-outline-secondary active">月度</button>
                                              <button class="btn btn-outline-secondary">年度</button>
                                          </div>
                                      </div>
                                      <div class="card-body px-4 pb-0 pt-2 d-flex flex-column">
                                          <p class="text-muted small mb-0">展示本企业与行业平均水平及行业优秀水平的差异</p>
                                          <div id="benchmarkCompareBox" style="flex-grow: 1; min-height: 250px;"></div>
                                          <p class="text-muted small mb-3 border-top pt-2 mt-2"><strong>企业当前碳排放水平高于行业平均值，仍存在一定优化空间。</strong></p>
                                      </div>
                                  </div>
                              </div>
                              
                              <!-- 3D Digital Twin Card -->
                              <div class="col-12 mt-3">
                                  <div class="card shadow-lg border-0 overflow-hidden">
                                      <div class="card-header bg-dark text-info fw-bold border-0 d-flex flex-column">
                                          <div class="d-flex justify-content-between align-items-center">
                                              <span><i class="fas fa-cubes me-2"></i>企业碳排放数字孪生监测舱</span>
                                              <div>
                                                  <span class="badge bg-danger fade-anim">LIVE</span>
                                                  <span class="badge bg-success ms-1">在线监测中</span>
                                                  <span class="badge bg-secondary ms-1">示例数据驱动</span>
                                                  <span class="badge bg-secondary text-light ms-1" style="font-family: monospace;">ENG: THREE.JS v135</span>
                                              </div>
                                          </div>
                                          <p class="text-secondary small mb-0 mt-1 fw-normal">基于实时运行参数与核算结果，动态展示设备状态、排放速率与负载水平</p>
                                      </div>
                                      
                                      <div class="card-body p-0 position-relative">
                                          <div id="factory3dContainer" style="width: 100%; height: 400px; background: #050510;"></div>

                                          <div class="position-absolute top-0 start-0 m-3 text-white" style="pointer-events: none; z-index: 10;">
                                              <div class="p-2 rounded twin-sensor" style="background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); font-family: monospace; font-size: 13px; border-left: 3px solid #0dcaf0;">
                                                  <p class="mb-1 text-info"><i class="fas fa-satellite-dish me-2"></i>实时传感采集点位(IOT)</p>
                                                  <p class="mb-1">STATUS: <span class="text-success flash-status">ONLINE 联机</span></p>
                                                  <p class="mb-1">RATE: <span id="twinEmissionsRate" class="text-warning fw-bold fs-5">0.82</span> <span class="text-muted">kgCO₂/sec</span></p>
                                                  <p class="mb-0">TEMP: <span class="text-danger">85.4°C</span> | LOAD: <span class="text-primary">92%</span></p>
                                              </div>
                                          </div>
                                          
                                          <div class="position-absolute bottom-0 start-0 w-100 p-2" style="background: rgba(0,0,0,0.7); z-index: 10;">
                                              <div class="d-flex justify-content-between align-items-center px-2">
                                                  <div>
                                                      <button class="btn btn-sm btn-outline-info active text-white border-info me-2" style="font-size:12px;">总排放模式</button>
                                                      <button class="btn btn-sm btn-outline-danger text-white border-secondary me-2" style="font-size:12px;">风险热区模式</button>
                                                      <button class="btn btn-sm btn-outline-success text-white border-secondary" style="font-size:12px;">ESG视图</button>
                                                  </div>
                                                  <div class="text-light small text-end" style="font-size: 12px; font-family: sans-serif;">
                                                      <i class="fas fa-info-circle text-info me-1"></i> 当前监测结果显示，核心排放节点主要集中于高负载电力设备区域，建议优先关注用电结构优化。
                                                  </div>
                                              </div>
                                          </div>
                                      </div>
                                  </div>
                              </div>

                              <!-- 分析摘要区 -->
                              <div class="col-12 mt-4">
                                  <div class="card shadow-sm border-0 bg-light">
                                      <div class="card-header bg-white fw-bold border-bottom">
                                          <i class="fas fa-clipboard-check text-primary me-2"></i>核算结论与优化建议
                                      </div>
                                      <div class="card-body">
                                          <div class="row">
                                              <div class="col-md-6 border-end pe-4">
                                                  <h6 class="text-dark fw-bold mb-3"><i class="fas fa-chart-line text-success me-2"></i>核算结论</h6>
                                                  <p class="text-muted small mb-2">1. 本期企业总碳排放量为 <strong class="text-dark">7.26 tCO₂e</strong>，整体水平略高于行业平均。</p>
                                                  <p class="text-muted small mb-2">2. 排放主要集中于<strong class="text-dark">电力消耗与燃料使用环节</strong>，是当前减排的重点方向。</p>
                                                  <p class="text-muted small mb-0">3. 运输活动数据波动较明显，存在进一步核验与优化空间。</p>
                                              </div>
                                              <div class="col-md-6 ps-4">
                                                  <h6 class="text-dark fw-bold mb-3"><i class="fas fa-lightbulb text-warning me-2"></i>系统建议</h6>
                                                  <p class="text-muted small mb-2">1. 优先优化高负载设备的用电结构，提高能源利用效率。</p>
                                                  <p class="text-muted small mb-2">2. 对运输环节进行分项记录，提升活动数据的完整性与准确性。</p>
                                                  <p class="text-muted small mb-0">3. 结合行业基准值制定分阶段减排目标，并生成专项分析报告。</p>
                                              </div>
                                          </div>
                                      </div>
                                  </div>
                              </div>

                          </div>
                      </div>
                  </section>'''
    
    content = content[:match.start()] + new_section + content[match.end():]
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated index.html layout.")
else:
    print("Could not find demo-carbon section.")
