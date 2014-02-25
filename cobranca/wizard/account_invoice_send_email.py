# -*- encoding: utf-8 -*-

import logging
import time
from osv import osv, fields
from __builtin__ import len

_logger = logging.getLogger(__name__)

class account_invoice_send_email(osv.osv_memory):

    _name = 'account.invoice.send_email'

    def action_send(self, cr, uid, ids, context=None):
        [wizard] = self.browse(cr, uid, ids)
        self.write(cr,uid,wizard.id,{'state': 'doing'})
        invoice_ids = context.get('active_ids', [])
        tam = len(invoice_ids)
        naoenviado = []
        attachment_ids = []
        if tam > 0:
            invoice_pool = self.pool.get('account.invoice')
            email_pool = self.pool.get('email.template')
            partner_pool = self.pool.get('res.partner')
            atach_pool = self.pool.get('ir.attachment')
            template_ids = email_pool.search(cr, uid, [('name', '=', 'faturamento')])
            if not template_ids:
                raise osv.except_osv('Erro', 'Atenção:\nInclua o modelo para o e-mail nomeando como "faturamento"!' )
                return False
                
            x = 0
            for invoice in invoice_pool.browse(cr, uid, invoice_ids):
                #time.sleep(1)
                if wizard.teste:
                    recipients = [wizard.cc]
                else:
                    recipients = []
                    partner = partner_pool.browse(cr, uid, invoice.partner_id.id)
                    if partner.child_ids:
                        for child in partner.child_ids:
                            if child.name[:11] == 'faturamento':
                                recipients.append(child.email)
                    if not recipients:
                        if partner.email:
                            recipients.append(partner.email)
                    if wizard.cc:
                        recipients.append(wizard.cc)
                        
                if recipients:
                    _logger.info(str(invoice.internal_number)+') Recipients: ['+str(recipients)+']')
                    #email = email_pool.browse(cr, uid, template_ids[0])
                    #email_to = email.to  
                    #email_bcc = email.bcc  
                    #email_cc = email.cc  
                    #email_subject = email.subject  'res_id': record.id,
                    #email_body = email.body_html
                    
                    atach_ids = atach_pool.search(cr, uid, [('res_model', '=', 'account.invoice'),('res_id','=',invoice.id)])
                    
                    
                    _logger.info('atach IDs: ['+str(atach_ids)+']')
                    
                    if atach_ids:
#                         for atach in atach_ids:
#                             attachment_ids.append((6,1,[atach]))
                        attachment_ids.append((6,1,atach_ids))
                        email_pool.write(cr, uid, template_ids, {'attachment_ids': attachment_ids})  
                        
                    _logger.info('atach IDs *: '+str(attachment_ids))
                    
                    email_pool.write(cr, uid, template_ids, {'email_to': ','.join(recipients)})
                    email_pool.send_mail(cr, uid, template_ids[0], invoice.id)
                else:
                    _logger.info(str(invoice.internal_number)+') No Recipients....')
                    naoenviado.append(invoice.internal_number)
                    
                x = x + 1
                porcent = (100/tam) * x
                self.write(cr,uid,wizard.id,{'progress_rate': porcent})
        return True 
    
    def _progress_rate(self, cr, uid, ids, name, arg, context=None):
        _logger.info('progress rate')

        return 0

    _columns = {
                'teste': fields.boolean('Teste'),
                'cc': fields.char('C/C',size=128),
                'progress_rate': fields.float('Progress', readonly=True, help="Total dos e-mails enviados."), 
                'state': fields.selection([('init','init'),('doing','doing'),('done','done')])
                }
    _defaults = {
                 'state': 'init'
                 }
    
account_invoice_send_email()