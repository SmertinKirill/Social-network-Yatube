from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required

from .models import Post, Group, Follow
from .forms import PostForm, CommentForm

LIMIT = 10
User = get_user_model()


def get_paginator(post_list, request):
    paginator = Paginator(post_list, LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'page_obj': page_obj
    }


def index(request) -> str:
    context = get_paginator(Post.objects.select_related('group'), request)
    return render(request, 'posts/index.html', context)


def group_post(request, slug) -> str:
    group = get_object_or_404(Group, slug=slug)
    template = 'posts/group_list.html'
    context = {
        'group': group,
    }
    context.update(get_paginator(group.posts.all(), request))
    return render(request, template, context)


def profile(request, username) -> str:
    author = get_object_or_404(User, username=username)
    follow_check = Follow.objects.filter(
        user=request.user.id,
        author=author,
    )
    following = (
        request.user.is_authenticated
        and request.user != author
        and follow_check.exists()
    )
    context = {
        'author': author,
        'following': following
    }
    context.update(get_paginator(author.posts.all(), request))
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id) -> str:
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request) -> str:
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author)
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id) -> str:
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None,
                    instance=post,
                    files=request.FILES or None)
    groups = Group.objects.all()
    if request.user == post.author:
        if form.is_valid():
            post = form.save()
            return redirect('posts:post_detail', post.id)
        context = {
            'is_edit': is_edit,
            'post': post,
            'form': form,
            'groups': groups
        }
        return render(request, 'posts/create_post.html', context)
    return redirect('posts:post_detail', post.id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    authors_posts = Follow.objects.values("author").filter(user=request.user)
    context = get_paginator(Post.objects.filter(author__in=authors_posts),
                            request)
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            user=request.user,
            author=author,
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.get(
        user=request.user,
        author=author,
    ).delete()
    return redirect('posts:profile', username=username)
