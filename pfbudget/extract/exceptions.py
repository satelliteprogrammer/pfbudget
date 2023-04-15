class ExtractError(Exception):
    pass


class BankError(ExtractError):
    pass


class PSD2ClientError(ExtractError):
    pass


class CredentialsError(PSD2ClientError):
    pass


class DownloadError(PSD2ClientError):
    pass
