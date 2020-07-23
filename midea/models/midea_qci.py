# -*- coding: utf-8 -*-
#
# Copyright 2018-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import models, fields, api


class MideaQci(models.Model):
    _name = 'midea.qci'

    code = fields.Char('Code', required=True)
    name = fields.Char('Name',
                       required=True,
                       translate=True)
    active = fields.Boolean('Active', default=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed'),
                              ('cancel', 'Canceled')],
                             'State',
                             required=True,
                             readonly=True,
                             default='draft')

