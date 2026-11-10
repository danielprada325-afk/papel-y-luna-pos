from django.conf import settings
class CorsMiddleware:
    def __init__(self, get_response): self.get_response=get_response
    def __call__(self, request):
        if request.method == "OPTIONS":
            from django.http import HttpResponse
            response=HttpResponse(status=204)
        else: response=self.get_response(request)
        origin=request.headers.get("Origin", "")
        if origin in settings.CORS_ALLOWED_ORIGINS:
            response["Access-Control-Allow-Origin"]=origin
            response["Access-Control-Allow-Credentials"]="true"
            response["Access-Control-Allow-Headers"]="Content-Type, X-CSRFToken"
            response["Access-Control-Allow-Methods"]="GET, POST, PATCH, PUT, DELETE, OPTIONS"
            response["Vary"]="Origin"
        return response
