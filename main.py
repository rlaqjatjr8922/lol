from shared.app_state import AppState
from ui.main_ui import run_ui


def main():
    print("[main] program started")

    app_state = AppState()
    run_ui(app_state)


if __name__ == "__main__":
    main()