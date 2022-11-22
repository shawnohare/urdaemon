"""Game information ssuch as a display name an EAccess Protocol code."""
from dataclasses import dataclass

from typing import Dict, List


@dataclass(frozen=True)
class GameInfo:
    """A container containing a game's display name and login code."""

    name: str
    code: str
    description: str = ""


DragonRealmsPrime = GameInfo("DragonRealms: Prime", "DR")
DragonRealmsPlatinum = GameInfo("DragonRealms: Platinum", "DRX")
DragonRealmsDevelopment = GameInfo("DragonRealms: Development", "DRD")
DragonRealmsPrimeTest = GameInfo("DragonRealms: Prime (Test)", "DRT")
DragonRealmsFallen = GameInfo("DragonReaalms: The Fallen", "DRF")
GemStonePrime = GameInfo("GemStone IV: Prime", "GS3")
GemStonePrimeTest = GameInfo("GemStone IV: Prime (Test)", "GST")
GemStonePlatinum = GameInfo("GemStone IV: Platinum", "GSX")
GemStoneShattered = GameInfo("Gemstone IV: Shattered", "GSF")
GemStoneDevelopment = GameInfo("Gemstone IV: Development", "GS4D")


class Games:
    DragonRealmsPrime = GameInfo("DragonRealms: Prime", "DR")
    DragonRealmsPlatinum = GameInfo("DragonRealms: Platinum", "DRX")
    DragonRealmsDevelopment = GameInfo("DragonRealms: Development", "DRD")
    DragonRealmsPrimeTest = GameInfo("DragonRealms: Prime (Test)", "DRT")
    DragonRealmsFallen = GameInfo("DragonReaalms: The Fallen", "DRF")
    GemStonePrime = GameInfo("GemStone IV: Prime", "GS3")
    GemStonePrimeTest = GameInfo("GemStone IV: Prime (Test)", "GST")
    GemStonePlatinum = GameInfo("GemStone IV: Platinum", "GSX")
    GemStoneShattered = GameInfo("Gemstone IV: Shattered", "GSF")
    GemStoneDevelopment = GameInfo("Gemstone IV: Development", "GS4D")

    _game_list = [
        DragonRealmsPrime,
        DragonRealmsPlatinum,
        DragonRealmsDevelopment,
        DragonRealmsPrimeTest,
        DragonRealmsFallen,
        GemStonePrime,
        GemStonePrimeTest,
        GemStonePlatinum,
        GemStoneShattered,
        GemStoneDevelopment,
    ]

    _lookup: Dict[str, GameInfo] = {
        # 'cs': CyberStrike,
        # 'cyberstrike': CyberStrike,
        "dr": DragonRealmsPrime,
        "dr.prime": DragonRealmsPrime,
        "dr.platinum": DragonRealmsPlatinum,
        "dr.fallen": DragonRealmsFallen,
        "dr.test": DragonRealmsPrimeTest,
        "dr.dev": DragonRealmsDevelopment,
        "dragonrealms": DragonRealmsPrime,
        "dragonrealms.prime": DragonRealmsPrime,
        "dragonrealms.platinum": DragonRealmsPlatinum,
        "dragonrealms.fallen": DragonRealmsFallen,
        "dragonrealms.test": DragonRealmsPrimeTest,
        "dragonrealms.dev": DragonRealmsDevelopment,
        "gs": GemStonePrime,
        "gs.prime": GemStonePrime,
        "gs.platinum": GemStonePlatinum,
        "gs.shattered": GemStoneShattered,
        "gs.fallen": GemStoneShattered,
        "gs.test": GemStonePrimeTest,
        "gs.dev": GemStoneDevelopment,
        "gemstone": GemStonePrime,
        "gemstone.prime": GemStonePrime,
        "gemstone.fallen": GemStoneShattered,
        "gemstone.shattered": GemStoneShattered,
        "gemstone.platinum": GemStonePlatinum,
        "gemstone.test": GemStonePrimeTest,
        "gemstone.dev": GemStoneDevelopment,
    } | {x.code.lower(): x for x in _game_list}

    @classmethod
    def list(cls) -> List[GameInfo]:
        """Return a list of Simutronics games."""
        return cls._game_list

    @classmethod
    def get(cls, key: str) -> GameInfo:
        """Get a GameInfo instance by key.

        Args:
            key: A string reference to the GameInfo instance,
                such as a human readable name or game code.
        """
        return cls._lookup[key.lower()]
