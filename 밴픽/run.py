from pathlib import Path
print("RUN FILE =", Path(__file__).resolve())

from src.pipeline.pregame_pipeline import run_pregame_pipeline

if __name__ == "__main__":
    run_pregame_pipeline()