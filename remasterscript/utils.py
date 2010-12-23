# -*- coding:utf8 -*-
import subprocess
import shlex
import re

import gobject

import const

class Process(gobject.GObject):
    def __init__(self, command, priority=gobject.PRIORITY_LOW):
        gobject.GObject.__init__(self)
        self._command = shlex.split(command)
        self._process = subprocess.Popen(self._command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._stdin = self._process.stdin
        self._stdout = self._process.stdout
        self._stderr = self._process.stderr
        self._stdin_handle = gobject.io_add_watch(self._stdin,
                                                    gobject.IO_OUT,
                                                    self._on_stdin,
                                                    priority=priority)
        self._stdout_handle = gobject.io_add_watch(self._stdout,
                                                    gobject.IO_IN | gobject.IO_ERR | gobject.IO_HUP | gobject.IO_PRI,
                                                    self._on_stdout,
                                                    priority=priority)
        self._stderr_handle = gobject.io_add_watch(self._stderr,
                                                   gobject.IO_IN | gobject.IO_PRI,
                                                   self._on_stderr,
                                                   priority=priority)
        self._buffer = []
    
    def wait(self):
        self._process.wait()
    
    def kill(self):
        self._process.kill()
        
    def write(self, string):
        self._buffer.append(string)
        
    def _on_stdin(self, fileno, condition):
        self.emit('stdin', fileno)
        if self._buffer:
            for string in self._buffer:
                fileno.write(string)
                self._buffer.remove(string)
            self._buffer = None
        return True
    
    def _on_stdout(self, fileno, condition):
        if condition == gobject.IO_ERR or condition == gobject.IO_HUP:
            self._process.wait()
            gobject.source_remove(self._stdin_handle)
            gobject.source_remove(self._stdin_handle)
            self.emit('close', self._process.returncode)
            return False
        elif condition == gobject.IO_IN or condition == gobject.IO_PRI:
            self.emit('stdout', fileno)
            return True
    
    def _on_stderr(self, fileno, condition):
        self.emit('stderr', fileno)
        return True

gobject.type_register(Process)
gobject.signal_new('stdin',
                        Process,
                        gobject.SIGNAL_RUN_LAST,
                        gobject.TYPE_BOOLEAN,
                        (gobject.TYPE_PYOBJECT,))
gobject.signal_new('stdout',
                        Process,
                        gobject.SIGNAL_RUN_LAST,
                        gobject.TYPE_BOOLEAN,
                        (gobject.TYPE_PYOBJECT,))
gobject.signal_new('stderr',
                        Process,
                        gobject.SIGNAL_RUN_LAST,
                        gobject.TYPE_BOOLEAN,
                        (gobject.TYPE_PYOBJECT,))
gobject.signal_new('close',
                        Process,
                        gobject.SIGNAL_RUN_LAST,
                        gobject.TYPE_BOOLEAN,
                        (gobject.TYPE_INT,))

class Util(gobject.GObject):
    def __init__(self, command):
        gobject.GObject.__init__(self)
        self._process = Process('%s' % (command))
        self._process.connect('close', self._on_close)
        
    def kill(self):
        self._process.kill()
        
    def _on_close(self, process, returncode):
        if returncode == 0:
            self.emit('success')
        else:
            self.emit('error', returncode)

gobject.type_register(Util)
gobject.signal_new('success',
                        Util,
                        gobject.SIGNAL_RUN_LAST,
                        gobject.TYPE_BOOLEAN,
                        ())
gobject.signal_new('error',
                        Util,
                        gobject.SIGNAL_RUN_LAST,
                        gobject.TYPE_BOOLEAN,
                        (gobject.TYPE_INT,))

class ExtractCompressedFs(gobject.GObject):
    def __init__(self, source, target):
        gobject.GObject.__init__(self)
        self._process = Process('"%s" "%s" "%s"' % (const.BINARY_EXTRACT_COMPRESSED_FS,
                                                    source,
                                                    target))
        self._process.connect('stderr', self._on_out)
        self._process.connect('close', self._on_close)
        self._number = re.compile('^[0-9]+')
        
    def kill(self):
        self._process.kill()
        
    def _on_out(self, process, fileno):
        data = self._number.match(fileno.readline())
        if data:
            self.emit('update', int(data.group(0)))
        
    def _on_close(self, process, returncode):
        if returncode == 0:
            self.emit('success')
        else:
            self.emit('error', returncode)
            
gobject.type_register(ExtractCompressedFs)
gobject.signal_new('update',
                        ExtractCompressedFs,
                        gobject.SIGNAL_RUN_LAST,
                        gobject.TYPE_BOOLEAN,
                        (gobject.TYPE_INT,))
gobject.signal_new('success',
                        ExtractCompressedFs,
                        gobject.SIGNAL_RUN_LAST,
                        gobject.TYPE_BOOLEAN,
                        ())
gobject.signal_new('error',
                        ExtractCompressedFs,
                        gobject.SIGNAL_RUN_LAST,
                        gobject.TYPE_BOOLEAN,
                        (gobject.TYPE_INT,))