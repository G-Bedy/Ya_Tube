import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

TEST_OF_POST: int = 13
User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание',
        )

        list_posts: list = []
        for i in range(TEST_OF_POST):
            list_posts.append(Post(text=f'Тестовый текст {i}',
                                   group=cls.group,
                                   author=cls.user))
        Post.objects.bulk_create(list_posts)

        cls.guest_client_urls: tuple = (
            reverse('posts:index'),
            reverse('posts:profile',
                    kwargs={'username': cls.user.username}),
            reverse('posts:group_list',
                    kwargs={'slug': cls.group.slug})
        )

        cls.authorized_client_urls: tuple = (
            reverse('posts:index'),
            reverse('posts:profile',
                    kwargs={'username': cls.user.username}),
            reverse('posts:group_list',
                    kwargs={'slug': cls.group.slug})
        )

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTests.user)

    def test_correct_page_context_guest_client(self):
        '''Проверка количества постов на первой и второй страницах
        неввторизаванного пользователя.'''
        for page in PaginatorViewsTests.guest_client_urls:
            with self.subTest(page=page):
                response1 = self.guest_client.get(page)
                response2 = self.guest_client.get(page + '?page=2')
                count_posts1 = len(response1.context['page_obj'])
                count_posts2 = len(response2.context['page_obj'])
                error_name1 = (
                    f'Ошибка пагинатора на первой странице {page}:'
                    f'показывает {count_posts1} постов, а должно быть 10'
                )
                error_name2 = (
                    f'Ошибка пагинатора на второй странице {page}:'
                    f'показывает {count_posts1} постов, а должно быть 3'
                )
                self.assertEqual(count_posts1, 10, error_name1)
                self.assertEqual(count_posts2, 3, error_name2)

    def test_correct_page_context_authorized_client(self):
        '''Проверка количества постов на первой и второй страницах
        ввторизаванного пользователя.'''
        for page in PaginatorViewsTests.authorized_client_urls:
            with self.subTest(page=page):
                response1 = self.authorized_client.get(page)
                response2 = self.authorized_client.get(page + '?page=2')
                count_posts1 = len(response1.context['page_obj'])
                count_posts2 = len(response2.context['page_obj'])
                error_name1 = (
                    f'Ошибка пагинатора на первой странице {page}:'
                    f'показывает {count_posts1} постов, а должно быть 10'
                )
                error_name2 = (
                    f'Ошибка пагинатора на второй странице {page}:'
                    f'показывает {count_posts1} постов, а должно быть 3'
                )
                self.assertEqual(count_posts1, 10, error_name1)
                self.assertEqual(count_posts2, 3, error_name2)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовое описание поста',
            group=cls.group,
            image=cls.uploaded
        )

        cls.templates_url_names: dict = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                'slug': cls.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': cls.user.username}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': cls.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={
                'post_id': cls.post.id}): 'posts/create_post.html'
        }
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, temp in PostPagesTests.templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                error_name = f'Ошибка: {reverse_name} ожидал шаблон {temp}'
                self.assertTemplateUsed(response, temp, error_name)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj']
        error_name = 'Контекст в index сформирован не верно'
        self.assertIn(self.post, first_object, error_name)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}))
        first_object = response.context['page_obj']
        error_name = 'Контекст group_posts сформирован не верно'
        self.assertIn(self.post, first_object, error_name)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username}))
        first_object = response.context['page_obj']
        error_name = 'Контекст group_posts сформирован не верно'
        self.assertIn(self.post, first_object, error_name)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id})))
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').group, self.post.group)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_create_post_pages_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        for value, expected in PostPagesTests.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_pages_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        )
        form_field = response.context.get('form').fields.get('text')
        expected = PostPagesTests.form_fields['text']
        error_name = f'ошибка при {form_field} - {expected}'
        self.assertIsInstance(form_field, expected, error_name)

    def test_cache_context(self):
        '''Проверка кэширования страницы index'''
        before_create_post = self.authorized_client.get(
            reverse('posts:index'))
        first_item_before = before_create_post.content
        Post.objects.create(
            author=self.user,
            text='Проверка кэша',
            group=self.group)
        after_create_post = self.authorized_client.get(
            reverse('posts:index'))
        first_item_after = after_create_post.content
        self.assertEqual(first_item_after, first_item_before)
        cache.clear()
        after_clear = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_item_after, after_clear)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth1')
        cls.user2 = User.objects.create_user(username='auth2')
        cls.author = User.objects.create_user(username='someauthor')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_user_follower_authors(self):
        '''Посты доступны пользователю, который подписался на автора.
           Увеличение подписок автора'''
        count_follow = Follow.objects.filter(user=FollowViewsTest.user).count()
        data_follow = {'user': FollowViewsTest.user,
                       'author': FollowViewsTest.author}
        url_redirect = reverse(
            'posts:profile',
            kwargs={'username': FollowViewsTest.author.username})
        response = self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={
                'username': FollowViewsTest.author.username}),
            data=data_follow, follow=True)
        new_count_follow = Follow.objects.filter(
            user=FollowViewsTest.user).count()
        self.assertTrue(Follow.objects.filter(
                        user=FollowViewsTest.user,
                        author=FollowViewsTest.author).exists())
        self.assertRedirects(response, url_redirect)
        self.assertEqual(count_follow + 1, new_count_follow)

    def test_user_unfollower_authors(self):
        '''Посты не доступны пользователю, который не подписался на автора.
           Не происходит увеличение подписок автора'''
        count_follow = Follow.objects.filter(
            user=FollowViewsTest.user).count()
        data_follow = {'user': FollowViewsTest.user,
                       'author': FollowViewsTest.author}
        url_redirect = ('/auth/login/?next=/profile/'
                        f'{self.author.username}/unfollow/')
        response = self.guest_client.post(
            reverse('posts:profile_unfollow', kwargs={
                'username': FollowViewsTest.author}),
            data=data_follow, follow=True)
        new_count_follow = Follow.objects.filter(
            user=FollowViewsTest.user).count()
        self.assertFalse(Follow.objects.filter(
            user=FollowViewsTest.user,
            author=FollowViewsTest.author).exists())
        self.assertRedirects(response, url_redirect)
        self.assertEqual(count_follow, new_count_follow)

    def test_follower_see_new_post(self):
        '''У подписчика появляется новый пост избранного автора.
           А у не подписчика его нет'''
        new_post_follower = Post.objects.create(
            author=FollowViewsTest.author,
            text='Текстовый текст')
        Follow.objects.create(user=FollowViewsTest.user,
                              author=FollowViewsTest.author)
        response_follower = self.authorized_client.get(
            reverse('posts:follow_index'))
        new_posts = response_follower.context['page_obj']
        self.assertIn(new_post_follower, new_posts)

    def test_unfollower_no_see_new_post(self):
        '''У не подписчика поста нет'''
        new_post_follower = Post.objects.create(
            author=FollowViewsTest.author,
            text='Текстовый текст')
        Follow.objects.create(user=FollowViewsTest.user,
                              author=FollowViewsTest.author)
        response_unfollower = self.authorized_client2.get(
            reverse('posts:follow_index'))
        new_post_unfollower = response_unfollower.context['page_obj']
        self.assertNotIn(new_post_follower, new_post_unfollower)
