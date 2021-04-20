#!/usr/bin/env python
# Default model classes for use in BlogEngine

from notmm.dbapi.orm import model

class AuthorManager(model.ModelManager):
    model = 'Author'

class CommentManager(model.ModelManager):
    model = 'Comment'

class MessageManager(model.ModelManager):
    model = 'Message'

