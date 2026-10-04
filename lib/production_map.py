ITEM_NAMES = {
    "biomass_mixer_upgrade_pack_mk2": "Biomass Mixer Mk II Upgrade Pack",  #TODO: not produced anywhere
    "cargo_pod_large": "Cargo Pod (Large)",
    "cargo_pod_medium": "Cargo Pod (Medium)",
    "cargo_pod_small": "Cargo Pod (Small)",
    "drone_large": "Drone (Large)",
    "drone_medium": "Drone (Medium)",
    "drone_service_station_kit": "Drone Service Station Kit",
    "drone_small": "Drone (Small)",
    "drone_station_kit": "Drone Depot Kit",
    "drone_station_kit_large": "Drone Depot Kit (Large)",
    "drone_station_kit_medium": "Drone Depot Kit (Medium)",
    "feed_bone_walker": "Bone Walker Feed",  #TODO: not produced anywhere
    "feed_crustal_echo": "Crustal Echo Feed",  #TODO: not produced anywhere
    "feed_ferric_sea_lily": "Ferric Sea-Lily Feed",  #TODO: not produced anywhere
    "feed_glacial_wyrm": "Glacial Wyrm Feed",  #TODO: not produced anywhere
    "feed_glasswing_mantis": "Glasswing Mantis Feed",  #TODO: not produced anywhere
    "feed_hive_sentinel": "Hive Sentinel Feed",  #TODO: not produced anywhere
    "feed_hollow_choir": "Hollow Choir Feed",  #TODO: not produced anywhere
    "feed_magmatic_annelid": "Magmatic Annelid Feed",  #TODO: not produced anywhere
    "feed_mantle_strider": "Mantle Strider Feed",  #TODO: not produced anywhere
    "feed_mycelial_husk": "Mycelial Husk Feed",  #TODO: not produced anywhere
    "feed_salt_tortoise": "Salt Tortoise Feed",  #TODO: not produced anywhere
    "feed_spire_drake": "Spire Drake Feed",  #TODO: not produced anywhere
    "feed_tital_cephalopod": "Tidal Cephalopod Feed",  #TODO: not produced anywhere
    "feed_vault_crab": "Vault Crab Feed",  #TODO: not produced anywhere
    "feed_veil_mantle": "Veil Mantle Feed",  #TODO: not produced anywhere
    "feed_vent_drifter": "Vent Drifter Feed",  #TODO: not produced anywhere
    "fertilizer_mk2": "Fertilizer Mk II",
    "fertilizer_mk3": "Fertilizer Mk III",
    "forage": "Plant Forage",  #TODO: not produced anywhere
    "garbage_disposal_kit": "Waste Processor Kit",
    "grow_lamp_upgrade_pack_mk2": "Grow Lamp Mk II Upgrade Pack",
    "grow_lamp_upgrade_pack_mk3": "Grow Lamp Mk III Upgrade Pack",
    "habitat_upgrade_pack_mk2": "Habitat Mk II Upgrade Pack",
    "heat_upgrade_pack_mk4": "Heat Upgrade Pack Mk IV",
    "mining_drill_heavy_kit": "Heavy Mining Drill Kit",
    "mining_drill_industrial_kit": "Industrial Mining Drill Kit",
    "oil_tank_large": "Oil Tank (Large)",
    "oil_tank_medium": "Oil Tank (Medium)",
    "oil_tank_small": "Oil Tank (Small)",
    "oxygen_upgrade_pack_mk4": "Oxygen Upgrade Pack Mk IV",
    "plant_terraformer_upgrade_pack_mk2": "Plant Terraformer Mk II Upgrade Pack",
    "pressure_upgrade_pack_mk4": "Pressure Upgrade Pack Mk IV",
    "seed_brinethorn": "Brinethorn Seed",  #TODO: not produced anywhere
    "seed_crowncap": "Crowncap Seed",  #TODO: not produced anywhere
    "seed_dewmoss": "Dewmoss Seed",  #TODO: not produced anywhere
    "seed_glowvine": "Glowvine Seed",  #TODO: not produced anywhere
    "seed_grandbloom": "Grandbloom Seed",  #TODO: not produced anywhere
    "seed_lonethorn": "Lonethorn Seed",  #TODO: not produced anywhere
    "seed_packfern": "Packfern Seed",  #TODO: not produced anywhere
    "seed_pondmoss": "Pondmoss Seed",  #TODO: not produced anywhere
    "seed_saltbloom": "Saltbloom Seed",  #TODO: not produced anywhere
    "seed_saltmate": "Saltmate Seed",  #TODO: not produced anywhere
    "seed_shadeleaf": "Shadeleaf Seed",  #TODO: not produced anywhere
    "seed_spitebud": "Spitebud Seed",  #TODO: not produced anywhere
    "seed_sunpetal": "Sunpetal Seed",  #TODO: not produced anywhere
    "seed_sunspur": "Sunspur Seed",  #TODO: not produced anywhere
    "seed_twinvine": "Twinvine Seed",  #TODO: not produced anywhere
    "sprinkler_upgrade_pack_mk2": "Sprinkler Mk II Upgrade Pack",
    "sprinkler_upgrade_pack_mk3": "Sprinkler Mk III Upgrade Pack",
}
#TODO: life forms (p811+), biome essences (p852+), exotic gases (p853+), exotic liquide (p854+)
#TODO: nuclear_battery, raw_uranium, fuel_rod, salt not produced anywhere
#  (salt is byproduct produced by wells)

def itemName(itemId):
    return ITEM_NAMES.get(itemId, " ".join(tok.capitalize() for tok in itemId.split("_")))


