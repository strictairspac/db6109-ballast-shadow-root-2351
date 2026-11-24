from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class Revision:
    number: int
    pointers: Mapping[str, int]


class PageBudgetExceeded(ValueError):
    pass


class ShadowPager:
    """Keep active pages immutable until the new root is durably published."""

    def __init__(self, recipes, budget, pinned):
        self.budget = budget
        pointers = {recipe.code: page_id for page_id, recipe in enumerate(recipes, 1)}
        self.pages = {pointers[recipe.code]: recipe for recipe in recipes}
        self.root = Revision(0, MappingProxyType(pointers))
        self.backup = self.root if pinned else None
        self.used = set(self.pages)

    @property
    def protected(self):
        referenced = set(self.root.pointers.values())
        if self.backup:
            referenced.update(self.backup.pointers.values())
        return referenced

    def reclaim(self):
        returned = sorted(self.pages.keys() - self.protected)
        for page_id in returned:
            del self.pages[page_id]
        return returned

    def release(self):
        self.backup = None
        return self.reclaim()

    def replace(self, recipes, phase):
        current = self.root.pointers
        changed = [
            recipe for recipe in recipes
            if recipe.code not in current or self.pages[current[recipe.code]] != recipe
        ]
        if not changed:
            return [], [], [], "配方内容未变"
        free = [page_id for page_id in range(1, self.budget + 1) if page_id not in self.pages]
        if len(free) < len(changed):
            raise PageBudgetExceeded(f"需 {len(changed)} 页，只有 {len(free)} 个未引用页")
        pending = dict(zip(free, changed))
        proposed = current | {recipe.code: page_id for page_id, recipe in pending.items()}
        if phase == "volatile":
            return list(pending), [], [], "已断电，未刷盘的影子页丢弃"
        recycled = sorted(pending.keys() & self.used)
        self.pages.update(pending)
        self.used.update(pending)
        if phase == "flushed":
            return list(pending), recycled, self.reclaim(), "已断电，旧根有效，回收孤儿页"
        self.root = Revision(self.root.number + 1, MappingProxyType(proposed))
        return list(pending), recycled, self.reclaim(), "原子发布新根"
