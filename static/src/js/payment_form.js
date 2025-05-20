/** @odoo-module **/
/* global Razorpay */

import { _t } from '@web/core/l10n/translation';
import { loadJS } from '@web/core/assets';
import paymentForm from '@payment/js/payment_form';

paymentForm.include({
    async _prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow) {
        if (providerCode !== 'custom_razorpay') {
            this._super(...arguments);
            return;
        }

        if (flow === 'token') {
            return;
        }

        this._setPaymentFlow('direct');
    },

    async _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode !== 'custom_razorpay') {
            this._super(...arguments);
            return;
        }

        console.log('Processing Values:', processingValues);

        const razorpayOptions = this._prepareRazorpayOptions(processingValues);

        if (!razorpayOptions.key) {
            console.error('Razorpay Key is missing in options:', razorpayOptions);
            this._displayErrorDialog(_t("Payment processing failed"), _t("Razorpay key is missing."));
            return;
        }

        await loadJS('https://checkout.razorpay.com/v1/checkout.js');

        const RazorpayJS = new Razorpay(razorpayOptions);
        RazorpayJS.open();

        RazorpayJS.on('payment.failed', response => {
            this._displayErrorDialog(_t("Payment processing failed"), response.error.description);
        });
    },

    _prepareRazorpayOptions(processingValues) {
        console.log('Preparing Razorpay Options with:', processingValues);

        return Object.assign({}, processingValues, {
            'key': processingValues['razorpay_key_id'],
            'customer_id': processingValues['razorpay_customer_id'],
            'order_id': processingValues['razorpay_order_id'],
            'description': processingValues['reference'],
            'recurring': processingValues['is_tokenize_request'] ? '1' : '0',
            'handler': response => {
                if (
                    response['razorpay_payment_id'] &&
                    response['razorpay_order_id'] &&
                    response['razorpay_signature']
                ) {
                    window.location = '/payment/status';
                }
            },
            'modal': {
                'ondismiss': () => {
                    window.location.reload();
                }
            },
        });
    }
});
