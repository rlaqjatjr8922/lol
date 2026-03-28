import subprocess


def run_adb_command(args):
    try:
        result = subprocess.run(
            ["adb", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)