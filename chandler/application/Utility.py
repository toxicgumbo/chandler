__version__ = "$Revision: 5915 $"
__date__ = "$Date: 2005-07-09 11:49:30 -0700 (Sat, 09 Jul 2005) $"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


import gettext, os, sys, crypto, logging, logging.config, string
from optparse import OptionParser
from repository.persistence.DBRepository import DBRepository
from repository.persistence.RepositoryError \
     import VersionConflictError, MergeError, RepositoryPasswordError, \
     RepositoryOpenDeniedError, ExclusiveOpenDeniedError,\
     RepositoryVersionError
from repository.item.RefCollections import RefList


# Increment this value whenever the schema changes and edit its comment 
#    to let others know what changed.  
# Your comment also helps Subversion detect a conflict, in case 
#    someone else changes it at about the same time.
SCHEMA_VERSION = "43" # moved osaf.framework.sharing to osaf.sharing

logger = None # initialized in initLogging()


def locateProfileDir():
    """
    Locate the Chandler repository.
    The location is determined either by parameters, or if not specified, by
    the presence of a .chandler directory in the users home directory.
    """

    def _makeRandomProfileDir(pattern):
        import M2Crypto.BN as BN
        profileDir = pattern.replace('*', '%s') % (BN.randfname(8))
        os.makedirs(profileDir, 0700)
        return profileDir


    if os.name == 'nt':
        dataDir = None

        if os.environ.has_key('APPDATA'):
            dataDir = os.environ['APPDATA']
        elif os.environ.has_key('USERPROFILE'):
            dataDir = os.environ['USERPROFILE']
            if os.path.isdir(os.path.join(dataDir, 'Application Data')):
                dataDir = os.path.join(dataDir, 'Application Data')

        if dataDir is None or not os.path.isdir(dataDir):
            if os.environ.has_key('HOMEDRIVE') and \
                os.environ.has_key('HOMEPATH'):
                dataDir = '%s%s' % (os.environ['HOMEDRIVE'],
                                    os.environ['HOMEPATH'])

        if dataDir is None or not os.path.isdir(dataDir):
            dataDir = os.path.expanduser('~')

        profileDir = os.path.join(dataDir,
                                  'Open Source Applications Foundation',
                                  'Chandler')

    elif sys.platform == 'darwin':
        dataDir = os.path.join(os.path.expanduser('~'),
                               'Library',
                               'Application Support')
        profileDir = os.path.join(dataDir,
                                  'Open Source Applications Foundation',
                                  'Chandler')

    else:
        dataDir = os.path.expanduser('~')
        profileDir = os.path.join(dataDir, '.chandler')

    # Deal with the random part
    pattern = '%s%s*.default' % (profileDir, os.sep)
    try:
        import glob
        profileDir = glob.glob(pattern)[0]
    except IndexError:
        try:
            profileDir = _makeRandomProfileDir(pattern)
        except:
            profileDir = None
    except:
        profileDir = None

    return profileDir


