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
