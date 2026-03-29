from config.paths import RAW_PREGAME_DIR, DATASET_DIR, DEBUG_RESULT_DIR, DEBUG_PREVIEW_DIR
from src.utils.image_io import list_images, read_image, save_image
from src.extract.crop_slots import export_slots_from_image
from src.match.champion_matcher import match_champion
from src.match.role_matcher import is_role_icon, match_role
from src.match.match_debug import save_pair_debug
from src.match.slot_turn_detector import (
    detect_turn_slot,
    draw_turn_debug,
    is_my_turn_soon,
    crop_ally_turn_roi,
    crop_enemy_turn_roi,
    MY_PICK_SLOT,
)


def process_team(folder_path):
    results = []

    image_paths = sorted(list_images(folder_path))
    for image_path in image_paths:
        img = read_image(image_path)
        if img is None:
            continue

        if is_role_icon(img):
            role, score, best_raw, best_path = match_role(img)
            champ = None
            label = f"ROLE:{role}"
        else:
            champ, score, best_raw, best_path = match_champion(img)
            role = None
            label = f"CHAMP:{champ}"

        print(f"{image_path.name} -> {label} ({score:.4f})")

        results.append({
            "file": image_path.name,
            "role": role,
            "champ": champ,
            "score": score,
        })

        if best_raw is not None and best_path is not None:
            out_path = DEBUG_RESULT_DIR / f"{image_path.stem}__PAIR.png"
            save_pair_debug(
                output_path=out_path,
                query_img=img,
                cand_img=best_raw,
                score=score,
                query_name=image_path.name,
                cand_name=best_path.name,
            )
            print(f"[PAIR 저장] {out_path}")

    return results


def _format_ratio_map(d):
    parts = []
    for k in sorted(d.keys()):
        parts.append(f"{k}:{d[k]:.2f}")
    return "{" + ", ".join(parts) + "}"


def run_recommend_logic(turn_info):
    """
    추천 로직 실행 자리
    현재는 로그만 찍음
    나중에 여기서 챔피언 추천 함수 연결하면 됨
    """
    print("\n=== 추천 로직 실행 ===")
    print(f"아군 픽 차례: {turn_info['is_ally_pick_turn']}")
    print(f"노랑 감지: {turn_info['is_my_turn']}")
    print("조건 만족 -> 추천 시작")

    # TODO:
    # 여기서 실제 추천 함수 연결
    # 예:
    # recommend_pick(...)
    # build_recommendation(...)
    # save_recommend_result(...)


def run_pregame_pipeline():
    image_paths = list_images(RAW_PREGAME_DIR)
    if not image_paths:
        print("[안내] dataset/raw_screens/pregame 폴더에 이미지가 없습니다.")
        return

    print("=== 밴픽 파이프라인 시작 ===")

    for image_path in image_paths:
        print(f"\n[처리] {image_path.name}")

        img = read_image(image_path)
        if img is None:
            print(f"[실패] 이미지 읽기 실패: {image_path.name}")
            continue

        # =========================
        # 1) 턴 감지
        # =========================
        turn_info = detect_turn_slot(img)

        print("[TURN RAW]")
        print(f"  BLUE slots    = {turn_info['blue_slots']}")
        print(f"  YELLOW slots  = {turn_info['yellow_slots']}")
        print(f"  RED slots     = {turn_info['red_slots']}")
        print(f"  BLUE ratios   = {_format_ratio_map(turn_info['blue_slot_ratios'])}")
        print(f"  YELLOW ratios = {_format_ratio_map(turn_info['yellow_slot_ratios'])}")
        print(f"  RED ratios    = {_format_ratio_map(turn_info['red_slot_ratios'])}")

        print("[TURN PATTERN]")
        print(f"  ally_active_slots = {turn_info['ally_active_slots']}")
        print(f"  enemy_active_slots = {turn_info['enemy_active_slots']}")
        print(f"  ally_pattern = {turn_info['ally_pattern']}")
        print(f"  enemy_pattern = {turn_info['enemy_pattern']}")
        print(f"  ally_stage = {turn_info['ally_stage']}")
        print(f"  enemy_stage = {turn_info['enemy_stage']}")
        print(f"  pick_turn_team = {turn_info['pick_turn_team']}")

        if turn_info["is_ally_pick_turn"]:
            print("  아군이 지금 픽할 차례")
        elif turn_info["is_enemy_pick_turn"]:
            print("  적군이 지금 픽할 차례")
        else:
            print("  픽 차례 판정 불가")

        print("[TURN RESULT]")
        print(
            f"  ally_slot={turn_info['ally_slot']} "
            f"enemy_slot={turn_info['enemy_slot']} "
            f"is_my_turn={turn_info['is_my_turn']}"
        )

        if turn_info["is_my_turn"]:
            print(f"  노랑 불 감지됨 (아군 슬롯 {turn_info['ally_slot']})")
        else:
            print(f"  노랑 불 없음")

        is_now, is_next = is_my_turn_soon(turn_info["ally_slot"], MY_PICK_SLOT)
        if is_now:
            print("  지금 내 픽 차례")
        elif is_next:
            print("  다음이 내 픽 차례")

        # =========================
        # 2) 추천 로직 실행 조건
        # =========================
        should_run_recommend = (
            turn_info["is_ally_pick_turn"] and
            turn_info["is_my_turn"]
        )

        print(f"[RECOMMEND CHECK] should_run_recommend = {should_run_recommend}")

        if should_run_recommend:
            run_recommend_logic(turn_info)
        else:
            print("추천 로직 실행 안 함")

        # =========================
        # 3) 턴 ROI 저장
        # =========================
        ally_roi_img = crop_ally_turn_roi(img)
        ally_roi_path = DEBUG_PREVIEW_DIR / f"{image_path.stem}__ALLY_TURN_ROI.png"
        save_image(ally_roi_path, ally_roi_img)
        print(f"[ALLY TURN ROI 저장] {ally_roi_path}")

        enemy_roi_img = crop_enemy_turn_roi(img)
        enemy_roi_path = DEBUG_PREVIEW_DIR / f"{image_path.stem}__ENEMY_TURN_ROI.png"
        save_image(enemy_roi_path, enemy_roi_img)
        print(f"[ENEMY TURN ROI 저장] {enemy_roi_path}")

        # =========================
        # 4) 턴 디버그 이미지 저장
        # =========================
        turn_debug = draw_turn_debug(img, turn_info)
        turn_debug_path = DEBUG_PREVIEW_DIR / f"{image_path.stem}__TURN_DEBUG.png"
        save_image(turn_debug_path, turn_debug)
        print(f"[TURN DEBUG 저장] {turn_debug_path}")

        # =========================
        # 5) 기존 슬롯 crop 저장
        # =========================
        export_slots_from_image(
            img=img,
            image_stem=image_path.stem,
            original_name=image_path.name,
        )

        # =========================
        # 6) crop된 슬롯 매칭
        # =========================
        ally_dir = DATASET_DIR / "champion" / "pick_crop" / "ally_picks"
        enemy_dir = DATASET_DIR / "champion" / "pick_crop" / "enemy_picks"

        print("\n=== ALLY PICKS MATCH ===")
        process_team(ally_dir)

        print("\n=== ENEMY PICKS MATCH ===")
        process_team(enemy_dir)

    print("\n=== 완료 ===")