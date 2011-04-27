addhook arch_update to post_recipe_parse first before base_after_parse

def arch_update(d):
    import oelite.arch
    oelite.arch.update(d)
