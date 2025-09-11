class Scope:
    def __init__(self, key, name, description):
        self.key = key
        self.name = name
        self.description = description

    def __str__(self):
        return self.key


class APIScopes:
    # Public API Scopes
    METERS_READ = Scope(
        "meters:read",
        "Read Meters",
        "Read-only access to meters.",
    )

    # Secret API Scopes
    AUTH_ME_READ = Scope(
        "auth:me:read",
        "Read Authenticated User",
        "Read-only access to the authenticated user.",
    )
    ORGS_READ = Scope(
        "orgs:read",
        "Read Organizations",
        "Read-only access to organizations.",
    )
    ORGS_WRITE = Scope(
        "orgs:write",
        "Write Organizations",
        "Write access to organizations.",
    )
    INVITATIONS_READ = Scope(
        "invitations:read",
        "Read Invitations",
        "Read-only access to invitations.",
    )
    INVITATIONS_WRITE = Scope(
        "invitations:write",
        "Write Invitations",
        "Write access to invitations.",
    )
    WALLET_READ = Scope(
        "wallet:read",
        "Read Wallet",
        "Read-only access to the wallet.",
    )
    WALLET_WRITE = Scope(
        "wallet:write",
        "Write Wallet",
        "Write access to the wallet.",
    )
    METERS_WRITE = Scope(
        "meters:write",
        "Write Meters",
        "Write access to meters.",
    )
    API_KEYS_READ = Scope(
        "api-keys:read",
        "Read API Keys",
        "Read-only access to API keys.",
    )
    API_KEYS_WRITE = Scope(
        "api-keys:write",
        "Write API Keys",
        "Write access to API keys.",
    )
    TOKEN_PURCHASE = Scope(
        "token:purchase",
        "Purchase Token",
        "Purchase tokens for meters.",
    )

    @classmethod
    def get_all_scopes(cls):
        return [
            getattr(cls, attr)
            for attr in dir(cls)
            if isinstance(getattr(cls, attr), Scope)
        ]

    @classmethod
    def get_scope_by_key(cls, key):
        for scope in cls.get_all_scopes():
            if scope.key == key:
                return scope
        return None

    @classmethod
    def get_public_scopes(cls):
        return [cls.METERS_READ]

    @classmethod
    def get_secret_scopes(cls):
        return [
            cls.AUTH_ME_READ,
            cls.ORGS_READ,
            cls.ORGS_WRITE,
            cls.INVITATIONS_READ,
            cls.INVITATIONS_WRITE,
            cls.WALLET_READ,
            cls.WALLET_WRITE,
            cls.METERS_READ,
            cls.METERS_WRITE,
            cls.API_KEYS_READ,
            cls.API_KEYS_WRITE,
            cls.TOKEN_PURCHASE,
        ]
