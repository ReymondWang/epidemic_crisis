import enum


class HealthLevel(enum.IntEnum):
    PERFECT = 5
    GOOD = 4
    COMMON = 3
    BAD = 2
    POOR = 1
    DEAD = 0


class InfectionLevel(enum.IntEnum):
    CLEAN = 0
    TINY = 1
    COMMON = 2
    SERIOUS = 3
    CRITICAL = 4
    DEAD = 5


class EffectLevel(enum.IntEnum):
    POOR = 4
    COMMON = 2
    GOOD = 1


class RelationLevel(enum.IntEnum):
    STRANGE = 1
    COMMON = 2
    FAMILIAR = 3
    INTIMATE = 4

if __name__ == "__main__":
    first_level = InfectionLevel.TINY
    print(first_level)
    first_level = InfectionLevel(first_level + 1)
    print(first_level)
