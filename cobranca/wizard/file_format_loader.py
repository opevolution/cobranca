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
import time
import netsvc
from tools.translate import _
from osv import osv, fields

from lxml.etree import XML, XMLParser
import logging
import base64

from openerp.addons.cobranca import file_format

_logger = logging.getLogger(__name__)

FORMAT_TYPES = file_format.FORMAT_TYPES

def create_new_rows(func, values, sequence=False):
    return map(lambda *args: (0, 0, func(*args)), values, *([range(len(values))] if sequence else []))

class FileFormatLoader(osv.osv_memory):
    _name = 'cnab.wizard.file_format_loader'
    
    def load(self, cr, uid, ids, context=None):
        pool = self.pool.get('cnab.file_format')
        parser = Parser()
        [wizard] = self.browse(cr, uid, ids)
        xml = base64.b64decode(wizard.file)
        data = parser.parse_schema(xml)
        data['type'] = wizard.type
        if wizard.replace:
            old_ids = pool.search(cr, uid, [('name', '=', data['name'])])
            pool.unlink(cr, uid, old_ids)
        new_id = pool.create(cr, uid, data)
        
        return {
                'type': 'ir.actions.act_window',
                'res_model': 'cnab.file_format',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': new_id,
                #'views': [(resource_id, 'form')],
               }
        
    _columns = {
                'file': fields.binary('File', required=True),
                'type': fields.selection(zip(FORMAT_TYPES, FORMAT_TYPES), 'Type', required=True),
                'replace': fields.boolean('Replace any entries with the same name'),
                }

class Parser(object):

    _total_lenght = 0
    _reg_anterior = False
    
    def parse_schema(self, xml_schema):
        xml = XML(xml_schema, parser=XMLParser(remove_comments=True))
        return self.parse_file(xml)
    
    def parse_file(self, xml):
        _total_lenght = 0
        layout_element = xml.find('FlatFile/layout')
        records_elements = xml.findall('FlatFile/GroupOfRecords/Record')
        return {
                'name': layout_element.find('name').text,
                'version': layout_element.find('version').text,
                'description': layout_element.find('description').text,
                'bank_name': layout_element.find('bank_name').text,
                'bank_code': layout_element.find('bank_code').text,
                'records_ids': create_new_rows(self.parse_record, records_elements),
                }
    
    def parse_record(self, record):
        if self._reg_anterior != False:
            if self._total_lenght != 400:
                _logger.info('Tamanho diferente de 400: '+str(self._reg_anterior.get('name'))+' ['+str(self._total_lenght)+']')
                 
        group_of_fields = record.find('GroupOfFields')
        fields_elements = list(group_of_fields) if group_of_fields is not None else []
        group_of_inner_records = record.find('GroupOfInnerRecords')
        inner_records = list(group_of_inner_records) if group_of_inner_records is not None else []
        is_repeatable = False if 'repeatable' not in record.keys() else (record.get('repeatable') == 'true')
        self._reg_anterior = record
        self._total_lenght = 0
        return {
                'name': record.get('name'),
                'description': record.get('description'),
                'repeatable': is_repeatable,
                'fields_ids': create_new_rows(self.parse_field, fields_elements, sequence=True),
                'records_ids': create_new_rows(self.parse_record, inner_records),
                }
    
    def parse_field(self, field, sequence):
        self._total_lenght = self._total_lenght + int(field.get('length'))
        optional = lambda e, k: e.get(k) if k in e.keys() else False
        optional_int = lambda e, k: int(optional(e, k)) if optional(e, k) is not False else False
        #_logger.info('Tratando Field: '+str(field.get('name')+'['+str(field.get('length'))+'/'+str(self._total_lenght)+']'))
        return {
                'sequence': sequence,
                'type': field.tag,
                'name': field.get('name'),
                'value': optional(field, 'value'),
                'length': int(field.get('length')),
                'position': optional_int(field, 'position'),
                'value_type': optional(field, 'type'),
                'format': optional(field, 'format'),
                'padding': optional(field, 'padding'),
               }
