from __future__ import annotations


class MainWindow:
    def update_result(self, result: dict) -> None:
        print("[UI] latest result:")
        for key, value in result.items():
            print(f"  - {key}: {value}")
