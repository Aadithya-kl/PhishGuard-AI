class ResponseGuard:
    # Organization-wide maximums per action
    MAX_USERS = 100
    MAX_MAILBOXES = 1000
    MAX_DOMAINS = 0 # Cannot block domains widely without extreme caution
    
    @classmethod
    def check_blast_radius(cls, blast_radius: dict) -> bool:
        if blast_radius.get("affected_users", 0) > cls.MAX_USERS:
            return False
        if blast_radius.get("affected_mailboxes", 0) > cls.MAX_MAILBOXES:
            return False
        if blast_radius.get("affected_domains", 0) > cls.MAX_DOMAINS:
            return False
            
        return True
