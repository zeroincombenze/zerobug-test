from odoo import models, fields, api


class MetaModel(api.Meta):
    pass

class BaseModel(object):

    @api.model
    def example(self):
        return True
