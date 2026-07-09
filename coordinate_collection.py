import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pyautogui


COORDINATES_FILE = Path("food_cooker_coordinates.json")

POINT_SEQUENCE = [
    ("next_button", "the yellow Next button from the dish selection screen"),
    ("confirm_invite_button", "the yellow Confirm Invite button on the doll invite screen"),
    ("skip_animation_button", "the Skip Animation control in the upper-right cooking animation screen"),
    ("skip_first_dialogue_button", "the first Skip control in the upper-right dialogue screen"),
    ("dialogue_choice", "the dialogue choice/continue point you want clicked"),
    ("skip_second_dialogue_button", "the second Skip control after choosing the dialogue response"),
    ("return_to_cooking_button", "the yellow Return to cooking button on the result screen"),
]

FIRST_FOOD_SLOT_HOVER_SECONDS = 5
LATER_FOOD_SLOT_HOVER_SECONDS = 3
SELECT_FOOD_BEFORE_NEXT_SECONDS = 3
STAGED_BUTTON_HOVER_SECONDS = 8


@dataclass
class Point:
    x: int
    y: int


def ask_positive_int(prompt: str) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
        except ValueError:
            print("Please enter a whole number.")
            continue

        if value <= 0:
            print("Please enter a number greater than 0.")
            continue

        return value


def wait_for_hover(label: str, description: str, seconds: int = 5) -> Point:
    print()
    print(f"Get ready to hover {description}.")
    for remaining in range(seconds, 0, -1):
        print(f"Capturing in {remaining}...")
        time.sleep(1)

    x, y = pyautogui.position()
    print(f"Saved {label}: ({x}, {y})")
    return Point(x=x, y=y)


def wait_for_manual_action(description: str, seconds: int) -> None:
    print()
    print(description)
    for remaining in range(seconds, 0, -1):
        print(f"Continuing in {remaining}...")
        time.sleep(1)


def save_coordinates(food_slots: list[Point], points: dict[str, Point]) -> None:
    data = {
        "food_slots": [{"x": point.x, "y": point.y} for point in food_slots],
        "points": {name: {"x": point.x, "y": point.y} for name, point in points.items()},
    }

    COORDINATES_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print()
    print(f"Coordinates saved to {COORDINATES_FILE}")


def load_coordinates() -> tuple[list[Point], dict[str, Point]]:
    if not COORDINATES_FILE.exists():
        print(f"Missing {COORDINATES_FILE}. Run calibration first:")
        print("  python food_cooker.py calibrate")
        sys.exit(1)

    try:
        data = json.loads(COORDINATES_FILE.read_text(encoding="utf-8"))
        food_slots = [Point(x=int(slot["x"]), y=int(slot["y"])) for slot in data["food_slots"]]
        points = {
            name: Point(x=int(value["x"]), y=int(value["y"]))
            for name, value in data["points"].items()
        }
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"{COORDINATES_FILE} is invalid: {exc}")
        print("Run calibration again:")
        print("  python food_cooker.py calibrate")
        sys.exit(1)

    missing = [name for name, _ in POINT_SEQUENCE if name not in points]
    if missing:
        print(f"{COORDINATES_FILE} is missing points: {', '.join(missing)}")
        print("Run calibration again:")
        print("  python food_cooker.py calibrate")
        sys.exit(1)

    if not food_slots:
        print(f"{COORDINATES_FILE} does not contain any food slot coordinates.")
        print("Run calibration again:")
        print("  python food_cooker.py calibrate")
        sys.exit(1)

    return food_slots, points


def calibrate_coordinates() -> None:
    print("Food cooker coordinate calibration")
    print()
    print("Keep the game window in its final position before starting.")
    print("Coordinates are screen-position based, so moving or resizing the window after calibration will break them.")
    print()
    print("For food boxes, hover only the visible boxes you want the script to know about.")
    print("Do not include boxes that require scrolling; scrolling support can be added later.")

    food_slot_count = ask_positive_int("How many visible food box positions should be calibrated? ")
    food_slots = []

    for slot_number in range(1, food_slot_count + 1):
        hover_seconds = FIRST_FOOD_SLOT_HOVER_SECONDS if slot_number == 1 else LATER_FOOD_SLOT_HOVER_SECONDS
        food_slots.append(
            wait_for_hover(
                f"food_slot_{slot_number}",
                f"food box position {slot_number} in left-to-right, top-to-bottom order",
                seconds=hover_seconds,
            )
        )

    wait_for_manual_action(
        "Select any food item in-game now so the Next button is available.",
        SELECT_FOOD_BEFORE_NEXT_SECONDS,
    )

    points = {}
    for index, (name, description) in enumerate(POINT_SEQUENCE):
        points[name] = wait_for_hover(name, description, seconds=STAGED_BUTTON_HOVER_SECONDS)

        if index < len(POINT_SEQUENCE) - 1:
            print("Click the button/area you are hovering over now to advance to the next stage.")

    save_coordinates(food_slots, points)