def initOptions(chandlerDirectory, **kwds):
    """
    Load and parse the command line options, with overrides in **kwds.
    Returns options
    """

    #    option name,  (value, short cmd, long cmd, type flag, default, environment variable, help text)
    _configItems = {
        'parcelPath':  ('-p', '--parcelPath','s', None,  'PARCELPATH', 'Parcel search path'),
        'webserver':  ('-W', '--webserver',  'b', False, 'CHANDLERWEBSERVER', 'Activate the built-in webserver'),
        'profileDir': ('-P', '--profileDir', 's', None,  'PROFILEDIR', 'location of the Chandler Repository'),
        'profile':    ('',   '--prof',       'b', False, None, 'save profiling data'),
        'script':     ('-s', '--script',     's', None,  None, 'script to execute after startup'),
        'scriptFile': ('-f', '--scriptFile', 's', None,  None, 'script file to execute after startup'),
        'stderr':     ('-e', '--stderr',     'b', False, None, 'Echo error output to log file'),
        'create':     ('-c', '--create',     'b', False, "CREATE", 'Force creation of a new repository'),
        'ramdb':      ('-d', '--ramdb',      'b', False, None, ''),
        'restore':    ('-r', '--restore',    's', None,  None, 'repository backup to restore from before repository open'),
        'recover':    ('-R', '--recover',    'b', False, None, 'open repository with recovery'),
        'nocatch':    ('-n', '--nocatch',    'b', False, 'CHANDLERNOCATCH', ''),
        'wing':       ('-w', '--wing',       'b', False, None, ''),
        'komodo':     ('-k', '--komodo',     'b', False, None, ''),
        'refreshui':  ('-u', '--refresh-ui', 'b', False, None, 'Refresh the UI from the repository during startup'),
        'locale':     ('-l', '--locale',     's', None,  None, 'Set the default locale'),
        'encrypt':    ('-S', '--encrypt',    'b', False, None, 'Request prompt for password for repository encryption'),
        'nosplash':    ('-N', '--nosplash',  'b', False, 'CHANDLERNOSPLASH', ''),
        'logging':     ('-L', '--logging',   's', 'logging.conf',  'CHANDLERLOGCONFIG', 'The logging config file'),
        'createData': ('-C', '--createData', 's', None,  None, 'csv file with items definition to load after startup'),
    }


    # %prog expands to os.path.basename(sys.argv[0])
    usage  = "usage: %prog [options]"
    parser = OptionParser(usage=usage, version="%prog " + __version__)

    for key in _configItems:
        (shortCmd, longCmd, optionType, defaultValue, environName, helpText) \
            = _configItems[key]

        if environName and os.environ.has_key(environName):
            defaultValue = os.environ[environName]

        if optionType == 'b':
            parser.add_option(shortCmd,
                              longCmd,
                              dest=key,
                              action='store_true',
                              default=defaultValue,
                              help=helpText)
        else:
            parser.add_option(shortCmd,
                              longCmd,
                              dest=key,
                              default=defaultValue,
                              help=helpText)

    (options, args) = parser.parse_args()

    if not options.profileDir:
        profileDir = locateProfileDir()
        if profileDir is None:
            profileDir = chandlerDirectory
        options.profileDir = os.path.expanduser(profileDir)

    for (opt,val) in kwds.iteritems():
        setattr(options, opt, val)

    if options.locale is not None:
        from PyICU import Locale
        Locale.setDefault(Locale(options.locale))

    return options


def initLogging(options):
    global logger

    if logger is None:
        # Make PROFILEDIR available within the logging config file
        logging.PROFILEDIR = options.profileDir

        logConfFile = options.logging
        if os.path.isfile(logConfFile):
            # Replacing the standard fileConfig with our own, below
            # logging.config.fileConfig(options.logging)
            fileConfig(options.logging)
        else:
            # Log config file doesn't exist
            logging.basicConfig(level=logging.WARNING,
                format='%(asctime)s %(name)s %(levelname)s: %(message)s',
                filename=os.path.join(options.profileDir, 'chandler.log'),
                filemode='a')

        logger = logging.getLogger(__name__)

        # Send twisted output to twisted.log in the profile directory
        import twisted.python.log
        twistedLogFile = os.path.join(options.profileDir, 'twisted.log')
        twisted.python.log.startLogging(file(twistedLogFile, 'a+'), 0)


def locateChandlerDirectory():
    """
    Find the directory that Chandler lives in by looking up the file that
    the application module lives in.
    """
    return os.path.dirname(os.path.dirname(__file__))


def locateRepositoryDirectory(profileDir):
    if profileDir:
        path = os.sep.join([profileDir, '__repository__'])
    else:
        path = '__repository__'
    return path


def initRepository(directory, options):

    repository = DBRepository(directory)

    kwds = { 'stderr': options.stderr,
             'ramdb': options.ramdb,
             'create': True,
             'recover': options.recover,
             'exclusive': True,
             'refcounted': True }

    if options.restore:
        kwds['restore'] = options.restore

    while True:
        try:
            if options.encrypt:
                from getpass import getpass
                kwds['password'] = getpass("password> ")

            if options.create:
                repository.create(**kwds)
            else:
                repository.open(**kwds)
        except RepositoryPasswordError, e:
            if options.encrypt:
                print e.args[0]
            else:
                options.encrypt = True
            continue
        except RepositoryVersionError:
            repository.close()
            raise
        else:
            del kwds
            break

    view = repository.getCurrentView()

    if not view.findPath("//Packs/Chandler"):
        view.loadPack("repository/packs/chandler.pack")

    return view


