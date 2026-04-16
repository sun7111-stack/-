-- Demo seed data for the current backend schema
-- Mapping note:
--   enterprise_info          -> enterprise_profiles + users
--   raw_data_record          -> raw_data_record
--   parsed_data_record        -> parsed_data_record
--   activity_record           -> activity_record
--   emission_factor           -> emission_factor_items
--   analysis_result           -> analysis_results
--   analysis_breakdown        -> analysis_breakdowns
--   esg_result                -> stored in enterprise_profiles.esg_score + comment-like fields via analysis / risk tables
--   risk_result               -> risk_results
--   report_record             -> report_records
--   event_stream              -> event_stream
--   evidence_chain_record     -> evidence_chain_record
--
-- Usage:
--   1) Run on a fresh development database.
--   2) If your DB already has data, review the explicit IDs before executing.

SET NAMES utf8mb4;
START TRANSACTION;

-- ----------------------------
-- 1. Users
-- ----------------------------
INSERT INTO users (
    id, email, password_hash, name, company, company_type, position, phone, enterprise_account,
    failed_login_attempts, is_active
) VALUES
(9001, 'demo-e001@carbon-ai.com', '', '绿能科技管理员', '绿能科技有限公司', 'ecommerce', '数据负责人', '13800138001', 'E001_ADMIN', 0, 1),
(9002, 'demo-e002@carbon-ai.com', '', '环宇制造管理员', '环宇制造有限公司', 'manufacture', '数据负责人', '13900139002', 'E002_ADMIN', 0, 1)
ON DUPLICATE KEY UPDATE
email = VALUES(email),
name = VALUES(name),
company = VALUES(company),
company_type = VALUES(company_type),
position = VALUES(position),
phone = VALUES(phone),
enterprise_account = VALUES(enterprise_account),
failed_login_attempts = VALUES(failed_login_attempts),
is_active = VALUES(is_active);

-- ----------------------------
-- 2. Enterprise profiles
-- ----------------------------
INSERT INTO enterprise_profiles (
    id, user_id, company_name, industry, company_scale, annual_revenue, employee_count, main_products,
    address, legal_person, established_date, credit_code, contact_person, contact_phone,
    total_carbon_emission, logistics_carbon_intensity, energy_intensity, esg_score, carbon_efficiency_grade
) VALUES
(9001, 9001, '绿能科技有限公司', '跨境电商', '中小型企业', 1480.00, 86,
 '跨境物流、海外仓运营、电商销售', '华中地区', '张伟', '2021-06-15', '91420100MA4XXX001', '张明', '13800138001',
 12.17, 0.47, 0.82, 73.7, 'B'),
(9002, 9002, '环宇制造有限公司', '通用设备制造', '中型企业', 4668.00, 260,
 '机械加工、零部件生产、仓储物流', '华东地区', '李强', '2019-09-20', '91320200MA4XXX002', '李华', '13900139002',
 35.01, 0.18, 0.75, 78.0, 'B+')
ON DUPLICATE KEY UPDATE
user_id = VALUES(user_id),
company_name = VALUES(company_name),
industry = VALUES(industry),
company_scale = VALUES(company_scale),
annual_revenue = VALUES(annual_revenue),
employee_count = VALUES(employee_count),
main_products = VALUES(main_products),
address = VALUES(address),
legal_person = VALUES(legal_person),
established_date = VALUES(established_date),
credit_code = VALUES(credit_code),
contact_person = VALUES(contact_person),
contact_phone = VALUES(contact_phone),
total_carbon_emission = VALUES(total_carbon_emission),
logistics_carbon_intensity = VALUES(logistics_carbon_intensity),
energy_intensity = VALUES(energy_intensity),
esg_score = VALUES(esg_score),
carbon_efficiency_grade = VALUES(carbon_efficiency_grade);

