# GFL2 Food Cooker

Small Windows-oriented click automation for the GFL2 experimental cooking flow.

This uses the same practical approach as `gfl2elo/gfl2-attachment-calibrator`: collect screen coordinates by hovering, save them to JSON, then replay clicks with `pyautogui`. Coordinates are tied to the current game window position and resolution.

It's also vibe coded slop.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Calibrate

Put the game on the first cooking screen and keep the window where it will stay.

```powershell
python food_cooker.py calibrate
```

When prompted for food boxes, hover the visible food boxes in left-to-right, top-to-bottom order. Do not include boxes that require scrolling; scrolling support can be added later.

The remaining prompts ask for the fixed buttons in the cooking flow:

- Next
- Confirm Invite
- Skip Animation
- First Skip Dialogue
- Dialogue choice/continue
- Second Skip Dialogue
- Return to cooking

Coordinates are saved to `food_cooker_coordinates.json`.

Coordinate collection and JSON persistence live in `coordinate_collection.py`, so the click runner stays separate from calibration logic.

## Run

```powershell
python food_cooker.py run
```

The script asks how many food items to consider and then asks for each item as `use/max`, for example `14/14`.

The first value is how many cooking loops to run for that item. `0/max` is allowed and skips that box without consuming it, so it stays in place and affects later shifting. The second value is used to determine whether that item is fully consumed; fully consumed items disappear, so later items shift into earlier slots.

While running:

- `F9` pauses/resumes (sometimes)
- `F10` stops after the current action (sometimes)
- Moving the mouse to a screen corner triggers PyAutoGUI's failsafe (do not touch your PC)
