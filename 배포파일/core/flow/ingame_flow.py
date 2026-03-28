from core.logic.ingame_logic import analyze_ingame_state
from device.capture import load_latest_frame, read_image_korean
from device.device_state import DeviceState


def run_ingame_once(device_state: DeviceState, use_gpt: bool = False, image_path: str | None = None):
    try:
        from core.logic.matcher_logic import IngameOCRMatcher
    except Exception as e:
        return None, None, f"OCR 모듈 로드 실패: {e}"

    if image_path:
        frame = read_image_korean(image_path)
        path = image_path
    else:
        frame, path = load_latest_frame(device_state)

    if frame is None:
        return None, None, "이미지 없음"

    try:
        matcher = IngameOCRMatcher()
        state, debug = matcher.extract_state_from_frame(frame)
        result = analyze_ingame_state(state, use_gpt=use_gpt)
        return state, result, debug
    except Exception as e:
        return None, None, f"인게임 분석 실패: {e}"