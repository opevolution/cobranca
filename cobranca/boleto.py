# -*- coding: utf-8 -*-

import datetime
from osv import fields, osv


class boleto_partner_config(osv.osv):
    """Boleto Partner Configuration"""
    _name = 'boleto.partner_config'
    _columns = {'name': fields.char(u'Descrição',size=30,required=True),
                'convenio_id': fields.many2one('res.partner.bank', u'Convênio'), 
                'tx_juros': fields.float('Taxa Juros', digits=(12, 6)),
                'tx_multa': fields.float('Taxa Multa', digits=(12, 6)),
                'dias_protesto': fields.integer('Dias Protesto'),
                'instrucoes': fields.text(u'Instruções'),
               }
    _defaults = {
                 'tx_juros': 0,
                 'tx_multa': 0,
                 'dias_protesto': 0,
                }

boleto_partner_config()

class boleto_boleto(osv.osv):
    """Boleto"""
    _name = 'boleto.boleto'
    
    def _get_data_documento(self, cr, uid, ids, context=None):
        dt_atual = datetime.datetime.today()
        return dt_atual.strftime('%Y-%m-%d')
    
    _columns = {
        'name': fields.char('Name', size=20, required=True),
        # do cliente
        'carteira': fields.char('Carteira', size=10, readonly=True, states={'novo': [('readonly', False)]}),
        #'carteira': fields.char('Carteira', size=10),
        'txjuros': fields.float('% Juros', digits=(12, 6)),
        'txmulta': fields.float('% Multa', digits=(12, 6)),
        'instrucoes': fields.text(u'Instruções'),
        'sacado': fields.many2one('res.partner', 'Sacado', required=True),
        # da empresa
        'banco': fields.selection([
                                   ('bb', 'Banco do Brasil'), 
                                   ('real', 'Banco Real'), 
                                   ('bradesco', 'Banco Bradesco'), 
                                   ('caixa', 'Banco Caixa Federal')], 
                                  'Banco', required=True),
        'agencia_cedente': fields.char('Agencia', size=6),
        'conta_cedente': fields.char('Conta', size=8),
        'convenio': fields.char('Convenio', size=8),
        'nosso_numero': fields.integer(u'Nosso Número'),
        'cedente': fields.many2one('res.company', 'Empresa'),
        # da fatura
        'move_line_id': fields.many2one('account.move.line', 'Fatura'),
        'data_vencimento': fields.date('Data do Vencimento'),
        'data_documento': fields.date('Data do Documento'),
        'data_processamento': fields.date('Data do Processamento'),
        'valor': fields.float('Valor', digits=(12, 2)),
        'numero_documento': fields.char(u'Número do Documento', size=20),
        'endereco': fields.char(u'Endereço', size=60),
        #Recebimento
        'vlJuros': fields.float('Vl.Multa', digits=(12, 2)),
        'vlMulta': fields.float('Vl.Juros', digits=(12, 2)),
        'vlDesconto': fields.float('Vl.Desconto', digits=(12, 2)),
        'vlPrincipal': fields.float('Vl.Principal', digits=(12, 2)),
        #Estatus
        'state'         : fields.selection([
            ('novo','Novo'),
            ('enviado','Enviado'),
            ('cancelado','Cancelado'),
            ('recebido','Recebido'),
            ], 'Status', readonly=True),
    }
    _defaults = {
        'name': lambda *a: 'boleto',
        'state' : lambda *a: 'novo',
        'data_documento': _get_data_documento,
        'data_vencimento': _get_data_documento,
         }

boleto_boleto()
