from functools import wraps
from django.http import JsonResponse
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited


def api_ratelimit(key='ip', rate='10/m', method='POST'):
    """
    Custom rate limit decorator for DRF API views
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            # Apply the rate limit
            try:
                # Get the request object (it could be args[0] or args[1] depending on the view)
                request = None
                if hasattr(args[0], 'request'):
                    request = args[0].request
                elif hasattr(args[1], 'method'):
                    request = args[1]
                
                if request and request.method == method:
                    # Check rate limit
                    from django_ratelimit.core import is_ratelimited
                    
                    old_limited = getattr(request, 'limited', False)
                    ratelimited = is_ratelimited(
                        request=request,
                        group=None,
                        fn=view_func,
                        key=key,
                        rate=rate,
                        method=[method],
                        increment=True
                    )
                    
                    request.limited = ratelimited or old_limited
                    
                    if ratelimited:
                        return JsonResponse({
                            'error': 'Rate limit exceeded. Please try again later.',
                            'detail': f'Maximum {rate} requests allowed.',
                            'retry_after': '60 seconds'
                        }, status=429)
                
                return view_func(*args, **kwargs)
            except Exception as e:
                return view_func(*args, **kwargs)
        
        return wrapped_view
    return decorator