-- ----------------------------
-- 3. Raw data records
-- ----------------------------
INSERT INTO raw_data_record (
    id, enterprise_id, data_type, file_name, file_path, upload_time, parse_status
) VALUES
(1001, 9001, 'electricity_invoice', '电费账单_2026_03.jpg', '/demo/files/e001_power_202603.jpg', '2026-04-10 10:20:00', 'success'),
(1002, 9001, 'logistics_record', '物流清单_2026_03.xlsx', '/demo/files/e001_logistics_202603.xlsx', '2026-04-10 10:30:00', 'success'),
(1003, 9001, 'storage_energy', '仓储能耗表_2026_03.xlsx', '/demo/files/e001_storage_202603.xlsx', '2026-04-10 10:40:00', 'success'),
(1004, 9002, 'electricity_invoice', '电费账单_2026_03.jpg', '/demo/files/e002_power_202603.jpg', '2026-04-10 11:00:00', 'success'),
(1005, 9002, 'fuel_record', '柴油消耗表_2026_03.xlsx', '/demo/files/e002_fuel_202603.xlsx', '2026-04-10 11:10:00', 'success'),
(1006, 9002, 'production_energy', '生产能耗表_2026_03.xlsx', '/demo/files/e002_production_202603.xlsx', '2026-04-10 11:20:00', 'success')
ON DUPLICATE KEY UPDATE
enterprise_id = VALUES(enterprise_id),
data_type = VALUES(data_type),
file_name = VALUES(file_name),
file_path = VALUES(file_path),
upload_time = VALUES(upload_time),
parse_status = VALUES(parse_status);

-- ----------------------------
-- 4. Parsed data records
-- ----------------------------
INSERT INTO parsed_data_record (
    id, raw_data_id, raw_field_name, raw_field_value, parsed_field_name, parsed_field_value, confidence_score, created_at
) VALUES
(2001, 1001, '用电量', '12500度', 'electricity_usage', '12500', 0.96, '2026-04-10 10:21:00'),
(2002, 1001, '地区', '湖北省武汉市', 'region', '华中', 0.94, '2026-04-10 10:21:00'),
(2003, 1001, '计费周期', '2026年3月', 'period', '2026-03', 0.98, '2026-04-10 10:21:00'),
(2004, 1002, '运输方式', '公路运输', 'transport_mode', 'road', 0.95, '2026-04-10 10:31:00'),
(2005, 1002, '总运输距离', '8500公里', 'transport_distance', '8500', 0.97, '2026-04-10 10:31:00'),
(2006, 1002, '货运总重量', '120吨', 'cargo_weight', '120', 0.92, '2026-04-10 10:31:00'),
(2007, 1003, '仓储用电量', '4200度', 'storage_usage', '4200', 0.95, '2026-04-10 10:41:00'),
(2008, 1004, '用电量', '28000度', 'electricity_usage', '28000', 0.96, '2026-04-10 11:01:00'),
(2009, 1005, '柴油消耗量', '3200升', 'fuel_usage', '3200', 0.97, '2026-04-10 11:11:00'),
(2010, 1006, '生产用电量', '15000度', 'production_usage', '15000', 0.94, '2026-04-10 11:21:00'),
(2011, 1003, '包装耗材用量', '300kg', 'packaging_usage', '300', 0.91, '2026-04-10 10:42:00'),
(2012, 1006, '仓储补录能耗', '3500度', 'storage_usage', '3500', 0.90, '2026-04-10 11:24:00')
ON DUPLICATE KEY UPDATE
raw_data_id = VALUES(raw_data_id),
raw_field_name = VALUES(raw_field_name),
raw_field_value = VALUES(raw_field_value),
parsed_field_name = VALUES(parsed_field_name),
parsed_field_value = VALUES(parsed_field_value),
confidence_score = VALUES(confidence_score),
created_at = VALUES(created_at);

-- ----------------------------
-- 5. Standardized activity records
-- ----------------------------
INSERT INTO activity_record (
    id, enterprise_id, parsed_id, activity_type, activity_amount, activity_unit, amount_raw, unit_raw,
    scope, scope3_category, stage, dq_activity_level, region_code, period_time, clean_status, created_at
) VALUES
(3001, 9001, 2001, 'electricity', 12500, 'kWh', 12500, '度', 'S2', '', 'production', 'A', '华中', '2026-03', 'success', '2026-04-10 10:23:00'),
(3002, 9001, 2005, 'logistics_road', 8500, 't·km', 8500, '公里', 'S3', 'transport', 'transport', 'A', '全国', '2026-03', 'success', '2026-04-10 10:33:00'),
(3003, 9001, 2007, 'storage_energy', 4200, 'kWh', 4200, '度', 'S2', 'warehouse', 'storage', 'A', '华中', '2026-03', 'success', '2026-04-10 10:43:00'),
(3004, 9001, 2011, 'packaging', 300, 'kg', 300, 'kg', 'S3', 'packaging', 'procurement', 'B', '华中', '2026-03', 'success', '2026-04-10 10:44:00'),
(3005, 9002, 2008, 'electricity', 28000, 'kWh', 28000, '度', 'S2', '', 'production', 'A', '华东', '2026-03', 'success', '2026-04-10 11:03:00'),
(3006, 9002, 2009, 'fuel_diesel', 3200, 'L', 3200, '升', 'S1', '', 'transport', 'A', '全国', '2026-03', 'success', '2026-04-10 11:13:00'),
(3007, 9002, 2010, 'production_energy', 15000, 'kWh', 15000, '度', 'S2', '', 'production', 'A', '华东', '2026-03', 'success', '2026-04-10 11:23:00'),
(3008, 9002, 2012, 'storage_energy', 3500, 'kWh', 3500, '度', 'S2', 'warehouse', 'storage', 'B', '华东', '2026-03', 'success', '2026-04-10 11:24:00')
ON DUPLICATE KEY UPDATE
enterprise_id = VALUES(enterprise_id),
parsed_id = VALUES(parsed_id),
activity_type = VALUES(activity_type),
activity_amount = VALUES(activity_amount),
activity_unit = VALUES(activity_unit),
amount_raw = VALUES(amount_raw),
unit_raw = VALUES(unit_raw),
scope = VALUES(scope),
scope3_category = VALUES(scope3_category),
stage = VALUES(stage),
dq_activity_level = VALUES(dq_activity_level),
region_code = VALUES(region_code),
period_time = VALUES(period_time),
clean_status = VALUES(clean_status),
created_at = VALUES(created_at);

