import multiprocessing, sys

from PySide6.QtWidgets import QApplication

from ui.MainWindow import MainWindow


if __name__ == '__main__':
	multiprocessing.freeze_support()  # This is needed to make multiprocessing work in a PyInstaller EXE
	gamepath = None
	filter = None
	for arg in sys.argv[1:]:
		if arg.startswith('gamepath='):
			gamepath = arg.split('=', 1)[1]
		elif arg.startswith('filter='):
			filter = arg.split('=', 1)[1]

	app = QApplication()
	app.setApplicationName("ThimbleMonkey")
	mainWindow = MainWindow(gamepath, filter)
	mainWindow.show()
	sys.exit(app.exec())
