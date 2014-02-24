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
import unicodedata
from tools.translate import _
from osv import osv, fields

from datetime import datetime, date, timedelta
from decimal import Decimal, Context, Inexact
from itertools import count

import logging
import base64
import re

#from collections import OrderedDict

from generator import CNABGenerator
from emiteboleto import BoletoGenerator

_logger = logging.getLogger(__name__)

def counter(start=0):
    try:
        return count(start=start)
    except TypeError:
        c = count()
        c.next()
        return c

if hasattr(Decimal, 'from_float'):
    float_to_decimal = Decimal.from_float
else:
    def float_to_decimal(f):
        "Convert a floating point number to a Decimal with no loss of information"
        n, d = f.as_integer_ratio()
        numerator, denominator = Decimal(n), Decimal(d)
        ctx = Context(prec=60)
        result = ctx.divide(numerator, denominator)
        while ctx.flags[Inexact]:
            ctx.flags[Inexact] = False
            ctx.prec *= 2
            result = ctx.divide(numerator, denominator)
        return result

def somente_ascii(valor):
    ant = unicode(valor)
    ret = unicodedata.normalize('NFD', ant).encode('ascii', 'ignore')
    return ret

class CNABExporter(osv.osv_memory):
    _name = 'cnab.wizard.exporter'
    
    _sequencia = 0
    
    _cnab_name = ''
    
    _debug = True
    
    def log(self, msg, value):
        if self._debug == True:
            _logger.info(self._name+"=["+str(msg)+": '"+str(value)+"']")
            
    def _round(self, v):
        v = float_to_decimal(v)
        return (v * Decimal('100')).quantize(1)
    
    def _only_digits(self, v):
        return re.sub('[^0-9]', '', v)
    
    def _get_param(self, cr, uid, PartnerBankId, param):
        res = False
        CnabCustomPool = self.pool.get('cnab.custom_property')
        CnabCustom_Ids = CnabCustomPool.search(cr, uid, [('name','=',param),('partner_bank_id','=',PartnerBankId)])
        if CnabCustom_Ids:
            CnabCustomId = CnabCustom_Ids[0]
            [CnabCustom] = CnabCustomPool.browse(cr, uid, [CnabCustomId])
            res = CnabCustom.value
        return res
    
    def _get_address(self, partner):
        parts = []
        if partner.street:
            parts.append(partner.street)
        if partner.street2:
            parts.append(partner.street2)
        return ",".join(parts)
    
    def _header(self, cr, user, conta):
        obj_seq = self.pool.get('ir.sequence')
        c = {}
        self._sequencia = obj_seq.next_by_id(cr, user.id, conta.CNAB_sequence_id.id, context=c)
#        _logger.info(str(res))
#         cnab_info = user.company_id.cnab_info_id
#         assert cnab_info != False, "Company must have CNAB information"
        if conta.bank.bic == "001":
            res = {
                    'IDReg': '0',
                    'NroAgencia': int(conta.bra_number),
                    'DvAgencia': conta.bra_number_dig,
                    'NroContaCorrente': int(conta.acc_number),
                    'DvContaCorrente': conta.acc_number_dig,
                    'NomeCedente': somente_ascii(user.company_id.partner_id.legal_name).upper(),
                    'DataGravacaoArquivo': date.today(),
                    'NroSequencialRemessa': self._sequencia,
                    'NroConvLider': 0,
                   }
        elif conta.bank.bic == "999":
            res = {
                    'IDReg': '0',
                    'CodigoEmpresa': 0, #cnab_info.codigo_empresa,
                    'NomeEmpresa': user.company_id.name,
                    'DataGravacaoArquivo': date.today(),
                    'NroSequencialArquivo': self.pool.get('ir.sequence').get(cr, user.id, 'cnab.bradesco.remessa.sequence'),
                   }
        return res
    
    def _calc_juros_dia(self, valor, taxa):
        return round((valor * taxa)/30,2)
    
    def _invoice(self, cr, user, ids, invoice, conta):
        