-- ----------------------------
-- 6. Emission factor items
-- ----------------------------
INSERT INTO emission_factor_items (
    id, activity_type, industry_type, region, factor_value, factor_unit, source, version,
    year, version_tag, valid_from, valid_to, method, source_type, dq_factor_level, gsd_factor, description
) VALUES
(4001, 'electricity', 'general', '华中', 0.5703, 'kgCO2e/kWh', '生态环境部《省级电网排放因子2024修订版》', '2024', 2024, '2024', '2024-01-01', '2024-12-31', 'default', 'government_factor', 'A', 0.03, '华中电网排放因子'),
(4002, 'electricity', 'general', '华东', 0.5307, 'kgCO2e/kWh', '生态环境部《省级电网排放因子2024修订版》', '2024', 2024, '2024', '2024-01-01', '2024-12-31', 'default', 'government_factor', 'A', 0.03, '华东电网排放因子'),
(4003, 'logistics_road', 'general', '全国', 0.112, 'kgCO2e/(t·km)', '《交通运输企业温室气体排放核算指南2024》', '2024', 2024, '2024', '2024-01-01', '2024-12-31', 'default', 'government_factor', 'B', 0.06, '公路运输因子'),
(4004, 'storage_energy', 'general', '华中', 0.5703, 'kgCO2e/kWh', '同电网因子', '2024', 2024, '2024', '2024-01-01', '2024-12-31', 'default', 'government_factor', 'A', 0.03, '仓储用电因子'),
(4005, 'storage_energy', 'general', '华东', 0.5307, 'kgCO2e/kWh', '同电网因子', '2024', 2024, '2024', '2024-01-01', '2024-12-31', 'default', 'government_factor', 'A', 0.03, '仓储用电因子'),
(4006, 'fuel_diesel', 'general', '全国', 3.1603, 'kgCO2e/L', '《工业企业温室气体排放核算要求2024》', '2024', 2024, '2024', '2024-01-01', '2024-12-31', 'default', 'government_factor', 'A', 0.04, '柴油因子'),
(4007, 'packaging', 'general', '全国', 1.25, 'kgCO2e/kg', 'CEADs中国产品碳足迹数据库', '2024', 2024, '2024', '2024-01-01', '2024-12-31', 'default', 'government_factor', 'B', 0.08, '包装纸/纸箱因子')
ON DUPLICATE KEY UPDATE
activity_type = VALUES(activity_type),
industry_type = VALUES(industry_type),
region = VALUES(region),
factor_value = VALUES(factor_value),
factor_unit = VALUES(factor_unit),
source = VALUES(source),
version = VALUES(version),
year = VALUES(year),
version_tag = VALUES(version_tag),
valid_from = VALUES(valid_from),
valid_to = VALUES(valid_to),
method = VALUES(method),
source_type = VALUES(source_type),
dq_factor_level = VALUES(dq_factor_level),
gsd_factor = VALUES(gsd_factor),
description = VALUES(description);

-- ----------------------------
-- 7. Industry benchmarks
-- ----------------------------
INSERT INTO industry_benchmarks (
    id, industry, industry_cn, carbon_per_revenue, energy_metric, other_metric
) VALUES
(4101, 'cross_border_ecommerce', '跨境电商', 0.71, 10.60, 0.38),
(4102, 'manufacture_general', '通用设备制造', 0.70, 32.70, 0.62)
ON DUPLICATE KEY UPDATE
industry_cn = VALUES(industry_cn),
carbon_per_revenue = VALUES(carbon_per_revenue),
energy_metric = VALUES(energy_metric),
other_metric = VALUES(other_metric);

