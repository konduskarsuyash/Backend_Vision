from django.conf import settings
from django.shortcuts import redirect
from django.core.exceptions import ValidationError
from urllib.parse import urlencode
import requests
from django.contrib.auth.models import User
import logging
import os


GOOGLE_ACCESS_TOKEN_OBTAIN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USER_INFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'
LOGIN_URL = f'{settings.BASE_APP_URL}/login'

logger = logging.getLogger(__name__)

def google_get_access_token(code: str, redirect_uri: str) -> str:
    """
    Exchange the authorization code for an access token.
    """
    data = {
        'code': code,
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('SECRET'),
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }

    response = requests.post(GOOGLE_ACCESS_TOKEN_OBTAIN_URL, data=data)
    
    # Ensure the request was successful
    if response.status_code != 200:
        logger.error(f"Failed to obtain access token: {response.text}")
        raise ValidationError('Failed to obtain access token from Google.')

    try:
        token_data = response.json()
        access_token = token_data.get('access_token')
        if not access_token:
            logger.error(f"Access token missing in response: {token_data}")
            raise ValidationError('Access token missing in Google response.')
        return access_token
    except ValueError:
        logger.error("Error parsing access token response as JSON.")
        raise ValidationError('Could not parse the access token response from Google.')

def google_get_user_info(access_token: str):
    """
    Retrieve user information from Google using the access token.
    """
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get(GOOGLE_USER_INFO_URL, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to obtain user info: {response.text}")
        raise ValidationError('Failed to obtain user info from Google.')

    try:
        user_info = response.json()
        return user_info
    except ValueError:
        logger.error("Error parsing user info response as JSON.")
        raise ValidationError('Could not parse the user info response from Google.')

def get_user_data(validated_data):
    """
    Main logic for handling the OAuth response and user creation.
    """
    domain = settings.BASE_API_URL
    redirect_uri = f'{domain}/account/login/google/'

    code = validated_data.get('code')
    error = validated_data.get('error')

    if error or not code:
        params = urlencode({'error': error})
        return redirect(f'{LOGIN_URL}?{params}')
    
    try:
        # Get access token
        access_token = google_get_access_token(code=code, redirect_uri=redirect_uri)
        
        # Get user information
        user_data = google_get_user_info(access_token=access_token)

        # Log the user data for debugging
        logger.info(f"User data retrieved from Google: {user_data}")

        # Create or get user in the database
        user, created = User.objects.get_or_create(
            username=user_data['email'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data.get('given_name', ''),
                'last_name': user_data.get('family_name', ''),
            }
        )

        # Prepare the profile data to return
        profile_data = {
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        return profile_data

    except Exception as e:
        logger.error(f"An error occurred while processing user data: {str(e)}")
        raise ValidationError('An error occurred during Google login process.')
