import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from posts.models import Post, Group
from posts.forms import PostForm
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test',
            slug='test',
            description='test',
        )
        cls.group_2 = Group.objects.create(
            title='test2',
            slug='test2',
            description='test2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test',
            group=cls.group
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Проверка создания постов."""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'test',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertTrue(Post.objects.filter(text='test',
                                            image='posts/small.gif',
                                            group=self.group.id).exists())
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_edit_post(self):
        """Проверка редактирования постов."""
        post_count = Post.objects.filter(group=self.group.id).count()
        form_data = {
            'text': 'new test',
            'group': self.group_2.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': self.post.id}))
        self.assertNotEqual(self.post.text, form_data['text'])
        self.assertEqual(Post.objects.filter(group=self.group.id).count(),
                         post_count - 1)
