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

from datetime import datetime
import logging
import os

TYPE_ADAPTERS = {
                 'INTEGER': int,
                 'DATE': lambda s: datetime.strptime(s, "%d%m%y").date(),
                 'CHARACTER': lambda s: s,
                }

class CNABParser(object):
    def get_record_formats(self, parent):
        record_formats = dict((r.identifier, r) for r in parent.records_ids)
        for child_record in parent.records_ids:
            record_formats.update(self.get_record_formats(child_record))
        return record_formats
    
    def consume_whitespace(self, cnab_file):
        while True:
            c = cnab_file.read(1)
            if c not in '\r\n':
                cnab_file.seek(-1, os.SEEK_CUR)
                return
            if c == '':
                return
    
    def get_record_format(self, cnab_file, record_formats, idtype_length):
        idtype = cnab_file.read(idtype_length)
        cnab_file.seek(-idtype_length, os.SEEK_CUR)
        if idtype == '':
            return None
        record_format = record_formats[idtype]
        return record_format
    
    def parse_file(self, format, cnab_file):
        record_formats = self.get_record_formats(format)
        idtype_length = len(format.records_ids[0].identifier)
        records = []
        while True:
            record_format = self.get_record_format(cnab_file, record_formats, idtype_length)
            if record_format is None:
                break
            records.append(self.parse_record(record_format, cnab_file))
            self.consume_whitespace(cnab_file)
        return records
    
    def parse_record(self, format, cnab_file):
        record = {}
        for field in format.fields_ids:
            value = cnab_file.read(field.length).strip()
            if value == '':
                value = False
            if value and field.value_type:
                try:
                    adapter = TYPE_ADAPTERS[field.value_type]
                    value = adapter(value)
                except ValueError as e:
                    logging.warn('ValueError: %s, on field %s', repr(e), field.name)
                    raise e
            record[field.name] = value
        return record
