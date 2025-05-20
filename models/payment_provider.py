# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import ValidationError
from odoo.addons.payment_razorpay import const
import hashlib
import hmac
import logging
import pprint
import requests

_logger = logging.getLogger(__name__)

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('custom_razorpay', "Razorpay Custom")], ondelete={'custom_razorpay': 'cascade'},)
    custom_razorpay_key_id = fields.Char(string="Key Id")
    custom_razorpay_key_secret = fields.Char(string="Key Secret")
    custom_razorpay_webhook_secret = fields.Char(string="Webhook Secret")


    def _razorpay_make_request(self, endpoint, payload=None, method='POST'):
        """ Make a request to Razorpay API at the specified endpoint.

        Note: self.ensure_one()

        :param str endpoint: The endpoint to be reached by the request.
        :param dict payload: The payload of the request.
        :param str method: The HTTP method of the request.
        :return The JSON-formatted content of the response.
        :rtype: dict
        :raise ValidationError: If an HTTP error occurs.
        """
        self.ensure_one()

        # TODO: Make api_version a kwarg in master.
        api_version = self.env.context.get('razorpay_api_version', 'v1')
        url = f'https://api.razorpay.com/{api_version}/{endpoint}'
        headers = None
        if access_token := self._razorpay_get_access_token():
            headers = {'Authorization': f'Bearer {access_token}'}
        auth = (self.custom_razorpay_key_id, self.custom_razorpay_key_secret) if self.custom_razorpay_key_id else None
        try:
            if method == 'GET':
                response = requests.get(
                    url,
                    params=payload,
                    headers=headers,
                    auth=auth,
                    timeout=10,
                )
            else:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    auth=auth,
                    timeout=10,
                )
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                _logger.exception(
                    "Invalid API request at %s with data:\n%s", url, pprint.pformat(payload),
                )
                raise ValidationError("Razorpay: " + _(
                    "Razorpay gave us the following information: '%s'",
                    response.json().get('error', {}).get('description')
                ))
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            _logger.exception("Unable to reach endpoint at %s", url)
            raise ValidationError(
                "Razorpay: " + _("Could not establish the connection to the API.")
            )
        return response.json()

