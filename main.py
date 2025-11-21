import sys
import argparse
# from PyQt6.QtWidgets import QApplication  <-- Removed global import
# from ui.main_window import MainWindow     <-- Removed global import

def main():
    parser = argparse.ArgumentParser(description="AraUltra - AI-Powered Vulnerability Scanner")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode (no GUI)")
    parser.add_argument("--target", type=str, help="Target URL for headless scan")
    args = parser.parse_args()

    if args.headless:
        if not args.target:
            print("Error: --target is required for headless mode.")
            sys.exit(1)
        
        from core.headless_runner import HeadlessRunner
        runner = HeadlessRunner()
        runner.start(args.target)
    else:
        # GUI Mode
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.main_window import MainWindow
        except ImportError:
            print("Error: PyQt6 not installed. Install it or run with --headless.")
            sys.exit(1)

        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main()