#         partner_cnab_info = invoice.partner_id.cnab_info_id
#         assert partner_cnab_info != False, "Partner must have CNAB information"
#         company_cnab_info = user.company_id.cnab_info_id
#         assert company_cnab_info != False, "Company must have CNAB information"
#         rateio_credito = ("R" if company_cnab_info.rateio_credito else " ")
        def preenche_sacador_BB(self, cr, uid, idSacador):
            res = False
            sacador = self.pool.get('res.partner').browse(cr, uid, idSacador) 
            self.log('CNPJ', sacador.cnpj_cpf)
            self.log('Nome', sacador.legal_name)
            docSac = self._only_digits(str(sacador.cnpj_cpf))
            if sacador.is_company:
                res = str(somente_ascii(sacador.legal_name[:21]).rjust(21)+' CNPJ'+docSac)
            else:
                res = str(somente_ascii(sacador.legal_name[:25]).rjust(21)+' CPF'+docSac)
            self.log('Sacador', res)    
            return res
        
        [wizard] = self.browse(cr, user.id, ids)
        
        InfoCob = False
        
        if wizard.cob_info_id:
            [InfoCob] = self.pool.get("boleto.partner_config").browse(cr, user.id, [wizard.cob_info_id.id])

        self.log("wizard ",str(wizard.sacador_id.id)) 
        
        identificacao_inscricao_sacado = ('01' if not invoice.partner_id.is_company else '02')
        val_fatura = invoice.amount_total
        res = False
        if conta.bank.bic == "001":
            NossoNumero = "0000000000" 
            IndSacador = ' '
            TxtSacador = ' '
            codigo_multa = '9'
            data_ini_cob = '000000'
            valor_multa = 0
            valor_juros_dia = 0
            NroDiaProt = 0
            InstCodific = 0
            MsgProtesto = ''
            DocSacador = ''
            NomeSacador = ''

            if conta.cod_carteira in ['12','15','17'] and conta.enable_boleto == True:
                NossoNumero = "%s%s" % (conta.nro_convenio.rjust(7),str(invoice.number).zfill(10))
                self.log("Nosso Número", NossoNumero)
            
            if wizard.sacador_id:
                IndSacador = 'A'
                DocSacador = wizard.sacador_id.cnpj_cpf
                NomeSacador = wizard.sacador_id.legal_name
                self.log("Sacador ID",str(wizard.sacador_id.id))
                TxtSacador = preenche_sacador_BB(self, cr, user.id, wizard.sacador_id.id)
                
            self.log("Documento Sacador",str(DocSacador))
            self.log("Nome Sacador",str(NomeSacador))
            self.log("Sacador",str(TxtSacador))
            
            if InfoCob:
                if InfoCob.tx_multa > 0:
                    codigo_multa = '1'
                    novadata = datetime.strptime(invoice.date_due, '%Y-%m-%d') + timedelta(days=1)
                    data_ini_cob = novadata.strftime("%d%m%y")
                    valor_multa = round(val_fatura*InfoCob.tx_multa,2)
                if InfoCob.tx_juros and InfoCob.tx_juros > 0:
                    valor_juros_dia = self._calc_juros_dia(val_fatura,InfoCob.tx_juros)
            else:
                if conta.tx_multa and conta.tx_multa > 0:
                    codigo_multa = '1'
                    novadata = datetime.strptime(invoice.date_due, '%Y-%m-%d') + timedelta(days=1)
                    data_ini_cob = novadata.strftime("%d%m%y")
                    valor_multa = round(val_fatura*conta.tx_multa,2)
                if conta.tx_juros and conta.tx_juros > 0:
                    valor_juros_dia = self._calc_juros_dia(val_fatura,conta.tx_juros)

            if InfoCob:
                NroDiaProt = InfoCob.dias_protesto
            else:
                NroDiaProt = conta.dias_protesto
            self.log("Nro Dias Protesto", str(NroDiaProt))
                
            if NroDiaProt in [3,4,5,10,15,20,25,30,45]:
                InstCodific = NroDiaProt
                MsgProtesto = u'Protestar no %d dia útil após vencido' % NroDiaProt
                NroDiaProt = 0
            elif NroDiaProt >= 6 and NroDiaProt <= 29:
                InstCodific = 6
                MsgProtesto = u'Protestar no %d dia após vencido' % NroDiaProt
            else:
                InstCodific = 7
                NroDiaProt = 0
                MsgProtesto = False
            try:
                if invoice.contract_id:
                    Demon = u'REFERENTE AO CONTRATO NÚMERO %s, NFS-e NÚMERO %06d' % (invoice.contract_id.name, int(invoice.internal_number) )
                else:
                    Demon = u'REFERENTE A NFS-e NÚMERO %06d' % (int(invoice.internal_number) )
            except:
                Demon = u'REFERENTE A NFS-e NÚMERO %06d' % (int(invoice.internal_number) )
                
            self.log("Intrução Codificadas", str(InstCodific))
            self.log("Nro Dias Protesto", str(NroDiaProt))
                            
            self.log('Juros ao dia',str(valor_juros_dia))
            self.log('Multa após o vencimento',str(valor_multa)+' a partir da data de '+data_ini_cob)

            res= [{
                    'IDReg': '7',
                    'TpInscrCedente': '02',
                    'CnpjCpfCedente': self._only_digits(user.company_id.partner_id.cnpj_cpf),
                    'NroAgencia': int(conta.bra_number),
                    'DvAgencia': conta.bra_number_dig,
                    'NroContaCorrente': int(conta.acc_number),
                    'DvContaCorrente': conta.acc_number_dig,
                    'NroConvCobCedente': conta.nro_convenio,
                    'CodCtrolEmpresa': str(invoice.id),
                    'NossoNumero': NossoNumero,
                    'IndMensagemSacAva': IndSacador,
                    'VariacaoCarteira': self._get_param(cr, user.id, conta.id, "VariacaoCarteira"),
                    'ContaCaucao': 0,
                    'NumeroBordero': 0,
                    'TipoCobranca': ' ',
                    'CarteiraCobranca': conta.cod_carteira,
                    'Comando': 1,
                    'NroTitulo': invoice.number,
                    'DataVencimentoTitulo': datetime.strptime(invoice.date_due, '%Y-%m-%d'),
                    'ValorTitulo': self._round(invoice.amount_total),
                    'EspecieTitulo': self._get_param(cr, user.id, conta.id, "EspecieTitulo"),
                    'AceiteTitulo': self._get_param(cr, user.id, conta.id, "AceiteTitulo"),
                    'DataEmissaoTitulo': datetime.strptime(invoice.date_invoice, '%Y-%m-%d'),
                    'InstrucaoCodificada1': InstCodific,
                    'InstrucaoCodificada2': 0,
                    'MoraDiaria': self._round(valor_juros_dia),
                    'ValorJurosDia': valor_juros_dia,
                    'ValorMulta': valor_multa,
                    'DataLimiteDesconto': '000000',
                    'ValorDesconto': 0,
                    'ValorIOF': 0,
                    'ValorAbatimento': 0,
                    'TipoInscSacado': identificacao_inscricao_sacado,
                    'CnpjCpfSacado': self._only_digits(invoice.partner_id.cnpj_cpf),
                    'NomeSacado': somente_ascii(invoice.partner_id.name).upper(),
                    'EnderecoSacado': somente_ascii(invoice.partner_id.street + ', '+ invoice.partner_id.number).upper(),
                    'BairroSacado': somente_ascii(invoice.partner_id.district).upper(),
                    'CepSacado': invoice.partner_id.zip,
                    'CidadeSacado': somente_ascii(invoice.partner_id.l10n_br_city_id.name).upper(),
                    'UfCidadeSacado': invoice.partner_id.state_id.code,
                    'DocSacador': DocSacador,  #Boleto
                    'NomeSacador': NomeSacador, #Boleto
                    'txtDemonstra': Demon, #Boleto
                    'Avalista-2Mensagem': TxtSacador,
                    'DiasProtesto': NroDiaProt,
                    'MsgProtesto': MsgProtesto,
                    }, {
                    'IDReg': '51',
                    'TipoServico': '99',
                    'CodMulta': codigo_multa,
                    'DataInicioCobranca': data_ini_cob,
                    'ValorPercMulta': self._round(valor_multa),
                    }]
        elif conta.bank.bic == "999": 
            res = [{
                    'IDReg': '1',
#                     'AgenciaDebito': partner_cnab_info.codigo_agencia,
#                     'DigitoAgenciaDebito': partner_cnab_info.digito_agencia,
#                     'RazaoContaCorrenteDebito': partner_cnab_info.razao_conta,
#                     'ContaCorrenteDebito': partner_cnab_info.numero_conta,
#                     'DigitoContaCorrenteDebito': partner_cnab_info.digito_conta,
#                     'Carteira': company_cnab_info.codigo_carteira,
#                     'AgenciaCedente': company_cnab_info.codigo_agencia,
#                     'ContaCorrente': company_cnab_info.numero_conta,
#                     'DigitoContaCorrente': company_cnab_info.digito_conta,
#                     'NroControleParticipante': invoice.id,
#                     'Multa': 0, #FIXME
#                     'PercentagemMulta': 0, #FIXME
#                     'NossoNumero': 0, #FIXME
#                     'EmissaoPapeletaCobranca': company_cnab_info.emissao_papeleta,
#                     'EmissaoPapeletaDebitoAutomatico': company_cnab_info.registro_debito_automatico,
#                     'IndicadorRateioCredito': rateio_credito,
#                     'AvisoDebitoAutomatico': company_cnab_info.aviso_debito_automatico,
#                     'NDocumento': invoice.number,
#                     'DataVencimentoTitulo': datetime.strptime(invoice.date_due, '%Y-%m-%d'),
#                     'ValorTitulo': self._round(invoice.amount_total),
#                     'EspecieTitulo': 1, #FIXME
#                     'Identificacao': 'N', #FIXME
#                     'DataEmissaoTitulo': date.today(),
#                     '1Instrucao': 0, #FIXME
#                     '2Instrucao': 0, #FIXME
#                     'MoraDiaria': 0, #FIXME
#                     'DataLimiteDesconto': date(2013, 05, 15), #FIXME
#                     'ValorDesconto': 0, #FIXME
#                     'ValorAbatimento': 0, #FIXME
#                     'IdentificacaoInscricaoSacado': identificacao_inscricao_sacado,
#                     'NInscricaoSacado': self._only_digits(invoice.partner_id.cnpj_cpf),
#                     'NomeSacado': invoice.partner_id.name,
#                     'EnderecoCompleto': self._get_address(invoice.partner_id),
#                     '1Mensagem': invoice.comment,
#                     'Cep': invoice.partner_id.zip,
                    'Avalista-2Mensagem': ' ', #FIXME
                    }, {
                    'IDReg': '2',
                    'Mensagem1': ' ', #FIXME
                    'Mensagem2': ' ', #FIXME
                    'Mensagem3': ' ', #FIXME
                    'Mensagem4': ' ', #FIXME
                    'Filler': ' ', #?
#                     'Carteira': company_cnab_info.codigo_carteira,
#                     'Agencia': company_cnab_info.codigo_agencia,
#                     'ContaCorrente': company_cnab_info.numero_conta,
#                     'DigitoCC': company_cnab_info.digito_conta,
                    'NossoNumero': 0, #FIXME
                    }]
        return res
    
    def _trailer(self):
        return {'IDReg': '9'}
    
    def prepare_data(self, cr, uid, ids, format, account_id, invoice_ids):
        invoice_pool = self.pool.get('account.invoice')
        [user] = self.pool.get('res.users').browse(cr, uid, [uid])
        [conta] = self.pool.get('res.partner.bank').browse(cr, uid, [account_id])
        
        lines = [self._header(cr, user, conta)]
        
        for invoice in invoice_pool.browse(cr, uid, invoice_ids):
            if not invoice.state == 'draft':
                line = self._invoice(cr, user, ids, invoice, conta)
                if conta.enable_boleto:
                    self.geraBoleto(cr, user, invoice, conta, line)
                lines.extend(line)
        lines.append(self._trailer())
         
        #add sequence numbers
        for i, line in zip(counter(start=1), lines):
            line['NroSequencialRegistro'] = i
            
        return lines
    
    def load_format(self, cr, uid, account_id):
        formato = False
        pool = self.pool.get('cnab.file_format')
        account = self.pool.get('res.partner.bank').browse(cr, uid, account_id)
        try:
            format_id = pool.search(cr, uid, [('id', '=', account.leiaute_remessa.id)])
            [formato] = pool.browse(cr, uid, format_id)
            return formato
        except ValueError:
            raise osv.except_osv('Error', 'CNAB File format for Arquivo-Remessa not found')
        return formato

    def geraBoleto(self, cr, user, invoice, conta, linha):
        context = {}
        boleto = BoletoGenerator()
        result = boleto.generate_boleto(cr, user, invoice, conta, linha)
        
        boleto_name='Boleto_'+str(invoice.number).zfill(6)+'_'+time.strftime('%Y%m%d%H%M%S')+'.pdf'
        self._cnab_name='cnab_'+str(invoice.number).zfill(6)+'_'+time.strftime('%Y%m%d%H%M%S')+'.txt'
        attach_id=self.pool.get('ir.attachment').create(cr, user.id, {
                                                                  'name': boleto_name,
                                                                  'datas': base64.encodestring(result),
                                                                  'datas_fname': boleto_name,
                                                                  'res_model': 'account.invoice',
                                                                  'res_id': invoice.id,
                                                                    }, context=context)
        attach_id=self.pool.get('ir.attachment').create(cr, user.id, {
                                                                  'name': boleto_name,
                                                                  'datas': base64.encodestring(result),
                                                                  'datas_fname': boleto_name,
                                                                  'res_model': 'res.partner',
                                                                  'res_id': invoice.partner_id.id,
                                                                    }, context=context)
        
        return result
    
    def do_save_file(self, cr, uid, ids, file):
        context = {}
        [wizard] = self.browse(cr, uid, ids) 
        ArqName = wizard.filename
        ArquivoRemessa = self.pool.get('cnab.arquivo_remessa')
        valor = {
                 'bank_partner_id': wizard.bank_partner_id.id,
                 'sacador_id': wizard.sacador_id.id,
                 'cob_info_id': wizard.cob_info_id.id,
                 'nro_sequencia': wizard.Nro_Seq,
                 'data_in': wizard.data_in,
                 }
        _logger.info(str(valor))
        idRemessa = ArquivoRemessa.create(cr,uid,valor,context)
        attach_id=self.pool.get('ir.attachment').create(cr, uid, {
                                                                  'name': ArqName,
                                                                  'datas': base64.encodestring(file),
                                                                  'datas_fname': ArqName,
                                                                  'res_model': 'cnab.arquivo_remessa',
                                                                  'res_id': idRemessa,
                                                                    }, context=context)
        
        return True
    
    def serialize(self, cr, uid, format, data):
