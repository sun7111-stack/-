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
