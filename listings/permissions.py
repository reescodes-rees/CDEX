from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Assumes the model instance has an 'owner' or 'lister' attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the snippet.
        # Check for 'owner' (e.g. Card) or 'lister' (e.g. Listing)
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        if hasattr(obj, 'lister'):
            return obj.lister == request.user
        return False

class IsBidderOrListingOwner(permissions.BasePermission):
    """
    Custom permission for bids:
    - Bidder can see their own bids.
    - Listing owner can see all bids on their listing.
    - Others cannot see bids (unless further refined).
    """
    def has_object_permission(self, request, view, obj):
        # obj is a Bid instance
        if request.method in permissions.SAFE_METHODS: # GET, HEAD, OPTIONS
            return obj.bidder == request.user or obj.listing.lister == request.user
        # No one should typically edit/delete bids directly via API, handled by system.
        return False
