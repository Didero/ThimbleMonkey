from typing import Callable

from PySide6 import QtGui, QtWidgets

def createMenuAction(parentMenu: QtWidgets.QMenu, actionLabel: str, actionMethod: Callable, tooltipText: str = None):
	action = QtGui.QAction(actionLabel, parentMenu)
	if tooltipText:
		action.setToolTip(tooltipText)
		action.setStatusTip(tooltipText)
	action.triggered.connect(actionMethod)
	parentMenu.addAction(action)
	return action

def showErrorMessage(title: str, message: str, parent: QtWidgets.QWidget = None):
	messageBox = QtWidgets.QMessageBox()
	messageBox.setWindowTitle(title)
	messageBox.setText(message)
	messageBox.setIcon(QtWidgets.QMessageBox.Critical)
	if parent:
		messageBox.setParent(parent)
	messageBox.exec_()
