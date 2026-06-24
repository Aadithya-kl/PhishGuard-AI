from slowapi import Limiter
from slowapi.util import get_remote_address

# Default key is remote IP, but we can override this per route to use the authenticated user
def get_user_identifier(request):
    # If the user is authenticated, use their email or ID from the request state
    if hasattr(request.state, "user_id"):
        return request.state.user_id
    # Fallback to IP address
    return get_remote_address(request)

limiter = Limiter(key_func=get_remote_address)
user_limiter = Limiter(key_func=get_user_identifier)
