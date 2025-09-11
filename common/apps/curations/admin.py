from django.contrib import admin
from .models import CuratedImages, CuratedCollections


@admin.register(CuratedImages)
class CuratedImagesAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_active', 'created_by', 'created_at')
    list_filter = ('is_active', 'created_at')
    filter_horizontal = ('images',)
    readonly_fields = ('created_by', 'created_at', 'updated_at')
    exclude = ('created_by',)  # Hide created_by from form
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Show only the single curation or create one if it doesn't exist
        if not qs.exists():
            self.model.objects.create(created_by=request.user)
        return qs
    
    def has_add_permission(self, request):
        # Only allow adding if no curation exists
        return not self.model.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of the main curation
        return False
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'images':
            from common.apps.gallery.models import Image
            kwargs["queryset"] = Image.objects.filter(is_active=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by when creating
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CuratedCollections)
class CuratedCollectionsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_active', 'created_by', 'created_at')
    list_filter = ('is_active', 'created_at')
    filter_horizontal = ('collections',)
    readonly_fields = ('created_by', 'created_at', 'updated_at')
    exclude = ('created_by',)  # Hide created_by from form
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Show only the single curation or create one if it doesn't exist
        if not qs.exists():
            self.model.objects.create(created_by=request.user)
        return qs
    
    def has_add_permission(self, request):
        # Only allow adding if no curation exists
        return not self.model.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of the main curation
        return False
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'collections':
            from common.apps.gallery.models import Collection
            kwargs["queryset"] = Collection.objects.filter(is_active=True, view='public')
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by when creating
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
