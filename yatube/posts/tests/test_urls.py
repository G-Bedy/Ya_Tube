from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовое описание поста',
            group=cls.group,
        )

        cls.templates_url_names: dict = {
            '/': 'posts/index.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
        }

        cls.public_urls: tuple = (
            '/',
            f'/group/{cls.group.slug}/',
            f'/profile/{cls.user.username}/',
            f'/posts/{cls.post.id}/'
        )

        cls.authorized_client_urls: tuple = (
            '/create/',
            f'/posts/{cls.post.id}/edit/'
        )

        cls.urls_redirect_guest_client: dict = {
            '/create/': '/auth/login/?next=/create/',
            f'/posts/{cls.post.id}/edit/':
                f'/auth/login/?next=/posts/{cls.post.id}/edit/'
        }

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_urls_guest_client(self):
        """Доступ неавторизованного пользователя"""
        for page in PostURLTests.public_urls:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                error_name = f'Ошибка: нет доступа до страницы {page}'
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    error_name
                )

    def test_urls_authorized_client(self):
        """Доступ авторизованного пользователя"""
        for page in PostURLTests.authorized_client_urls:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                error_name = f'Ошибка: нет доступа до страницы {page}'
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    error_name
                )

    def test_unexists_page(self):
        """Несуществующая страница возвращает ошибку 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_unexists_page_404_html(self):
        """Несуществующая страница возвращает шаблон 404.html"""
        response = self.guest_client.get('/unexisting_page/')
        template = 'core/404.html'
        error_name = 'Page_not_found не возвращает шаблон core/404.html'
        self.assertTemplateUsed(response, template, error_name)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in PostURLTests.templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                error_name = f'Ошибка: {address} ожидал шаблон {template}'
                self.assertTemplateUsed(response, template, error_name)

    def test_urls_redirect_guest_client(self):
        """Редирект неавторизованного пользователя"""
        for page, value in PostURLTests.urls_redirect_guest_client.items():
            with self.subTest(address=page):
                response = self.guest_client.get(page)
                self.assertRedirects(response, value)
