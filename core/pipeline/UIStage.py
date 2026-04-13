class UIStage:
    def __init__(self, app_state):
        self.app_state = app_state

    def run(self):
        print("\n" + "=" * 50)
        print("[UIStage] 화면 업데이트")
        print("=" * 50 + "\n")
        return True

