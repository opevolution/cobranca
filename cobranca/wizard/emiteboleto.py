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

import logging
from pyboleto.bank.real import BoletoReal
from pyboleto.bank.bradesco import BoletoBradesco
from pyboleto.bank.caixa import BoletoCaixa
from pyboleto.bank.bancodobrasil import BoletoBB
from pyboleto.pdf import BoletoPDF
from datetime import datetime, date

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

_logger = logging.getLogger(__name__)

class BoletoGenerator(object):
    
    def generate_boleto(self, cr, user, invoice, conta, linha):
        
        _logger.info('Invoice: '+str(invoice.partner_id.cnpj_cpf))
#        if conta.bank.bic == "001":
        fbuffer = StringIO()
        boleto_pdf = BoletoPDF(fbuffer)

        boleto = BoletoBB(7, 2)

        try:
            juros_dia = float(linha[0]['ValorJurosDia'])
        except ValueError:
            juros_dia = 0
            
        try:
            val_multa = float(linha[0]['ValorMulta'])
        except ValueError:
            val_multa = 0
           
        _logger.info('Após vencimento, multa de R$ '+str(val_multa)+' e mora de R$ '+str(juros_dia))
        
        MsgProtesto = linha[0]['MsgProtesto'] 
        
        boleto.cedente = str(user.company_id.partner_id.legal_name)
        boleto.cedente_logradouro = user.company_id.partner_id.street + ', ' + user.company_id.partner_id.number
        boleto.cedente_cidade = 'Curitiba' #user.company_id.partner_id.l10n_br_city.name
        boleto.cedente_uf = 'PR'
        boleto.cedente_bairro = 'Centro'
        boleto.cedente_cep = str(user.company_id.partner_id.zip)
        
        boleto.sacado_nome = (invoice.partner_id.legal_name or invoice.partner_id.name)
        boleto.sacado_documento = str(invoice.partner_id.cnpj_cpf)
        boleto.sacado_cidade = invoice.partner_id.l10n_br_city_id.name
        boleto.sacado_uf = invoice.partner_id.state_id.code
        boleto.sacado_endereco = "%s, %s" % (invoice.partner_id.street, invoice.partner_id.number)
        boleto.sacado_bairro = invoice.partner_id.district
        boleto.sacado_cep = invoice.partner_id.zip
        
        boleto.sacador_documento = "779.529.449-91"
        boleto.sacador_nome = "Alexandre Defendi"

        boleto.cedente_documento = str(user.company_id.partner_id.cnpj_cpf)
        boleto.carteira = str(conta.cod_carteira)
        boleto.agencia_cedente = conta.bra_number
        boleto.conta_cedente = conta.acc_number
        boleto.data_vencimento = datetime.date(datetime.strptime(invoice.date_due, '%Y-%m-%d'))
        boleto.data_documento = datetime.date(datetime.strptime(invoice.date_invoice, '%Y-%m-%d'))
        boleto.data_processamento = date.today()
        boleto.valor_documento = str(invoice.amount_total)
        #boleto.valor = '100'
        boleto.nosso_numero = invoice.number
        boleto.numero_documento = str(invoice.number)
        boleto.convenio = str(conta.nro_convenio)
        
        Linha_Juros = ''
        if juros_dia > 0 and val_multa > 0:
            Linha_Juros = u'Após vencimento, multa de R$ %.2f e mora de R$ %.2f .\r\n' % (val_multa,juros_dia)
        
        if MsgProtesto:
            Linha_Juros = Linha_Juros + MsgProtesto + '\r\n'
        
        if conta.instrucoes:
            boleto.instrucoes = Linha_Juros + conta.instrucoes + '\r\n'
        else:
            boleto.instrucoes = Linha_Juros
        
        
        boleto.especie = 'R$'
        boleto.especie_documento = 'R$'
        boleto.aceite = 'N'
        boleto.quantidade = ''
        #boleto.nosso_numero = 1
        boleto.sacado = [
                         u"%s - %s" % (invoice.partner_id.cnpj_cpf,(invoice.partner_id.legal_name or invoice.partner_id.name)),
                         u"%s, %s - %s - %s - %s - Cep. %s" % (invoice.partner_id.street, invoice.partner_id.number, invoice.partner_id.district, invoice.partner_id.l10n_br_city_id.name, invoice.partner_id.state_id.code, invoice.partner_id.zip),
                         u'',]

#             boleto.sacado = [
#                 "%s" % (invoice.partner_id.legal_name or invoice.partner_id.name),
#                 "%s, %s - %s - %s - Cep. %s" % (invoice.partner_id.street, invoice.partner_id.number, invoice.partner_id.district, invoice.partner_id.city, invoice.partner_id.zip),
#                 ""
#                 ]
#         nosso_numero = str(boleto.format_nosso_numero())
#         linha[0]['NossoNumero'] = nosso_numero[:17]
#         _logger.info('NossoNumero: '+str(boleto.format_nosso_numero()))
        boleto_pdf.drawBoleto(boleto)
        boleto_pdf.nextPage()

        boleto_pdf.save()

        fbuffer.seek(0)
        conteudo = fbuffer.read()
        res = conteudo
        return res
            
            
        
