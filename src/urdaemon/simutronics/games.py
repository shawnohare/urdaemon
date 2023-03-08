"""Game information ssuch as a display name an EAccess Protocol code."""
from dataclasses import dataclass


@dataclass(frozen=True)
class GameInfo:
    """Contains a game's display name and login code as returned from the
    EAccess GetGames command.
    ."""

    name: str
    code: str
    description: str = ""


DragonRealms = GameInfo("DragonRealms: Prime", "DR")
DragonRealmsPrime = DragonRealms
DragonRealmsPlatinum = GameInfo("DragonRealms: Platinum", "DRX")
DragonRealmsDevelopment = GameInfo("DragonRealms: Development", "DRD")
DragonRealmsPrimeTest = GameInfo("DragonRealms: Prime (Test)", "DRT")
DragonRealmsFallen = GameInfo("DragonReaalms: The Fallen", "DRF")
GemStone = GameInfo("GemStone IV: Prime", "GS3")
GemStonePrime = GemStone
GemStonePrimeTest = GameInfo("GemStone IV: Prime (Test)", "GST")
GemStonePlatinum = GameInfo("GemStone IV: Platinum", "GSX")
GemStoneShattered = GameInfo("Gemstone IV: Shattered", "GSF")
GemStoneDevelopment = GameInfo("Gemstone IV: Development", "GS4D")
