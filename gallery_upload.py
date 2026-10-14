"""把画图结果上传到图库网站（纯 httpx 实现，不依赖 nekro_agent，便于单独测试）。"""

from __future__ import annotations

import base64
import random
import time
from typing import Optional, Tuple

import httpx

GALLERY_NAME_PREFIX = "nekro_"
MAX_UPLOAD_BYTES = 32 * 1024 * 1024
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def build_name(prefix: str = GALLERY_NAME_PREFIX) -> str:
    return "%s%s_%03d" % (prefix, time.strftime("%Y%m%d_%H%M%S"), random.randint(100, 999))


async def upload_to_gallery(
    image_bytes: bytes,
    meta: dict,
    url: str,
    key: str,
    name: Optional[str] = None,
    timeout: float = 300.0,
) -> Tuple[bool, str]:
    """上传图片 + 生成参数到图库，返回 (是否成功, 文件名或错误信息)。"""
    if not image_bytes:
        return False, "图片为空"
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        return False, "图片超过图库大小上限"
    if not image_bytes.startswith(PNG_MAGIC):
        return False, "只支持 PNG 图片"
    name = name or build_name()
    payload = {
        "name": name,
        "image_b64": base64.b64encode(image_bytes).decode("ascii"),
        "meta": dict(meta or {}),
    }
    try:
        async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
            response = await client.post(url, json=payload, headers={"X-Upload-Key": key})
    except Exception as exc:
        return False, f"请求失败: {exc}"
    if response.status_code != 200:
        return False, f"HTTP {response.status_code}: {response.text[:120]}"
    try:
        result = response.json()
    except Exception:
        return False, "响应不是 JSON"
    if not isinstance(result, dict) or not result.get("ok"):
        detail = result.get("error") if isinstance(result, dict) else None
        return False, str(detail or "图库返回失败")
    return True, str(result.get("name") or name)


# Denia durable gallery outbox. The original HTTP uploader above is retained.
_denia_outbox_instance = None

def _denia_box(root=None):
    global _denia_outbox_instance
    if _denia_outbox_instance is None:
        from pathlib import Path
        import json
        from .denia_outbox import Outbox, read_config
        from .denia_classification import classify
        data = Path(root) if root else Path(__file__).resolve().parents[3] / 'plugin_data/Denia.denia_novelai'
        def tags(meta):
            try:
                catalog = json.loads((data / 'presets.json').read_text())
            except (OSError, ValueError):
                catalog = {}
            return classify(meta, catalog)['tags']
        _denia_outbox_instance = Outbox(data / 'gallery_outbox', upload_to_gallery, lambda: read_config(data), tags)
    return _denia_outbox_instance

async def denia_start_outbox(root=None):
    _denia_box(root).start()

async def denia_stop_outbox():
    if _denia_outbox_instance is not None:
        await _denia_outbox_instance.stop()

async def denia_enqueue_to_gallery(image_bytes, meta, url, key, name=None):
    if not url or not key:
        return False, 'Gallery upload is not configured'
    try:
        box = _denia_box()
        result = box.enqueue(image_bytes, meta, name or build_name())
        box.start()
        return True, result
    except Exception as exc:
        return False, type(exc).__name__
