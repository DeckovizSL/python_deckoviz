from rest_framework.views import APIView
from rest_framework.response import Response 
from .serializers import RegisterSerializer, UserSerializer,AddressSerializer,NewsLetterSubscriberSerializer,UserProfileSerializer, ForgotPasswordSerializer, ResetPasswordSerializer, EmailVerificationSerializer, ResendVerificationSerializer, MyTokenObtainPairSerializer
from rest_framework import mixins,viewsets,status,generics
from rest_framework.permissions import IsAuthenticated,AllowAny
from django.contrib.auth import get_user_model
from .models import Address,NewsLetterSubscriber,UserProfile, PasswordResetToken, EmailVerificationToken
from common.apps.utils.google_sheet import GoogleSheet
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from social_django.utils import load_strategy, load_backend
from social_core.exceptions import MissingBackend
from django.shortcuts import redirect
from django.conf import settings
from django.core.mail import send_mail
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework_simplejwt.views import TokenObtainPairView

User = get_user_model()
_google_sheet = None

def get_google_sheet():
    global _google_sheet
    if _google_sheet is None:
        try:
            _google_sheet = GoogleSheet(sheet_name="Deckoviz-User-Waiting-List")
        except Exception as e:
            print(f"Warning: Failed to initialize Google Sheets client: {e}")
            _google_sheet = None
    return _google_sheet
    
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

@extend_schema(
    request=RegisterSerializer,
    responses={201: OpenApiResponse(description='User registered successfully. Please verify your email.')},
    description="Register a new user. Sends a verification email."
)
class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [] 
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Invalidate old tokens
            EmailVerificationToken.objects.filter(user=user, is_used=False).update(is_used=True)
            token = EmailVerificationToken.generate_token()
            EmailVerificationToken.objects.create(user=user, token=token)
            send_mail(
                subject='Verify your email',
                message=f'Your email verification code is: {token}',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@deckoviz.com',
                recipient_list=[user.email],
                fail_silently=True,
            )
            return Response({"message": "User registered successfully. Please verify your email."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
     
class UserView(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return super().get_queryset().filter(id=self.request.user.id)
    
class AddressView(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # use manager directly since QuerySet lacks for_user
        return Address.objects.for_user(self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NewsLetterSubscriberView(generics.CreateAPIView):
    queryset = NewsLetterSubscriber.objects.all()
    serializer_class = NewsLetterSubscriberSerializer
    permission_classes = [AllowAny]
 
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def perform_create(self,serializer):
        instance = serializer.save()
        # Try to add to Google Sheet, but don't fail if it doesn't work
        google_sheet = get_google_sheet()
        if google_sheet:
            google_sheet.append_to_google_sheet(instance.name,instance.email)

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Initiates the Google OAuth2 login process
        """
        strategy = load_strategy(request)
        try:
            # Specify the redirect URI explicitly
            redirect_uri = 'http://localhost:8000/auth/login/google/callback/'
            backend = load_backend(strategy=strategy, name='google-oauth2', redirect_uri=redirect_uri)
        except MissingBackend:
            return Response({"error": "Google OAuth2 backend not configured"}, status=status.HTTP_400_BAD_REQUEST)
            
        auth_url = backend.auth_url()
        return Response({"auth_url": auth_url})

class GoogleCallbackView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Handles the Google OAuth2 callback
        """
        code = request.GET.get('code')
        if not code:
            return Response({"error": "No authorization code provided"}, status=status.HTTP_400_BAD_REQUEST)
            
        strategy = load_strategy(request)
        try:
            # Use the same redirect URI as in the login view
            redirect_uri = 'http://localhost:8000/auth/login/google/callback/'
            backend = load_backend(strategy=strategy, name='google-oauth2', redirect_uri=redirect_uri)
        except MissingBackend:
            return Response({"error": "Google OAuth2 backend not configured"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # Complete the authentication process
            user = backend.complete(request=request)
            
            # Create JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            # Return tokens in response
            return Response({
                "access_token": access_token,
                "refresh_token": str(refresh),
                "user": UserSerializer(user).data
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def get_object(self):
        # Always return the profile for the current user, create if not exists
        obj, created = UserProfile.objects.get_or_create(user=self.request.user)
        return obj

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@extend_schema(
    request=ForgotPasswordSerializer,
    responses={200: OpenApiResponse(description='If the email exists, a reset link will be sent.')},
    description="Request a password reset. Sends a reset code to the user's email if they exist."
)
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].lower()
        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({'detail': 'If the email exists, a reset link will be sent.'}, status=status.HTTP_200_OK)
        # Invalidate old tokens
        PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
        token = PasswordResetToken.generate_token()
        PasswordResetToken.objects.create(user=user, token=token)
        # Send email
        send_mail(
            subject='Password Reset Request',
            message=f'Your password reset code is: {token}',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@deckoviz.com',
            recipient_list=[user.email],
            fail_silently=True,
        )
        return Response({'detail': 'If the email exists, a reset link will be sent.'}, status=status.HTTP_200_OK)

@extend_schema(
    request=ResetPasswordSerializer,
    responses={200: OpenApiResponse(description='Password has been reset successfully.')},
    description="Reset password using the code sent to the user's email."
)
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']
        try:
            reset_token = PasswordResetToken.objects.get(token=token, is_used=False)
        except PasswordResetToken.DoesNotExist:
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
        if reset_token.is_expired():
            reset_token.is_used = True
            reset_token.save()
            return Response({'detail': 'Token has expired.'}, status=status.HTTP_400_BAD_REQUEST)
        user = reset_token.user
        user.set_password(password)
        user.save()
        reset_token.is_used = True
        reset_token.save()
        return Response({'detail': 'Password has been reset successfully.'}, status=status.HTTP_200_OK) 

@extend_schema(
    request=EmailVerificationSerializer,
    responses={200: OpenApiResponse(description='Email verified successfully. You can now log in.')},
    description="Verify user email using the code sent to their email."
)
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        try:
            verification_token = EmailVerificationToken.objects.get(token=token, is_used=False)
        except EmailVerificationToken.DoesNotExist:
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
        if verification_token.is_expired():
            verification_token.is_used = True
            verification_token.save()
            return Response({'detail': 'Token has expired.'}, status=status.HTTP_400_BAD_REQUEST)
        user = verification_token.user
        user.email_verified = True
        user.is_active = True
        user.save()
        verification_token.is_used = True
        verification_token.save()
        return Response({'detail': 'Email verified successfully. You can now log in.'}, status=status.HTTP_200_OK) 

@extend_schema(
    request=ResendVerificationSerializer,
    responses={200: OpenApiResponse(description='If the email exists and is not verified, a new verification email has been sent.')},
    description="Resend the email verification code to the user if not yet verified."
)
class ResendVerificationView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].lower()
        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=email)
            if not user.email_verified:
                # Invalidate old tokens
                EmailVerificationToken.objects.filter(user=user, is_used=False).update(is_used=True)
                token = EmailVerificationToken.generate_token()
                EmailVerificationToken.objects.create(user=user, token=token)
                send_mail(
                    subject='Verify your email',
                    message=f'Your email verification code is: {token}',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@deckoviz.com',
                    recipient_list=[user.email],
                    fail_silently=True,
                )
        except User.DoesNotExist:
            pass  # Always return the same message
        return Response({'detail': 'If the email exists and is not verified, a new verification email has been sent.'}, status=status.HTTP_200_OK) 