-- ----------------------------
-- 8. Analysis results
-- ----------------------------
INSERT INTO analysis_results (
    id, user_id, enterprise_name, analysis_time, total_emission, carbon_intensity, industry_deviation,
    scope1, scope2, scope3, ci95_low, ci95_high, uncertainty_mode, risk_level, major_source,
    top_contributor_activity_id, advice_text
) VALUES
(5001, 9001, '绿能科技有限公司', '2026-04-10 11:20:00', 12.17, 0.82, 0.15, 0.00, 7.13, 5.04, 11.70, 12.65, 'analytic', 'high', 'logistics', 3002,
 '物流排放占比超45%，建议优化运输路线、合并订单；逐步替换新能源仓储叉车'),
(5002, 9002, '环宇制造有限公司', '2026-04-10 12:00:00', 35.01, 0.75, 0.07, 10.11, 22.81, 2.09, 33.50, 36.52, 'analytic', 'medium', 'electricity', 3005,
 '电力排放占比超60%，建议安装光伏分布式电站；推进生产设备能效改造')
ON DUPLICATE KEY UPDATE
user_id = VALUES(user_id),
enterprise_name = VALUES(enterprise_name),
analysis_time = VALUES(analysis_time),
total_emission = VALUES(total_emission),
carbon_intensity = VALUES(carbon_intensity),
industry_deviation = VALUES(industry_deviation),
scope1 = VALUES(scope1),
scope2 = VALUES(scope2),
scope3 = VALUES(scope3),
ci95_low = VALUES(ci95_low),
ci95_high = VALUES(ci95_high),
uncertainty_mode = VALUES(uncertainty_mode),
risk_level = VALUES(risk_level),
major_source = VALUES(major_source),
top_contributor_activity_id = VALUES(top_contributor_activity_id),
advice_text = VALUES(advice_text);

-- ----------------------------
-- 9. Analysis breakdowns
-- ----------------------------
INSERT INTO analysis_breakdowns (
    id, analysis_id, source_type, emission_value, proportion
) VALUES
(6001, 5001, 'logistics', 5.71, 0.47),
(6002, 5001, 'electricity', 7.13, 0.32),
(6003, 5001, 'storage', 2.40, 0.20),
(6004, 5001, 'packaging', 0.38, 0.03),
(6005, 5002, 'electricity', 22.81, 0.65),
(6006, 5002, 'fuel_diesel', 10.11, 0.29),
(6007, 5002, 'production', 1.86, 0.05),
(6008, 5002, 'storage', 0.23, 0.01)
ON DUPLICATE KEY UPDATE
analysis_id = VALUES(analysis_id),
source_type = VALUES(source_type),
emission_value = VALUES(emission_value),
proportion = VALUES(proportion);

-- ----------------------------
-- 10. Risk results
-- ----------------------------
INSERT INTO risk_results (
    id, user_id, analysis_id, risk_score, risk_level, risk_reason, risk_advice
) VALUES
(7001, 9001, 5001, 76, '高风险', '碳强度高于行业15%；物流排放占比超行业均值9个百分点；治理维度评分低于行业均值', '优先优化运输组织，建立月度碳排放监测机制；完善ESG信息披露制度'),
(7002, 9002, 5002, 59, '中风险', '电力排放占比高于行业均值3个百分点；生产设备能效未达行业先进水平', '推进分布式光伏建设；开展生产设备能效诊断；建立能耗精细化管理体系')
ON DUPLICATE KEY UPDATE
user_id = VALUES(user_id),
analysis_id = VALUES(analysis_id),
risk_score = VALUES(risk_score),
risk_level = VALUES(risk_level),
risk_reason = VALUES(risk_reason),
risk_advice = VALUES(risk_advice);

-- ----------------------------
-- 11. Report records
-- ----------------------------
INSERT INTO report_records (
    id, user_id, analysis_id, report_type, report_title, generate_time, export_status, file_path, report_context, report_preview
) VALUES
(8001, 9001, 'AN001', '碳排分析报告', '绿能科技2026年3月碳排分析报告', '2026-04-10 11:40:00', 'generated', '/demo/reports/rp001.pdf',
 JSON_OBJECT('enterprise_name', '绿能科技有限公司', 'analysis_date', '2026-04-10', 'report_type', '碳排分析报告'),
 JSON_OBJECT('summary', '示例碳排分析报告', 'risk_level', '高风险')),
