"""Basic Reachy Mini Lite movement test on Jetson (Mock Mode).

Simulates movement sequences for diagnostic purposes since the
hardware SDK is not available in the current environment.
"""

import time
import numpy as np

# --- MOCK CLASS ΓΙΑ ΠΑΡΑΚΑΜΨΗ ΤΟΥ SDK ---
class MockReachy:
    def wake_up(self): pass
    def goto_target(self, pose, duration): pass
    def set_target_antenna_joint_positions(self, pos): pass
    def look_at_world(self, x, y, z, duration): pass
    def goto_sleep(self): pass
    def disable_motors(self): pass

def main():
    print("Mocking Reachy Mini Lite connection...")
    reachy = MockReachy()
    print("Interface ready (no hardware required)!\n")

    try:
        # 1. Wake up
        print("1. Waking up (mocked)...")
        reachy.wake_up()
        time.sleep(1)

        # 2. Look left, center, right
        print("2. Looking around (mocked)...")
        reachy.goto_target(None, duration=0.8)
        time.sleep(1)
        reachy.goto_target(None, duration=0.8)
        time.sleep(1)
        reachy.goto_target(None, duration=0.6)
        time.sleep(0.5)

        # 3. Nod
        print("3. Nodding (mocked)...")
        reachy.goto_target(None, duration=0.4)
        time.sleep(0.5)
        reachy.goto_target(None, duration=0.3)
        time.sleep(0.4)
        reachy.goto_target(None, duration=0.3)
        time.sleep(0.5)

        # 4. Tilt head
        print("4. Tilting head (mocked)...")
        reachy.goto_target(None, duration=0.5)
        time.sleep(0.8)
        reachy.goto_target(None, duration=0.5)
        time.sleep(0.8)
        reachy.goto_target(None, duration=0.4)
        time.sleep(0.5)

        # 5. Wiggle antennas
        print("5. Wiggling antennas (mocked)...")
        for _ in range(3):
            reachy.set_target_antenna_joint_positions([0.5, -0.5])
            time.sleep(0.3)
            reachy.set_target_antenna_joint_positions([-0.5, 0.5])
            time.sleep(0.3)
        reachy.set_target_antenna_joint_positions([0.0, 0.0])
        time.sleep(0.5)

        # 6. Look at world point
        print("6. Looking at world point (mocked)...")
        reachy.look_at_world(x=0.3, y=0.0, z=0.1, duration=1.0)
        time.sleep(1)
        reachy.look_at_world(x=0.3, y=0.15, z=0.0, duration=0.8)
        time.sleep(1)
        reachy.look_at_world(x=0.3, y=-0.15, z=0.0, duration=0.8)
        time.sleep(1)

        # 7. Sleep
        print("7. Going to sleep (mocked)...")
        reachy.goto_sleep()
        time.sleep(1)

        print("\nDone! All logic checks completed in Mock Mode.")

    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        reachy.disable_motors()
        print("Motors disabled.")

if __name__ == "__main__":
    main()
