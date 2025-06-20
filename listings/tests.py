from django.contrib.auth import get_user_model
from django.urls import reverse, reverse_lazy
from django.test import TestCase, Client # For web view tests
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase, APIClient # For API tests
from rest_framework import status

from .models import Game, Card, Listing, Bid
from .forms import ListingCreateEditForm, BidForm
from .forms import UserCardForm

User = get_user_model()

# Helper function to create users
def create_user(username_suffix, email_suffix, password='password123'):
    return User.objects.create_user(
        username=f'testuser_{username_suffix}',
        email=f'test_{email_suffix}@example.com',
        password=password
    )

class GameModelTests(TestCase):
    def test_game_creation_and_slug(self):
        game = Game.objects.create(name="Pokémon Trading Card Game")
        self.assertEqual(str(game), "Pokémon Trading Card Game")
        self.assertEqual(game.slug, "pokemon-trading-card-game")

class CardModelTests(TestCase):
    def setUp(self):
        self.user = create_user("cardowner", "cardowner")
        self.game = Game.objects.create(name="Test Game")

    def test_card_creation(self):
        card = Card.objects.create(
            owner=self.user,
            game=self.game,
            card_name="Test Card",
            condition='NM'
        )
        self.assertEqual(str(card), f"Test Card ({self.user.username})")
        self.assertEqual(card.owner, self.user)
        self.assertEqual(card.game, self.game)

class ListingModelTests(TestCase):
    def setUp(self):
        self.user = create_user("lister", "lister")
        self.card_owner = create_user("cardholder", "cardholder")
        self.game = Game.objects.create(name="Card Game X")
        self.card = Card.objects.create(owner=self.card_owner, game=self.game, card_name="Mega Card")

    def test_listing_creation(self):
        listing = Listing.objects.create(
            lister=self.user,
            card_for_listing=self.card, # Note: In real scenario, lister should own the card. Test this in forms/views.
            listing_type='SALE',
            price=100.00,
            seller_location_city="Testville"
        )
        self.assertEqual(str(listing), f"For Sale of Mega Card by {self.user.username}")
        self.assertEqual(listing.status, 'ACTIVE')

class BidModelTests(TestCase):
    def setUp(self):
        self.lister = create_user("auctionlister", "auctionlister")
        self.bidder = create_user("bidder", "bidder")
        self.card = Card.objects.create(owner=self.lister, card_name="Auctionable Card")
        self.auction = Listing.objects.create(
            lister=self.lister,
            card_for_listing=self.card,
            listing_type='AUCTION',
            auction_start_price=10.00,
            auction_end_datetime=timezone.now() + timedelta(days=1)
        )

    def test_bid_creation(self):
        bid = Bid.objects.create(listing=self.auction, bidder=self.bidder, amount=15.00)
        self.assertEqual(str(bid), f"Bid of 15.0 by {self.bidder.username} on Auctionable Card") # Changed 15.00 to 15.0


# --- API Tests ---
class GameAPITests(APITestCase):
    def setUp(self):
        self.game1 = Game.objects.create(name="Alpha Game", slug="alpha-game")
        self.game2 = Game.objects.create(name="Beta Game", slug="beta-game")
        self.list_url = reverse('game-list') # Assuming router basename 'game'

    def test_list_games(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data), 2) # Check for pagination

    def test_retrieve_game(self):
        detail_url = reverse('game-detail', kwargs={'slug': self.game1.slug})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.game1.name)


class UserCardAPITests(APITestCase):
    def setUp(self):
        self.user = create_user("cardapi", "cardapi", password="aVeryComplexP@ssw0rd!") # Use complex password
        self.client = APIClient()
        # Manually create an auth token or use session auth if dj-rest-auth setup provides it easily
        # For dj-rest-auth with JWT cookie auth, login should set the cookie
        login_payload = {'email': self.user.email, 'password': "aVeryComplexP@ssw0rd!"}
        login_response = self.client.post(reverse('rest_login'), login_payload, format='json')
        if login_response.status_code != status.HTTP_200_OK:
             print(f"API Test Login Error for UserCardAPITests: {login_response.data}")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "API Test User Login Failed")

        self.game = Game.objects.create(name="Collectible Game")
        self.list_create_url = reverse('usercard-list')
        self.card_data = {
            'game': self.game.pk,
            'card_name': 'Awesome Card',
            'condition': 'M',
        }

    def test_create_user_card(self):
        response = self.client.post(self.list_create_url, self.card_data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print("Create Card API Error:", response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Card.objects.count(), 1)
        self.assertEqual(Card.objects.first().owner, self.user)

    def test_list_user_cards(self):
        Card.objects.create(owner=self.user, game=self.game, card_name="Card 1")
        Card.objects.create(owner=self.user, game=self.game, card_name="Card 2")
        other_user = create_user("other", "other", password="aVeryComplexP@ssw0rd!")
        Card.objects.create(owner=other_user, game=self.game, card_name="Other User Card")

        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data), 2)


