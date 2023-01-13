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

def createButton(buttonText: str, onPressMethod: Callable, parentLayout: QtWidgets.QLayout = None) -> QtWidgets.QPushButton:
	button = QtWidgets.QPushButton(buttonText)
	button.clicked.connect(onPressMethod)
	parentLayout.addWidget(button)
	return button

def _createMessageBox(title: str, message: str, icon, parent: QtWidgets.QWidget = None):
	messageBox = QtWidgets.QMessageBox()
	messageBox.setWindowTitle(title)
	messageBox.setText(message)
	messageBox.setIcon(icon)
	if parent:
		messageBox.setParent(parent)
	return messageBox

def showErrorMessage(title: str, message: str, parent: QtWidgets.QWidget = None):
	messageBox = _createMessageBox(title, message, QtWidgets.QMessageBox.Critical, parent)
	messageBox.exec_()

def askConfirmation(title: str, message: str, question: str, parent: QtWidgets.QWidget = None) -> bool:
	messageBox = _createMessageBox(title, message, QtWidgets.QMessageBox.Question, parent)
	messageBox.setInformativeText(question)
	messageBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
	reply = messageBox.exec_()
	return reply == QtWidgets.QMessageBox.Yes

def showInfoMessage(title: str, message: str, parent: QtWidgets.QWidget = None):
	messageBox = _createMessageBox(title, message, QtWidgets.QMessageBox.Information, parent)
	messageBox.exec_()
