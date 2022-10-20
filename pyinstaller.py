import time

import PyInstaller.__main__

if __name__ == '__main__':
	startTime = time.perf_counter()
	programName = 'ThimbleMonkey'

	pyInstallerArguments = [
		'main.py',
		'--name=' + programName,
		'--onefile',
		'--clean',  # Always start with a new cache
		'--noconfirm',  # Clean the 'dist' folder
		'--noconsole'
	]
	PyInstaller.__main__.run(pyInstallerArguments)
	print(f"Build took {time.perf_counter() - startTime} seconds")
