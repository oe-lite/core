__all__ = [
    "NoSuchRecipe",
    "NoSuchPackage",
    "NoSuchItem",
    "NoSuchTask",
    "InvalidRecipe",
    "NoProvider",
    "RecursiveDepends",
    "MultipleProviders",
    ]


class NoSuchRecipe(Exception):
    pass

class NoSuchPackage(Exception):
    pass

class NoSuchItem(Exception):
    pass

class NoSuchTask(Exception):
    pass

class InvalidRecipe(Exception):
    pass

class NoProvider(Exception):
    pass

class RecursiveDepends(Exception):
    pass

class MultipleProviders(Exception):
    pass

class HookFailed(Exception):
    def __init__(self, name, function, retval):
        self.name = name
        self.function = function
        self.retval = retval
        return
    def __str__(self):
        return "Hook failed: %s.%s: %s"%(
            self.name, self.function, repr(self.retval))