def stopRepository(view):
    try:
        try:
            view.commit()
        except VersionConflictError, e:
            logger.warning(str(e))
    finally:
        view.repository.close()


def verifySchema(view):
    # Fetch the top-level parcel item to check schema version info
    parcelRoot = view.findPath("//parcels")
    if parcelRoot is not None:
        if (not hasattr(parcelRoot, 'version') or
            parcelRoot.version != SCHEMA_VERSION):
            logger.info("Schema version of repository doesn't match app")
            return False
    return True


def initParcelEnv(chandlerDirectory, path):
    """
    PARCEL_IMPORT defines the import directory containing parcels
    relative to chandlerDirectory where os separators are replaced
    with "." just as in the syntax of the import statement.
    """
    PARCEL_IMPORT = 'parcels'

    """
    Load the parcels which are contained in the PARCEL_IMPORT directory.
    It's necessary to add the "parcels" directory to sys.path in order
    to import parcels. Making sure we modify the path as early as possible
    in the initialization as possible minimizes the risk of bugs.
    """
    parcelPath = []
    parcelPath.append(os.path.join(chandlerDirectory,
                      PARCEL_IMPORT.replace ('.', os.sep)))

    """
    If PARCELPATH env var is set, append those directories to the
    list of places to look for parcels.
    """
    if path:
        for directory in path.split(os.pathsep):
            if os.path.isdir(directory):
                parcelPath.append(directory)
            else:
                logger.warning("'%s' not a directory; skipping" % directory)

    insertionPoint = 1
    for directory in parcelPath:
        sys.path.insert(insertionPoint, directory)
        insertionPoint += 1

    logger.info("Using PARCELPATH %s" % parcelPath)

    return parcelPath


def initParcels(view, path):
    import Parcel # Delayed so as not to trigger an extra logging addHandler().
                  # Importing Parcel has the side effect of importing schema
                  # which has the side effect of creating a NullRepositoryView
                  # which calls addHandler( ).

    Parcel.Manager.get(view, path=path).loadParcels()

    # Record the current schema version into the repository
    parcelRoot = view.findPath("//parcels")
    parcelRoot.version = SCHEMA_VERSION


def initLocale(locale):
    """
      Setup internationalization
    To experiment with a different locale, try 'fr' and wx.LANGUAGE_FRENCH
    """
    os.environ['LANGUAGE'] = locale
    gettext.install('chandler', 'locale')


def initCrypto(profileDir):
    crypto.startup(profileDir)


def stopCrypto(profileDir):
    crypto.shutdown(profileDir)

def initTwisted():
    from osaf.startup import run_reactor
    run_reactor()

def stopTwisted():
    from osaf.startup import stop_reactor
    stop_reactor()

def initWakeup(view):
    from osaf.startup import run_startup
    run_startup(view)


def stopWakeup():
    pass

class SchemaMismatchError(Exception):
    """ The schema version in the repository doesn't match the application. """
    pass

# Replacement for logging.config.fileConfig, which doesn't disable loggers:

