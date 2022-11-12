import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        """Валидная форма создает запись в базе данных."""
        posts_count = Post.objects.count()
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
            'text': 'Текст записанный в форму',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        error_name1 = 'Данные поста не совпадают'
        error_name2 = 'Поcт не добавлен в базу данных'
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=form_data['group'],
            author=self.user,
            image='posts/small.gif'
        ).exists(), error_name1)
        self.assertRedirects(response,
                             (reverse('posts:profile', kwargs={
                                 'username': self.user.username})))
        self.assertEqual(Post.objects.count(), posts_count + 1, error_name2)

    def test_changing_post(self):
        """Валидная форма изменяет конкретную запись в Post."""
        posts_count = Post.objects.count()
        self.post = Post.objects.create(text='Старый текст поста',
                                        author=self.user,
                                        group=self.group)
        old_post = self.post
        self.group2 = Group.objects.create(title='Тестовая группа2',
                                           slug='test-group2',
                                           description='Описание')
        form_data = {'text': 'Новый текст поста',
                     'group': self.group2.id}
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': old_post.id}),
            data=form_data,
            follow=True
        )
        error_text = 'Текст поста не был изменен'
        error_group = 'Группа аоста не была изменен'
        error_posts_count = 'Вместо редактирования был создан новый пост'
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(old_post.text, form_data['text'], error_text)
        self.assertNotEqual(old_post.group, form_data['group'], error_group)
        self.assertEqual(
            Post.objects.count(),
            posts_count + 1,
            error_posts_count
        )


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(CommentCreateFormTests.user)

    def test_comment_form_guest_client_not_access(self):
        '''комментировать посты может только авторизованный пользователь'''
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Текст записанный в форму',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        error_comment_count = 'Гостевой клиент комментарий не имея на это прав'
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(
            Comment.objects.count(),
            comment_count + 1,
            error_comment_count
        )

    def test_comment_create_authorized_client(self):
        '''авторизованный пользователь создает комментарий'''
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Текст тестового комментария',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        error_comment = 'комментарий не был создан'
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            Comment.objects.count(),
            comment_count + 1,
            error_comment
        )
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
                author=self.user,
                post=self.post.id
            ).exists(),
            error_comment
        )
