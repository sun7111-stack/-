"""首页事件流与证据链模型"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func

from database import Base


class EventStream(Base):
    """首页滚动事件流"""

    __tablename__ = "event_stream"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    enterprise_name = Column(String(200), nullable=False, default="", index=True)
    event_type = Column(String(50), nullable=False, default="", index=True)
    event_desc = Column(Text, nullable=False, default="")
    event_status = Column(String(30), nullable=False, default="done", index=True)
    event_time = Column(DateTime, nullable=False, server_default=func.now(), index=True)


class EvidenceChainRecord(Base):
    """证据链步骤记录"""

    __tablename__ = "evidence_chain_record"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    raw_data_id = Column(String(64), nullable=False, default="", index=True)
    analysis_id = Column(String(64), nullable=False, default="", index=True)
    step_name = Column(String(100), nullable=False, default="", index=True)
    hash_value = Column(String(64), nullable=False, default="", index=True)
    chain_status = Column(String(30), nullable=False, default="stored", index=True)
    meta_payload = Column(JSON, nullable=False, default=dict)
    timestamp = Column(DateTime, nullable=False, server_default=func.now(), index=True)


class EvidenceObject(Base):
    """证据对象（D1-D5）"""

    __tablename__ = "evidence_object"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    object_id = Column(String(64), nullable=False, default="", unique=True, index=True)
    analysis_id = Column(String(64), nullable=False, default="", index=True)
    object_type = Column(String(40), nullable=False, default="", index=True)
    canonical_json = Column(Text, nullable=False, default="")
    object_hash = Column(String(64), nullable=False, default="", index=True)
    encrypted_blob_ref = Column(String(255), nullable=False, default="")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)


class EvidenceChainStep(Base):
    """证据链步骤（链式摘要）"""

    __tablename__ = "evidence_chain_step"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    analysis_id = Column(String(64), nullable=False, default="", index=True)
    step_name = Column(String(100), nullable=False, default="", index=True)
    prev_hash = Column(String(64), nullable=False, default="", index=True)
    object_hash = Column(String(64), nullable=False, default="", index=True)
    current_hash = Column(String(64), nullable=False, default="", index=True)
    timestamp = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    status = Column(String(30), nullable=False, default="stored", index=True)


class EvidenceAnchor(Base):
    """链上锚定记录"""

    __tablename__ = "evidence_anchor"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    analysis_id = Column(String(64), nullable=False, default="", unique=True, index=True)
    merkle_root = Column(String(64), nullable=False, default="", index=True)
    tx_id = Column(String(128), nullable=False, default="", index=True)
    chain_name = Column(String(64), nullable=False, default="fabric-devnet")
    issuer = Column(String(120), nullable=False, default="platform")
    block_time = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    tsa_token = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)


class EvidenceProof(Base):
    """Merkle 审计路径"""

    __tablename__ = "evidence_proof"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    leaf_id = Column(String(64), nullable=False, default="", unique=True, index=True)
    analysis_id = Column(String(64), nullable=False, default="", index=True)
    leaf_hash = Column(String(64), nullable=False, default="", index=True)
    merkle_path_json = Column(JSON, nullable=False, default=list)
    root_hash = Column(String(64), nullable=False, default="", index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)


class TrustScoreRecord(Base):
    """可信度评分记录"""

    __tablename__ = "trust_score_record"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    analysis_id = Column(String(64), nullable=False, default="", unique=True, index=True)
    trust_score = Column(Integer, nullable=False, default=0)
    components_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
