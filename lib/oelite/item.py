from oebakery import die, err, warn, info, debug


class OEliteItem:

    def __init__(self, item, context = ("DEPENDS", None)):
        item = item.split(":", 1)
        if len(item) == 1:
            self.type = None
            item = item[0]
        else:
            self.type = item[0]
            item = item[1]
        item = item.split("_", 1)
        self.name = item[0]
        if len(item) == 1:
            self.version = None
        else:
            self.version = item[1]
        assert isinstance(context, tuple) and len(context) == 2
        assert context[0] in ("DEPENDS", "RDEPENDS", "FDEPENDS")
        try:
            self.type = TYPEMAP[context[0]][context[1]][self.type]
        except KeyError:
            raise Exception("Invalid item type %s in %s %s context"%(
                self.type, context[0], context[1]))
        return

    def __str__(self):
        if self.type:
            string = self.type + ":" + self.name
        else:
            string = self.name
        if self.version:
            string += "_" + self.version
        return string

    def __eq__(self, other):
        return (self.type == other.type and
                self.item == other.item and
                self.version == other.version)


TYPEMAP = {

    "DEPENDS": {

        None : {
            None		: None,
            "native"		: "native",
            "cross"		: "cross",
            "machine"		: "machine",
            "sdk-cross"		: "sdk-cross",
            "sdk"		: "sdk",
            "canadian-cross"	: "canadian-cross",
            },

        "native" : {
            None		: "native",
            "native"		: "native",
            "cross"		: "native",
            "build"		: "native",
            "host"		: "native",
            "target"		: "native",
            "host-cross"	: "native",
            "target-cross"	: "native",
            },

        "cross" : {
            None		: "cross",
            "native"		: "native",
            "cross"		: "cross",
            "machine"		: "machine",
            "build"		: "native",
            "host"		: "native",
            "target"		: "machine",
            "host-cross"	: "native",
            "target-cross"	: "cross",
            },

        "machine" : {
            None		: "machine",
            "native"		: "native",
            "cross"		: "cross",
            "machine"		: "machine",
            "build"		: "native",
            "host"		: "machine",
            "target"		: "machine",
            "host-cross"	: "cross",
            "target-cross"	: "cross",
            },

        "sdk-cross" : {
            None		: "sdk-cross",
            "native"		: "native",
            "sdk-cross"		: "sdk-cross",
            "sdk"		: "sdk",
            "build"		: "native",
            "host"		: "native",
            "target"		: "sdk",
            "host-cross"	: "native",
            "target-cross"	: "sdk-cross",
            },

        "sdk" : {
            None		: "sdk",
            "native"		: "native",
            "sdk-cross"		: "sdk-cross",
            "sdk"		: "sdk",
            "build"		: "native",
            "host"		: "sdk",
            "target"		: "sdk",
            "host-cross"	: "sdk-cross",
            "target-cross"	: "sdk-cross",
            },

        "canadian-cross" : {
            None		: "canadian-cross",
            "native"		: "native",
            "cross"		: "cross",
            "machine"		: "machine",
            "sdk-cross"		: "sdk-cross",
            "sdk"		: "sdk",
            "canadian-cross"	: "canadian-cross",
            "build"		: "native",
            "host"		: "sdk",
            "target"		: "machine",
            "host-cross"	: "sdk-cross",
            "target-cross"	: "cross",
            },
        },

    "RDEPENDS": {

        "machine" : {
            None		: "machine",
            "machine"		: "machine",
            "host"		: "machine",
            "target"		: "machine",
            },

        "sdk" : {
            None		: "sdk",
            "sdk"		: "sdk",
            "host"		: "sdk",
            "target"		: "sdk",
            },

        "canadian-cross" : {
            None		: "canadian-cross",
            "machine"		: "machine",
            "sdk"		: "sdk",
            "canadian-cross"	: "canadian-cross",
            "host"		: "sdk",
            "target"		: "machine",
            },
        },

    "FDEPENDS": {

        None : {
            None		: "native",
            "native"		: "native",
            },

        "native" : {
            None		: "native",
            "native"		: "native",
            },

        "cross" : {
            None		: "native",
            "native"		: "native",
            },

        "machine" : {
            None		: "native",
            "native"		: "native",
            },

        "sdk-cross" : {
            None		: "native",
            "native"		: "native",
            },

        "sdk" : {
            None		: "native",
            "native"		: "native",
            },

        "canadian-cross" : {
            None		: "native",
            "native"		: "native",
            },
        },
}

def typemap(type):
    assert type
