from django.http import JsonResponse
from django_ratelimit.exceptions import Ratelimited


class RateLimitMiddleware:
    """
    Middleware to handle rate limit exceptions and return JSON responses
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, Ratelimited):
            return JsonResponse({
                'error': 'Rate limit exceeded. Please try again later.',
                'detail': 'Too many requests from this IP address.',
                'retry_after': '60 seconds'
            }, status=429)
        return None
