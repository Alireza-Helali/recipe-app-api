import tempfile
from PIL import Image
import os

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Recipe, Tag, Ingredient
from recpie.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """Return url for recipe image upload"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def sample_tag(user, name='italian'):
    """Create and return sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='vanilla'):
    """Create and return sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **kwargs):
    """Create and return sample recipe"""
    payload = {
        'title': 'pasta alfredo',
        'time': 5,
        'price': 5.00
    }
    payload.update(kwargs)
    return Recipe.objects.create(user=user, **payload)


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


class PublicRecipeApiTest(TestCase):
    """Test unauthenticated recipe api access"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required"""
        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTest(TestCase):
    """Test unauthenticated recipe api access"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create(email='test@test.com', password='test-pass')
        self.client.force_authenticate(self.user)

    def test_retrieve_recipe(self):
        """"Test retrieving a list of recipes"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)
        res = self.client.get(RECIPE_URL)

        recipe = Recipe.objects.all()
        serializer = RecipeSerializer(recipe, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test retrieving recipes for user"""
        sample_recipe(user=self.user)
        user2 = get_user_model().objects.create(email='test2@test.com', password='test-pass')
        sample_recipe(user=user2)
        recipe = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipe, many=True)

        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing recipe detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tag.add(sample_tag(user=self.user))
        recipe.ingredient.add(sample_ingredient(user=self.user))

        res = self.client.get(detail_url(recipe.pk))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating a recipe"""
        payload = {
            'title': 'chocolate cake',
            'time': 10,
            'price': 15.00
        }
        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tag(self):
        """Test creating recipe with tags"""
        tag1 = sample_tag(user=self.user, name='italian')
        tag2 = sample_tag(user=self.user, name='pasta')
        payload = {
            'title': 'pasta alfredo',
            'time': 10,
            'price': 15.00,
            'tag': [tag2.id, tag1.id]
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tag.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredient(self):
        """Test creating recipe with ingredient"""
        ingredient1 = sample_ingredient(user=self.user, name="salt")
        ingredient2 = sample_ingredient(user=self.user, name="tomato")

        payload = {
            'title': 'pasta',
            'time': 20,
            'price': 10.00,
            'ingredient': [ingredient1.id, ingredient2.id]
        }
        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredient.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update_recipe(self):
        """"Test updating recipe with patch"""
        recipe = sample_recipe(user=self.user)
        recipe.tag.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='chinese')
        payload = {
            'title': 'italian pizza',
            'tag': [new_tag.id]
        }
        res = self.client.patch(detail_url(recipe.id), payload)

        recipe.refresh_from_db()
        self.assertEqual(res.data['title'], payload['title'])

        tags = recipe.tag.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """Test updating recipe with put"""
        recipe = sample_recipe(user=self.user)
        recipe.tag.add(sample_tag(user=self.user))
        recipe.ingredient.add(sample_ingredient(user=self.user))
        new_ingredient = sample_ingredient(user=self.user, name='cream')
        new_tag = sample_tag(user=self.user, name='iran')
        payload = {
            'title': 'ghorme sabzi',
            'time': 24,
            'price': 500.00,
            'tag': [new_tag.id],
            'ingredient': [new_ingredient.id]
        }
        self.client.put(detail_url(recipe.id), payload)
        recipe.refresh_from_db()
        tags = recipe.tag.all()
        ingredients = recipe.ingredient.all()
        self.assertEqual(len(tags), 1)
        self.assertEqual(len(ingredients), 1)
        self.assertEqual(recipe.price, payload['price'])
        self.assertEqual(recipe.title, payload['title'])


class RecipeImageUploadTest(TestCase):
    """Test for uploading image"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(email='test@test.com', password='test-pass')
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def tes_uploading_image_recipe(self):
        """test uploading an image to recipe"""
        with tempfile.NamedTemporaryFile(suffix='jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(image_upload_url(self.recipe.id),
                                   {'image': ntf}, format='multipart')
        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid an image"""
        res = self.client.post(image_upload_url(self.recipe.id),
                               {'image': 'not image'}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipes_by_tags(self):
        """Test returning recipes with specific tags"""
        recipe1 = sample_recipe(user=self.user, title='thai food')
        recipe2 = sample_recipe(user=self.user, title='burger')
        tag1 = sample_tag(user=self.user, name='persian')
        tag2 = sample_tag(user=self.user, name='thailand')
        recipe1.tag.add(tag1)
        recipe2.tag.add(tag2)
        recipe3 = sample_recipe(user=self.user, title='fish and chips')

        res = self.client.get(RECIPE_URL, {'tag': f'{tag1.id}, {tag2.id}'})
        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipes_by_ingredient(self):
        """Test returning recipes with specific ingredient"""
        recipe1 = sample_recipe(user=self.user, title='thai food')
        recipe2 = sample_recipe(user=self.user, title='burger')
        recipe3 = sample_recipe(user=self.user, title='fish and chips')
        ingredient1 = sample_ingredient(user=self.user, name='salt')
        ingredient2 = sample_ingredient(user=self.user, name='carry')

        recipe1.ingredient.add(ingredient1)
        recipe2.ingredient.add(ingredient2)

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        res = self.client.get(RECIPE_URL, {'ingredient': f'{ingredient1.id},{ingredient2.id}'})
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)
