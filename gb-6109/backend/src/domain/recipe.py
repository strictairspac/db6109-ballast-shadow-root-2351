import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Recipe:
    code: str
    fine: int
    coarse: int

    @classmethod
    def from_row(cls, row):
        if not isinstance(row, dict):
            raise ValueError("配方行必须是对象")
        code, fine, coarse = row.get("recipe"), row.get("fine_bp"), row.get("coarse_bp")
        if not isinstance(code, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,24}", code):
            raise ValueError("配方号仅允许 1 至 24 位字母、数字、下划线或连字符")
        if type(fine) is not int or type(coarse) is not int or not 0 <= fine <= 10000 or fine + coarse != 10000:
            raise ValueError("细、粗料均需为非负整数基点，总和为 10000")
        return cls(code, fine, coarse)


def recipe_set(rows, name):
    if not isinstance(rows, list) or not 1 <= len(rows) <= 32:
        raise ValueError(f"{name} 须为 1 至 32 条配方")
    recipes = [Recipe.from_row(row) for row in rows]
    if len({recipe.code for recipe in recipes}) != len(recipes):
        raise ValueError(f"{name} 含重复配方号")
    return recipes
