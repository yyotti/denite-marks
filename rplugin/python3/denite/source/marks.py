# ============================================================================
# FILE: marks.py
# AUTHOR: Y.Tsutsui <yosuke.tsutsui at gmail.com>
# License: MIT license
# ============================================================================
from .base import Base
from ..kind.file import Kind as File

BUFFER_HIGHLIGHT_SYNTAX = [
    {'name': 'InvalidMark', 'link': 'Error', 're': r'-\[.\{-}\]-'},
]


class Source(Base):
    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'marks'
        self.kind = Kind(vim)

        self.mark_chars = ''.join(
            [chr(c) for c in range(ord('a'), ord('z')+1)] +
            [chr(c) for c in range(ord('A'), ord('Z')+1)] +
            [chr(c) for c in range(ord('0'), ord('9')+1)]
        )

    def highlight(self):
        for syn in BUFFER_HIGHLIGHT_SYNTAX:
            self.vim.command(
                'syntax match {0}_{1} /{2}/ contained containedin={0}'.format(
                    self.syntax_name, syn['name'], syn['re']))
            self.vim.command(
                'highlight default link {0}_{1} {2}'.format(
                    self.syntax_name, syn['name'], syn['link']))

    def gather_candidates(self, context):
        lines = []
        try:
            lines = self.vim.call(
                'execute', 'marks ' + self.mark_chars).split('\n')[2:]
        except Exception:
            pass

        marks = []
        for m in lines:
            line = m.split(None, 3)

            [m_chr, linenr, col] = [line[0],
                                    int(line[1]),
                                    int(line[2]) + 1]
            file_text = line[3] if len(line) > 3 else ''

            [buf, _, _, _] = self.vim.call('getpos', "'" + m_chr)
            cur_buf = buf == 0 or self.vim.call('bufnr', '%') == buf

            if buf == 0:
                # current buffer
                text = self.vim.call('getline', linenr)
                path = self.vim.call('bufname', '%')
            elif self.vim.call('bufloaded', buf):
                # loaded buffer
                path = self.vim.call('bufname', buf)

                lines = self.vim.call('getbufline', buf, linenr)
                if len(lines) > 0:
                    text = '%s:[%s]' % (lines[0], path)
                else:
                    # invalid linenr
                    text = '-[%s]-' % (file_text,)
            elif self.vim.call('filereadable',
                               self.vim.call('fnamemodify', file_text, ':p')):
                # file not loaded
                text = file_text
                path = file_text
            else:
                # invalid mark
                text = '-[%s]-' % (file_text,)
                path = file_text

            marks.append({
                'word': '%-2s  %4d:%-3d  %s' % (
                    m_chr + ('#' if cur_buf else ''), linenr, col, text),
                'attr': '%s %s' % (text, path),
                'action__path': self.vim.call('fnamemodify', path, ':p'),
                'action__line': linenr,
                'action__col': col,
                'action__mark': m_chr,
            })

        context['__marks'] = marks
        return list(context['__marks'])


class Kind(File):
    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'file'
        self.persist_actions += ['delete']
        self.redraw_actions += ['delete']

    def action_delete(self, context):
        marks = ''.join([x['action__mark'] for x in context['targets']])
        self.vim.call('execute', ['delmarks ' + marks, 'wviminfo!'])
