"""Head-tilt diagnostic for Reachy Mini (Mock Mode).

Streams a sequence of distinct head orientations using the MockReachy interface
to bypass hardware/SDK dependencies.
"""

import sys
import time
from pathlib import Path
import numpy as np
from rich.console import Console

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Config

# --- MOCK CLASS & UTILS ---
class MockReachy:
    def set_target(self, head=None, antennas=None, body_yaw=None):
        pass # Mock κίνηση

def create_head_pose(yaw=0.0, pitch=0.0, roll=0.0, degrees=True):
    # Επιστρέφουμε ένα dictionary αντί για το αντικείμενο του SDK
    return {'yaw': yaw, 'pitch': pitch, 'roll': roll}

console = Console()
_NEUTRAL_ANT = np.array([0.0, 0.0], dtype=np.float64)

def stream_pose(reachy, label, *, yaw=0.0, pitch=0.0, roll=0.0, secs=2.5, hz=100):
    """Hold a head pose by streaming the target at hz."""
    console.print(f"  -> {label}  (yaw={yaw:+.0f}  pitch={pitch:+.0f}  roll={roll:+.0f})")
    pose = create_head_pose(yaw=yaw, pitch=pitch, roll=roll, degrees=True)
    period = 1.0 / hz
    t0 = time.monotonic()
    while time.monotonic() - t0 < secs:
        try:
            reachy.set_target(head=pose, antennas=_NEUTRAL_ANT, body_yaw=0.0)
        except Exception as e:
            console.print(f"    [red]set_target failed: {e}[/red]")
            return
        time.sleep(period)

def main():
    config = Config.load()
    # Χρήση του Mock interface
    reachy = MockReachy()
    console.print("[cyan]Running diagnostic in MOCK mode (No hardware required).[/cyan]")

    sequence = [
        ("CENTER (neutral)",           dict(secs=1.5)),
        ("YAW LEFT  (yaw = +25)",        dict(yaw=+25)),
        ("CENTER",                     dict(secs=1.0)),
        ("YAW RIGHT (yaw = -25)",        dict(yaw=-25)),
        ("CENTER",                     dict(secs=1.0)),
        ("PITCH UP   (pitch = +18)",    dict(pitch=+18)),
        ("CENTER",                     dict(secs=1.0)),
        ("PITCH DOWN (pitch = -18)",    dict(pitch=-18)),
        ("CENTER",                     dict(secs=1.0)),
        ("ROLL  (roll = +20)",          dict(roll=+20)),
        ("CENTER",                     dict(secs=1.0)),
        ("DIAGONAL (yaw +20, pitch +12)", dict(yaw=+20, pitch=+12)),
        ("CENTER (return)",             dict(secs=1.5)),
    ]

    console.print("\n[bold cyan]Head tilt diagnostic[/bold cyan] — mocking motor output.\n")
    try:
        for label, kwargs in sequence:
            stream_pose(reachy, label, **kwargs)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
    finally:
        stream_pose(reachy, "settle neutral", secs=1.0)
        console.print("\n[green]Done.[/green]")

if __name__ == "__main__":
    main()
