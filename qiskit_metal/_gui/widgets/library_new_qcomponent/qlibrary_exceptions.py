class PEDASetupException(Exception):
    pass


class InvalidFilePathException(PEDASetupException):
    pass

class LibraryQComponentException(Exception):
    pass


class InvalidParameterEntryException(LibraryQComponentException):
    pass


class MissingClassException(LibraryQComponentException):
    pass
