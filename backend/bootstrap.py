"""后端启动自检脚本。

用途：
1) 校验主应用可成功导入。
2) 校验关键路由是否注册。
3) 将常见Pydantic告警视为失败，提前阻断回归。
"""

from __future__ import annotations

import sys
import warnings
from typing import Iterable, List, Tuple


BLOCKED_WARNING_KEYWORDS = [
	"protected namespace",
	"class-based `config` is deprecated",
]


def _contains_blocked_warning(messages: Iterable[str]) -> List[str]:
	matched: List[str] = []
	for msg in messages:
		lowered = msg.lower()
		if any(k in lowered for k in BLOCKED_WARNING_KEYWORDS):
			matched.append(msg)
	return matched


def _check_routes() -> Tuple[bool, List[str]]:
	from main import app

	paths = {r.path for r in app.routes}
	required = {
		"/api/carbon/calculate",
		"/api/carbon/result/{analysis_id}",
		"/api/carbon/flow/{analysis_id}",
		"/api/carbon/explain/{analysis_id}",
		"/api/ocr/chain-overview",
		"/api/evidence/store",
		"/api/evidence/verify",
		"/api/evidence/proof/{leaf_id}",
	}

	missing = sorted([p for p in required if p not in paths])
	return len(missing) == 0, missing


def main() -> int:
	print("[BOOTSTRAP] 开始后端自检...")

	with warnings.catch_warnings(record=True) as caught:
		warnings.simplefilter("always")
		try:
			from main import app  # noqa: F401
		except Exception as exc:  # pragma: no cover
			print(f"[BOOTSTRAP] FAIL: 主应用导入失败 -> {exc}")
			return 1

		warn_texts = [str(w.message) for w in caught]
		blocked = _contains_blocked_warning(warn_texts)
		if blocked:
			print("[BOOTSTRAP] FAIL: 检测到阻断告警:")
			for idx, msg in enumerate(blocked, start=1):
				print(f"  {idx}. {msg}")
			return 2

	ok, missing = _check_routes()
	if not ok:
		print("[BOOTSTRAP] FAIL: 关键路由缺失:")
		for p in missing:
			print(f"  - {p}")
		return 3

	print("[BOOTSTRAP] PASS: 导入、告警、关键路由检查全部通过")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
