import random
import re
import sys
import threading
import time
from dataclasses import dataclass

import keyboard
import pyautogui

from coordinate_collection import Point, calibrate_coordinates, load_coordinates


# Delay settings. Tune these values if your game loads faster or slower.
DELAY_AFTER_FOOD_SLOT_SECONDS = 0.8
DELAY_AFTER_NEXT_SECONDS = 0.8
DELAY_AFTER_CONFIRM_INVITE_SECONDS = 2.0
DELAY_AFTER_SKIP_ANIMATION_SECONDS = 2.0
DELAY_AFTER_FIRST_DIALOGUE_SKIP_SECONDS = 2.0
DELAY_AFTER_DIALOGUE_CHOICE_SECONDS = 2.5
DELAY_AFTER_SECOND_DIALOGUE_SKIP_SECONDS = 3.5
DELAY_AFTER_RETURN_TO_COOKING_SECONDS = 3

# Startup countdown before automation begins.
COUNTDOWN_SECONDS = 5

FOOD_USAGE_REMINDER = (
    "Reminder: consider saving 21x Sweet Potato, 7x Cucumber, 7x Red Meat, "
    "7x Fish, 3x White Meat, 3x Greenhouse Vegetables (-7 on Sweet Potato + "
    "Cucumber/Red Meat/Fish and +7x White Meat +7x Tomato if using the electro "
    "team) and DO NOT USE Bellpeppers. Close applications that can show popup "
    "messages and block the bot, such as Discord."
)

pause_event = threading.Event()
exit_event = threading.Event()


@dataclass
class FoodItem:
    index: int
    use_count: int
    max_count: int
    slot_index: int

    @property
    def fully_consumed(self) -> bool:
        return self.use_count == self.max_count


def install_hotkeys() -> None:
    keyboard.add_hotkey("F9", toggle_pause)
    keyboard.add_hotkey("F10", request_exit)


def toggle_pause() -> None:
    if pause_event.is_set():
        pause_event.clear()
        print("Resumed.")
    else:
        pause_event.set()
        print("Paused. Press F9 to resume.")


def request_exit() -> None:
    exit_event.set()
    print("Exit requested. Stopping after the current action.")


def check_pause_exit() -> None:
    if exit_event.is_set():
        print("Exiting.")
        sys.exit(0)

    while pause_event.is_set():
        time.sleep(0.2)
        if exit_event.is_set():
            print("Exiting.")
            sys.exit(0)


def ask_positive_int(prompt: str, *, max_value: int | None = None) -> int:
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

        if max_value is not None and value > max_value:
            print(f"Please enter {max_value} or less.")
            continue

        return value


def ask_use_max(item_number: int) -> tuple[int, int]:
    prompt = f"How many of item {item_number} would you like to process? Format use/max, e.g. 14/14: "
    pattern = re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s*$")

    while True:
        raw = input(prompt)
        match = pattern.match(raw)
        if not match:
            print("Please use the exact format use/max, for example 14/14.")
            continue

        use_count = int(match.group(1))
        max_count = int(match.group(2))

        if max_count <= 0:
            print("The max value must be greater than 0.")
            continue

        if use_count < 0:
            print("The use value cannot be negative.")
            continue

        if use_count > max_count:
            print("The use value cannot be greater than the max value.")
            continue

        return use_count, max_count


def jitter(point: Point, x_radius: int = 8, y_radius: int = 4) -> Point:
    return Point(
        x=point.x + random.randint(-x_radius, x_radius),
        y=point.y + random.randint(-y_radius, y_radius),
    )


def click_point(label: str, point: Point, delay_after: float) -> None:
    check_pause_exit()
    target = jitter(point)
    print(f"Clicking {label} at ({target.x}, {target.y})")
    pyautogui.moveTo(target.x, target.y, duration=random.uniform(0.06, 0.14))
    pyautogui.click()
    time.sleep(delay_after)


def build_food_plan(food_slots: list[Point]) -> list[FoodItem]:
    item_count = ask_positive_int(
        "How many food items should be processed? ",
        max_value=len(food_slots),
    )

    print()
    print(FOOD_USAGE_REMINDER)
    print()

    items: list[FoodItem] = []
    consumed_before = 0

    for item_index in range(1, item_count + 1):
        use_count, max_count = ask_use_max(item_index)
        slot_index = item_index - consumed_before

        if slot_index < 1 or slot_index > len(food_slots):
            print()
            print("The shifting logic placed an item outside the calibrated visible slots.")
            print("Re-run calibration with more visible food box positions, or process fewer items.")
            sys.exit(1)

        item = FoodItem(
            index=item_index,
            use_count=use_count,
            max_count=max_count,
            slot_index=slot_index,
        )
        items.append(item)

        if item.fully_consumed:
            consumed_before += 1

    return items


def print_plan(items: list[FoodItem]) -> None:
    print()
    print("Planned processing:")
    total_cycles = 0
    for item in items:
        total_cycles += item.use_count
        if item.use_count == 0:
            shift_note = "skipped, remains in slot"
        elif item.fully_consumed:
            shift_note = "fully consumed, later items shift"
        else:
            shift_note = "partially consumed, remains in slot"

        print(
            f"  Item {item.index}: {item.use_count}/{item.max_count}, "
            f"click calibrated food slot {item.slot_index} ({shift_note})"
        )
    print(f"Total cooking loops: {total_cycles}")


def run() -> None:
    food_slots, points = load_coordinates()
    items = build_food_plan(food_slots)
    print_plan(items)

    print()
    print("Controls while running: F9 pauses/resumes, F10 stops after the current action.")
    print("Focus the game now.")
    for remaining in range(COUNTDOWN_SECONDS, 0, -1):
        print(f"Starting in {remaining}...")
        time.sleep(1)

    completed = 0
    total = sum(item.use_count for item in items)

    for item in items:
        food_point = food_slots[item.slot_index - 1]

        for item_cycle in range(1, item.use_count + 1):
            completed += 1
            print()
            print(f"Loop {completed}/{total}: item {item.index}, use {item_cycle}/{item.use_count}")

            click_point("food slot", food_point, DELAY_AFTER_FOOD_SLOT_SECONDS)
            click_point("Next", points["next_button"], DELAY_AFTER_NEXT_SECONDS)
            click_point("Confirm Invite", points["confirm_invite_button"], DELAY_AFTER_CONFIRM_INVITE_SECONDS)
            click_point("Skip Animation", points["skip_animation_button"], DELAY_AFTER_SKIP_ANIMATION_SECONDS)
            click_point(
                "first Skip Dialogue",
                points["skip_first_dialogue_button"],
                DELAY_AFTER_FIRST_DIALOGUE_SKIP_SECONDS,
            )
            click_point("dialogue choice", points["dialogue_choice"], DELAY_AFTER_DIALOGUE_CHOICE_SECONDS)
            click_point(
                "second Skip Dialogue",
                points["skip_second_dialogue_button"],
                DELAY_AFTER_SECOND_DIALOGUE_SKIP_SECONDS,
            )
            click_point(
                "Return to cooking",
                points["return_to_cooking_button"],
                DELAY_AFTER_RETURN_TO_COOKING_SECONDS,
            )

            check_pause_exit()

    print()
    print(f"Finished {completed} cooking loops.")


def print_usage() -> None:
    print("Usage:")
    print("  python food_cooker.py calibrate")
    print("  python food_cooker.py run")


def main() -> None:
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.03
    install_hotkeys()

    command = sys.argv[1].strip().lower() if len(sys.argv) > 1 else ""

    if command == "calibrate":
        calibrate_coordinates()
    elif command == "run":
        run()
    else:
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
