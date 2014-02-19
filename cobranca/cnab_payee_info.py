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

import time
import netsvc
from tools.translate import _
from osv import osv, fields

class CNABPayeeInfo(osv.osv):
    _name = 'cnab.payee_info'
    
    _columns = {
                'codigo_empresa': fields.char(u'Código da Empresa', size=20, required=True),
                'codigo_carteira': fields.char(u'Código da Carteira', size=3, required=True),
                'codigo_agencia': fields.char(u'Código da Agência', size=5, required=True),
                'numero_conta': fields.char(u'Número', size=7, required=True),
                'digito_conta': fields.char(u'Dígito', size=1, required=True),
                'emissao_papeleta': fields.selection((('1', u'Emissão pelo Banco'),
                                                      ('2', u'Apenas processamento')),
                                                     u'Emissão de papeleta de cobrança', required=True),
                'registro_debito_automatico': fields.selection((('N', u'Rejeitar na cobrança (não emitir papeleta)'),
                                                                ('S', u'Registrar na cobrança (emitir papeleta)')),
                                                               u'Dados de débito incorretos', required=True),
                'rateio_credito': fields.boolean(u'Participar no Rateio de Crédito'),
                'aviso_debito_automatico': fields.selection((('2', u'Não emitir'),
                                                             ('1', u'Emitir para endereço no Arquivo-Rememessa'),
                                                             ('3', u'Emitir para endereço no cadastro do banco')),
                                                            'Alerta de Débito Automático', required=True),
                'sequencia_registro': fields.integer(u'Sequencia de Arquivos-Remessa', required=True),
               }
    
    _defaults = {
                 'codigo_empresa': '0',
                 'codigo_carteira': '0',
                 'codigo_agencia': '0',
                 'numero_conta': '0',
                 'digito_conta': '0',
                 'emissao_papeleta': '1',
                 'registro_debito_automatico': 'N',
                 'rateio_credito': True,
                 'aviso_debito_automatico': '1',
                 'sequencia_registro': 0,
                }
