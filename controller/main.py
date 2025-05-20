from odoo import http
from odoo.http import request
import logging
import json
import hmac
import hashlib

_logger = logging.getLogger(__name__)


class CustomRazorpayController(http.Controller):
    @http.route('/payment/custom_razorpay/create_order', type='json', auth='public', methods=['POST'])
    def razorpay_create_order(self, provider_id, reference, amount, currency_id):
        """Create a Razorpay order and return necessary data for checkout."""
        _logger.info("Creating Razorpay order for reference: %s, amount: %s, currency_id: %s", reference, amount,
                     currency_id)
        provider = request.env['payment.provider'].sudo().browse(int(provider_id))
        if provider.code != 'custom_razorpay':
            _logger.error("Invalid provider for Razorpay order creation: %s", provider.code)
            return {'error': 'Invalid provider'}

        currency = request.env['res.currency'].browse(int(currency_id))
        try:
            order_data = provider._razorpay_create_order(amount, currency, reference)
            _logger.info("Razorpay order created: %s", order_data)
            return {
                'key_id': provider.custom_razorpay_key_id,
                'order_id': order_data.get('id'),
                'amount': int(amount * 100),  # Convert to paise
                'currency': currency.name
            }
        except Exception as e:
            _logger.error("Failed to create Razorpay order: %s", str(e))
            return {'error': str(e)}

    @http.route('/payment/custom_razorpay/return', type='http', auth='public', methods=['POST', 'GET'], csrf=False)
    def razorpay_return(self, **post):
        """Handle return from Razorpay after payment."""
        _logger.info("Received Razorpay return data: %s", post)
        tx = request.env['payment.transaction'].sudo()._get_tx_from_notification_data('custom_razorpay', post)
        if not tx:
            _logger.error("No transaction found for Razorpay return data: %s", post)
            return request.redirect('/payment/status')

        try:
            result = tx._custom_razorpay_form_validate(post)
            _logger.info("Transaction validation result for %s: %s", tx.reference, result)
        except Exception as e:
            _logger.error("Error validating Razorpay transaction %s: %s", tx.reference, str(e))
            tx._set_error(f"Validation error: {str(e)}")

        return request.redirect('/payment/status')

    @http.route('/payment/custom_razorpay/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def razorpay_webhook(self):
        """Handle Razorpay webhook notifications."""
        data = request.jsonrequest
        _logger.info("Received Razorpay webhook: %s", data)
        event = data.get('event')
        payload = data.get('payload', {}).get('payment', {}).get('entity', {})

        provider = request.env['payment.provider'].sudo().search([('code', '=', 'custom_razorpay')], limit=1)
        if not provider:
            _logger.error("No provider found for webhook")
            return {'status': 'error', 'message': 'Provider not found'}

        # Verify webhook signature
        signature = request.httprequest.headers.get('X-Razorpay-Signature')
        generated_signature = hmac.new(
            provider.custom_razorpay_webhook_secret.encode('utf-8'),
            json.dumps(data, separators=(',', ':')).encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        if signature != generated_signature:
            _logger.warning("Invalid Razorpay webhook signature: expected=%s, received=%s", generated_signature,
                            signature)
            return {'status': 'error', 'message': 'Invalid signature'}

        if event in ('payment.authorized', 'payment.captured'):
            tx = request.env['payment.transaction'].sudo().search([
                ('razorpay_payment_id', '=', payload.get('id'))
            ], limit=1)
            if tx:
                _logger.info("Processing webhook for transaction %s, event: %s", tx.reference, event)
                tx._custom_razorpay_form_validate({
                    'razorpay_payment_id': payload.get('id'),
                    'razorpay_order_id': payload.get('order_id'),
                    'razorpay_signature': signature
                })
            else:
                _logger.warning("No transaction found for webhook payment_id: %s", payload.get('id'))
        elif event == 'payment.failed':
            tx = request.env['payment.transaction'].sudo().search([
                ('razorpay_payment_id', '=', payload.get('id'))
            ], limit=1)
            if tx:
                _logger.info("Marking transaction %s as failed due to webhook", tx.reference)
                tx._set_error("Payment failed via webhook.")
            else:
                _logger.warning("No transaction found for failed webhook payment_id: %s", payload.get('id'))

        return {'status': 'success'}