class ListingAPITests(APITestCase):
    def setUp(self):
        self.user1 = create_user("listinguser1", "listinguser1", password="aVeryComplexP@ssw0rd!")
        self.user2 = create_user("listinguser2", "listinguser2", password="aVeryComplexP@ssw0rd!")
        self.game = Game.objects.create(name="Popular Game")
        self.card_user1 = Card.objects.create(owner=self.user1, game=self.game, card_name="User1's Card", condition="NM")

        self.client = APIClient()
        login_payload_user1 = {'email': self.user1.email, 'password': "aVeryComplexP@ssw0rd!"}
        login_response_user1 = self.client.post(reverse('rest_login'), login_payload_user1, format='json')
        self.assertEqual(login_response_user1.status_code, status.HTTP_200_OK, "API Test User1 Login Failed")

        self.list_create_url = reverse('listing-list')
        self.listing_data = {
            'card_for_listing': self.card_user1.pk,
            'listing_type': 'SALE',
            'price': 50.00,
            'seller_location_city': 'Cityville',
            'shipping_policy_description': 'Ships fast!',
        }

    def test_create_listing(self):
        response = self.client.post(self.list_create_url, self.listing_data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print("Create Listing API Error:", response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Listing.objects.count(), 1)
        self.assertEqual(Listing.objects.first().lister, self.user1)

    def test_list_active_listings(self):
        Listing.objects.create(lister=self.user1, card_for_listing=self.card_user1, listing_type='SALE', price=10.00)
        card_user2 = Card.objects.create(owner=self.user2, game=self.game, card_name="User2 Card")
        Listing.objects.create(lister=self.user2, card_for_listing=card_user2, listing_type='TRADE')

        unauth_client = APIClient()
        response = unauth_client.get(self.list_create_url + "?status=ACTIVE")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data), 2)

    def test_update_own_listing(self):
        listing = Listing.objects.create(lister=self.user1, card_for_listing=self.card_user1, listing_type='SALE', price=20.00)
        detail_url = reverse('listing-detail', kwargs={'pk': listing.pk})
        updated_data = {'price': 25.00, 'listing_description': 'Price updated!'}

        response = self.client.patch(detail_url, updated_data, format='json')
        if response.status_code != status.HTTP_200_OK:
            print("Update Listing API Error:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listing.refresh_from_db()
        self.assertEqual(listing.price, 25.00)

    def test_cannot_update_others_listing(self):
        card_user2_other = Card.objects.create(owner=self.user2, game=self.game, card_name="User2 Card 2")
        other_user_listing = Listing.objects.create(lister=self.user2, card_for_listing=card_user2_other, listing_type='SALE', price=30.00)
        detail_url = reverse('listing-detail', kwargs={'pk': other_user_listing.pk})

        response = self.client.patch(detail_url, {'price': 35.00}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_place_bid_api(self):
        card_for_auction = Card.objects.create(owner=self.user2, game=self.game, card_name="Auction Card")
        auction_listing = Listing.objects.create(
            lister=self.user2,
            card_for_listing=card_for_auction,
            listing_type='AUCTION',
            auction_start_price=10.00,
            auction_bid_increment=1.00,
            auction_end_datetime=timezone.now() + timedelta(days=2)
        )
        bid_url = reverse('listing-place-bid', kwargs={'pk': auction_listing.pk})
        bid_data = {'amount': 11.00}

        response = self.client.post(bid_url, bid_data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print("Place Bid API Error:", response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        auction_listing.refresh_from_db()
        self.assertEqual(auction_listing.current_highest_bid, 11.00)
        self.assertEqual(auction_listing.current_high_bidder, self.user1)


# --- Form Tests ---
class ListingFormTests(TestCase):
    def setUp(self):
        self.user = create_user("formuser", "formuser")
        self.game = Game.objects.create(name="Game For Forms")
        self.card1 = Card.objects.create(owner=self.user, game=self.game, card_name="Form Card 1")
        self.card2 = Card.objects.create(owner=self.user, game=self.game, card_name="Form Card 2")

    def test_listing_create_form_valid(self):
        form_data = {
            'card_for_listing': self.card1.pk,
            'listing_type': 'SALE',
            'price': 10.00,
            'seller_location_city': 'Formville',
            'shipping_policy_description': 'Test shipping',
            # Add dummy auction fields to prevent validation error for non-AUCTION types before clean()
            'auction_start_price': None, # Or some default valid value if model requires non-null
            'auction_bid_increment': 1.00, # Model default
            'auction_end_datetime': timezone.now() + timedelta(days=30) # Dummy future date
        }
        form = ListingCreateEditForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid(), msg=f"Form errors: {form.errors.as_json()}")

    def test_listing_create_form_card_queryset(self):
        form_user = create_user("form_owner", "form_owner")
        Card.objects.create(owner=form_user, card_name="Owned Card")
        other_user_card_owner = create_user("other_owner", "other_owner") # Renamed variable
        Card.objects.create(owner=other_user_card_owner, card_name="Not Owned Card")

        form = ListingCreateEditForm(user=form_user)
        self.assertEqual(form.fields['card_for_listing'].queryset.count(), 1)
        self.assertEqual(form.fields['card_for_listing'].queryset.first().card_name, "Owned Card")


# --- Web View Tests (Django Client) ---
class ListingWebViewTests(TestCase):
    def setUp(self):
        self.user = create_user("webuser", "webuser", password="aVeryComplexP@ssw0rd!")
        self.game = Game.objects.create(name="Web Game")
        self.card = Card.objects.create(owner=self.user, game=self.game, card_name="Web Card")
        self.listing = Listing.objects.create(lister=self.user, card_for_listing=self.card, listing_type='SALE', price=5.00)

        self.client = Client()
        self.client.login(email=self.user.email, password="aVeryComplexP@ssw0rd!")

        self.list_page_url = reverse('listings:listing-list')
        self.create_page_url = reverse('listings:listing-create')
        self.detail_page_url = reverse('listings:listing-detail', kwargs={'pk': self.listing.pk})
        self.edit_page_url = reverse('listings:listing-edit', kwargs={'pk': self.listing.pk})

    def test_listing_list_view(self):
        response = self.client.get(self.list_page_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.listing.card_for_listing.card_name)
        self.assertTemplateUsed(response, 'listings/listing_list.html')

    def test_listing_detail_view(self):
        response = self.client.get(self.detail_page_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.listing.card_for_listing.card_name)
        self.assertTemplateUsed(response, 'listings/listing_detail.html')

    def test_listing_create_view_get(self):
        response = self.client.get(self.create_page_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'listings/listing_form.html')

    def test_listing_create_view_post(self):
        new_card = Card.objects.create(owner=self.user, game=self.game, card_name="Newly Created Card for Listing")
        form_data = {
            'card_for_listing': new_card.pk,
            'listing_type': 'SALE',
            'price': 123.45,
            'seller_location_city': 'New City',
            'shipping_policy_description': 'Ships new items',
            # Add dummy auction fields for SALE type
            'auction_start_price': '', # Changed None to empty string
            'auction_bid_increment': 1.00,
            'auction_end_datetime': (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%dT%H:%M'),
        }
        response = self.client.post(self.create_page_url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Listing.objects.filter(card_for_listing__card_name="Newly Created Card for Listing").exists())
        self.assertContains(response, "Listing created successfully!")


    def test_listing_edit_view_permissions(self):
        other_user = create_user("otherweb", "otherweb", password="aVeryComplexP@ssw0rd!")
        other_client = Client()
        other_client.login(email=other_user.email, password="aVeryComplexP@ssw0rd!")

        response = other_client.get(self.edit_page_url)
        self.assertEqual(response.status_code, 403)

        response_owner = self.client.get(self.edit_page_url)
        self.assertEqual(response_owner.status_code, 200)


    def test_bid_submission_on_detail_page(self):
        auction_lister = create_user("auctionpage_lister", "auctionpage_lister")
        auction_card = Card.objects.create(owner=auction_lister, card_name="AuctionPageCard")
        auction = Listing.objects.create(
            lister=auction_lister,
            card_for_listing=auction_card,
            listing_type='AUCTION',
            auction_start_price=5.00,
            auction_bid_increment=1.00,
            auction_end_datetime=timezone.now() + timedelta(days=1)
        )
        auction_detail_url = reverse('listings:listing-detail', kwargs={'pk': auction.pk})

        bid_data = {'amount': 6.00}
        response = self.client.post(auction_detail_url, bid_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bid of $6.0 placed successfully!") # Changed $6.00 to $6.0
        auction.refresh_from_db()
        self.assertEqual(auction.current_highest_bid, 6.00) # Keep as 6.00 for Decimal comparison if needed, or use Decimal('6.0')
        self.assertEqual(auction.current_high_bidder, self.user)



# --- User Card Collection Form Tests ---
class UserCardFormTests(TestCase):
    def setUp(self):
        self.user = create_user("cardformuser", "cardformuser")
        self.game = Game.objects.create(name="Game for Card Forms")
        self.valid_data = {
            'game': self.game.pk,
            'card_name': 'Valid Test Card',
            'condition': 'NM',
            'public_description': 'A very nice card.',
            'is_graded': True,
            'grader': 'PSA',
            'grade': '9',
            # image fields are not required by default in form
        }

    def test_user_card_form_valid_data(self):
        form = UserCardForm(data=self.valid_data)
        if not form.is_valid():
            print(f"UserCardForm (valid data) errors: {form.errors.as_json()}")
        self.assertTrue(form.is_valid())

    def test_user_card_form_missing_required_fields(self):
        invalid_data = self.valid_data.copy()
        del invalid_data['card_name'] # card_name is required
        form = UserCardForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('card_name', form.errors)

    def test_user_card_form_grading_logic_graded_no_details(self):
        # is_graded is True, but no grader/grade provided
        invalid_data = self.valid_data.copy()
        invalid_data['is_graded'] = True
        del invalid_data['grader']
        del invalid_data['grade']
        form = UserCardForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('grader', form.errors)
        self.assertIn('grade', form.errors)

    def test_user_card_form_grading_logic_not_graded_clears_details(self):
        # is_graded is False, but grader/grade provided (should be cleared)
        data = self.valid_data.copy()
        data['is_graded'] = False
        data['grader'] = 'PSA' # This should be cleared by the form's clean method
        data['grade'] = '9'   # This should be cleared
        form = UserCardForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Form errors: {form.errors.as_json()}")
        # Check that grader and grade are cleared in cleaned_data
        self.assertIsNone(form.cleaned_data.get('grader'))
        self.assertIsNone(form.cleaned_data.get('grade'))
        self.assertEqual(form.cleaned_data.get('certification_number'), '')


# --- User Card Collection Web View Tests ---
class UserCardCollectionViewTests(TestCase):
    def setUp(self):
        self.user = create_user("collection_user", "collection_user", password="aVeryComplexP@ssw0rd!")
        self.other_user = create_user("other_collection", "other_collection", password="aVeryComplexP@ssw0rd!")
        self.game = Game.objects.create(name="Collection Game")

        self.card1_user = Card.objects.create(owner=self.user, game=self.game, card_name="My Card 1", condition="M")
        self.card2_user = Card.objects.create(owner=self.user, game=self.game, card_name="My Card 2", condition="LP")
        self.card_other_user = Card.objects.create(owner=self.other_user, game=self.game, card_name="Other's Card", condition="NM")

        self.client = Client()
        self.client.login(email=self.user.email, password="aVeryComplexP@ssw0rd!")

        self.list_url = reverse('listings:my-card-list')
        self.create_url = reverse('listings:my-card-create')
        self.detail_url_user_card1 = reverse('listings:my-card-detail', kwargs={'pk': self.card1_user.pk})
        self.edit_url_user_card1 = reverse('listings:my-card-edit', kwargs={'pk': self.card1_user.pk})
        self.delete_url_user_card1 = reverse('listings:my-card-delete', kwargs={'pk': self.card1_user.pk})
        self.detail_url_other_user_card = reverse('listings:my-card-detail', kwargs={'pk': self.card_other_user.pk})


    def test_my_card_list_view_authenticated(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'listings/my_collection/my_card_list.html')
        self.assertContains(response, self.card1_user.card_name)
        self.assertContains(response, self.card2_user.card_name)
        self.assertNotContains(response, self.card_other_user.card_name) # Should only show user's cards

    def test_my_card_list_view_unauthenticated_redirects(self):
        unauth_client = Client()
        response = unauth_client.get(self.list_url)
        self.assertEqual(response.status_code, 302) # Redirect to login
        self.assertTrue(reverse('account_login') in response.url)

    def test_my_card_create_view_get(self):
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], UserCardForm)
        self.assertTemplateUsed(response, 'listings/my_collection/my_card_form.html')

    def test_my_card_create_view_post_success(self):
        card_count_before = Card.objects.filter(owner=self.user).count()
        form_data = {
            'game': self.game.pk,
            'card_name': 'New Awesome Card',
            'condition': 'NM',
            'public_description': 'Just pulled!',
            'is_graded': False
            # Ensure all other non-required fields are handled by form if not provided
        }
        response = self.client.post(self.create_url, form_data, follow=True)
        if response.status_code != 200 or not response.redirect_chain: # Check for form errors if not redirecting as expected
             if hasattr(response, 'context') and response.context and 'form' in response.context:
                 print(f"Create Card View POST errors: {response.context['form'].errors.as_json()}")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.redirect_chain) # Ensure it redirected
        self.assertEqual(Card.objects.filter(owner=self.user).count(), card_count_before + 1)
        new_card = Card.objects.get(card_name='New Awesome Card', owner=self.user)
        self.assertRedirects(response, reverse('listings:my-card-detail', kwargs={'pk': new_card.pk}))
        self.assertContains(response, "Card &#x27;New Awesome Card&#x27; added to your collection!")


    def test_my_card_detail_view_owner_access(self):
        response = self.client.get(self.detail_url_user_card1)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.card1_user.card_name)
        self.assertTemplateUsed(response, 'listings/my_collection/my_card_detail.html')

    def test_my_card_detail_view_other_user_no_access(self):
        response = self.client.get(self.detail_url_other_user_card)
        self.assertEqual(response.status_code, 403)

    def test_my_card_update_view_owner_access_and_success(self):
        response_get = self.client.get(self.edit_url_user_card1)
        self.assertEqual(response_get.status_code, 200)
        self.assertTemplateUsed(response_get, 'listings/my_collection/my_card_form.html')

        updated_name = "My Card 1 Updated"
        # Minimal data for update, assuming other fields are optional or retain old values
        form_data_update = {
            'game': self.card1_user.game.pk, # Required by form
            'card_name': updated_name,       # Required by form
            'condition': self.card1_user.condition, # Required by form
            'is_graded': self.card1_user.is_graded, # Required by form
            # Other fields from UserCardForm are not strictly required by model but form might need them
            # if they don't have defaults or blank=True in model and form doesn't override.
            # The UserCardForm makes many fields not required.
            'public_description': 'Updated description.'
        }
        response_post = self.client.post(self.edit_url_user_card1, form_data_update, follow=True)
        if response_post.status_code != 200 or not response_post.redirect_chain:
            if hasattr(response_post, 'context') and response_post.context and 'form' in response_post.context:
                 print(f"Update Card View POST errors: {response_post.context['form'].errors.as_json()}")

        self.assertEqual(response_post.status_code, 200)
        self.assertTrue(response_post.redirect_chain)
        self.card1_user.refresh_from_db()
        self.assertEqual(self.card1_user.card_name, updated_name)
        self.assertRedirects(response_post, self.detail_url_user_card1)
        self.assertContains(response_post, f"Card &#x27;{updated_name}&#x27; updated successfully!")


    def test_my_card_delete_view_owner_access_and_success(self):
        response_get = self.client.get(self.delete_url_user_card1)
        self.assertEqual(response_get.status_code, 200)
        self.assertTemplateUsed(response_get, 'listings/my_collection/my_card_confirm_delete.html')

        card_count_before = Card.objects.filter(owner=self.user).count()
        response_post = self.client.post(self.delete_url_user_card1, follow=True)
        self.assertEqual(response_post.status_code, 200)
        self.assertTrue(response_post.redirect_chain)
        self.assertEqual(Card.objects.filter(owner=self.user).count(), card_count_before - 1)
        self.assertRedirects(response_post, self.list_url)
        self.assertContains(response_post, f"Card &#x27;{self.card1_user.card_name}&#x27; deleted from your collection.")

    def test_my_card_delete_view_prevent_if_active_listing(self):
        Listing.objects.create(lister=self.user, card_for_listing=self.card1_user, listing_type='SALE', price=10.00, status='ACTIVE')

        response_post = self.client.post(self.delete_url_user_card1, follow=True)
        self.assertEqual(response_post.status_code, 200)
        self.assertTrue(response_post.redirect_chain) # Should redirect
        self.assertTrue(Card.objects.filter(pk=self.card1_user.pk).exists())
        self.assertContains(response_post, f"Cannot delete &#x27;{self.card1_user.card_name}&#x27; as it is part of one or more active listings.")
        self.assertRedirects(response_post, self.detail_url_user_card1)
