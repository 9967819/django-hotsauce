#!/usr/bin/env python
from notmm.dbapi.orm import model

class MessageManager(model.ModelManager):
    model = 'Message'

