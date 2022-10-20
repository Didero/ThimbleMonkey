import sys

from PySide6.QtWidgets import QApplication

from ui.MainWindow import MainWindow


if __name__ == '__main__':
	gamepath = None
	for arg in sys.argv[1:]:
		if arg.startswith('gamepath='):
			gamepath = arg.split('=', 1)[1]

	app = QApplication()
	app.setApplicationName("ThimbleMonkey")
	mainWindow = MainWindow(gamepath)
	mainWindow.show()
	sys.exit(app.exec())
