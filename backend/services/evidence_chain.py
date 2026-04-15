"""证据链服务：分层哈希、链式摘要、Merkle 与可信度评分。"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple


REQUIRED_STEPS = [
    "raw_uploaded",
    "parsed",
    "governed",
    "calculated",
    "reported",
    "anchored",
]


@dataclass
class TrustScoreResult:
    trust_score: float
    components: Dict[str, float]


def canonicalize_object(obj: Dict[str, Any]) -> str:
    """统一 JSON 规范化，避免键顺序导致哈希不稳定。"""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def hash_evidence_object(obj: Dict[str, Any]) -> str:
    return _sha256(canonicalize_object(obj))


def build_chain_step(prev_hash: str, object_hash: str, timestamp: str) -> str:
    payload = f"chain-step|{prev_hash}|{object_hash}|{timestamp}"
    return _sha256(payload)


def build_merkle_root(hashes: Sequence[str]) -> str:
    if not hashes:
        return _sha256("empty-merkle")

    level = [h for h in hashes]
    while len(level) > 1:
        next_level: List[str] = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else left
            next_level.append(_sha256(f"merkle|{left}|{right}"))
        level = next_level
    return level[0]


def build_merkle_proofs(hashes: Sequence[str]) -> Dict[int, List[Dict[str, str]]]:
    """返回 index -> merkle path（left/right sibling）。"""
    if not hashes:
        return {}

    levels: List[List[str]] = [list(hashes)]
    while len(levels[-1]) > 1:
        cur = levels[-1]
        nxt: List[str] = []
        for i in range(0, len(cur), 2):
            left = cur[i]
            right = cur[i + 1] if i + 1 < len(cur) else left
            nxt.append(_sha256(f"merkle|{left}|{right}"))
        levels.append(nxt)

    proofs: Dict[int, List[Dict[str, str]]] = {i: [] for i in range(len(hashes))}
    for leaf_idx in range(len(hashes)):
        idx = leaf_idx
        for depth in range(len(levels) - 1):
            cur_level = levels[depth]
            sibling_idx = idx ^ 1
            sibling_hash = cur_level[sibling_idx] if sibling_idx < len(cur_level) else cur_level[idx]
            position = "right" if sibling_idx > idx else "left"
            proofs[leaf_idx].append({"position": position, "hash": sibling_hash})
            idx //= 2
    return proofs


def verify_hash_chain(steps: Sequence[Dict[str, Any]]) -> bool:
    if not steps:
        return False

    previous_current = None
    for idx, step in enumerate(steps):
        ts = step.get("timestamp")
        if isinstance(ts, datetime):
            ts_str = ts.isoformat()
        else:
            ts_str = str(ts)

        prev_hash = str(step.get("prev_hash", ""))
        if idx == 0:
            if not prev_hash:
                return False
        else:
            if previous_current is None or prev_hash != previous_current:
                return False

        expected = build_chain_step(prev_hash, str(step.get("object_hash", "")), ts_str)
        if expected != str(step.get("current_hash", "")):
            return False
        previous_current = str(step.get("current_hash", ""))
    return True


def verify_merkle_proof(leaf: str, proof: Sequence[Dict[str, str]], root: str) -> bool:
    current = leaf
    for item in proof:
        sibling = item.get("hash", "")
        position = item.get("position", "right")
        if position == "left":
            current = _sha256(f"merkle|{sibling}|{current}")
        else:
            current = _sha256(f"merkle|{current}|{sibling}")
    return current == root


def _to_epoch(value: Any) -> float:
    if isinstance(value, datetime):
        return value.timestamp()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return 0.0
    return 0.0


def compute_trust_score(
    steps: Sequence[Dict[str, Any]],
    merkle_ok: bool,
    anchor_time: Optional[Any],
    issuer_or_tx: str,
    w_complete: float = 0.30,
    w_hash: float = 0.35,
    w_time: float = 0.20,
    w_sig: float = 0.15,
) -> TrustScoreResult:
    present = {str(s.get("step_name", "")) for s in steps}
    complete_ratio = sum(1 for r in REQUIRED_STEPS if r in present) / len(REQUIRED_STEPS)

    hash_ok = 1.0 if (verify_hash_chain(steps) and merkle_ok) else 0.0

    ordered = sorted(steps, key=lambda x: _to_epoch(x.get("timestamp")))
    monotonic = 1.0
    for i in range(1, len(ordered)):
        if _to_epoch(ordered[i].get("timestamp")) < _to_epoch(ordered[i - 1].get("timestamp")):
            monotonic = 0.0
            break

    if anchor_time is not None and ordered:
        anchor_ok = 1.0 if _to_epoch(anchor_time) >= _to_epoch(ordered[-1].get("timestamp")) else 0.0
    else:
        anchor_ok = 0.0
    time_score = 0.5 * monotonic + 0.5 * anchor_ok

    sig_score = 1.0 if issuer_or_tx else 0.0

    score = (
        w_complete * complete_ratio
        + w_hash * hash_ok
        + w_time * time_score
        + w_sig * sig_score
    )

    components = {
        "I_complete": round(complete_ratio, 4),
        "I_hash": round(hash_ok, 4),
        "I_time": round(time_score, 4),
        "I_sig": round(sig_score, 4),
    }
    return TrustScoreResult(trust_score=round(score, 4), components=components)


def make_anchor_tx_id(analysis_id: str, merkle_root: str, now_iso: str) -> str:
    return _sha256(f"anchor|{analysis_id}|{merkle_root}|{now_iso}")
