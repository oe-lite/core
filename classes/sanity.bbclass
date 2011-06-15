addhook sanity to post_recipe_parse last
def sanity(d):
    pn = d.get("PN")
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9\-\+]*$", pn):
        raise Exception("Invalid recipe name (${PN}): %s"%(pn))
    version = d.get("PV") or "0"
    machine = d.get("MACHINE")
    distro = d.get("DISTRO")
    standard_overrides = ("local", "machine", "native", "sdk",
                          "cross", "sdk-cross", "canadian-cross")
    if machine in standard_overrides:
        raise Exception("Invalid machine name (${MACHINE}): %s"%(machine))
    if distro in standard_overrides:
        raise Exception("Invalid machine name (${MACHINE}): %s"%(distro))
    if machine == distro:
        raise Exception("Machine name == distro name: %s"%(machine))
    overrides = (d.get("OVERRIDES") or "").split()
    if not overrides:
        raise Exception("Overrides not defined (${OVERRIDES})")
    for override in overrides:
        if '${' in override:
            raise Exception("Unexpanded variables in OVERRIDES")
    
