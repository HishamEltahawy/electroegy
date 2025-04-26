from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from datetime import datetime, timedelta
from .serializers import SzSignup, SzUsers
from .models import Profile
from rest_framework.views import APIView
from .models import Wishlist
from ProductsApp.models import Products
from django_ratelimit.decorators import ratelimit

# SignUp
@api_view(['POST'])
def register(request):
    data = request.data
    serializer = SzSignup(data=data)
    if serializer.is_valid():
        if not User.objects.filter(email=data['email']).exists():
            user = User.objects.create(
                username=data['username'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                password=make_password(data['password']),  # Use make_password library to encrypt password
            )
            # Ensure a profile is created for the user
            if not hasattr(user, 'profile'):  # Check if the user already has a profile
                Profile.objects.create(user=user)
            return Response({'details': 'Add User Successful'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'details': 'This Account Already Exist'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(serializer.errors)
    
    
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def current_user(request):
    user = request.user # Get the currently authenticated user
    serializer = SzUsers(user)
    return Response(serializer.data)


# Update user details
@permission_classes([IsAuthenticated])
@api_view(['PUT'])
def update_user(request):
    user = request.user
    data = request.data

    user.first_name = data['first_name']
    user.last_name = data['last_name']
    user.username = data['username']
    user.email = data['email']

    if data['password'] != "":
        user.password = make_password(data['password'])
    
    user.save()
    serializer = SzUsers(user, many=False)
    return Response(serializer.data)


def get_current_host(request):
    protocol = request.is_secure() and 'https' or 'http'
    host = request.get_host()
    return '{protocol}://{host}/'.format(protocol=protocol, host = host)

# Forget password
@api_view(['POST'])
def forget_password(request):
    data = request.data
    user = get_object_or_404(User, email=data['email']) # all fields about this user (id, username, password, ...)
    
    generate_token = get_random_string(40)
    token_ex_date = datetime.now() + timedelta(minutes=30)
    user.profile.new_token = generate_token
    user.profile.ex_date = token_ex_date
    user.profile.save()
    
    link = 'http://127.0.0.1:8000/api/accounts/reset_password/{generate_token}'.format(generate_token=generate_token)
    body = 'Your password-reset link is {link}'.format(link=link)
    
    send_mail(
        'Password reset from hisham',
        body,
        'hishameltahawy555@gmail.com',
        [data['email']]
    )
    return Response({'details': 'Password reset link sent to email: {email}'.format(email=data['email'])})


# Reset password
@api_view(['POST'])
def reset_password(request, token):
    data = request.data
    user = get_object_or_404(User, profile__new_token=token)  # all fields about this user (id, username, password, ...)
    
    if user.profile.ex_date is None or user.profile.ex_date.replace(tzinfo=None) < datetime.now():
        return Response({'error': 'Token is expired'}, status=status.HTTP_400_BAD_REQUEST)
    
    if data['password'] != data['confirmPassword']:
        return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

    # Make token and its expire date empty to never user or anyone use this api again without call forget password 
    user.password = make_password(data['password'])
    user.profile.new_token = ""
    user.profile.ex_date = None
    
    user.profile.save()
    user.save()
    return Response({'result': 'Password changed successfully.'}, status=status.HTTP_200_OK)


class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            products = wishlist.products.all()
            product_data = [
                {
                    "id": product.id,
                    "name": product.name,
                    "price": product.price,
                    "category": product.category.name if product.category else None,
                }
                for product in products
            ]
            return Response({"wishlist": product_data}, status=status.HTTP_200_OK)
        except Wishlist.DoesNotExist:
            return Response({"wishlist": []}, status=status.HTTP_200_OK)

    def post(self, request):
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Products.objects.get(id=product_id)
            wishlist, created = Wishlist.objects.get_or_create(user=request.user)
            wishlist.products.add(product)
            return Response({"message": "Product added to wishlist."}, status=status.HTTP_201_CREATED)
        except Products.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Products.objects.get(id=product_id)
            wishlist = Wishlist.objects.get(user=request.user)
            wishlist.products.remove(product)
            return Response({"message": "Product removed from wishlist."}, status=status.HTTP_200_OK)
        except Products.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        except Wishlist.DoesNotExist:
            return Response({"error": "Wishlist not found."}, status=status.HTTP_404_NOT_FOUND)


class Enable2FAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = request.user.profile
        if profile.two_factor_enabled:
            return Response({"error": "2FA is already enabled."}, status=status.HTTP_400_BAD_REQUEST)

        profile.two_factor_enabled = True
        profile.save()
        return Response({"message": "2FA has been enabled."}, status=status.HTTP_200_OK)


class Disable2FAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = request.user.profile
        if not profile.two_factor_enabled:
            return Response({"error": "2FA is not enabled."}, status=status.HTTP_400_BAD_REQUEST)

        profile.two_factor_enabled = False
        profile.two_factor_code = None
        profile.save()
        return Response({"message": "2FA has been disabled."}, status=status.HTTP_200_OK)


class Verify2FAView(APIView):
    permission_classes = [IsAuthenticated]

    @ratelimit(key='ip', rate='3/m', block=True)
    def post(self, request):
        code = request.data.get("code")
        profile = request.user.profile

        if not profile.two_factor_enabled:
            return Response({"error": "2FA is not enabled."}, status=status.HTTP_400_BAD_REQUEST)

        if profile.verify_two_factor_code(code):  # Use the decryption method to verify the code
            profile.two_factor_code = None  # Clear the code after successful verification
            profile.save()
            return Response({"message": "2FA verification successful."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid 2FA code."}, status=status.HTTP_400_BAD_REQUEST)


class Request2FACodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = request.user.profile

        if not profile.two_factor_enabled:
            return Response({"error": "2FA is not enabled."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate a random 6-digit code
        code = get_random_string(length=6, allowed_chars='0123456789')
        profile.set_two_factor_code(code)  # Use the encryption method to set the code

        # Send the code via email
        send_mail(
            subject="Your 2FA Code",
            message=f"Your 2FA code is: {code}",
            from_email="noreply@electroegy.com",
            recipient_list=[request.user.email],
        )

        return Response({"message": "2FA code has been sent to your email."}, status=status.HTTP_200_OK)


@ratelimit(key='ip', rate='5/m', block=True)
def login_view(request):
    # ...existing login logic...
    pass

