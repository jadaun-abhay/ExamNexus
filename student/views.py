from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.

def index(request):
    res = {"message": "Hello World"}
    return JsonResponse(res, status= 200)
