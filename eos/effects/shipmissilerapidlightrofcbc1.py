# Used by:
# Ship: Nighthawk
type = "passive"
def handler(fit, ship, context):
    level = fit.character.getSkill("Caldari Battlecruiser").level
    fit.modules.filteredItemBoost(lambda mod: mod.item.group.name == "Missile Launcher Rapid Light",
                                  "speed", ship.getModifiedItemAttr("shipBonusCBC1") * level)
