#!/usr/bin/env python2.6

import re

class Enumerate(object):
    """A general-purpose enumerated type class that accepts its types as an
    iterable or series of comma-delimited arguments  during initialization. The
    string representation of each object in the iterable/argument array is used
    as the attribute name, and the attribute value is a unique, incrementing
    integer starting at 0 for the first element in the iterable/array.

    Because of this underlying use of integers, iterables are comparable based
    on the order of values in the iterable supplied during initialization.
    Duplicate values would be problematic in terms of ordering, and so are
    ignored.

    If a singleton string enumerator is desired, the proper invocation would be
    e = Enumerate(['SINGLETON']) such that e.SINGLETON is defined, rather than
    the e.S, e.I, e.N, ... that would result from iterating through the
    characters in the string.

    """
    def __init__(self, *args):
        if len(args) < 1:
            raise TypeError("Enumerate.__init__() takes at least 1 argument "
                "(0 given)")
        if len(args) > 1:
            namelist = [str(x) for x in args]
        else:
            namelist = [str(x) for x in args[0]]

        for number, name in enumerate(namelist):
            # from http://docs.python.org/reference/lexical_analysis.html
            if not re.match("^[a-zA-Z_][a-zA-Z0-9_]*$", name):
                raise ValueError("'{0}' is an illegal identifier".format(name))
            try:
                getattr(self, name)
            except AttributeError:
                setattr(self, name, number)

        self.__setattr__ = None
