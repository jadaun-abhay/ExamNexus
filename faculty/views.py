from django.http import JsonResponse
from django.shortcuts import render

from portal.functions import check_role


# Create your views here.

def index(request):
    res = {"message": "Hello World"}
    return JsonResponse(res, status= 200)

def create_schedule(request):
    flag = check_role(request.user, ["coe"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status= flag["status"])
