"""首页图谱、事件流、证据链路由"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import get_db
from models.flow import (
    EventStream,
    EvidenceChainRecord,
    EvidenceObject,
    EvidenceChainStep,
    EvidenceAnchor,
    EvidenceProof,
    TrustScoreRecord,
)
from models.analysis import AnalysisResult, RiskResult
from services.evidence_chain import (
    canonicalize_object,
    hash_evidence_object,
    build_chain_step,
    build_merkle_root,
    build_merkle_proofs,
    verify_hash_chain,
    verify_merkle_proof,
    compute_trust_score,
    make_anchor_tx_id,
)
from utils.auth import get_current_user_optional

router = APIRouter(prefix="/api", tags=["首页图谱与证据链"])


class EvidenceStoreBody(BaseModel):
    raw_data_id: str = ""
    analysis_id: str = ""
    step_name: str = ""
    hash_value: str = ""
    chain_status: str = "stored"
    payload: Dict[str, Any] = {}
    issuer: str = "platform"
    chain_name: str = "fabric-devnet"
    evidence_objects: List[Dict[str, Any]] = []


class EvidenceVerifyBody(BaseModel):
    analysis_id: Optional[str] = None
    leaf_id: Optional[str] = None


def _to_iso(value: Optional[datetime]) -> str:
    return value.isoformat() if value else ""


def _collect_step_dicts(steps: List[EvidenceChainStep]) -> List[Dict[str, Any]]:
    return [
        {
            "step_name": s.step_name,
            "prev_hash": s.prev_hash,
            "object_hash": s.object_hash,
            "current_hash": s.current_hash,
            "timestamp": s.timestamp,
            "status": s.status,
        }
        for s in steps
    ]


def _verify_timeline_time(steps: List[EvidenceChainStep], anchor: Optional[EvidenceAnchor]) -> bool:
    if not steps:
        return False
    ordered = sorted(steps, key=lambda x: x.timestamp)
    for i in range(1, len(ordered)):
        if ordered[i].timestamp < ordered[i - 1].timestamp:
            return False
    if anchor is not None:
        return anchor.block_time >= ordered[-1].timestamp
    return False


def _compute_merkle_inclusion_pass(analysis_id: str, db: Session) -> bool:
    proof_rows = (
        db.query(EvidenceProof)
        .filter(EvidenceProof.analysis_id == analysis_id)
        .order_by(EvidenceProof.id.asc())
        .all()
    )
    if not proof_rows:
        return False
    for row in proof_rows:
        if not verify_merkle_proof(row.leaf_hash, row.merkle_path_json or [], row.root_hash):
            return False
    return True


def _build_chain_response(analysis_id: str, db: Session) -> Dict[str, Any]:
    steps = (
        db.query(EvidenceChainStep)
        .filter(EvidenceChainStep.analysis_id == analysis_id)
        .order_by(EvidenceChainStep.timestamp.asc(), EvidenceChainStep.id.asc())
        .all()
    )
    if not steps:
        return {}

    anchor = db.query(EvidenceAnchor).filter(EvidenceAnchor.analysis_id == analysis_id).first()
    trust = db.query(TrustScoreRecord).filter(TrustScoreRecord.analysis_id == analysis_id).first()

    hash_chain_ok = verify_hash_chain(_collect_step_dicts(steps))
    merkle_ok = _compute_merkle_inclusion_pass(analysis_id, db)
    timestamp_ok = _verify_timeline_time(steps, anchor)

    return {
        "analysis_id": analysis_id,
        "anchor": {
            "type": "onchain",
            "chain": anchor.chain_name if anchor else "",
            "tx_id": anchor.tx_id if anchor else "",
            "block_time": _to_iso(anchor.block_time) if anchor else "",
            "merkle_root": anchor.merkle_root if anchor else "",
            "issuer": anchor.issuer if anchor else "",
        },
        "trust_score": round((trust.trust_score / 100.0), 4) if trust else 0.0,
        "timeline": [
            {
                "step": s.step_name,
                "time": _to_iso(s.timestamp),
                "hash": s.current_hash,
                "ok": s.status == "stored",
            }
            for s in steps
        ],
        "verify": {
            "hash_chain": "pass" if hash_chain_ok else "fail",
            "merkle_inclusion": "pass" if merkle_ok else "fail",
            "timestamp": "pass" if timestamp_ok else "fail",
        },
    }


@router.get("/home/graph", summary="首页图谱数据")
def home_graph(current_user=Depends(get_current_user_optional)):
    enterprise_name = "Demo企业"
    if current_user is not None:
        enterprise_name = current_user.company or "Demo企业"

    return {
        "nodes": [
            {"id": "enterprise", "name": enterprise_name, "category": "enterprise"},
            {"id": "voucher", "name": "凭证中心", "category": "evidence"},
            {"id": "carbon", "name": "核算引擎", "category": "engine"},
            {"id": "risk", "name": "风控模块", "category": "risk"},
            {"id": "bank", "name": "金融机构", "category": "finance"},
        ],
        "links": [
            {"source": "enterprise", "target": "voucher", "value": 1},
            {"source": "voucher", "target": "carbon", "value": 1},
            {"source": "carbon", "target": "risk", "value": 1},
            {"source": "risk", "target": "bank", "value": 1},
        ],
    }


@router.get("/events/latest", summary="首页最新事件流")
def latest_events(limit: int = 8, db: Session = Depends(get_db)):
    records = (
        db.query(EventStream)
        .order_by(EventStream.event_time.desc())
        .limit(limit)
        .all()
    )

    if records:
        return {
            "events": [
                {
                    "event_id": r.id,
                    "enterprise_name": r.enterprise_name,
                    "event_type": r.event_type,
                    "event_desc": r.event_desc,
                    "event_status": r.event_status,
                    "event_time": r.event_time.isoformat() if r.event_time else "",
                }
                for r in records
            ]
        }

    now = datetime.now().isoformat()
    return {
        "events": [
            {"event_id": 1, "enterprise_name": "Demo企业", "event_type": "ocr_done", "event_desc": "OCR识别完成", "event_status": "done", "event_time": now},
            {"event_id": 2, "enterprise_name": "Demo企业", "event_type": "govern_done", "event_desc": "数据治理完成", "event_status": "done", "event_time": now},
            {"event_id": 3, "enterprise_name": "Demo企业", "event_type": "carbon_done", "event_desc": "碳核算完成", "event_status": "done", "event_time": now},
            {"event_id": 4, "enterprise_name": "Demo企业", "event_type": "risk_alert", "event_desc": "风控扫描完成", "event_status": "warning", "event_time": now},
            {"event_id": 5, "enterprise_name": "Demo企业", "event_type": "report_done", "event_desc": "报告预览已生成", "event_status": "done", "event_time": now},
        ]
    }


@router.post("/evidence/store", summary="写入证据链步骤")
def evidence_store(body: EvidenceStoreBody, db: Session = Depends(get_db)):
    analysis_id = (body.analysis_id or "").strip()
    if not analysis_id:
        analysis_id = f"AN-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    objects = body.evidence_objects or []
    if not objects:
        # 兼容旧调用：把单步 payload 也当做一个证据对象。
        objects = [
            {
                "object_type": body.step_name or "custom",
                "step_name": body.step_name or "custom",
                "payload": body.payload or {},
                "blob_ref": "",
            }
        ]

    prev_step = (
        db.query(EvidenceChainStep)
        .filter(EvidenceChainStep.analysis_id == analysis_id)
        .order_by(EvidenceChainStep.timestamp.desc(), EvidenceChainStep.id.desc())
        .first()
    )
    prev_hash = prev_step.current_hash if prev_step else "GENESIS"

    hashes: List[str] = []
    leaf_ids: List[str] = []

    for idx, obj in enumerate(objects):
        step_name = str(obj.get("step_name") or obj.get("object_type") or f"step_{idx+1}")
        object_type = str(obj.get("object_type") or step_name)
        payload = obj.get("payload") if isinstance(obj.get("payload"), dict) else {}
        blob_ref = str(obj.get("blob_ref") or "")

        canonical_json = canonicalize_object(payload)
        object_hash = hash_evidence_object(payload)

        now_ts = datetime.utcnow().replace(microsecond=0)
        now_iso = now_ts.isoformat()
        object_id = make_anchor_tx_id(analysis_id, object_hash, f"{now_iso}|{idx}")
        current_hash = build_chain_step(prev_hash, object_hash, now_iso)

        db.add(
            EvidenceObject(
                object_id=object_id,
                analysis_id=analysis_id,
                object_type=object_type,
                canonical_json=canonical_json,
                object_hash=object_hash,
                encrypted_blob_ref=blob_ref,
            )
        )

        db.add(
            EvidenceChainStep(
                analysis_id=analysis_id,
                step_name=step_name,
                prev_hash=prev_hash,
                object_hash=object_hash,
                current_hash=current_hash,
                timestamp=now_ts,
                status="stored",
            )
        )

        # 兼容旧表，保留历史展示能力。
        db.add(
            EvidenceChainRecord(
                raw_data_id=body.raw_data_id or "",
                analysis_id=analysis_id,
                step_name=step_name,
                hash_value=current_hash,
                chain_status="stored",
                meta_payload={
                    "object_type": object_type,
                    "object_hash": object_hash,
                    "prev_hash": prev_hash,
                },
            )
        )

        hashes.append(object_hash)
        leaf_ids.append(object_id)
        prev_hash = current_hash

    merkle_root = build_merkle_root(hashes)
    block_time = datetime.utcnow()
    tx_id = "0x" + make_anchor_tx_id(analysis_id, merkle_root, block_time.isoformat())[:24]

    anchor = db.query(EvidenceAnchor).filter(EvidenceAnchor.analysis_id == analysis_id).first()
    if anchor is None:
        anchor = EvidenceAnchor(
            analysis_id=analysis_id,
            merkle_root=merkle_root,
            tx_id=tx_id,
            chain_name=body.chain_name,
            issuer=body.issuer,
            block_time=block_time,
            tsa_token="",
        )
        db.add(anchor)
    else:
        anchor.merkle_root = merkle_root
        anchor.tx_id = tx_id
        anchor.chain_name = body.chain_name
        anchor.issuer = body.issuer
        anchor.block_time = block_time

    # 锚定步骤也写入链式摘要，保证时间轴完整（... -> anchored）。
    anchor_ts = block_time.replace(microsecond=0)
    anchor_hash = build_chain_step(prev_hash, merkle_root, anchor_ts.isoformat())
    db.add(
        EvidenceChainStep(
            analysis_id=analysis_id,
            step_name="anchored",
            prev_hash=prev_hash,
            object_hash=merkle_root,
            current_hash=anchor_hash,
            timestamp=anchor_ts,
            status="stored",
        )
    )
    db.add(
        EvidenceChainRecord(
            raw_data_id=body.raw_data_id or "",
            analysis_id=analysis_id,
            step_name="anchored",
            hash_value=anchor_hash,
            chain_status="stored",
            meta_payload={"merkle_root": merkle_root, "tx_id": tx_id},
        )
    )

    proofs = build_merkle_proofs(hashes)
    for idx, leaf_id in enumerate(leaf_ids):
        row = db.query(EvidenceProof).filter(EvidenceProof.leaf_id == leaf_id).first()
        if row is None:
            row = EvidenceProof(
                leaf_id=leaf_id,
                analysis_id=analysis_id,
                leaf_hash=hashes[idx],
                merkle_path_json=proofs.get(idx, []),
                root_hash=merkle_root,
            )
            db.add(row)
        else:
            row.leaf_hash = hashes[idx]
            row.merkle_path_json = proofs.get(idx, [])
            row.root_hash = merkle_root

    db.flush()

    steps = (
        db.query(EvidenceChainStep)
        .filter(EvidenceChainStep.analysis_id == analysis_id)
        .order_by(EvidenceChainStep.timestamp.asc(), EvidenceChainStep.id.asc())
        .all()
    )
    step_dicts = _collect_step_dicts(steps)
    trust = compute_trust_score(
        steps=step_dicts,
        merkle_ok=True,
        anchor_time=block_time,
        issuer_or_tx=tx_id,
    )

    trust_row = db.query(TrustScoreRecord).filter(TrustScoreRecord.analysis_id == analysis_id).first()
    trust_percent = int(round(trust.trust_score * 100))
    if trust_row is None:
        trust_row = TrustScoreRecord(
            analysis_id=analysis_id,
            trust_score=trust_percent,
            components_json=trust.components,
        )
        db.add(trust_row)
    else:
        trust_row.trust_score = trust_percent
        trust_row.components_json = trust.components

    db.commit()

    return {
        "success": True,
        "analysis_id": analysis_id,
        "stored_objects": len(objects),
        "leaf_ids": leaf_ids,
        "merkle_root": merkle_root,
        "tx_id": tx_id,
        "trust_score": round(trust.trust_score, 4),
        "timestamp": _to_iso(block_time),
    }


@router.get("/evidence/chain/{record_id}", summary="查询证据链")
def evidence_chain(record_id: str, db: Session = Depends(get_db)):
    # 先走新证据链查询（analysis_id）。
    chain_payload = _build_chain_response(record_id, db)
    if chain_payload:
        return chain_payload

    # 兼容旧表查询。
    rows: List[EvidenceChainRecord] = (
        db.query(EvidenceChainRecord)
        .filter(
            or_(
                EvidenceChainRecord.raw_data_id == record_id,
                EvidenceChainRecord.analysis_id == record_id,
            )
        )
        .order_by(EvidenceChainRecord.timestamp.asc())
        .all()
    )

    if rows:
        chain = [
            {
                "evidence_id": r.id,
                "raw_data_id": r.raw_data_id,
                "analysis_id": r.analysis_id,
                "step_name": r.step_name,
                "hash_value": r.hash_value,
                "chain_status": r.chain_status,
                "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                "payload": r.meta_payload,
            }
            for r in rows
        ]
        return {"record_id": record_id, "chain": chain}

    return {
        "record_id": record_id,
        "chain": [
            {"step_name": "凭证上传", "timestamp": "", "hash_value": "", "chain_status": "pending"},
            {"step_name": "OCR识别", "timestamp": "", "hash_value": "", "chain_status": "pending"},
            {"step_name": "碳核算", "timestamp": "", "hash_value": "", "chain_status": "pending"},
            {"step_name": "链上存证", "timestamp": "", "hash_value": "", "chain_status": "pending"},
        ],
    }


@router.post("/evidence/verify", summary="证据链验真")
def evidence_verify(body: EvidenceVerifyBody, db: Session = Depends(get_db)):
    if body.leaf_id:
        row = db.query(EvidenceProof).filter(EvidenceProof.leaf_id == body.leaf_id).first()
        if row is None:
            return {"success": False, "message": "leaf不存在"}
        ok = verify_merkle_proof(row.leaf_hash, row.merkle_path_json or [], row.root_hash)
        return {
            "success": True,
            "leaf_id": body.leaf_id,
            "verify": "pass" if ok else "fail",
            "root_hash": row.root_hash,
        }

    if body.analysis_id:
        chain_payload = _build_chain_response(body.analysis_id, db)
        if not chain_payload:
            return {"success": False, "message": "analysis_id不存在"}
        return {
            "success": True,
            "analysis_id": body.analysis_id,
            "verify": chain_payload.get("verify", {}),
            "trust_score": chain_payload.get("trust_score", 0.0),
        }

    return {"success": False, "message": "至少提供 analysis_id 或 leaf_id"}


@router.get("/evidence/proof/{leaf_id}", summary="获取Merkle审计路径")
def evidence_proof(leaf_id: str, db: Session = Depends(get_db)):
    row = db.query(EvidenceProof).filter(EvidenceProof.leaf_id == leaf_id).first()
    if row is None:
        return {"success": False, "message": "leaf不存在"}

    return {
        "success": True,
        "leaf_id": leaf_id,
        "analysis_id": row.analysis_id,
        "leaf_hash": row.leaf_hash,
        "proof": row.merkle_path_json,
        "root_hash": row.root_hash,
        "verify": "pass" if verify_merkle_proof(row.leaf_hash, row.merkle_path_json or [], row.root_hash) else "fail",
    }


@router.post("/demo/run-once", summary="示例企业一键体验")
def demo_run_once(db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
    company = "Demo企业"
    user_id: Optional[int] = None
    if current_user is not None:
        company = current_user.company or "Demo企业"
        user_id = current_user.id

    events = [
        EventStream(enterprise_name=company, event_type="ocr_done", event_desc="OCR识别完成", event_status="done"),
        EventStream(enterprise_name=company, event_type="govern_done", event_desc="数据治理完成", event_status="done"),
        EventStream(enterprise_name=company, event_type="carbon_done", event_desc="碳核算完成", event_status="done"),
        EventStream(enterprise_name=company, event_type="risk_done", event_desc="风控评估完成", event_status="warning"),
        EventStream(enterprise_name=company, event_type="report_done", event_desc="报告预览生成", event_status="done"),
    ]
    db.add_all(events)
    db.flush()

    analysis_id = None
    if user_id is not None:
        analysis = AnalysisResult(
            user_id=user_id,
            enterprise_name=company,
            total_emission=420.5,
            carbon_intensity=0.12,
            industry_deviation=-0.06,
            risk_level="medium",
            major_source="electricity",
            advice_text="优先优化电力与运输排放，持续监控退货率。",
        )
        db.add(analysis)
        db.flush()
        analysis_id = analysis.id

        db.add(
            RiskResult(
                user_id=user_id,
                analysis_id=analysis_id,
                risk_score=62.3,
                risk_level="medium",
                risk_reason="碳强度接近阈值，运输环节波动较大",
                risk_advice="按月复盘运输与能耗指标，设置预警阈值",
            )
        )

    db.add_all([
        EvidenceChainRecord(raw_data_id="demo-raw-1", analysis_id=str(analysis_id or "demo-analysis"), step_name="凭证上传", hash_value="demohash001", chain_status="stored", meta_payload={"by": "demo"}),
        EvidenceChainRecord(raw_data_id="demo-raw-1", analysis_id=str(analysis_id or "demo-analysis"), step_name="OCR识别", hash_value="demohash002", chain_status="stored", meta_payload={"by": "demo"}),
        EvidenceChainRecord(raw_data_id="demo-raw-1", analysis_id=str(analysis_id or "demo-analysis"), step_name="碳核算", hash_value="demohash003", chain_status="stored", meta_payload={"by": "demo"}),
        EvidenceChainRecord(raw_data_id="demo-raw-1", analysis_id=str(analysis_id or "demo-analysis"), step_name="链上存证", hash_value="demohash004", chain_status="stored", meta_payload={"by": "demo"}),
    ])
    db.commit()

    return {
        "success": True,
        "enterprise_name": company,
        "analysis_id": analysis_id,
        "message": "示例企业全流程已触发，可直接用于答辩演示。",
    }
