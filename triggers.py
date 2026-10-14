"""Literal message-start triggers; regex supplied by users is never executed."""
from .generation import Rejected


def validate_triggers(draw, redraw):
    for value in (draw, redraw):
        if not value or not value.strip('/') or len(value) > 40 or any(c.isspace() for c in value):
            raise Rejected('画图和重画触发词不能为空、不能含空白，最长 40 字。')
    if draw == redraw:
        raise Rejected('画图和重画触发词不能相同。')
    reserved = {'额度','来点','看参数','反推','添加人物','删除人物','人物列表','添加风格','删除风格','风格列表','拉黑','解除拉黑','黑名单'}
    if draw.lstrip('/') in reserved or redraw.lstrip('/') in reserved:
        raise Rejected('触发词不能与插件其他指令重名。')


def match_trigger(text, draw, redraw):
    validate_triggers(draw, redraw)
    text = str(text or '').strip()
    for kind, prefix in sorted((('draw',draw),('redraw',redraw)), key=lambda x:len(x[1]), reverse=True):
        if not prefix.startswith('/') and text.startswith(prefix):
            return kind, text[len(prefix):].lstrip(' +＋:：,，')
    return None
