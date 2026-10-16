class ValidationError(ValueError):
    pass


class InvalidTitle(ValidationError):
    pass


class InvalidISBN(ValidationError):
    pass


class InvalidPrice(ValidationError):
    pass


class InvalidAuthorName(ValidationError):
    pass


class InvalidBirthDate(ValidationError):
    pass
