"""PyInstaller entry point with package-safe imports."""

import os


if __name__ == "__main__":
    if os.environ.get("SPEECHTYPER_SMOKE_TEST") == "1":
        # Lets packaging CI verify frozen imports without opening the GUI.
        import speechtyper.app  # noqa: F401
    else:
        from speechtyper.app import main

        main()
