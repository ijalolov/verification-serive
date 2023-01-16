from django.core.cache import cache


def sms_check_verified(uuid) -> bool:
    # Check if phone number is verified
    # Is it necessary to delete after valid verification?
    data = cache.get_many(cache.keys(f"*_{uuid}"))
    for d in data:
        if data[d]['verified']:
            return True
    return False
