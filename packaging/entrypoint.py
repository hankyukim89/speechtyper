"""PyInstaller entry point with package-safe imports."""

import multiprocessing
import os


if __name__ == "__main__":
    # PyInstaller worker/resource-tracker processes re-enter this executable.
    # This must run before importing the application or they recursively open
    # another complete SpeechTyper instance.
    multiprocessing.freeze_support()

    if os.environ.get("SPEECHTYPER_SMOKE_TEST") == "1":
        # Lets packaging CI verify frozen imports without opening the GUI.
        import speechtyper.app  # noqa: F401
    else:
        from speechtyper.app import main

        main()
