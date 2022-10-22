import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms
from django.core.cache import cache
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

PAGE_OBJ = 'page_obj'
ALL_POST_PAG = 13
FIRST_PAGE_PAG = 10
SEC_PAGE_PAG = 3
NAME_IMAGE = 'posts/small.gif'


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='test',
            slug='test',
            description='test',
        )
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='test',
            image=uploaded,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)
        self.INDEX_REV = reverse('posts:index')
        self.POST_CREATE_REV = reverse('posts:post_create')
        self.GROUP_POST_REV = reverse('posts:group_post',
                                      kwargs={'slug': self.group.slug})
        self.POST_EDIT_REV = reverse('posts:post_edit',
                                     kwargs={'post_id': self.post.id})
        self.PROFILE_REV = reverse('posts:profile',
                                   kwargs={'username': self.user})
        self.POST_DETAIL_REV = reverse('posts:post_detail',
                                       kwargs={'post_id': self.post.id})
        self.FOLLOW_REV = reverse('posts:profile_follow',
                                  kwargs={'username': self.post.author})
        self.UNFOLLOW_REV = reverse('posts:profile_unfollow',
                                    kwargs={'username': self.post.author})
        self.FOLLOW_INDEX = reverse('posts:follow_index')

    #   Проверка вызываемых HTML-шаблонов
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            self.INDEX_REV: 'posts/index.html',
            self.POST_CREATE_REV: 'posts/create_post.html',
            self.GROUP_POST_REV: 'posts/group_list.html',
            self.POST_EDIT_REV: 'posts/create_post.html',
            self.PROFILE_REV: 'posts/profile.html',
            self.POST_DETAIL_REV: 'posts/post_detail.html',
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    #   Проверка переданных контекстов
    def test_home_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.INDEX_REV)
        first_object = response.context[PAGE_OBJ][0]
        self.assertEqual(first_object.text, 'test')
        self.assertEqual(first_object.image, NAME_IMAGE)

    def test_group_page_show_correct_context(self):
        """Шаблон group list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            self.GROUP_POST_REV
        )
        first_object = response.context['group']
        second_object = response.context[PAGE_OBJ].object_list[0]
        self.assertEqual(first_object.slug, 'test')
        self.assertEqual(second_object.image, NAME_IMAGE)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            self.PROFILE_REV
        )
        first_object = response.context['author']
        second_object = response.context[PAGE_OBJ][0]
        self.assertEqual(first_object.username, 'auth')
        self.assertEqual(second_object.text, 'test')
        self.assertEqual(second_object.image, NAME_IMAGE)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            self.POST_DETAIL_REV
        )
        first_object = response.context['post']
        self.assertEqual(first_object.text, 'test')
        self.assertEqual(first_object.image, NAME_IMAGE)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.POST_CREATE_REV)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            self.POST_EDIT_REV
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    # Дополнительная проверка при создании поста
    def test_post_page_show_correct(self):
        """При создании поста указать группу, который появится на
           главной странице сайта, на странице выбранной группы,
           в профайле пользователя."""
        post = Post.objects.create(
            author=self.user,
            text='test',
            group=self.group,
        )
        pages = [
            self.INDEX_REV,
            self.GROUP_POST_REV,
            self.PROFILE_REV,
        ]
        for i in pages:
            with self.subTest(i=i):
                response = self.authorized_client.get(i)
        self.assertIn(post, response.context[PAGE_OBJ])

    # Проверка работы кеширования
    def test_cache(self):
        """Тест для проверки кеширования главной страницы."""
        response = self.authorized_client.get(self.INDEX_REV)
        first_cache = response.content
        response = self.authorized_client.get(self.INDEX_REV)
        second_cache = response.content
        cache.clear()
        response = self.authorized_client.get(self.INDEX_REV)
        third_cache = response.content
        self.assertEqual(first_cache, second_cache)
        self.assertNotEqual(first_cache, third_cache)

    # Проверка подписки/отписки
    def test_follow(self):
        """Авторизованный пользователь может подписываться на других
           пользователей."""
        follow_count = Follow.objects.count()
        self.authorized_client2.post(self.FOLLOW_REV)
        self.assertEqual(follow_count, Follow.objects.count() - 1)
        self.assertTrue(
            Follow.objects.filter(user=self.user2,
                                  author=self.post.author).exists())

    def test_unfollow(self):
        """Авторизованный пользователь может удалять их из подписок."""
        follow_count = Follow.objects.count()
        self.authorized_client2.post(self.FOLLOW_REV)
        self.authorized_client2.post(self.UNFOLLOW_REV)
        self.assertEqual(follow_count, Follow.objects.count())
        self.assertFalse(
            Follow.objects.filter(user=self.user2,
                                  author=self.post.author).exists())

    def test_follow_authorized_client(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
           подписан."""
        self.authorized_client2.post(self.FOLLOW_REV)
        response = self.authorized_client2.get(self.FOLLOW_INDEX)
        follow_count_1 = len(response.context[PAGE_OBJ])
        Post.objects.create(
            author=self.user,
            text='test',
            group=self.group,
        )
        response = self.authorized_client2.get(self.FOLLOW_INDEX)
        follow_count_2 = len(response.context[PAGE_OBJ])
        self.assertEqual(follow_count_1, follow_count_2 - 1)

    def test_follow_unauthorized_client(self):
        """Новая запись пользователя не появляется в ленте тех,
           кто не подписан."""
        self.authorized_client2.post(self.FOLLOW_REV)
        response = self.authorized_client.get(self.FOLLOW_INDEX)
        follow_count_1 = len(response.context[PAGE_OBJ])
        Post.objects.create(
            author=self.user,
            text='test',
            group=self.group,
        )
        response = self.authorized_client.get(self.FOLLOW_INDEX)
        follow_count_2 = len(response.context[PAGE_OBJ])
        self.assertEqual(follow_count_1, follow_count_2)


# Проверка Paginator
class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth2')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.posts = [Post(
            author=cls.user,
            text='test',
        ) for i in range(ALL_POST_PAG)
        ]
        cls.group = Group.objects.create(
            title='test',
            slug='test',
            description='test'
        )
        Post.objects.bulk_create(cls.posts)

    def test_first_page_contains_ten_records(self):
        pages = [
            self.INDEX_REV,
            self.GROUP_POST_REV,
            self.PROFILE_REV,
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.client.get(page + '?page=1')
        self.assertEqual(len(response.context[PAGE_OBJ]), FIRST_PAGE_PAG)

    def test_first_page_contains_ten_records(self):
        pages = [
            reverse('posts:index'),
            reverse('posts:group_post', kwargs={'slug': 'test'}),
            reverse('posts:profile', kwargs={'username': self.user}),
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.client.get(page + '?page=2')
        self.assertEqual(len(response.context[PAGE_OBJ]), SEC_PAGE_PAG)
