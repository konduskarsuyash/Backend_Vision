from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status 
from .serializers import RegisterSerializer,LoginSerializer
from rest_framework.permissions import AllowAny
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from django.contrib.auth.models import User
from .serializers import AuthSerializer
from .services import get_user_data
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth import login

class RegisterView(APIView):
    permission_classes = [AllowAny]  
    def post(self,request):
        try:
            data = request.data 
            serializer = RegisterSerializer(data=data)
            
            if not serializer.is_valid():
                return Response({'data':serializer.errors,'message':"somethingwent wrong"},status=status.HTTP_400_BAD_REQUEST)   
            
            serializer.save()
            
            return Response({'data':{},'message':"Your account is created"},status= status.HTTP_201_CREATED)
        
        except Exception as e:
            print("******")
            print(e)
            return Response({'data':{},'message':"somethingwent wrong"},status=status.HTTP_400_BAD_REQUEST)
        

class LoginView(APIView):
    permission_classes=[AllowAny]
    def post(self, request):
        try:
            data = request.data 
            serializer = LoginSerializer(data=data)
            
            if not serializer.is_valid():
                return Response({'data': serializer.errors, 'message': "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)   
            
            token_data = serializer.get_jwt_token(serializer.validated_data)
            if 'access' not in token_data['data']:
                return Response(token_data, status=status.HTTP_401_UNAUTHORIZED)
            
            return Response(token_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            print("Exception:", e)
            return Response({'data': {}, 'message': "Something went wrong"}, status=status.HTTP_400_BAD_REQUEST)



class GoogleLoginApi(APIView):
    def get(self, request, *args, **kwargs):
        auth_serializer = AuthSerializer(data=request.GET)
        auth_serializer.is_valid(raise_exception=True)
        
        validated_data = auth_serializer.validated_data
        user_data = get_user_data(validated_data)
        
        try:
            user = User.objects.get(email=user_data['email'])
            login(request, user)
            # Redirect to /chatbot after successful login
            return redirect('/chatbot')
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_401_UNAUTHORIZED)

