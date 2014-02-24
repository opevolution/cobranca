# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2014  Alexandre Defendi - Open Evolution - Brazil             #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
#                                                                             #
# -versao_modulo  0.0                                                         #
# -versao_arquivo 0.1                                                         #
###############################################################################

{
    'name': 'Cobranca',
    'version': '0.005',
    'category': 'Accounting & Finance',
    'sequence': 1,
    'complexity': 'normal',
    'description': '''
== Módulo Cobrança Bancária =================================================

   + CNAB 400.
   + Boleto
   ''',
    'author': 'Alexandre Defendi @ Open Evoluir',
    'depends': ['base',
                'account',
                'l10n_br_base',
                'l10n_br_account'
                ],
    'init_xml': [],
    'update_xml': ['sequence_type.xml',
                   'root_menus.xml',
                   'cobranca_view.xml',
                   'boleto_view.xml',
                   'file_format_view.xml',
                   'res_bank_view.xml',
                   'sequences.xml',
                   'res_company_view.xml',
                   'res_partner_view.xml',
                   'wizard/file_format_loader_view.xml',
                   'wizard/export_cnab_view.xml',
                   'wizard/import_cnab_view.xml',
                   ],
    'demo_xml': [],
    'installable': True,
    'application': True,
    'certificate': '',
}
