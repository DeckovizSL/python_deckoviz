from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DetailView, FormView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, logout
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
import uuid
from django.db import transaction
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator

from common.apps.gallery.models import Collection, Image, CollectionImage, Audio
from .forms import (
    CollectionForm, ImageUploadForm, CollectionImageForm, 
    CollectionWithImagesForm, LoginForm, RegistrationForm
)


class DashboardHomeView(LoginRequiredMixin, ListView):
    """
    Dashboard home view that displays user's collections
    """
    model = Collection
    template_name = 'dashboard/home.html'
    context_object_name = 'collections'
    
    def get_queryset(self):
        # Only show collections belonging to the logged-in user
        return Collection.objects.filter(user=self.request.user, is_active=True)


class CollectionListView(LoginRequiredMixin, ListView):
    """
    View to list all collections for the logged-in user
    """
    model = Collection
    template_name = 'dashboard/collection_list.html'
    context_object_name = 'collections'
    
    def get_queryset(self):
        return Collection.objects.filter(user=self.request.user, is_active=True)


class CollectionCreateView(LoginRequiredMixin, CreateView):
    """
    View to create a new collection
    """
    model = Collection
    form_class = CollectionForm
    template_name = 'dashboard/collection_form.html'
    success_url = reverse_lazy('dashboard:collection-list')
    
    def form_valid(self, form):
        # Set the current user as the owner of the collection
        form.instance.user = self.request.user
        messages.success(self.request, 'Collection created successfully!')
        return super().form_valid(form)


class CollectionUpdateView(LoginRequiredMixin, UpdateView):
    """
    View to update an existing collection
    """
    model = Collection
    form_class = CollectionForm
    template_name = 'dashboard/collection_form.html'
    success_url = reverse_lazy('dashboard:collection-list')
    
    def get_queryset(self):
        # Ensure users can only edit their own collections
        return Collection.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Collection updated successfully!')
        return super().form_valid(form)


class CollectionDetailView(LoginRequiredMixin, DetailView):
    """
    View to show collection details including all images
    """
    model = Collection
    template_name = 'dashboard/collection_detail.html'
    context_object_name = 'collection'
    
    def get_queryset(self):
        # Ensure users can only view their own collections
        return Collection.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get collection images in order
        context['collection_images'] = CollectionImage.objects.filter(
            collection=self.object
        ).order_by('order')
        return context


class AddImagesToCollectionView(LoginRequiredMixin, DetailView):
    """
    View to add images to a collection using drag and drop
    """
    model = Collection
    template_name = 'dashboard/add_images.html'
    context_object_name = 'collection'
    
    def get_queryset(self):
        # Ensure users can only modify their own collections
        return Collection.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ImageUploadForm()
        context['existing_images'] = Image.objects.filter(
            uploaded_by=self.request.user,
            is_active=True
        )
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ImageUploadForm(request.POST, request.FILES)
        
        if form.is_valid() and 'image' in request.FILES:
            # Process the uploaded image
            image_file = request.FILES['image']
            
            # Create new image
            image = Image(
                file=image_file,
                image_id=str(uuid.uuid4()),
                uploaded_by=request.user,
                view=self.object.view  # Inherit view setting from collection
            )
            image.save()
            
            # Add to collection with next order
            next_order = CollectionImage.objects.filter(collection=self.object).count()
            CollectionImage.objects.create(
                collection=self.object,
                image=image,
                order=next_order,
                view=self.object.view
            )
            
            messages.success(request, 'Image added to collection successfully!')
            return HttpResponseRedirect(reverse('dashboard:collection-detail', kwargs={'pk': self.object.pk}))
        
        return self.render_to_response(self.get_context_data(form=form))