#        fake_data = [OrderedDict([(u'IDReg', '0'), (u'IdentificacaoRemessa', 1), (u'LiteralRemessa', 'REMESSA'), (u'CodigoServico', 1), (u'LiteralServico', 'COBRANCA'), (u'CodigoEmpresa', 74017), (u'NomeEmpresa', 'ASSOCIACAO MANTENEDORA ASSISTE'), (u'NumeroBanco', 237), (u'NomeBanco', 'BRADESCO'), (u'DataGravacaoArquivo', datetime.date(2013, 4, 24)), (u'Branco', False), (u'IdentificacaoSistema', 'MX'), (u'NroSequencialArquivo', 9000461), (u'Branco2', False), (u'NroSequencialRegistroH', 1)]), OrderedDict([(u'IDReg', '1'), (u'AgenciaDebito', '00000'), (u'DigitoAgenciaDebito', False), (u'RazaoContaCorrenteDebito', '00000'), (u'ContaCorrenteDebito', '0000000'), (u'DigitoContaCorrenteDebito', '0'), (u'Zero', 0), (u'Carteira', 9), (u'AgenciaCedente', 160), (u'ContaCorrente', 82800), (u'DigitoContaCorrente', 9), (u'NroControleParticipante', False), (u'CodigoBanco', 237), (u'Zeros', 0), (u'NossoNumero', 130001042568L), (u'DescontoBonificacaoDia', 0), (u'EmissaoPapeletaCobranca', 1), (u'EmissaoPapeletaDebitoAutomatico', 'S'), (u'Branco3', False), (u'IndicadorRateioCredito', False), (u'AvisoDebitoAutomatico', False), (u'Branco4', False), (u'IdentificacaoOcorrencia', 1), (u'NDocumento', '0000080631'), (u'DataVencimentoTitulo', datetime.date(2013, 5, 15)), (u'ValorTitulo', 6250), (u'BancoEncarregadoCobranca', 0), (u'AgenciaDepositaria', 0), (u'EspecieTitulo', 1), (u'Identificacao', 'N'), (u'DataEmissaoTitulo', datetime.date(2013, 4, 24)), (u'1Instrucao', 0), (u'2Instrucao', 0), (u'MoraDiaria', 0), (u'DataLimiteDesconto', 150513), (u'ValorDesconto', 0), (u'ValorIOF', 0), (u'ValorAbatimento', 0), (u'IdentificacaoInscricaoSacado', 1), (u'NInscricaoSacado', 20507679865L), (u'NomeSacado', 'SANDRA RIBEIRO DA SILVA ROCHA'), (u'EnderecoCompleto', 'R ESTRELA D OESTE,310'), (u'1Mensagem', False), (u'Cep', '06721010'), (u'Avalista-2Mensagem', False), (u'NroSequencialRegistroD', 2)]), OrderedDict([(u'IDReg', '2'), (u'Mensagem1', 'TAXA CERIMONIA DE FORMATURA                                                    .'), (u'Mensagem2', '941 FELIPE SILVA ROCHA                                                         .'), (u'Mensagem3', '8 PARCELAS                                                                     .'), (u'Mensagem4', 'APOS 60 DIAS PAGAVEL SOMENTE NA TESOURARIA DO COLEGIO                          .'), (u'Filler', False), (u'Carteira', 9), (u'Agencia', 160), (u'ContaCorrente', 82800), (u'DigitoCC', '9'), (u'NossoNumero', '13000104256'), (u'DigitoNN', '8'), (u'sequencia', 3)]), OrderedDict([(u'IDReg', '9'), (u'Branco5', False), (u'NroSequencialRegistroT', 4)])]
        generator = CNABGenerator()
        result = generator.generate_file(format, data).read()
        return result
    
    def export(self, cr, uid, ids, context=None):
        [wizard] = self.browse(cr, uid, ids)
        invoice_ids = context.get('active_ids', [])
            
        account_id = wizard.bank_partner_id.id
        #_logger.info('Banco ID:' + str(account_id))
        format = self.load_format(cr, uid, account_id)
        data = self.prepare_data(cr, uid, ids, format, account_id, invoice_ids)
        result = self.serialize(cr, uid, format, data)
        encoded_result = base64.b64encode(result)
        self.write(cr, uid, [wizard.id], {'Nro_Seq': self._sequencia,'filename': self._cnab_name,'file': encoded_result, 'state': 'done'})
        self.do_save_file(cr, uid, [wizard.id], result)
        
        return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': wizard.id,
                #'views': [(resource_id, 'form')],
                'target': 'new',
               }
        
    _columns = {
                'file': fields.binary('File', readonly=True),
                'filename': fields.char('Filename', size=128),
                'bank_partner_id': fields.many2one('res.partner.bank', u'Cobrança',required=True,domain=[('enable_cnab', '=', True)]),
                'sacador_id': fields.many2one('res.partner', u'Sacador'),
                'cob_info_id': fields.many2one('boleto.partner_config', u'Padrão Cobrança'),
                'Nro_Seq': fields.integer('Sequencia do CNAB'),
                'data_in': fields.date(u'Data Criação',), 
                #'format': fields.many2one('cnab.file_format', 'Format', required=True),
                'state': fields.selection([('init', 'init'), ('done', 'done')], 'state', readonly=True),
                }
    
    _defaults = {
                 'state': 'init',
                 'filename': 'result.txt',
                 'data_in': lambda *a: time.strftime('%Y-%m-%d'),
                 }
