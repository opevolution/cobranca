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

from cStringIO import StringIO
from decimal import Decimal
import logging
import base64

from parser import CNABParser

class CNABImporter(osv.osv_memory):
    _name = 'cnab.wizard.importer'
    
    def load_format(self, cr, uid):
        pool = self.pool.get('cnab.file_format')
        try:
            format_id = pool.search(cr, uid, [('type', '=', 'Arquivo-Retorno')])
            [format] = pool.browse(cr, uid, format_id)
            return format
        except ValueError:
            raise osv.except_osv('Error', 'CNAB File format for Arquivo-Retorno not found')
        return format
    
    def generate_payment_with_journal(self, cr, uid, journal_id, partner_id,
                                      amount, entry_name, date, should_validate, context):
        """
        Generate a voucher for the payment

        It will try to match with the invoice of the order by
        matching the payment ref and the invoice origin.

        The invoice does not necessarily exists at this point, so if yes,
        it will be matched in the voucher, otherwise, the voucher won't
        have any invoice lines and the payment lines will be reconciled
        later with "auto-reconcile" if the option is used.

        """
        voucher_obj = self.pool.get('account.voucher')
        voucher_line_obj = self.pool.get('account.voucher.line')
        move_line_obj = self.pool.get('account.move.line')
        
        journal = self.pool.get('account.journal').browse(
            cr, uid, journal_id, context=context)
        
        voucher_vals = {'reference': entry_name,
                        'journal_id': journal.id,
                        'amount': amount,
                        'date': date,
                        'partner_id': partner_id,
                        'account_id': journal.default_credit_account_id.id,
                        'currency_id': journal.company_id.currency_id.id,
                        'company_id': journal.company_id.id,
                        'type': 'receipt', }
        voucher_id = voucher_obj.create(cr, uid, voucher_vals, context=context)
        
        # call on change to search the invoice lines
        onchange_voucher = voucher_obj.onchange_partner_id(
            cr, uid, [],
            partner_id=partner_id,
            journal_id=journal.id,
            amount=amount,
            currency_id=journal.company_id.currency_id.id,
            ttype='receipt',
            date=date,
            context=context)['value']
            
        # keep in the voucher only the move line of the
        # invoice (eventually) created for this order
        matching_line = {}
        if onchange_voucher.get('line_cr_ids'):
            voucher_lines = onchange_voucher['line_cr_ids']
            line_ids = [line['move_line_id'] for line in voucher_lines]
            matching_ids = [line.id for line
                            in move_line_obj.browse(
                                cr, uid, line_ids, context=context)
                            if line.ref == entry_name]
            matching_lines = [line for line
                              in voucher_lines
                              if line['move_line_id'] in matching_ids]
            if matching_lines:
                matching_line = matching_lines[0]
                matching_line.update({
                    'amount': amount,
                    'voucher_id': voucher_id,
                })
                
        if matching_line:
            voucher_line_obj.create(cr, uid, matching_line, context=context)
        if should_validate:
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(
                uid, 'account.voucher', voucher_id, 'proforma_voucher', cr)
        return voucher_id
    
    def _pay_invoice(self, cr, uid, journal, invoice, payment_date, payment_amount):
        period_obj = self.pool.get('account.period')
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'account.voucher')
        [period_id] = period_obj.find(cr, uid, payment_date, {'company_id': company_id})
        account_id = invoice.partner_id.property_account_receivable.id
        self.generate_payment_with_journal(cr, uid, journal.id, invoice.partner_id.id, payment_amount, invoice.move_id.ref, payment_date, True, context={'invoice_id': invoice.id})
    
    def _cents_to_euros(self, value):
        return float((Decimal(value) / Decimal('100')).quantize(Decimal('1.00')))
    
    def import_file(self, cr, uid, ids, context=None):
        invoice_pool = self.pool.get('account.invoice')
        [wizard] = self.browse(cr, uid, ids)
        format = self.load_format(cr, uid)
        data = base64.b64decode(wizard.file)
        cnab_file = StringIO(data)
        try:
            parser = CNABParser()
            payments = [line for line in parser.parse_file(format, cnab_file) if line['IDReg'] == '1']
        except:
            raise osv.except_osv('Error', 'Invalid File')
        journal = wizard.bank_id.journal_id
        if not journal:
            raise osv.except_osv('Error', 'Please configure bank journal')
        not_found = []
        for line in payments:
            try:
                value = self._cents_to_euros(line['ValorPago'])
                payment_date = line['DataCredito'].isoformat()
                invoice_ids = invoice_pool.search(cr, uid, [('number', '=', line['IdentificacaoTitulo1'])])
                [invoice] = invoice_pool.browse(cr, uid, invoice_ids)
                print "I'm paying invoice %s with %s euros" % (invoice_id, value)
                self._pay_invoice(cr, uid, journal, invoice, payment_date, value)
            except ValueError:
                not_found.append(str(line['IdentificacaoTitulo1']))
        logging.error('Couldn\'t find the following invoices: %s', ', '.join(not_found))
        return {'type': 'ir.actions.act_window_close'}
    
    _columns = {
                'file': fields.binary('File', required=True),
                'bank_id': fields.many2one('res.partner.bank', 'Bank', domain=[('bank.enable_cnab', '=', True)])
                }
