"""
Console logger widget for MARS (Modal Analysis Response Solver).

Provides a Logger class that redirects stdout to a QTextEdit widget with buffered updates.
"""

import sys
import threading
from PyQt5.QtCore import QObject, QTimer, pyqtSlot
from PyQt5.QtGui import QTextCursor


class Logger(QObject):
    """
    Logger that redirects stdout to a QTextEdit widget with buffering.
    
    This class captures console output and displays it in a GUI text widget,
    using a buffer and timer to batch updates for better performance.
    """
    
    def __init__(self, text_edit, flush_interval=200):
        """
        Initialize the Logger.
        
        Args:
            text_edit: QTextEdit widget to display log messages.
            flush_interval: Interval in milliseconds to flush the buffer (default: 200).
        """
        super().__init__()
        self.text_edit = text_edit
        self.terminal = sys.stdout
        self.log_buffer = ""  # Buffer for messages
        self._buffer_lock = threading.Lock()
        self.flush_interval = flush_interval  # in milliseconds
        
        # Set up a QTimer to flush the buffer periodically
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.flush_buffer)
        self.timer.start(self.flush_interval)
    
    def write(self, message):
        """
        Write a message to both terminal and buffer.
        
        Args:
            message: Text message to write.
        """
        # Write to the original terminal when available (e.g., console builds).
        if self.terminal is not None and hasattr(self.terminal, "write"):
            self.terminal.write(message)
        # Append the message to the buffer
        with self._buffer_lock:
            self.log_buffer += message

    def _clear_last_console_line(self, cursor):
        """
        Clear the last visible line in the console box.

        This is used when incoming text wants to update the same line.
        """
        cursor.movePosition(QTextCursor.End)
        cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()

    def _insert_text_with_line_replacement(self, text):
        """Insert text and replace the last line when `\\r` appears."""
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)

        segments = text.split('\r')
        if segments:
            cursor.insertText(segments[0])

        for segment in segments[1:]:
            self._clear_last_console_line(cursor)
            if segment:
                cursor.insertText(segment)

        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()
    
    @pyqtSlot()
    def flush_buffer(self):
        """Flush the buffered messages to the text edit widget."""
        with self._buffer_lock:
            if not self.log_buffer:
                return
            buffered = self.log_buffer
            self.log_buffer = ""

        self._insert_text_with_line_replacement(buffered)
    
    def flush(self):
        """Flush the buffer (called by sys.stdout.flush())."""
        if self.terminal is not None and hasattr(self.terminal, "flush"):
            self.terminal.flush()
        self.flush_buffer()
