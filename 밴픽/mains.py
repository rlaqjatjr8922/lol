import time
from pathlib import Path

from capture import RealtimeCapture, save_image_korean_path
from match.slot_turn_detector import detect_turn_slot, draw_turn_debug

CAPTURE_FPS = 2


def main():
    project_root = Path(__file__).resolve().parent
    debug_dir = project_root / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)

    latest_frame_path = debug_dir / "realtime_latest.png"

    cap = RealtimeCapture()
    cap.open()

    frame_interval = 1.0 / CAPTURE_FPS
    last_save_time = 0.0

    try:
        while True:
            t0 = time.time()

            frame = cap.read()
            if frame is None:
                print("[오류] 프레임 캡처 실패")
                time.sleep(0.5)
                continue

            turn_info = detect_turn_slot(frame)
            debug_frame = draw_turn_debug(frame, turn_info)

            print(
                f"[TURN] ally={turn_info['ally_active_slots']} "
                f"enemy={turn_info['enemy_active_slots']} "
                f"pick_turn_team={turn_info['pick_turn_team']} "
                f"is_my_turn={turn_info['is_my_turn']}"
            )

            now = time.time()
            if now - last_save_time >= 0.5:
                ok = save_image_korean_path(latest_frame_path, debug_frame)
                print(f"[SAVE] {latest_frame_path} / ok={ok}")
                last_save_time = now

            elapsed = time.time() - t0
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    finally:
        cap.close()


if __name__ == "__main__":
    main()
