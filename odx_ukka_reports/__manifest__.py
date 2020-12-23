# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

{
    'name': 'Ukka Reports',
    'version': '13.0',
    'depends': ['base','report_xlsx',
    ],
    'author': 'Odox SoftHub',
    'website': 'http://www.odoxsofthub.com',
    'license': 'GPL-3',
    'data': [
        'wizard/deliver_boy_branch_wise_report_wizard_view.xml',
        'wizard/vendor_report_wizard_view.xml',
        'wizard/delivery_time_branch_wise_report_wizard_view.xml',
        'wizard/periodical_report_all_branch_wizard_view.xml',
        'reports/report.xml',

    ],
    'installable': True,
    'application': True,
}