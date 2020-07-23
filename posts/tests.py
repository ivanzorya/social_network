from django.test import TestCase
from django.contrib.auth.models import User
from django.test import Client
from django.shortcuts import get_object_or_404
from django.urls import reverse
import uuid

from posts.models import Post, Group


class ProfileTest(TestCase):
    cache_text = []

    def setUp(self):
        self.client = Client()
        self.username = uuid.uuid4().hex
        self.password = uuid.uuid4().hex
        self.user = User.objects.create_user(username=self.username, email=f"{self.username}@gmail.com",
                                             password=self.password)
        self.title = uuid.uuid4().hex
        self.slug = uuid.uuid4().hex
        self.description = uuid.uuid4().hex
        self.group = Group.objects.create(title=self.title, slug=self.slug, description=self.description)
        self.username_not_author = uuid.uuid4().hex
        self.password_not_author = uuid.uuid4().hex
        self.user_no_author = User.objects.create_user(username=self.username_not_author,
                                                       email=f"{self.username_not_author}@gmail.com",
                                                       password=self.password_not_author)
        self.text = uuid.uuid4().hex
        self.text_edit = uuid.uuid4().hex
        self.post = Post.objects.create(text=self.text, author=self.user, group=self.group)
        self.client.force_login(self.user)
        self.page_not_found = uuid.uuid4().hex
        self.cache_text.append(self.text)

    def test_profile(self):
        response_profile = self.client.get(reverse("profile", args=[self.user.username]))
        self.assertEqual(response_profile.status_code, 200)
        self.assertEqual(response_profile.context["user_req"], self.user)
        self.assertIn(bytes(f"""<strong class="d-block text-gray-dark">@{self.user.username}</strong>""",
                            encoding="UTF-8"), response_profile.content)
        self.assertIn(bytes(f"""{self.text}""", encoding="UTF-8"), response_profile.content)

    def test_new(self):
        response_login = self.client.get(reverse("new_post"))
        self.assertEqual(response_login.status_code, 200)
        self.assertIn(bytes("""<form action=" /new " method="post" enctype="multipart/form-data">""",
                            encoding="UTF-8"), response_login.content)
        self.client.logout()
        response_not_login = self.client.get(reverse("new_post"), follow=True)
        self.assertEqual(response_not_login.redirect_chain, [("/auth/login/?next=/new", 302)])

    def test_post_pub(self):
        response_post_index = self.client.get(reverse("index"))
        self.assertContains(response_post_index, self.cache_text[0], count=None, status_code=200, html=False)
        response_post_user = self.client.get(reverse("profile", args=[self.user.username]))
        self.assertContains(response_post_user, self.text, count=None, status_code=200, html=False)
        response_post = self.client.get(reverse("post", args=[self.user.username, self.post.pk]))
        self.assertContains(response_post, self.text, count=None, status_code=200, html=False)
        response_post_group = self.client.get(reverse("group", args=[self.slug]))
        self.assertContains(response_post_group, self.text, count=None, status_code=200, html=False)

    def test_post_edit(self):
        self.client.post(reverse("post_edit", args=[self.user.username, self.post.pk]),
                         {"text": self.text_edit, "group": self.group.pk}, follow=True)
        edit_post = Post.objects.get(pk=self.post.pk)
        self.assertEqual(edit_post.text, self.text_edit)
        response_post_edit_index = self.client.get(reverse("index"))
        self.assertContains(response_post_edit_index, self.cache_text[0], count=None, status_code=200, html=False)
        response_post_edit_user = self.client.get(reverse("profile", args=[self.user.username]))
        self.assertContains(response_post_edit_user, self.text_edit, count=1, status_code=200, html=False)
        response_post_edit = self.client.get(reverse("post", args=[self.user.username, self.post.pk]))
        self.assertContains(response_post_edit, self.text_edit, count=1, status_code=200, html=False)
        response_post_edit_group = self.client.get(reverse("group", args=[self.slug]))
        self.assertContains(response_post_edit_group, self.text_edit, count=1, status_code=200, html=False)
        self.client.logout()
        response_post_edit_logout = self.client.post(reverse("post_edit", args=[self.user.username, self.post.pk]),
                                                     {"text": self.text_edit, "group": self.group.pk}, follow=True)
        self.assertEqual(response_post_edit_logout.redirect_chain, [(f"/{self.user.username}/{self.post.pk}/", 302)])
        self.client.force_login(self.user_no_author)
        response_post_edit_not_author = self.client.post(reverse("post_edit", args=[self.user.username, self.post.pk]),
                                                         {"text": self.text_edit, "group": self.group.pk}, follow=True)
        self.assertEqual(response_post_edit_not_author.redirect_chain, [(f"/{self.user.username}/{self.post.pk}/", 302)])

    def test_page_not_found(self):
        response_page_not_found = self.client.get(f"/{self.page_not_found}/")
        self.assertEqual(response_page_not_found.status_code, 404)

    def test_image(self):
        with open('media/1.png', 'rb') as img:
            self.client.post(reverse("post_edit", args=[self.user.username, self.post.pk]),
                             {"text": self.text_edit, "group": self.group.pk, 'image': img}, follow=True)
        pages = [
            reverse("group", args=[self.slug]),
            reverse("profile", args=[self.user.username]),
            reverse("post", args=[self.user.username, self.post.pk])
        ]
        for page in pages:
            response_page = self.client.get(page)
            self.assertIn(bytes("""<img class="card-img" src="/media/cache/""", encoding="UTF-8"), response_page.content)

    def test_not_image(self):
        with open('media/1.txt', 'rb') as img:
            self.client.post(reverse("post_edit", args=[self.user.username, self.post.pk]),
                         {"text": self.text_edit, "group": self.group.pk, 'image': img}, follow=True)
        pages = [
            reverse("group", args=[self.slug]),
            reverse("profile", args=[self.user.username]),
            reverse("post", args=[self.user.username, self.post.pk])
        ]
        for page in pages:
            response_page = self.client.get(page)
            self.assertNotIn(bytes("""<img class="card-img" """, encoding="UTF-8"), response_page.content)

    def test_cache(self):
        response_index = self.client.get(reverse("index"))
        self.assertContains(response_index, self.cache_text[0], count=None, status_code=200, html=False)
        self.client.post(reverse("post_edit", args=[self.user.username, self.post.pk]),
                         {"text": self.text_edit, "group": self.group.pk}, follow=True)
        response_cache_post_edit_index = self.client.get(reverse("index"))
        self.assertContains(response_cache_post_edit_index, self.text, count=None, status_code=200, html=False)
        self.assertNotContains(response_cache_post_edit_index, self.text_edit, status_code=200, html=False)


class FollowCommentTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = uuid.uuid4().hex
        self.password = uuid.uuid4().hex
        self.user = User.objects.create_user(username=self.username, email=f"{self.username}@gmail.com",
                                             password=self.password)
        self.username_not_follow = uuid.uuid4().hex
        self.password_not_follow = uuid.uuid4().hex
        self.user_not_follow = User.objects.create_user(username=self.username_not_follow,
                                                        email=f"{self.username_not_follow}@gmail.com",
                                                        password=self.password_not_follow)
        self.username_follow = uuid.uuid4().hex
        self.password_follow = uuid.uuid4().hex
        self.user_follow = User.objects.create_user(username=self.username_follow,
                                                    email=f"{self.username_follow}@gmail.com",
                                                    password=self.password_follow)
        self.text = uuid.uuid4().hex
        self.text_edit = uuid.uuid4().hex
        self.post = Post.objects.create(text=self.text, author=self.user)

    def test_follow(self):
        self.client.force_login(self.user_follow)
        response_follow = self.client.post(reverse("profile_follow", args=[self.user.username]),
                                           {"username": self.user.username}, follow=True)
        self.assertEqual(response_follow.redirect_chain, [(f"/{self.user.username}/", 302)])
        user = get_object_or_404(User, username=self.username_follow)
        follower = user.follower.all()
        self.assertTrue(str(follower) != "<QuerySet []>")
        response_unfollow = self.client.post(reverse("profile_unfollow", args=[self.user.username]),
                                             {"username": self.user.username}, follow=True)
        self.assertEqual(response_unfollow.redirect_chain, [(f"/{self.user.username}/", 302)])
        un_follower = user.follower.all()
        self.assertTrue(str(un_follower) == "<QuerySet []>")

    def test_follow_index(self):
        self.client.force_login(self.user_follow)
        self.client.post(reverse("profile_follow", args=[self.user.username]), {"username": self.user.username}, follow=True)
        response_follow = self.client.get(reverse("follow_index"))
        self.assertContains(response_follow, self.text, count=None, status_code=200, html=False)
        self.client.force_login(self.user_not_follow)
        response_not_follow = self.client.get(reverse("follow_index"))
        self.assertNotContains(response_not_follow, self.text, status_code=200, html=False)

    def test_comment(self):
        response_not_auth_comment = self.client.post(reverse("add_comment", args=[self.user.username, self.post.pk]),
                                                     {"text": self.text}, follow=True)
        self.assertEqual(response_not_auth_comment.redirect_chain, [(f"/auth/login/?next=/{self.username}/1/comment/", 302)])
        self.client.force_login(self.user_follow)
        response_auth_comment = self.client.post(reverse("add_comment", args=[self.user.username, self.post.pk]),
                                                 {"text": self.text}, follow=True)
        self.assertEqual(response_auth_comment.status_code, 200)
        response_post_comment = self.client.get(reverse("post", args=[self.user.username, self.post.pk]))
        self.assertContains(response_post_comment, self.text, count=2, status_code=200, html=False)

