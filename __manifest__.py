# -*- coding: utf-8 -*-
{
    'name': 'Razorpay Payment Gateway',
    'version': '1.0',
    'summary': 'Razorpay Payment Gateway Integration',
    'author': 'Hafsana CA',
    'depends': ['base','website','payment'],
    'data': [
            'data/payment_provider_data.xml',
            'views/payment_provider_views.xml',
            'views/payment_razorpay_templates.xml',
    ],
    'assets': {
            'web.assets_frontend': [
                'custom_razorpay/static/src/js/payment_form.js',
            ],
    },
    'installable': True,
    'application': False,
}
