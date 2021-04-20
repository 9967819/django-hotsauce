#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import django.forms as forms

__all__ = ('LoginForm',)

class LoginForm(forms.Form):
    """Basic login form for generic User authentication/authorization"""
    username = forms.CharField(label="Username", max_length=30)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
#
