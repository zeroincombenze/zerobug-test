from odoo import http


class ExportTestData(object, http.Controller):

    @http.route('/web/export/test_data', type='http', auth="user")
    def index(self):
        return {}
