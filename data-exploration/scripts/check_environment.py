import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]

    print("MovePredict BH — Environment Check")
    print("-----------------------------------")
    print(f"Python version: {sys.version}")
    print(f"Project root: {project_root}")

    expected_folders = [
        "backend",
        "frontend",
        "data-exploration",
        "docs",
        "infra",
    ]

    print("\nChecking expected folders:")

    for folder in expected_folders:
        folder_path = project_root / folder

        if folder_path.exists():
            print(f"[OK] {folder}")
        else:
            print(f"[MISSING] {folder}")

    print("\nEnvironment check finished.")


if __name__ == "__main__":
    main()
