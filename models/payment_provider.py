# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('custom_razorpay', "Razorpay Custom")], ondelete={'custom_razorpay': 'cascade'},)
    custom_razorpay_key_id = fields.Char(string="Key Id")
    custom_razorpay_key_secret = fields.Char(string="Key Secret")
    custom_razorpay_webhook_secret = fields.Char(string="Webhook Secret")