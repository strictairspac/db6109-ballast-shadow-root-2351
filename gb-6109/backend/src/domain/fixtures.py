BASE = [
    {"recipe": "BR-051", "fine_bp": 2500, "coarse_bp": 7500},
    {"recipe": "BR-052", "fine_bp": 3000, "coarse_bp": 7000},
    {"recipe": "BR-053", "fine_bp": 2800, "coarse_bp": 7200},
]
REVISION = [
    {"recipe": "BR-051", "fine_bp": 2700, "coarse_bp": 7300},
    {"recipe": "BR-052", "fine_bp": 3200, "coarse_bp": 6800},
]

FIXTURES = [
    {
        "code": "BR-K7-1124",
        "title": "K7 段配方签发重试",
        "description": "先在影子页刷盘后断电，再重试发布；比对封存根、孤儿页和释放后的页号复用。",
        "payload": {
            "initial": BASE, "keep_baseline": True,
            "events": [
                {"op": "revise", "phase": "flushed", "changes": REVISION},
                {"op": "revise", "phase": "published", "changes": REVISION},
                {"op": "revise", "phase": "published",
                 "changes": [{"recipe": "BR-053", "fine_bp": 3100, "coarse_bp": 6900}]},
                {"op": "release_baseline"},
                {"op": "revise", "phase": "published",
                 "changes": [{"recipe": "BR-053", "fine_bp": 3100, "coarse_bp": 6900}]},
            ],
        },
    },
    {
        "code": "BR-K9-1124",
        "title": "K9 段刷盘前断电",
        "description": "暂存配方未落盘时不产生孤儿页；后续正式签发与同值重试可对比。",
        "payload": {
            "initial": BASE, "keep_baseline": False,
            "events": [
                {"op": "revise", "phase": "volatile", "changes": REVISION[:1]},
                {"op": "revise", "phase": "published", "changes": REVISION[:1]},
                {"op": "revise", "phase": "published", "changes": REVISION[:1]},
            ],
        },
    },
]
