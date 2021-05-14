from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import Tag, Ingredient, Recipe

from unittest.mock import patch
from core.models import recipe_image_file_path


def sample_user(email='test@test.com', password='test_pass'):
    """Create sample a user"""
    return get_user_model().objects.create_user(email, password)


class ModelTest(TestCase):
    def test_create_user_with_email(self):
        """testing creating a user with email"""
        email = 'test@test.com'
        password = 'admin'
        user = get_user_model().objects.create_user(
            email=email, password=password
        )
        self.assertEqual(email, user.email)
        self.assertTrue(user.check_password(password))

    def test_new_user_normalized(self):
        """testing creating new user with normalized email"""
        user = get_user_model().objects.create_user(email='test@TEST.COM', password='pass123456')
        self.assertEqual(user.email, user.email.lower())

    def test_new_user_invalid_email(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'test123')

    def test_create_new_superuser(self):
        user = get_user_model().objects.create_superuser(
            email='admin@admin.com', password='admin'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """Test the tag string representation"""
        tag = Tag.objects.create(
            user=sample_user(),
            name='Vegan'
        )
        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        """Test the string ingredient representation"""
        ingredient = Ingredient.objects.create(user=sample_user(), name='pizza')
        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        """Test the string recipe representation"""
        recipe = Recipe.objects.create(user=sample_user(),
                                       title='Alfredo pasta',
                                       time=5,
                                       price=5.00)
        self.assertEqual(str(recipe), recipe.title)

    @patch('uuid.uuid4')
    def test_recipe_filename_uuid(self, mock_uuid):
        """Test that image is save in correct location"""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = recipe_image_file_path(instance=None, filename='MyImage.jpg')

        exp_path = f'uploads/recipe/{uuid}.jpg'
        self.assertEqual(file_path, exp_path)
