addhook set_useflags to post_recipe_parse first after base_after_parse

#
# RECIPE_OPTIONS are to be defined in recipes, and should be a
# space-separated list of lower-case options, preferably prefixed with
# the recipe name (in lower-case).
#
# Distro configuration files can then define these as needed, and set
# them to the desired values, enabling distro customization of recipes
# without the need to include anything about the distros in the
# meta-data repository holding the repository.
#
def set_useflags(d):
    recipe_options = ((d.get('RECIPE_FLAGS') or "").split() +
                      (d.get('CLASS_FLAGS') or "").split())
    if not recipe_options:
        return
    recipe_arch = d.get('RECIPE_ARCH')
    recipe_arch_mach = d.get('RECIPE_ARCH_MACHINE')
    overrides = (d.get('OVERRIDES') or "")
    overrides_changed = False
    for option in recipe_options:
        recipe_val = d.get('RECIPE_USE_'+option)
        local_val = d.get('LOCAL_USE_'+option)
        machine_val = d.get('MACHINE_USE_'+option)
        distro_val = d.get('DISTRO_USE_'+option)
        default_val = d.get('DEFAULT_USE_'+option) or "0"
        if recipe_val is not None:
            val = recipe_val
        elif local_val is not None:
            val = local_val
        elif machine_val is not None:
            if recipe_arch != recipe_arch_mach:
                d.set('RECIPE_ARCH', '${RECIPE_ARCH_MACHINE}')
            val = machine_val
        elif distro_val is not None:
            val = distro_val
        else:
            val = default_val
        if val and val != "0":
            d.set('USE_'+option, val)
            overrides += ':USE_'+option
            overrides_changed = True
    if overrides_changed:
        d.set('OVERRIDES', overrides)
    return

BLACKLIST_PREFIX += "LOCAL_USE_ RECIPE_USE_ MACHINE_USE_ DISTRO_USE_ DEFAULT_USE_"