@method_decorator(require_POST, name='dispatch')
class ProcessBulkUploadsView(LoginRequiredMixin, View):
    """
    API view to handle bulk image uploads with AJAX
    """
    def post(self, request, *args, **kwargs):
        collection_id = request.POST.get('collection_id')
        
        try:
            collection = Collection.objects.get(id=collection_id, user=request.user)
        except Collection.DoesNotExist:
            return JsonResponse({'error': 'Collection not found'}, status=404)
        
        # Get the next order number
        next_order = CollectionImage.objects.filter(collection=collection).count()
        
        # Process uploaded images
        image_files = request.FILES.getlist('images[]')
        processed_count = 0
        
        try:
            with transaction.atomic():
                for image_file in image_files:
                    # Create image
                    image = Image(
                        file=image_file,
                        image_id=str(uuid.uuid4()),
                        uploaded_by=request.user,
                        view=collection.view
                    )
                    image.save()
                    
                    # Add to collection
                    CollectionImage.objects.create(
                        collection=collection,
                        image=image,
                        order=next_order + processed_count,
                        view=collection.view
                    )
                    processed_count += 1
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        
        return JsonResponse({
            'success': True,
            'message': f'{processed_count} images added to collection.',
            'redirect_url': reverse('dashboard:collection-detail', kwargs={'pk': collection.id})
        })


class CollectionWithImagesCreateView(LoginRequiredMixin, FormView):
    """
    View to create a collection and upload multiple images in a single form
    """
    template_name = 'dashboard/collection_with_images_form.html'
    form_class = CollectionWithImagesForm
    success_url = reverse_lazy('dashboard:collection-list')
    
    def post(self, request, *args, **kwargs):
        # Check if this is an AJAX request with multiple images
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and 'multiple_images' in request.POST:
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
            else:
                return JsonResponse({'error': 'Form validation failed'}, status=400)
        return super().post(request, *args, **kwargs)
    
    @transaction.atomic
    def form_valid(self, form):
        # Create the collection
        collection = Collection(
            user=self.request.user,
            name=form.cleaned_data['name'],
            view=form.cleaned_data['view'],
            display_time=form.cleaned_data['display_time'],
            music=form.cleaned_data.get('music'),
            music_preference=form.cleaned_data.get('music_preference', '')
        )
        collection.save()
        
        # Handle AJAX request with multiple images
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest' and 'multiple_images' in self.request.POST:
            # Get images from request
            image_files = self.request.FILES.getlist('images[]')
            processed_count = 0
            
            # Process each image
            for i, image_file in enumerate(image_files):
                # Create image
                image = Image(
                    file=image_file,
                    image_id=str(uuid.uuid4()),
                    uploaded_by=self.request.user,
                    view=form.cleaned_data['view']
                )
                image.save()
                
                # Add to collection
                CollectionImage.objects.create(
                    collection=collection,
                    image=image,
                    order=i,
                    view=form.cleaned_data['view']
                )
                processed_count += 1
            
            return JsonResponse({
                'success': True,
                'message': f'Collection "{collection.name}" created with {processed_count} images!',
                'redirect_url': reverse('dashboard:collection-list')
            })
        
        # Process a single image if provided (non-AJAX fallback)
        if 'image' in self.request.FILES:
            image_file = self.request.FILES['image']
            
            # Create image
            image = Image(
                file=image_file,
                image_id=str(uuid.uuid4()),
                uploaded_by=self.request.user,
                view=form.cleaned_data['view']
            )
            image.save()
            
            # Add to collection
            CollectionImage.objects.create(
                collection=collection,
                image=image,
                order=0,
                view=form.cleaned_data['view']
            )
            messages.success(self.request, f'Collection "{collection.name}" created with an image!')
        else:
            messages.success(self.request, f'Collection "{collection.name}" created!')
            
        return HttpResponseRedirect(self.success_url)


# Authentication Views
class LoginView(FormView):
    """
    View for user login
    """
    template_name = 'dashboard/auth/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('dashboard:home')
    
    def form_valid(self, form):
        # Log the user in
        login(self.request, form.user)
        messages.success(self.request, f'Welcome back, {form.user.username}!')
        
        # Redirect to the appropriate page
        next_url = self.request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Login'
        return context


class RegisterView(FormView):
    """
    View for user registration
    """
    template_name = 'dashboard/auth/register.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('dashboard:login')
    
    def form_valid(self, form):
        # Create and save the user
        user = form.save()
        messages.success(self.request, 'Account created successfully! You can now log in.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Register'
        return context


class LogoutView(View):
    """
    View for user logout
    """
    def get(self, request):
        logout(request)
        messages.success(request, 'You have been logged out.')
        return redirect('dashboard:login')
