#!/usr/bin/env python3
#
# Copyright 2016 Kenny Chan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import sqlite3
import sys
import subprocess
import contextlib
import tempfile
import os
import pathlib
import xml.etree.ElementTree as ET
import logging


logging.basicConfig(level=logging.INFO)


@contextlib.contextmanager
def mount(dmg):
    '''Mounts a *.dmg in a temporary folder.

    Returns the mount point (the Path of the temporary folder) which one could
    read the content of the *.dmg.
    '''
    with tempfile.TemporaryDirectory() as folder:
        logging.info('Mounting %s onto %s...', dmg, folder)
        subprocess.run([
            'hdiutil', 'attach',
            '-readonly', '-noverify', '-noautoopen', '-nobrowse', '-quiet',
            '-mountpoint', folder, dmg
        ])
        logging.info('Mounting %s onto %s done.', dmg, folder)
        try:
            yield pathlib.Path(folder)
        finally:
            subprocess.run(['hdiutil', 'detach', folder, '-quiet'])



def format_language(lang):
    return lang.replace('-', '_')



def get_language(lg):
    '''Obtains the language code for a *.lg.'''
    xml = ET.parse(str(lg))
    return format_language(next(xml.iter('tran')).get('loc'))



def add_file(db, project, path):
    '''Adds a localization file. Returns the ID for that file.
    '''
    cursor = db.execute('SELECT id FROM Files WHERE path = ?', [path])
    try:
        return next(cursor)[0]
    except StopIteration:
        with db:
            cursor = db.execute('INSERT INTO Files (project, path) VALUES (?, ?)', [project, path])
            return cursor.lastrowid



def add_text_item(db, text_item, file_id):
    description = text_item.find('Description').text
    position = text_item.find('Position').text
    translation_set = text_item.find('TranslationSet')
    base = translation_set.find('base')
    base_language = format_language(base.get('loc'))
    base_content = base.text
    with db:
        for tran in translation_set.findall('tran'):
            tran_language = format_language(tran.get('loc'))
            tran_content = tran.text
            sql = 'UPDATE Localizations SET {} = ? WHERE file_id = ? AND position = ?'.format(tran_language)
            cursor = db.execute(sql, [tran_content, file_id, position])
            if not cursor.rowcount:
                sql = 'INSERT INTO Localizations (file_id, position, description, {}, {}) VALUES (?, ?, ?, ?, ?)'.format(base_language, tran_language)
                db.execute(sql, [file_id, position, description, base_content, tran_content])



def add_localization_project(db, lg):
    '''Adds the localization project *.lg into the database.'''
    xml = ET.parse(str(lg))
    logging.debug('Processing %s', lg)
    project = xml.find('ProjName').text
    for f in xml.findall('File'):
        path = f.find('Filepath').text
        file_id = add_file(db, project, path)
        for text_item in f.findall('TextItem'):
            add_text_item(db, text_item, file_id)




def convert(db, dmg):
    with mount(dmg) as folder:
        files = list(folder.glob('*.lg'))
        language = get_language(files[0])
        add_language(db, language)
        for lg in files:
            add_localization_project(db, lg)




def create_table(db):
    '''Creates the localization table in the SQLite3 database.
    '''
    with db:
        db.executescript('''
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS Files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project TEXT NOT NULL,
                path TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS Localizations (
                file_id INTEGER NOT NULL,
                position TEXT NOT NULL,
                description TEXT,
                en TEXT NOT NULL,
                FOREIGN KEY(file_id) REFERENCES Files(id)
            );

            CREATE UNIQUE INDEX IF NOT EXISTS LocalizationIndex ON Localizations(file_id, position);
        ''')



def add_language(db, language):
    '''Inserts a language to the localization table.
    '''
    with db:
        try:
            db.execute('ALTER TABLE Localizations ADD COLUMN {} TEXT'.format(language))
        except sqlite3.OperationalError:
            pass



def main(filenames):
    db = sqlite3.connect('ios.sqlite')
    create_table(db)

    for filename in filenames:
        convert(db, filename)

    logging.info('Done')


if __name__ == '__main__':
    main(sys.argv[1:])

