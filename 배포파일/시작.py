from core.pregame_app import run_pregame_then_ingame as run_pregame
from core.ingame_coach import run_ingame


def main():
    print("=== Wildrift AI Coach 시작 ===")
    run_pregame()
    print("프리게임 코치 완료 → 인게임 코치 시작")
    run_ingame()


if __name__ == "__main__":
    main()
