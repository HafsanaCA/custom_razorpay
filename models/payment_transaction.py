# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
import time
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import _, api, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_razorpay import const


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_processing_values(self, processing_values):
        """ Override of `payment` to return razorpay-specific processing values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the
                                       transaction.
        :return: The provider-specific processing values.
        :rtype: dict
        """
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != 'custom_razorpay':
            return res

        if self.operation in ('online_token', 'offline'):
            return {}

        customer_id = self._razorpay_create_customer()['id']
        order_id = self._razorpay_create_order(customer_id)['id']
        return {
            'razorpay_key_id': self.provider_id.custom_razorpay_key_id,
            'razorpay_public_token': self.provider_id._razorpay_get_public_token(),
            'razorpay_customer_id': customer_id,
            'is_tokenize_request': self.tokenize,
            'razorpay_order_id': order_id,
        }

