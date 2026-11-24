from .fixtures import FIXTURES
from .pager import PageBudgetExceeded, ShadowPager
from .recipe import recipe_set


CONFIG = {
    "title": "岑砾道料·道砟配方影子页签发",
    "team": "岑砾道料 8 人试配与线下签发小组",
    "description": "用影子分页提交配方，对照断电前后有效根和可复用页，再安排生产签发。",
    "direction": "影子分页与写时复制发布",
    "mechanism": "不可变配方页、原子根指针切换、引用保护及孤儿页回收。",
    "modules": ["道料交班", "配方签发单", "发布重演", "可见配方根"],
    "unit": "配方签发单",
    "max_parameter": 128,
    "parameter_label": "可用物理页数（1–128）",
    "default_parameter": 5,
    "facts": ["已发布根次", "回收页次", "预算拒绝"],
    "palette": 9,
    "fixture": "BR-K7-1124 / K7 段",
}

PHASES = {"volatile": "刷盘前", "flushed": "刷盘后换根前", "published": "换根成功"}


def normalize(payload):
    if not isinstance(payload, dict):
        raise ValueError("输入需为对象")
    initial = recipe_set(payload.get("initial"), "initial")
    keep = payload.get("keep_baseline")
    if type(keep) is not bool:
        raise ValueError("keep_baseline 须为布尔值")
    events = payload.get("events")
    if not isinstance(events, list) or not 1 <= len(events) <= 64:
        raise ValueError("events 须有 1 至 64 个操作")
    normalized = []
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("events 各项必须是对象")
        if event.get("op") == "release_baseline":
            normalized.append(("release_baseline", []))
            continue
        phase = event.get("phase")
        if event.get("op") != "revise" or not isinstance(phase, str) or phase not in PHASES:
            raise ValueError("revise 需提供 volatile、flushed 或 published 阶段")
        normalized.append((phase, recipe_set(event.get("changes"), "changes")))
    return initial, keep, normalized


def validate(payload):
    normalize(payload)


def page_list(page_ids):
    return "、".join(str(page_id) for page_id in page_ids) or "—"


def run(payload, parameter, db):
    initial, keep, events = normalize(payload)
    if parameter < len(initial):
        raise ValueError("物理页预算放不下初始配方根")
    pager = ShadowPager(initial, parameter, keep)
    denied = recovered = reused = 0
    rows = []
    for index, (phase, changes) in enumerate(events, 1):
        assigned = recycled = released = []
        if phase == "release_baseline":
            released = pager.release()
            label = "释放基准快照"
        else:
            try:
                assigned, recycled, released, label = pager.replace(changes, phase)
            except PageBudgetExceeded as exc:
                denied += 1
                label = str(exc)
        recovered += len(released)
        reused += len(recycled)
        rows.append({
            "记录": f"步骤 {index}", "阶段": PHASES.get(phase, "解封基准"),
            "当前根": pager.root.number, "影子页": page_list(assigned),
            "回收页": page_list(released), "复用页": page_list(recycled),
            "结论": label,
        })
    for code, page_id in sorted(pager.root.pointers.items()):
        recipe = pager.pages[page_id]
        rows.append({
            "记录": code, "阶段": "生效配方", "当前根": pager.root.number,
            "影子页": str(page_id), "回收页": "—", "复用页": "—",
            "结论": f"细料 {recipe.fine} 基点 / 粗料 {recipe.coarse} 基点",
        })
    return {
        "summary": f"生效根 R{pager.root.number}，回收 {recovered} 页次，预算拒绝 {denied} 次。",
        "metrics": {"已发布根次": pager.root.number, "回收页次": recovered,
                    "预算拒绝": denied, "复用页次": reused, "占用物理页": len(pager.pages)},
        "rows": rows,
    }
