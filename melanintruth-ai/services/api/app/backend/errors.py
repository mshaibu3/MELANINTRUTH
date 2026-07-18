class DomainError(Exception):
    code = "domain_error"
    status_code = 400


class AuthenticationError(DomainError):
    code = "authentication_failed"
    status_code = 401


class AuthorizationError(DomainError):
    code = "not_authorized"
    status_code = 403


class ConsentRequiredError(AuthorizationError):
    code = "consent_required"


class ConflictError(DomainError):
    code = "conflict"
    status_code = 409


class NotFoundError(DomainError):
    code = "not_found"
    status_code = 404


class ValidationError(DomainError):
    code = "validation_failed"
    status_code = 422
