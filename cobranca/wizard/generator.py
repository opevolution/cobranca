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
from cStringIO import StringIO
from datetime import datetime
import os

_logger = logging.getLogger(__name__)

TYPE_ADAPTERS = {
                 'INTEGER': unicode,
                 'DATE': lambda d: d.strftime("%d%m%y"),
                 'CHARACTER': lambda s: s.upper(),
                }

DEBUG = True

class CNABGenerator(object):
   
    def get_record_formats(self, parent):
        record_formats = dict((r.identifier, r) for r in parent.records_ids)
        for child_record in parent.records_ids:
            record_formats.update(self.get_record_formats(child_record))
        return record_formats
    
    def pad_value(self, padding, length, value):
        value = str(value)
        if padding == 'ZERO_LEFT':
            value = value.rjust(length, '0')
        else:
            value = value.ljust(length, ' ')
        return value
    
    def get_record_format(self, cnab_file, record_formats, idtype_length):
        idtype = cnab_file.read(idtype_length)
        cnab_file.seek(-idtype_length, os.SEEK_CUR)
        if idtype == '':
            return None
        record_format = record_formats[idtype]
        return record_format
    
    def generate_file(self, format, records):
        record_formats = self.get_record_formats(format)
        result_file = StringIO()
        Nro = 0
        for record in records:
            if DEBUG:
                linha = '|'
            else:
                linha = ''
            Nro = Nro + 1
            record_format = record_formats[record['IDReg']]
            for field in record_format.fields_ids:
                if DEBUG:
                    valor = self.generate_field(field, record)+'|'
                else:
                    valor = self.generate_field(field, record)
                linha = linha + valor
            if DEBUG == False and len(linha) != 400:
                _logger.warning('Quantidade de caracteres na Linha '+str(Nro)+' = '+str(len(linha)))
            result_file.write(linha+'\r\n')
        result_file.seek(0)
        return result_file

#     def generate_file(self, format, records):
#         record_formats = self.get_record_formats(format)
#         _logger.info('Formatos: '+str(record_formats))
#         result_file = StringIO()
#         for record in records:
#             _logger.info('Registro: ['+str(record['IDReg'])+']')
#             record_format = record_formats[record['IDReg']]
#             _logger.info('Formato de Registro: ['+str(record_format)+']')
#             for field in record_format.fields_ids:
#                 self.generate_field(field, record, result_file)
#             result_file.write('\r\n')
#         result_file.seek(0)
#         return result_file
    
    def generate_field(self, field, record):
        if field.value is False:
            try:
                value = record[field.name]
            except:
                value = self.pad_value(field.padding, field.length, '')
        else:
            value = field.value
        if value is False or value is None:
            value = ''
        if field.value_type:
            adapter = TYPE_ADAPTERS[field.value_type]
            value = adapter(value)
        value = value[:field.length]
        value = self.pad_value(field.padding, field.length, value)
        return value

#     def generate_field(self, field, record, result_file):
#         if field.value is False:
#             try:
#                 value = record[field.name]
#             except:
#                 value = self.pad_value(field.padding, field.length, '')
#         else:
#             value = field.value
#         if value is False or value is None:
#             value = ''
#         if field.value_type:
#             adapter = TYPE_ADAPTERS[field.value_type]
#             value = adapter(value)
#         value = value[:field.length]
#         value = self.pad_value(field.padding, field.length, value)
#         result_file.write(value)
