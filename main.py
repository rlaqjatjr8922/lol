from controller.pregame_controller import PregameController
from shared.app_state import AppState


def main():
    print("[main] program started")

    app_state = AppState()
    controller = PregameController(app_state)
    controller.run()


if __name__ == "__main__":
    main()