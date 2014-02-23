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
from osv import osv, fields

class cnab_custom_property(osv.osv):
    _name = "cnab.custom_property"

    _columns = {
        'name': fields.char(u'Item', size=30),
        'value': fields.char(u'Valor', size=30),
        'partner_bank_id': fields.many2one('res.partner.bank', u'Convênio'),
    }

cnab_custom_property()    
    
class cnab_arquivo_remessa(osv.osv):
    _name = "cnab.arquivo_remessa"
    
    _columns = {
                'bank_partner_id': fields.many2one('res.partner.bank', u'Cobrança',required=True,domain=[('enable_cobranca', '=', True)]),
                'sacador_id': fields.many2one('res.partner', u'Sacador'),
                'cob_info_id': fields.many2one('boleto.partner_config', u'Padrão Cobrança'),
                'nro_sequencia': fields.integer('Sequencia do CNAB'),
                'data_in': fields.date(u'Data Criação',), 
                'state': fields.selection([('init', 'init'), ('done', 'done'), ('cancel', 'cancel')], 'state', readonly=True),
                }
 
cnab_arquivo_remessa()   
