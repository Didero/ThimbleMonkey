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