class ProductionSite:
    def __init__(self, local, produces, exports=None, onDemand=()):
        self.local = set(local)
        self.produces = set(produces)
        self.exports = exports or {}
        self.onDemand = set(onDemand)

PRODUCTION_SITES = {
    "Nocturna Base": ProductionSite(
        local=[
            "iron_ore",
            "steam",
            "water",
        ],
        produces=[
            "iron_ingot",
            "turbine_rotor",
        ],
        onDemand=[
            "battery_pack",
            "cargo_pod_large",
            "cargo_pod_medium",
            "cargo_pod_small",
            "dispenser_kit",
            "drone_large",
            "drone_medium",
            "drone_service_station_kit",
            "drone_small",
            "drone_station_kit",
            "drone_station_kit_large",
            "drone_station_kit_medium",
            "electric_thruster",
            "exotic_gas_cap_kit",
            "exotic_spring_tap_kit",
            "garbage_disposal_kit",
            "grow_lamp_kit",
            "grow_lamp_upgrade_pack_mk2",
            "grow_lamp_upgrade_pack_mk3",
            "habitat_upgrade_pack_mk2",
            "heat_upgrade_pack_mk4",
            "heli_thruster",
            "lead_cask",
            "lightning_rod",
            "mining_drill_kit",
            "mining_drill_kit_heavy",
            "mining_drill_kit_industrial",
            "oil_pump",
            "oil_tank_large",
            "oil_tank_medium",
            "oil_tank_small",
            "oxygen_upgrade_pack_mk4",
            "plant_terraformer_kit",
            "plant_terraformer_upgrade_pack_mk2",
            "pressure_upgrade_pack_mk4",
            "seed_maker_kit",
            "shield_plating",
            "sprinkler_kit",
            "sprinkler_upgrade_pack_mk2",
            "sprinkler_upgrade_pack_mk3",
            "thermal_cap_kit",
            "water_pump",
        ],
    ),
    "Lead Works": ProductionSite(
        local=["lead_ore"],
        produces=[
            "lead_ingot",
            "lead_plate",
        ],
        exports={
            "lead_plate": set(["Nocturna Base"]),
        },
    ),
    "Farm Supplies": ProductionSite(
        local=[
            "steam",
            "water",
        ],
        produces=[
            "coolant_loop",
            "fertilizer",
            "fertilizer_mk2",
            "fertilizer_mk3",
            "growth_accelerant",
            "neutron_capacitor",
            "yield_amplifier",
        ],
        exports={
            "coolant_loop": set(["Nocturna Base"]),
            "neutron_capacitor": set(["Nocturna Base"]),
        },
    ),
    "Petroleum Plant": ProductionSite(
        #TODO: needs forage, which isn't produced anywhere
        local=[
            "oil",
            "water",
        ],
        produces=[
            "battery_cell",
            "enrichment_compound",
            "lubricant",
            "plastic",
            "reinforced_biopolymer",
            "rubber",
            "tar",
        ],
        exports={
            "battery_cell": set(["Nocturna Base", "Farm Supplies"]),
            "lubricant": set(["Nocturna Base"]),
            "plastic": set(["Nocturna Base", "Farm Supplies"]),
            "rubber": set(["Nocturna Base"]),
            "tar": set(["Farm Supplies"]),
        },
    ),
    "Construction Supplies": ProductionSite(
        local=[
            "silicon",
            "water",
        ],
        produces=[
            "circuit_panel",
            "control_unit",
            "gas_pipe_segment",
            "glass",
            "liquid_pipe_segment",
            "machine_frame",
            "power_line_segment",
            "pressure_valve",
            "tank_lining",
        ],
        exports={
            "circuit_panel": set(["Nocturna Base", "Farm Supplies"]),
            "control_unit": set(["Nocturna Base", "Farm Supplies"]),
            "gas_pipe_segment": set(["Nocturna Base"]),
            "glass": set(["Nocturna Base", "Farm Supplies", "Petroleum Plant"]),
            "liquid_pipe_segment": set(["Nocturna Base", "Farm Supplies"]),
            "machine_frame": set(["Nocturna Base", "Farm Supplies"]),
            "pressure_valve": set(["Nocturna Base", "Farm Supplies"]),
            "tank_lining": set(["Nocturna Base"]),
        },
        onDemand=[
            "gas_pipe_bridge",
            "liquid_pipe_bridge",
            "power_line_bridge",
        ],
    ),
    "Iron Foundry": ProductionSite(
        local=["iron_ore"],
        produces=["iron_ingot"],
        exports={
            "iron_ingot": set(["Construction Supplies", "Petroleum Plant"]),
        },
    ),
    "Titanium Foundry": ProductionSite(
        local=["titanium"],
        produces=["titanium_ingot"],
        exports={
            "titanium_ingot": set(["Nocturna Base", "Construction Supplies", "Farm Supplies"]),
        },
    ),
    "Cobalt Foundry": ProductionSite(
        local=["cobalt"],
        produces=["cobalt_ingot"],
        exports={
            "cobalt_ingot": set(["Nocturna Base", "Petroleum Plant"]),
        },
    ),
    "Rare Earth Foundry": ProductionSite(
        local=["rare_earth"],
        produces=["rare_earth_core"],
        exports={
            "rare_earth_core": set(["Nocturna Base", "Farm Supplies"]),
        },
    ),
    "Neutronium Foundry": ProductionSite(
        local=["neutronium"],
        produces=["neutronium_bar"],
        exports={
            "neutronium_bar": set(["Farm Supplies"]),
        },
    ),
}
ON_DEMAND = set(prod for site in PRODUCTION_SITES.values() for prod in site.onDemand)
