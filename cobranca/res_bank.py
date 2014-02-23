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

import netsvc
from tools.translate import _
from osv import osv, fields

class res_partner_bank(osv.osv):
    _inherit = 'res.partner.bank'

    _columns = {
        'enable_cobranca': fields.boolean(u'Cobrança'),
        'nro_convenio': fields.char(u'Número Convênio', size=10),
        'cod_carteira': fields.char(u'Carteira', size=10),
        'tx_juros': fields.float('% Juros', digits=(12, 6)),
        'tx_multa': fields.float('% Multa', digits=(12, 6)),
        'dias_protesto': fields.integer('Dias Protesto'),
        'instrucoes': fields.text(u'Instruções'),
        'cod_empresa': fields.char(u'Código da Empresa', size=20),
        'enable_boleto': fields.boolean('Boleto'),
        'enable_cnab': fields.boolean('CNAB'),
        'leiaute_remessa': fields.many2one('cnab.file_format', u'Leiaute Remessa',domain="[('type','=','Arquivo-Remessa')]"),
        'leiaute_envio': fields.many2one('cnab.file_format', u'Leiaute Retorno',domain="[('type','=','Arquivo-Retorno')]"),
        'CNAB_sequence_id': fields.many2one('ir.sequence', u'Sequência'),
        'custom_property_ids': fields.one2many('cnab.custom_property', 'partner_bank_id', u'Propriedades Personalizadas'),
    }
    
