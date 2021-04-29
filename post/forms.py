from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms

from post.models import Post, get_all_tags
from django.contrib.postgres.forms import SimpleArrayField


class PostCreationForm(forms.ModelForm):
    content = forms.CharField(label='Содержание', widget=CKEditorUploadingWidget(config_name='default'))
    # tags = SimpleArrayField(forms.IntegerField)
    tags_str = forms.CharField(
        label='Тэги поста:',
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={'size': 67, 'placeholder': 'Тэги введите через запятую', }
        )
    )

    class Meta:
        model = Post
        exclude = ('tags', 'moderated', 'moderated_at', 'moderate_desc')
        fields = ('name', 'hub_category', 'tags_str', 'status', 'user', 'karma_count', 'content')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.help_text = ''
            if field_name in ('user', 'post_karma', 'status', 'karma_count'):
                field.widget = forms.HiddenInput()
            if field_name == 'hub_category':
                field.widget.attrs['required'] = True


class PostEditForm(forms.ModelForm):
    content = forms.CharField(label='Содержание', widget=CKEditorUploadingWidget(config_name='default'))
    tags_str = forms.CharField(
        label='Тэги поста:',
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={'size': 67, 'placeholder': 'Тэги введите через запятую', }
        )
    )

    class Meta:
        model = Post
        exclude = ('tags', 'moderated', 'moderated_at', 'moderate_desc')
        fields = ('name', 'hub_category', 'tags_str', 'status', 'user', 'karma_count', 'content')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.help_text = ''
            if field_name in ('user', 'post_karma', 'status', 'karma_count'):
                field.widget = forms.HiddenInput()
            if field_name == 'hub_category':
                field.widget.attrs['required'] = True


class PostModeratorEditForm(forms.ModelForm):

    STATUS_UNPUBLISHED = 'unpublished'
    STATUS_ON_MODERATE = 'on_moderate'
    STATUS_NEED_REVIEW = 'need_review'
    STATUS_MODERATE_FALSE = 'moderate_false'

    STATUSES = (
        (STATUS_UNPUBLISHED, 'модерация подтверждена'),
        (STATUS_ON_MODERATE, 'на модерации'),
        (STATUS_NEED_REVIEW, 'необходимы исправления'),
        (STATUS_MODERATE_FALSE, 'модерация не пройдена'),
    )

    content = forms.CharField(label='Содержание', widget=CKEditorUploadingWidget(config_name='default'))
    status = forms.ChoiceField(choices=STATUSES, label='Статус', initial=STATUS_ON_MODERATE)
    tags_str = forms.CharField(
        label='Тэги поста:',
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={'size': 67, 'placeholder': 'Тэги введите через запятую', }
        )
    )

    class Meta:
        model = Post
        exclude = ('tags', 'moderated', 'moderated_at', )
        fields = ('name', 'hub_category', 'tags_str', 'status', 'user', 'moderate_desc', 'karma_count', 'content')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.help_text = ''
            if field_name in ('post_karma', 'karma_count', 'user'):
                field.widget = forms.HiddenInput()
            # if field_name in ('user',):
            #     field.widget.attrs['readonly'] = True


class CommentForm(forms.Form):
    parent_comment = forms.IntegerField(
        widget=forms.HiddenInput,
        required=False
    )

    comment_area = forms.CharField(
        label="",
        widget=forms.Textarea
    )