(8002, 9002, 'AN002', 'ESG风险评估报告', '环宇制造2026年3月ESG风险评估报告', '2026-04-10 12:20:00', 'generated', '/demo/reports/rp002.pdf',
 JSON_OBJECT('enterprise_name', '环宇制造有限公司', 'analysis_date', '2026-04-10', 'report_type', 'ESG风险评估报告'),
 JSON_OBJECT('summary', '示例ESG风险评估报告', 'risk_level', '中风险'))
ON DUPLICATE KEY UPDATE
user_id = VALUES(user_id),
analysis_id = VALUES(analysis_id),
report_type = VALUES(report_type),
report_title = VALUES(report_title),
generate_time = VALUES(generate_time),
export_status = VALUES(export_status),
file_path = VALUES(file_path),
report_context = VALUES(report_context),
report_preview = VALUES(report_preview);

-- ----------------------------
-- 12. Event stream
-- ----------------------------
INSERT INTO event_stream (
    id, enterprise_name, event_type, event_desc, event_time, event_status
) VALUES
(9001, '绿能科技', '凭证上传', '成功上传2026年3月电费账单、物流清单共3份文件', '2026-04-10 10:20:00', 'success'),
(9002, '绿能科技', 'OCR识别', '成功提取电费账单12个字段，平均置信度96%', '2026-04-10 10:22:00', 'success'),
(9003, '环宇制造', '凭证上传', '成功上传2026年3月电费、柴油消耗、生产能耗共3份文件', '2026-04-10 11:00:00', 'success'),
(9004, '绿能科技', '碳核算完成', '完成2026年3月碳排放核算，总排放12.17吨CO₂e', '2026-04-10 11:20:00', 'success'),
(9005, '绿能科技', '数据上链', '碳排放原始凭证及核算结果已存证，哈希值：0x66bd4625ac7f9e3b...', '2026-04-10 11:25:00', 'success'),
(9006, '绿能科技', '报告生成', '智能碳排分析报告已生成，支持PDF导出', '2026-04-10 11:40:00', 'success'),
(9007, '环宇制造', '碳核算完成', '完成2026年3月碳排放核算，总排放35.01吨CO₂e', '2026-04-10 12:00:00', 'success'),
(9008, '环宇制造', '风控扫描', '完成ESG风险扫描，风险等级：中风险', '2026-04-10 12:10:00', 'success'),
(9009, '环宇制造', '报告生成', 'ESG风险评估报告已生成，支持PDF导出', '2026-04-10 12:20:00', 'success'),
(9010, '系统通知', '行业更新', '已同步2026年第一季度最新电网排放因子', '2026-04-10 12:30:00', 'info')
ON DUPLICATE KEY UPDATE
enterprise_name = VALUES(enterprise_name),
event_type = VALUES(event_type),
event_desc = VALUES(event_desc),
event_time = VALUES(event_time),
event_status = VALUES(event_status);

-- ----------------------------
-- 13. Legacy evidence chain records
-- ----------------------------
INSERT INTO evidence_chain_record (
    id, raw_data_id, analysis_id, step_name, hash_value, chain_status, meta_payload, timestamp
) VALUES
(10001, 'R001', 'AN001', '原始凭证上传', 'ec-hash-001', 'stored', JSON_OBJECT('object_type', 'electricity_invoice'), '2026-04-10 10:20:00'),
(10002, 'R001', 'AN001', 'OCR识别完成', 'ec-hash-002', 'parsed', JSON_OBJECT('object_type', 'ocr_result'), '2026-04-10 10:22:00'),
(10003, 'R001', 'AN001', '数据标准化完成', 'ec-hash-003', 'standardized', JSON_OBJECT('object_type', 'activity_record'), '2026-04-10 10:25:00'),
(10004, 'R001', 'AN001', '碳核算完成', 'ec-hash-004', 'analyzed', JSON_OBJECT('object_type', 'analysis_result'), '2026-04-10 11:20:00'),
(10005, 'R001', 'AN001', '链上存证成功', '0x66bd4625ac7f9e3b8d1c2a4f6b7e9d0c', 'stored', JSON_OBJECT('tx_id', '0x66bd4625ac7f9e3b8d1c2a4f6b7e9d0c'), '2026-04-10 11:25:00')
ON DUPLICATE KEY UPDATE
raw_data_id = VALUES(raw_data_id),
analysis_id = VALUES(analysis_id),
step_name = VALUES(step_name),
hash_value = VALUES(hash_value),
chain_status = VALUES(chain_status),
meta_payload = VALUES(meta_payload),
timestamp = VALUES(timestamp);

COMMIT;
