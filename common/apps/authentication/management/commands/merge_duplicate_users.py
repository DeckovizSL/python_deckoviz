from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models.functions import Lower
from django.db import transaction
from django.db import models

User = get_user_model()

class Command(BaseCommand):
    help = 'Finds and merges duplicate user accounts based on case-insensitive email addresses.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Starting duplicate user check...")

        # Find all emails that have duplicates (case-insensitive)
        duplicate_emails = (
            User.objects.values('email')
            .annotate(email_lower=Lower('email'))
            .values('email_lower')
            .annotate(count=models.Count('id'))
            .filter(count__gt=1)
            .values_list('email_lower', flat=True)
        )

        if not duplicate_emails.exists():
            self.stdout.write(self.style.SUCCESS("No duplicate email accounts found."))
            return

        self.stdout.write(f"Found {len(duplicate_emails)} email(s) with duplicate accounts.")

        for email_lower in duplicate_emails:
            self.stdout.write(f"\nProcessing duplicates for: {email_lower}")
            
            # Get all user accounts for this email (case-insensitive)
            users = User.objects.filter(email__iexact=email_lower).order_by('date_joined')

            # The first user registered is the primary account
            primary_user = users.first()
            self.stdout.write(f"  Primary account: {primary_user.email} (ID: {primary_user.id})")

            # These are the accounts to be merged and deleted
            duplicate_users = users[1:]

            for dup_user in duplicate_users:
                self.stdout.write(f"  Merging duplicate: {dup_user.email} (ID: {dup_user.id})")

                # Re-associate related objects from the duplicate to the primary user
                # This needs to be done for ALL related models.
                # Example for a 'Collection' model. You must add all other models.
                #
                # from common.apps.gallery.models import Collection
                # Collection.objects.filter(user=dup_user).update(user=primary_user)
                #
                # You must do this for every model that has a ForeignKey to User.
                # Common examples include: UserProfile, Address, Order, etc.

                # After re-associating all related objects, delete the duplicate user
                dup_user.delete()

            # Ensure the primary user has a lowercase email
            if primary_user.email != email_lower:
                primary_user.email = email_lower
                primary_user.save()
            
            self.stdout.write(f"  Finished merging for {email_lower}.")

        self.stdout.write(self.style.SUCCESS("\nSuccessfully merged all duplicate accounts.")) 