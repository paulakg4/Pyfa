# Used by:
# Ship: Basilisk
# Ship: Etana
type = "passive"
def handler(fit, ship, context):
    level = fit.character.getSkill("Logistics").level
    fit.modules.filteredItemBoost(lambda mod: mod.item.group.name == "Energy Transfer Array",
                                  "capacitorNeed", ship.getModifiedItemAttr("eliteBonusLogistics2") * level)
