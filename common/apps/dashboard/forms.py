from django import forms
from common.apps.gallery.models import Collection, Image, CollectionImage
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
import uuid

User = get_user_model()

class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['name', 'music', 'view', 'display_time', 'music_preference']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'music': forms.FileInput(attrs={'class': 'form-control'}),
            'view': forms.Select(attrs={'class': 'form-control'}),
            'display_time': forms.NumberInput(attrs={'class': 'form-control'}),
            'music_preference': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ImageUploadForm(forms.Form):
    # Using a normal FileField - we'll handle multiple uploads in the view
    image = forms.ImageField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        label='Select Image',
        required=False
    )
    
class CollectionImageForm(forms.ModelForm):
    class Meta:
        model = CollectionImage
        fields = ['image', 'order', 'view']
        widgets = {
            'image': forms.Select(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'view': forms.Select(attrs={'class': 'form-control'}),
        }
        
class CollectionWithImagesForm(forms.Form):
    name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    # Using a single file field - we'll handle multiple uploads in the view
    image = forms.ImageField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False
    )
    view = forms.ChoiceField(
        choices=[('private', 'Private'), ('public', 'Public')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    display_time = forms.IntegerField(
        initial=10,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    music = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False
    )
    music_preference = forms.CharField(
        max_length=255, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class LoginForm(forms.Form):
    """
    Form for user login
    """
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
            # Try to authenticate the user
            self.user = authenticate(username=email, password=password)
            if self.user is None:
                raise ValidationError('Invalid email or password')
            if not self.user.is_active:
                raise ValidationError('This account is inactive')
        return cleaned_data


class RegistrationForm(UserCreationForm):
    """
    Form for user registration
    """
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap classes to password fields
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('A user with this email already exists')
        return email
