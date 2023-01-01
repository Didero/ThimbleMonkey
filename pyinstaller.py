import os, time

import PyInstaller.__main__
from PyInstaller.utils.hooks import collect_dynamic_libs


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

	# Include the Ogg Vorbis DLLs if they're present, for Windows builds
	if os.path.isfile('libogg.dll'):
		pyInstallerArguments.append(f'--add-binary=libogg.dll{os.pathsep}.')
	if os.path.isfile('libvorbis.dll'):
		pyInstallerArguments.append(f'--add-binary=libvorbis.dll{os.pathsep}.')

	# PyOgg needs DLLs in particular places. Add those to the arguments list too
	pyOggBinaries = collect_dynamic_libs("pyogg")
	for dllSourcePath, dllTargetPath in pyOggBinaries:
		pyInstallerArguments.append(f'--add-binary={dllSourcePath}{os.pathsep}{dllTargetPath}')

	print("PyInstaller arguments:")
	print(pyInstallerArguments)
	PyInstaller.__main__.run(pyInstallerArguments)
	print(f"Build took {time.perf_counter() - startTime} seconds")
