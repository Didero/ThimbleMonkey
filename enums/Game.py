import os
from enum import Enum

class Game(Enum):
	UNKNOWN = '[Unknown]'
	THIMBLEWEED_PARK = 'Thimbleweed Park'
	DELORES = 'Delores'
	RETURN_TO_MONKEY_ISLAND = 'Return To Monkey Island'

	@staticmethod
	def ggpackPathToGameName(packPath):
		packName = os.path.splitext(os.path.basename(packPath))[0]
		if packName == 'ThimbleweedPark':
			return Game.THIMBLEWEED_PARK
		elif packName == 'Delores':
			return Game.DELORES
		elif packName == 'Weird':
			return Game.RETURN_TO_MONKEY_ISLAND
		return Game.UNKNOWN
