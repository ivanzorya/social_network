from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from django.contrib.auth.models import User

from posts.models import Post, Group, Follow
from posts.forms import PostForm, CommentForm


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "index.html",
        {
            "page": page,
            "paginator": paginator
        }
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "group.html",
        {
            "group": group,
            "page": page,
            "paginator": paginator
        }
    )


@login_required
def new_post(request):
    if request.method == "POST":
        form = PostForm(data=request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("index")
        return render(request, "new_post.html", {"form": form})
    form = PostForm()
    return render(request, "new_post.html", {"form": form})


def profile(request, username):
    user_req = get_object_or_404(User, username=username)
    posts = user_req.posts.all()
    following = user_req.following.all()
    follow = False
    authors = []
    for aut in following:
        author = aut.user
        authors.append(author)
    if request.user in authors:
        follow = True
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "profile.html",
        {
            "user_req": user_req,
            "page": page,
            "paginator": paginator,
            "follow": follow
        }
    )


def post_view(request, username, post_id):
    user_req = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm()
    return render(
        request,
        "post.html",
        {
            "user_req": user_req,
            "post": post,
            "comments": comments,
            "form": form
        }
    )


def post_edit(request, username, post_id):
    edit_post = get_object_or_404(Post, pk=post_id)
    if edit_post.author == request.user:
        if request.method == "POST":
            form = PostForm(request.POST, files=request.FILES or None, instance=edit_post)
            if form.is_valid():
                form.save()
                return redirect("post", username, post_id)
        form = PostForm(instance=edit_post)
        return render(
            request,
            "new_post.html",
            {
                "form": form,
                "username": username,
                "post_id": post_id,
                "edit_post": edit_post
            }
        )
    return redirect("post", username, post_id)


@login_required
def add_comment(request, username, post_id):
    user_req = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    if request.method == "POST":
        form = CommentForm(data=request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect("post", username, post_id)
        return render(
            request,
            "post.html",
            {
                "user_req": user_req,
                "post": post,
                "form": form,
                "comments": comments
            }
        )
    form = CommentForm()
    return render(
        request,
        "post.html",
        {
            "user_req": user_req,
            "post": post,
            "form": form,
            "comments": comments
        }
    )



@login_required
def follow_index(request):
    user = get_object_or_404(User, username=request.user)
    followings = user.follower.all()
    authors = set()
    for aut in followings:
        author = aut.author
        authors.add(author)
    post_list = Post.objects.filter(author__in=authors)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "follow.html",
        {
            "page": page,
            "paginator": paginator,
            "followings": followings
        }
    )

@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=request.user)
    author = get_object_or_404(User, username=username)
    if user == author:
        return redirect("profile", username)
    follow = Follow.objects.filter(user=user, author=author)
    if len(follow) > 0:
        return redirect("profile", username)
    Follow.objects.create(user=user, author=author)
    return redirect("profile", username)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=request.user)
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=user, author=author)
    follow.delete()
    return redirect("profile", username)
