from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Group, Post
from http import HTTPStatus

User = get_user_model()


class PostUrlsTest(TestCase):
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='test',
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент1
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем авторизованый клиент2
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user2)

    #   Тестирование общедоступных страниц
    def test_home_url_exists_at_desired_location(self):
        """ Тестирование общедоступных страниц """
        pages: tuple = ('/',
                        f'/posts/{self.post.id}/',
                        f'/group/{self.group.slug}/',
                        f'/profile/{self.user.username}/',
                        '/about/author/',
                        '/about/tech/',
                        '/unexisting_paje/')
        for page in pages:
            if page == '/unexisting_paje/':
                response = self.guest_client.get(page)
                error = f'Ошибка в {page}'
                self.assertEqual(response.status_code,
                                 HTTPStatus.NOT_FOUND, error)
                break
            response = self.guest_client.get(page)
            error = f'Ошибка в {page}'
            self.assertEqual(response.status_code, HTTPStatus.OK, error)

    #   Тестирование страниц, доступных только авторизированным пользователям
    def test_task_list_url_exists_at_desired_location(self):
        """ Тестирование страницы, доступной только авторизированным юзерам """
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_task_list_url_exists_at_desired_location(self):
        """ Тестирование страницы, доступной только автору поста """
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/',
                                              kwargs={'post_id': self.post.id})
        self.assertEqual(response.status_code, HTTPStatus.OK)

    #   Проверяем редиректы для неавторизованного пользователя
    def test_task_list_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_task_list_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /posts/<post_id>/edit/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    #   Проверяем редирект для авторизованного пользователя и не автора поста
    def test_task_list_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /posts/<post_id>/edit/ перенаправит
        пользователя на страницу логина.
        """
        response = self.authorized_client_2.get(
            f'/posts/{self.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(
            response, f'/posts/{self.post.id}/'
        )

    #   Проверка вызываемых HTML-шаблонов
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/create/': 'posts/create_post.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
