"""The subject under test: Algebra I — linear relationships & slope.

Each skill carries practice items and *transfer* items (novel framings of the
same concept). Items declare which misconception they trap, so the simulator can
tell "right answer" from "right answer for the wrong reason" and detect when a
misconception survives instruction.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Item:
    prompt: str
    answer: str
    traps: str = ""          # misconception key this item lures (e.g. "M1")
    transfer: bool = False   # True = novel framing, used only in transfer test


@dataclass
class Skill:
    key: str
    name: str
    misconceptions: list[str]
    items: list[Item] = field(default_factory=list)


# Misconception catalogue (cited in docs/research-notes.md)
MISCONCEPTIONS = {
    "M1": 'slope is "the number in front of x", even when not in y=mx+b form',
    "M2": "reversal error — '6 students per professor' written as 6S=P (Clement 1981)",
    "M3": "constant rate confused with the starting value (intercept)",
    "M4": '"=" read as "compute the answer" rather than balance',
    "M5": '"bigger number = steeper", ignoring sign',
}

SKILLS: list[Skill] = [
    Skill("slope_eq", "Slope from equation", ["M1", "M5"], [
        Item("What is the slope of y = 3x + 2?", "3", "M1"),
        Item("What is the slope of 2x + 3y = 12?", "-2/3", "M1"),
        Item("Line: 4x - y = 7. Slope?", "4", "M1"),
        Item("Which is steeper: y = -5x or y = 2x?", "y=-5x", "M5", transfer=True),
        Item("A line drops 3 units for every 1 right. Slope?", "-3", "M5", transfer=True),
    ]),
    Skill("slope_int", "Slope vs intercept", ["M3"], [
        Item("In y = 7x + 1, what is the y-intercept?", "1", "M3"),
        Item("In y = 7x + 1, what is the slope?", "7", "M3"),
        Item("A plant is 5cm tall and grows 2cm/week. Intercept?", "5", "M3", transfer=True),
        Item("Same plant: what is the slope?", "2", "M3", transfer=True),
    ]),
    Skill("rate_ctx", "Rate in context", ["M3", "M5"], [
        Item("Taxi: $3 base + $2/mile. Cost of 5 miles?", "13", "M3"),
        Item("Which costs more per mile: $2/mi or $1.50/mi?", "$2/mi", "M5"),
        Item("Phone plan: $20 + $0.10/min. Rate?", "0.10", "M3", transfer=True),
        Item("Savings: $50 now, +$15/week. Weekly rate?", "15", "M3", transfer=True),
    ]),
    Skill("solve_ms", "Multi-step solving", ["M4"], [
        Item("Solve 2x + 5 = 13", "4", "M4"),
        Item("Solve 3(x - 2) = 9", "5", "M4"),
        Item("Solve 5x - 4 = 2x + 11", "5", "M4", transfer=True),
        Item("Solve (x/2) + 3 = 7", "8", "M4", transfer=True),
    ]),
    Skill("translate", "Word problem to equation", ["M2"], [
        Item("There are 6 times as many students as professors. Equation? (S, P)",
             "S=6P", "M2"),
        Item("A number plus 4 equals 10. Equation?", "x+4=10", "M2"),
        Item("Twice a number, less 3, is 11. Equation?", "2x-3=11", "M2", transfer=True),
        Item("For every 3 dogs there are 2 cats. Relate D and C.", "2D=3C", "M2", transfer=True),
    ]),
]

SKILL_BY_KEY = {s.key: s for s in SKILLS}


def practice_items(skill: Skill) -> list[Item]:
    return [i for i in skill.items if not i.transfer]


def transfer_items(skill: Skill) -> list[Item]:
    return [i for i in skill.items if i.transfer]
