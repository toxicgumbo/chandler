


class Path(object):
    '''A path to an item in a repository.

    A path can be absolute to a repository in which case it starts with //.
    A path can be absolute to a repository root in which case it start with /.
    A path is relative to an item when it doesn't begin with '/' and is used in
    conjunction with an item, as in an item's find method.'''
    
    def __init__(self, *args):
        '''Construct a path.

        Any number of arguments are combined to for a list of names, a path.
        Individual Arguments are split along '/' characters allowing for paths
        to be constructed from path strings.
        Ending '/' are stripped.
        A path can be used as an iterator over its constituent names.'''
        
        super(Path, self).__init__()
        
        self._names = []

        for arg in args:
            if arg.startswith('//'):
                self._names.append('//')
                arg = arg[2:]
            elif arg[0] == '/':
                self._names.append('/')
                arg = arg[1:]

            if arg.endswith('/'):
                arg = arg[:-1]
                
            self._names.extend(arg.split('/'))

    def __repr__(self):

        path = ''
        i = 0
        
        for name in self._names:
            if i > 1 or i == 1 and path[0] != '/':
                path += '/'
            path += name
            i += 1

        return path

    def __getitem__(self, key):

        return self._names[key]

    def __len__(self):

        return self._names.__len__()

    def __iter__(self):

        return self._names.__iter__()

    def set(self, *args):

        self._names[:] = args

    def append(self, name):
        'Extend this path appending name it.'
        
        self._names.append(name)

    def extend(self, path):
        'Concatenate two paths. Leading '/' are not stripped.'

        self._names.extend(path._names)
