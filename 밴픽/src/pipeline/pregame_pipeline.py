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


def run_pregame_pipeline():
    image_paths = list_images(RAW_PREGAME_DIR)

    if not image_paths:
        print("[안내] dataset/raw_screens/pregame 폴더에 이미지가 없습니다.")
        return

    print("=== 밴픽 파이프라인 시작 ===")

    for image_path in image_paths:
        print(f"[처리] {image_path.name}")

        img = read_image(image_path)
        if img is None:
            print(f"[실패] 이미지 읽기 실패: {image_path.name}")
            continue

        # =========================
        # 1) 턴 감지
        # =========================
        turn_info = detect_turn_slot(img)

        print(
            f"[TURN] "
            f"blue_y={turn_info['blue_y']} "
            f"yellow_y={turn_info['yellow_y']} "
            f"red_y={turn_info['red_y']} "
            f"blue_s={turn_info['blue_strength']} "
            f"yellow_s={turn_info['yellow_strength']} "
            f"red_s={turn_info['red_strength']} "
            f"ally_slot={turn_info['ally_slot']} "
            f"enemy_slot={turn_info['enemy_slot']}"
        )

        if turn_info["is_my_turn"]:
            print(f"🔥 지금 내 차례로 감지됨 (아군 슬롯 {turn_info['ally_slot']})")
        else:
            print(f"⏳ 아군 진행 위치 감지 (아군 슬롯 {turn_info['ally_slot']})")

        print(f"🟥 상대 진행 위치 감지 (적군 슬롯 {turn_info['enemy_slot']})")

        is_now, is_next = is_my_turn_soon(turn_info["ally_slot"], MY_PICK_SLOT)

        if is_now:
            print("🚨 지금 내 픽 차례 → 추천 실행")
        elif is_next:
            print("⚠️ 다음이 내 차례 → 추천 준비")

        # =========================
        # 2) 턴 ROI 저장
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
        # 3) 턴 디버그 이미지 저장
        # =========================
        turn_debug = draw_turn_debug(img, turn_info)
        turn_debug_path = DEBUG_PREVIEW_DIR / f"{image_path.stem}__TURN_DEBUG.png"
        save_image(turn_debug_path, turn_debug)
        print(f"[TURN DEBUG 저장] {turn_debug_path}")

        # =========================
        # 4) 기존 슬롯 crop 저장
        # =========================
        export_slots_from_image(
            img=img,
            image_stem=image_path.stem,
            original_name=image_path.name,
        )

    # =========================
    # 5) crop된 슬롯 매칭
    # =========================
    ally_dir = DATASET_DIR / "champion" / "pick_crop" / "ally_picks"
    enemy_dir = DATASET_DIR / "champion" / "pick_crop" / "enemy_picks"

    print("\n=== ALLY PICKS MATCH ===")
    process_team(ally_dir)

    print("\n=== ENEMY PICKS MATCH ===")
    process_team(enemy_dir)

    print("\n=== 완료 ===")