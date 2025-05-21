from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class RazorpayController(http.Controller):

    @http.route('/payment/razorpay/validate', type='json', auth='public', csrf=False)
    def payment_razorpay_validate(self, **post):
        _logger.info("Razorpay Validation Called with: %s", post)

        order_id = post.get('razorpay_order_id')

        tx = request.env['payment.transaction'].sudo().search([
            ('reference', '=', order_id),
            ('provider_code', '=', 'custom_razorpay'),
            ('state', '=', 'draft'),
        ], limit=1)
        if not tx:
            _logger.error("Transaction not found for order %s", order_id)
            return {'success': False, 'error': 'Transaction not found'}

        tx._set_done(state_message="Payment confirmed by Razorpay")
        _logger.info("Transaction %s marked done", tx.reference)
        return {'success': True}