def fileConfig(fname, defaults=None):
    """
    Read the logging configuration from a ConfigParser-format file.

    This can be called several times from an application, allowing an end user
    the ability to select from various pre-canned configurations (if the
    developer provides a mechanism to present the choices and load the chosen
    configuration).
    In versions of ConfigParser which have the readfp method [typically
    shipped in 2.x versions of Python], you can pass in a file-like object
    rather than a filename, in which case the file-like object will be read
    using readfp.
    """
    import ConfigParser

    cp = ConfigParser.ConfigParser(defaults)
    if hasattr(cp, 'readfp') and hasattr(fname, 'readline'):
        cp.readfp(fname)
    else:
        cp.read(fname)
    #first, do the formatters...
    flist = cp.get("formatters", "keys")
    if len(flist):
        flist = string.split(flist, ",")
        formatters = {}
        for form in flist:
            sectname = "formatter_%s" % form
            opts = cp.options(sectname)
            if "format" in opts:
                fs = cp.get(sectname, "format", 1)
            else:
                fs = None
            if "datefmt" in opts:
                dfs = cp.get(sectname, "datefmt", 1)
            else:
                dfs = None
            f = logging.Formatter(fs, dfs)
            formatters[form] = f
    #next, do the handlers...
    #critical section...
    logging._acquireLock()
    try:
        try:
            #first, lose the existing handlers...
            logging._handlers.clear()
            #now set up the new ones...
            hlist = cp.get("handlers", "keys")
            if len(hlist):
                hlist = string.split(hlist, ",")
                handlers = {}
                fixups = [] #for inter-handler references
                for hand in hlist:
                    try:
                        sectname = "handler_%s" % hand
                        klass = cp.get(sectname, "class")
                        opts = cp.options(sectname)
                        if "formatter" in opts:
                            fmt = cp.get(sectname, "formatter")
                        else:
                            fmt = ""
                        klass = eval(klass, vars(logging))
                        args = cp.get(sectname, "args")
                        args = eval(args, vars(logging))
                        h = apply(klass, args)
                        if "level" in opts:
                            level = cp.get(sectname, "level")
                            h.setLevel(logging._levelNames[level])
                        if len(fmt):
                            h.setFormatter(formatters[fmt])
                        #temporary hack for FileHandler and MemoryHandler.
                        if klass == logging.handlers.MemoryHandler:
                            if "target" in opts:
                                target = cp.get(sectname,"target")
                            else:
                                target = ""
                            if len(target): #the target handler may not be loaded yet, so keep for later...
                                fixups.append((h, target))
                        handlers[hand] = h
                    except:     #if an error occurs when instantiating a handler, too bad
                        pass    #this could happen e.g. because of lack of privileges
                #now all handlers are loaded, fixup inter-handler references...
                for fixup in fixups:
                    h = fixup[0]
                    t = fixup[1]
                    h.setTarget(handlers[t])
            #at last, the loggers...first the root...
            llist = cp.get("loggers", "keys")
            llist = string.split(llist, ",")
            llist.remove("root")
            sectname = "logger_root"
            root = logging.root
            log = root
            opts = cp.options(sectname)
            if "level" in opts:
                level = cp.get(sectname, "level")
                log.setLevel(logging._levelNames[level])
            for h in root.handlers[:]:
                root.removeHandler(h)
            hlist = cp.get(sectname, "handlers")
            if len(hlist):
                hlist = string.split(hlist, ",")
                for hand in hlist:
                    log.addHandler(handlers[hand])
            #and now the others...
            #we don't want to lose the existing loggers,
            #since other threads may have pointers to them.
            #existing is set to contain all existing loggers,
            #and as we go through the new configuration we
            #remove any which are configured. At the end,
            #what's left in existing is the set of loggers
            #which were in the previous configuration but
            #which are not in the new configuration.
            existing = root.manager.loggerDict.keys()
            #now set up the new ones...
            for log in llist:
                sectname = "logger_%s" % log
                qn = cp.get(sectname, "qualname")
                opts = cp.options(sectname)
                if "propagate" in opts:
                    propagate = cp.getint(sectname, "propagate")
                else:
                    propagate = 1
                logger = logging.getLogger(qn)
                if qn in existing:
                    existing.remove(qn)
                if "level" in opts:
                    level = cp.get(sectname, "level")
                    logger.setLevel(logging._levelNames[level])
                for h in logger.handlers[:]:
                    logger.removeHandler(h)
                logger.propagate = propagate
                logger.disabled = 0
                hlist = cp.get(sectname, "handlers")
                if len(hlist):
                    hlist = string.split(hlist, ",")
                    for hand in hlist:
                        logger.addHandler(handlers[hand])
            #Disable any old loggers. There's no point deleting
            #them as other threads may continue to hold references
            #and by disabling them, you stop them doing any logging.
            # for log in existing:
            #     root.manager.loggerDict[log].disabled = 1
        except:
            import traceback
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2], None, sys.stderr)
            del ei
    finally:
        logging._releaseLock()

