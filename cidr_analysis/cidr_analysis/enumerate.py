class Enumerate(object):
    """A general-purpose enumerated type class that accepts its types during
    initialization.

    """
    def __init__(self, *args):
        if len(args) < 1:
            raise TypeError("Enumerate.__init__() takes at least 1 argument "
                "(0 given)")
        if len(args) == 1:
            if args[0] == str(args[0]):
                namelist = args[0].split()
            else:
                namelist = args[0]
        else:
            namelist = [str(x) for x in args]
        for number, name in enumerate(namelist):
            setattr(self, name, number)
