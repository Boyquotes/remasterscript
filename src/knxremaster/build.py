# -*- coding:utf-8 -*-
#
# Copyright (C) 2012, Maximilian Köhl <linuxmaxi@googlemail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import io
import os
import os.path
import subprocess

from knxremaster.toolkit import commands, cloop
from knxremaster.toolkit.progress import script, progress

@script
def build(script, source):
    filesystem = os.path.exists(os.path.join(source, 'knoppix'))
    minirt = os.path.exists(os.path.join(source, 'minirt'))
    
    @progress
    def prepare(progress):
        remove = [('remaster.iso',)]
        if filesystem:
            remove.append(('master', 'KNOPPIX', 'KNOPPIX'))
        if minirt:
            remove.append(('master', 'boot', 'isolinux', 'minirt.gz'))
            remove.append(('master', 'boot', 'isolinux', 'minirt'))
        for path in remove:
            path = os.path.join(source, *path)
            if os.path.exists(path):
                os.remove(path)
                
    @progress
    def minirt_files(progress):
        with open(os.path.join(source, 'minirt.files'), 'wb') as files:
            minirt = os.path.join(source, 'minirt')
            for root, dirnames, filenames in os.walk(os.path.join(source, 'minirt')):
                root = root.replace(minirt, '.')
                files.write(root + '\n')
                for file in filenames:
                    files.write(os.path.join(root, file) + '\n')
    
    @progress
    def cleanup(progress):
        for path in ['knoppix.iso', 'minirt.files']:
            path = os.path.join(source, path)
            if os.path.exists(path):
                os.remove(path)
                    
    yield 'prepare', prepare()
    if filesystem:
        yield 'filesystem_image', commands.mkisofs('-R', '-U', '-V', 'KNOPPIX.net filesystem', '-publisher', 'KNOPPIX', '-hide-rr-moved', '-cache-inodes', '-no-bak', '-pad', '-o', os.path.join(source, 'knoppix.iso'), os.path.join(source, 'knoppix'))
        yield 'filesystem_compress', cloop.create_compressed_fs(os.path.join(source, 'knoppix.iso'), os.path.join(source, 'master', 'KNOPPIX', 'KNOPPIX'))
    if minirt:
        yield 'minirt_files', minirt_files()
        yield 'minirt_image', commands.cpio('-oH' 'newc', stdin=open(os.path.join(source, 'minirt.files')), stdout=open(os.path.join(source, 'master', 'boot', 'isolinux', 'minirt'), 'wb'), cwd=os.path.join(source, 'minirt'))
        yield 'minirt_compress', commands.gzip(os.path.join(source, 'master', 'boot', 'isolinux', 'minirt'))
    yield 'iso_image', commands.mkisofs('-pad', '-l', '-r', '-J', '-v', '-V', 'KNOPPIX', '-no-emul-boot', '-boot-load-size', '4', '-boot-info-table', '-b', 'boot/isolinux/isolinux.bin', '-c', 'boot/isolinux/boot.cat', '-hide-rr-moved', '-o', os.path.join(source, 'remaster.iso'), os.path.join(source, 'master'))
    yield 'cleanup', cleanup()