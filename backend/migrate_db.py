"""
数据库迁移脚本 —— 新版前端适配
运行方式: python migrate_db.py

变更内容:
  1. users 表: 新增 position 列（职位）
  2. enterprise_profiles 表: 新增 company_scale 列（企业规模）
  3. contact_messages 表: 新增 company_type 列（企业类型）
  4. reports 表: template_type ENUM 新增 'reduction' 值
"""
from sqlalchemy import text
from database import engine


MIGRATIONS = [
    # 1. users.position
    {
        "name": "users.position",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='users' AND COLUMN_NAME='position'",
        "sql": "ALTER TABLE users ADD COLUMN position VARCHAR(100) NOT NULL DEFAULT '' COMMENT '职位'",
    },
    # 2. enterprise_profiles.company_scale
    {
        "name": "enterprise_profiles.company_scale",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='enterprise_profiles' AND COLUMN_NAME='company_scale'",
        "sql": "ALTER TABLE enterprise_profiles ADD COLUMN company_scale VARCHAR(20) NOT NULL DEFAULT '' COMMENT '企业规模: micro/small/medium/large'",
    },
    # 3. contact_messages.company_type
    {
        "name": "contact_messages.company_type",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='contact_messages' AND COLUMN_NAME='company_type'",
        "sql": "ALTER TABLE contact_messages ADD COLUMN company_type VARCHAR(50) NOT NULL DEFAULT '' COMMENT '企业类型: ecommerce/manufacture/logistics/other'",
    },
    # 4. reports.template_type ENUM 新增 reduction
    {
        "name": "reports.template_type (add reduction)",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='reports' "
                 "AND COLUMN_NAME='template_type' AND COLUMN_TYPE LIKE '%reduction%'",
        "sql": "ALTER TABLE reports MODIFY COLUMN template_type ENUM('basic','reduction','esg','finance') NOT NULL DEFAULT 'basic' COMMENT '报告类型'",
    },
    # 5. raw_data_record 核心原始凭证表
    {
        "name": "create raw_data_record",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='raw_data_record'",
        "sql": """
            CREATE TABLE raw_data_record (
                id INT AUTO_INCREMENT PRIMARY KEY,
                enterprise_id INT NULL,
                data_type VARCHAR(50) NOT NULL DEFAULT '',
                file_name VARCHAR(255) NOT NULL DEFAULT '',
                file_path VARCHAR(500) NOT NULL DEFAULT '',
                upload_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                parse_status VARCHAR(30) NOT NULL DEFAULT 'pending',
                INDEX idx_raw_enterprise_upload (enterprise_id, upload_time),
                INDEX idx_raw_status_upload (parse_status, upload_time),
                INDEX idx_raw_data_type (data_type),
                CONSTRAINT fk_raw_data_enterprise FOREIGN KEY (enterprise_id) REFERENCES enterprise_profiles(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
    },
    # 6. parsed_data_record OCR解析结果表
    {
        "name": "create parsed_data_record",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='parsed_data_record'",
        "sql": """
            CREATE TABLE parsed_data_record (
                id INT AUTO_INCREMENT PRIMARY KEY,
                raw_data_id INT NOT NULL,
                raw_field_name VARCHAR(120) NOT NULL DEFAULT '',
                raw_field_value TEXT NOT NULL,
                parsed_field_name VARCHAR(120) NOT NULL DEFAULT '',
                parsed_field_value TEXT NOT NULL,
                confidence_score FLOAT NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_parsed_raw_created (raw_data_id, created_at),
                CONSTRAINT fk_parsed_raw_data FOREIGN KEY (raw_data_id) REFERENCES raw_data_record(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
    },
    # 7. activity_record 标准化活动记录表
    {
        "name": "create activity_record",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='activity_record'",
        "sql": """
            CREATE TABLE activity_record (
                id INT AUTO_INCREMENT PRIMARY KEY,
                enterprise_id INT NULL,
                parsed_id INT NOT NULL,
                activity_type VARCHAR(80) NOT NULL DEFAULT '',
                activity_amount FLOAT NOT NULL DEFAULT 0,
                activity_unit VARCHAR(40) NOT NULL DEFAULT '',
                region_code VARCHAR(30) NOT NULL DEFAULT '全国',
                period_time VARCHAR(30) NOT NULL DEFAULT '',
                clean_status VARCHAR(30) NOT NULL DEFAULT 'warning',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_activity_enterprise_period (enterprise_id, period_time),
                INDEX idx_activity_status_created (clean_status, created_at),
                INDEX idx_activity_type (activity_type),
                CONSTRAINT fk_activity_enterprise FOREIGN KEY (enterprise_id) REFERENCES enterprise_profiles(id),
                CONSTRAINT fk_activity_parsed FOREIGN KEY (parsed_id) REFERENCES parsed_data_record(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
    },
    # 8. emission_factor_items.method
    {
        "name": "emission_factor_items.method",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='emission_factor_items' AND COLUMN_NAME='method'",
        "sql": "ALTER TABLE emission_factor_items ADD COLUMN method VARCHAR(50) NOT NULL DEFAULT 'default'",
    },
    # 9. emission_factor_items.source_type
    {
        "name": "emission_factor_items.source_type",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='emission_factor_items' AND COLUMN_NAME='source_type'",
        "sql": "ALTER TABLE emission_factor_items ADD COLUMN source_type VARCHAR(50) NOT NULL DEFAULT 'government_factor'",
    },
    # 10. emission_factor_items.year
    {
        "name": "emission_factor_items.year",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='emission_factor_items' AND COLUMN_NAME='year'",
        "sql": "ALTER TABLE emission_factor_items ADD COLUMN year INT NULL",
    },
    # 11. emission_factor_items.version_tag
    {
        "name": "emission_factor_items.version_tag",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='emission_factor_items' AND COLUMN_NAME='version_tag'",
        "sql": "ALTER TABLE emission_factor_items ADD COLUMN version_tag VARCHAR(50) NOT NULL DEFAULT ''",
    },
    # 12. emission_factor_items.valid_from
    {
        "name": "emission_factor_items.valid_from",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='emission_factor_items' AND COLUMN_NAME='valid_from'",
        "sql": "ALTER TABLE emission_factor_items ADD COLUMN valid_from VARCHAR(20) NOT NULL DEFAULT ''",
    },
    # 13. emission_factor_items.valid_to
    {
        "name": "emission_factor_items.valid_to",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='emission_factor_items' AND COLUMN_NAME='valid_to'",
        "sql": "ALTER TABLE emission_factor_items ADD COLUMN valid_to VARCHAR(20) NOT NULL DEFAULT ''",
    },
    # 14. emission_factor_items.dq_factor_level
    {
        "name": "emission_factor_items.dq_factor_level",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='emission_factor_items' AND COLUMN_NAME='dq_factor_level'",
        "sql": "ALTER TABLE emission_factor_items ADD COLUMN dq_factor_level VARCHAR(10) NOT NULL DEFAULT 'C'",
    },
    # 15. emission_factor_items.gsd_factor
    {
        "name": "emission_factor_items.gsd_factor",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='emission_factor_items' AND COLUMN_NAME='gsd_factor'",
        "sql": "ALTER TABLE emission_factor_items ADD COLUMN gsd_factor FLOAT NOT NULL DEFAULT 0.1",
    },
    # 16. activity_record.scope
    {
        "name": "activity_record.scope",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='activity_record' AND COLUMN_NAME='scope'",
        "sql": "ALTER TABLE activity_record ADD COLUMN scope VARCHAR(10) NOT NULL DEFAULT 'S3'",
    },
    # 17. activity_record.scope3_category
    {
        "name": "activity_record.scope3_category",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='activity_record' AND COLUMN_NAME='scope3_category'",
        "sql": "ALTER TABLE activity_record ADD COLUMN scope3_category VARCHAR(80) NULL DEFAULT ''",
    },
    # 18. activity_record.stage
    {
        "name": "activity_record.stage",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='activity_record' AND COLUMN_NAME='stage'",
        "sql": "ALTER TABLE activity_record ADD COLUMN stage VARCHAR(40) NOT NULL DEFAULT 'production'",
    },
    # 19. activity_record.dq_activity_level
    {
        "name": "activity_record.dq_activity_level",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='activity_record' AND COLUMN_NAME='dq_activity_level'",
        "sql": "ALTER TABLE activity_record ADD COLUMN dq_activity_level VARCHAR(10) NOT NULL DEFAULT 'C'",
    },
    # 20. activity_record.amount_raw
    {
        "name": "activity_record.amount_raw",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='activity_record' AND COLUMN_NAME='amount_raw'",
        "sql": "ALTER TABLE activity_record ADD COLUMN amount_raw FLOAT NULL DEFAULT 0",
    },
    # 21. activity_record.unit_raw
    {
        "name": "activity_record.unit_raw",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='activity_record' AND COLUMN_NAME='unit_raw'",
        "sql": "ALTER TABLE activity_record ADD COLUMN unit_raw VARCHAR(40) NOT NULL DEFAULT ''",
    },
    # 22. analysis_results.scope1
    {
        "name": "analysis_results.scope1",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='analysis_results' AND COLUMN_NAME='scope1'",
        "sql": "ALTER TABLE analysis_results ADD COLUMN scope1 FLOAT NOT NULL DEFAULT 0",
    },
    # 23. analysis_results.scope2
    {
        "name": "analysis_results.scope2",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='analysis_results' AND COLUMN_NAME='scope2'",
        "sql": "ALTER TABLE analysis_results ADD COLUMN scope2 FLOAT NOT NULL DEFAULT 0",
    },
    # 24. analysis_results.scope3
    {
        "name": "analysis_results.scope3",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='analysis_results' AND COLUMN_NAME='scope3'",
        "sql": "ALTER TABLE analysis_results ADD COLUMN scope3 FLOAT NOT NULL DEFAULT 0",
    },
    # 25. analysis_results.ci95_low
    {
        "name": "analysis_results.ci95_low",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='analysis_results' AND COLUMN_NAME='ci95_low'",
        "sql": "ALTER TABLE analysis_results ADD COLUMN ci95_low FLOAT NOT NULL DEFAULT 0",
    },
    # 26. analysis_results.ci95_high
    {
        "name": "analysis_results.ci95_high",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='analysis_results' AND COLUMN_NAME='ci95_high'",
        "sql": "ALTER TABLE analysis_results ADD COLUMN ci95_high FLOAT NOT NULL DEFAULT 0",
    },
    # 27. analysis_results.uncertainty_mode
    {
        "name": "analysis_results.uncertainty_mode",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='analysis_results' AND COLUMN_NAME='uncertainty_mode'",
        "sql": "ALTER TABLE analysis_results ADD COLUMN uncertainty_mode VARCHAR(20) NOT NULL DEFAULT 'analytic'",
    },
    # 28. analysis_results.top_contributor_activity_id
    {
        "name": "analysis_results.top_contributor_activity_id",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='analysis_results' AND COLUMN_NAME='top_contributor_activity_id'",
        "sql": "ALTER TABLE analysis_results ADD COLUMN top_contributor_activity_id INT NULL",
    },
    # 29. create factor_match_log
    {
        "name": "create factor_match_log",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='factor_match_log'",
        "sql": """
            CREATE TABLE factor_match_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                analysis_id INT NOT NULL,
                activity_id INT NULL,
                factor_id INT NULL,
                match_rule VARCHAR(100) NOT NULL DEFAULT '',
                fallback_level VARCHAR(50) NOT NULL DEFAULT '',
                match_explain TEXT NOT NULL,
                factor_value_snapshot FLOAT NOT NULL DEFAULT 0,
                factor_source_snapshot VARCHAR(255) NOT NULL DEFAULT '',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_factor_match_analysis (analysis_id),
                INDEX idx_factor_match_activity (activity_id),
                INDEX idx_factor_match_factor (factor_id),
                CONSTRAINT fk_factor_match_analysis FOREIGN KEY (analysis_id) REFERENCES analysis_results(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
    },
    # 30. create analysis_result_v2_snapshot
    {
        "name": "create analysis_result_v2_snapshot",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='analysis_result_v2_snapshot'",
        "sql": """
            CREATE TABLE analysis_result_v2_snapshot (
                id INT AUTO_INCREMENT PRIMARY KEY,
                analysis_id INT NOT NULL UNIQUE,
                model_version VARCHAR(10) NOT NULL DEFAULT 'v2',
                uncertainty_mode VARCHAR(20) NOT NULL DEFAULT 'analytic',
                scope_breakdown JSON NOT NULL,
                source_breakdown JSON NOT NULL,
                uncertainty JSON NOT NULL,
                top_contributors JSON NOT NULL,
                factor_trace JSON NOT NULL,
                carbon_flow_graph JSON NOT NULL,
                explain_trace JSON NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_analysis_v2_analysis (analysis_id),
                CONSTRAINT fk_analysis_v2_analysis FOREIGN KEY (analysis_id) REFERENCES analysis_results(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
    },
    # 31. create evidence_object
    {
        "name": "create evidence_object",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='evidence_object'",
        "sql": """
            CREATE TABLE evidence_object (
                id INT AUTO_INCREMENT PRIMARY KEY,
                object_id VARCHAR(64) NOT NULL,
                analysis_id VARCHAR(64) NOT NULL,
                object_type VARCHAR(40) NOT NULL DEFAULT '',
                canonical_json TEXT NOT NULL,
                object_hash VARCHAR(64) NOT NULL,
                encrypted_blob_ref VARCHAR(255) NOT NULL DEFAULT '',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_evidence_object_id (object_id),
                INDEX idx_evidence_object_analysis (analysis_id),
                INDEX idx_evidence_object_hash (object_hash)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
    },
    # 32. create evidence_chain_step
    {
        "name": "create evidence_chain_step",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='evidence_chain_step'",
        "sql": """
            CREATE TABLE evidence_chain_step (
                id INT AUTO_INCREMENT PRIMARY KEY,
                analysis_id VARCHAR(64) NOT NULL,
                step_name VARCHAR(100) NOT NULL DEFAULT '',
                prev_hash VARCHAR(64) NOT NULL DEFAULT '',
                object_hash VARCHAR(64) NOT NULL DEFAULT '',
                current_hash VARCHAR(64) NOT NULL DEFAULT '',
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(30) NOT NULL DEFAULT 'stored',
                INDEX idx_evidence_step_analysis (analysis_id),
                INDEX idx_evidence_step_current_hash (current_hash),
                INDEX idx_evidence_step_time (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
    },
    # 33. create evidence_anchor
    {
        "name": "create evidence_anchor",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='evidence_anchor'",
        "sql": """
            CREATE TABLE evidence_anchor (
                id INT AUTO_INCREMENT PRIMARY KEY,
                analysis_id VARCHAR(64) NOT NULL,
                merkle_root VARCHAR(64) NOT NULL,
                tx_id VARCHAR(128) NOT NULL DEFAULT '',
                chain_name VARCHAR(64) NOT NULL DEFAULT 'fabric-devnet',
                issuer VARCHAR(120) NOT NULL DEFAULT 'platform',
                block_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                tsa_token TEXT NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_evidence_anchor_analysis (analysis_id),
                INDEX idx_evidence_anchor_root (merkle_root),
                INDEX idx_evidence_anchor_tx (tx_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
    },
    # 34. create evidence_proof
    {
        "name": "create evidence_proof",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='evidence_proof'",
        "sql": """
            CREATE TABLE evidence_proof (
                id INT AUTO_INCREMENT PRIMARY KEY,
                leaf_id VARCHAR(64) NOT NULL,
                analysis_id VARCHAR(64) NOT NULL,
                leaf_hash VARCHAR(64) NOT NULL,
                merkle_path_json JSON NOT NULL,
                root_hash VARCHAR(64) NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_evidence_proof_leaf (leaf_id),
                INDEX idx_evidence_proof_analysis (analysis_id),
                INDEX idx_evidence_proof_root (root_hash)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
    },
    # 35. create trust_score_record
    {
        "name": "create trust_score_record",
        "check": "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                 "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='trust_score_record'",
        "sql": """
            CREATE TABLE trust_score_record (
                id INT AUTO_INCREMENT PRIMARY KEY,
                analysis_id VARCHAR(64) NOT NULL,
                trust_score INT NOT NULL DEFAULT 0,
                components_json JSON NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_trust_score_analysis (analysis_id),
                INDEX idx_trust_score_value (trust_score)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
    },
]


def run_migrations():
    for mig in MIGRATIONS:
        with engine.connect() as conn:
            count = conn.execute(text(mig["check"])).scalar()
            if count == 0:
                print(f"  [执行] {mig['name']}")
                with engine.begin() as txn:
                    txn.execute(text(mig["sql"]))
                print(f"  [完成] {mig['name']}")
            else:
                print(f"  [跳过] {mig['name']}（已存在）")

    print("\n迁移完成！")


if __name__ == "__main__":
    print("开始数据库迁移...")
    run_migrations()
