import os, shutil, time, zipfile

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

	# PyOgg needs DLLs in particular places. Add those to the arguments list too
	pyOggBinaries = collect_dynamic_libs("pyogg")
	for dllSourcePath, dllTargetPath in pyOggBinaries:
		pyInstallerArguments.append(f'--add-binary={dllSourcePath}{os.pathsep}.')

	print("PyInstaller arguments:")
	print(pyInstallerArguments)
	PyInstaller.__main__.run(pyInstallerArguments)

	# Copy the license and readme over too
	for filename in ('LICENSE', 'readme.md'):
		print(f"Copying {filename} to dist")
		shutil.copy2(filename, 'dist')
	print("Copying readme.md to readme.txt")
	shutil.copy2('readme.md', os.path.join('dist', 'readme.txt'))

	with zipfile.ZipFile(os.path.join('dist', f'{programName}.zip'), 'w') as distZip:
		print("Creating distribution zipfile " + distZip.filename)
		# .exe is Windows, .app is MacOS, no extension is Linux
		for filename in ('LICENSE', 'readme.md', 'readme.txt', f'{programName}.exe', f'{programName}.app', programName):
			filepath = os.path.join('dist', filename)
			if os.path.exists(filepath):
				print(f"Adding {filename} to distribution zipfile")
				distZip.write(filepath, filename)

	print(f"Build took {time.perf_counter() - startTime} seconds")
