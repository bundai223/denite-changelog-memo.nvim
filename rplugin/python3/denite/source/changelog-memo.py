
from .base import Base

LINE_NUMBER_SYNTAX = (
    'syntax match deniteSource_lineNumber '
    r'/\d\+\(:\d\+\)\?/ '
    'contained containedin=')
LINE_NUMBER_HIGHLIGHT = 'highlight default link deniteSource_lineNumber LineNR'


class Source(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'changelog-memo'
        self.kind = 'file'
        self.matchers = ['matcher_regexp']
        self.sorters = []

    def on_init(self, context):
        context['__linenr'] = self.vim.current.window.cursor[0]
        context['__bufnrs'] = [self.vim.current.buffer.number]
        context['__direction'] = 'all'
        context['__emptiness'] = 'empty'
        context['__fmt'] = '%' + str(len(
            str(self.vim.call('line', '$')))) + 'd: %s'
        argc = len(context['args'])

        direction = context['args'][0] if argc >= 1 else None
        if (direction == 'all' or direction == 'forward' or
                direction == 'backward'):
            context['__direction'] = direction
        elif direction == 'buffers':
            context['__bufnrs'] = [x.number for x in self.vim.buffers
                                   if x.options['buflisted']]
        elif direction == 'args':
            context['__bufnrs'] = [self.vim.call('bufnr', x) for x
                                   in self.vim.call('argv')]

        emptiness = context['args'][1] if argc >= 2 else None
        if emptiness == 'noempty':
            context['__emptiness'] = emptiness

    def highlight(self):
        self.vim.command(LINE_NUMBER_SYNTAX + self.syntax_name)
        self.vim.command(LINE_NUMBER_HIGHLIGHT)

    def gather_candidates(self, context):
        linenr = context['__linenr']
        candidates = []
        tab_removal = re.compile("^\t", re.M)
        entry_regex = re.compile("^\* .*:")
        date_regex = re.compile("^\t")

        for bufnr in context['__bufnrs']:
            blocks = []
            # lines = map(lambda x: tab_removal.sub("", x), self.vim.call('getbufline', bufnr, 1, '$')))
            raw_lines = self.vim.call('getbufline', bufnr, 1, '$')
            for line in list(filter(lambda t: !date_regex.search(t)), raw_lines)):
                l = tab_removal.sub("", line)
                if entry_regex.search(l):
                    blocks.append(l)
                else:
                    blocks[-1] = "{blocks[-1]}\n{l}"

            logs = [{
                'word': text,
                'abbr': (context['__fmt'] % (i + 1, text)),
                'action__path': self.vim.call('bufname', bufnr),
                'action__line': (i + 1),
                'action__text': text,
            } for [i, text] in enumerate(blocks)]

            if context['__emptiness'] == 'noempty':
                logs = list(filter(lambda c: c['word'] != '', logs))

            if context['__direction'] == 'all':
                candidates += logs
            elif context['__direction'] == 'backward':
                candidates += list(reversed(logs[:linenr])) + list(
                    reversed(logs[linenr:]))
            else:
                candidates += logs[linenr-1:] + logs[:linenr-1]
        return candidates
