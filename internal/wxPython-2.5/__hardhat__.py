import os, hardhatlib


info = {
        'name':'wxWindows-2.5.1.5',
        'root':'../osaf/chandler',
        'path':'../../wxPythonSrc-2.5.1.5',
       }

dependencies = (
                'python',
               )


def build(buildenv):

    version = buildenv['version']

    if buildenv['os'] in ('osx', 'posix'):


        # Create the build directory

        buildDir = os.path.abspath("build_%s" % version)
        if os.access(buildDir, os.F_OK):
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
             info['name'], 
             "Temporary build directory exists: " + buildDir)
        else:
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
             info['name'], 
             "Temporary build directory doesn't exist; creating: " + \
              buildDir)
            os.mkdir(buildDir)
        os.chdir(buildDir)

        # Prepare the wxWidgets command line

        buildOptions = [
         buildenv['sh'], 
         '../configure', 
         '--prefix=%s' % os.path.join(buildenv['root'],version),
         '--disable-monolithic',
         '--enable-geometry',
         '--enable-sound',
         '--with-sdl',
         '--enable-display',
         '--with-libpng=builtin',
        ]

        if version == "debug":
            buildOptions.append("--enable-debug")
        else:
            buildOptions.append("--enable-optimized")

        if buildenv['os'] == "osx":
            buildOptions.append("--with-mac")
            buildOptions.append("--with-opengl")

        if buildenv['os'] == "posix":
            buildOptions.append("--with-gtk")
            buildOptions.append("--enable-gtk2")
            buildOptions.append("--enable-unicode")

        # Configure

        if os.access('Makefile', os.F_OK):
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
             info['name'], "Already configured")
        else:
            hardhatlib.executeCommand(buildenv, info['name'],
             buildOptions,
             "Configuring wxWindows %s" % version)

        # Make

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make']], "Making wxWindows")

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make'], '-Ccontrib/src/gizmos'], "Making gizmos")

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make'],
          '-Ccontrib/src/ogl',
          'CXXFLAGS="-DwxUSE_DEPRECATED=0"',
          ], "Making ogl")

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make'], '-Ccontrib/src/stc'], "Making stc")

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make'], '-Ccontrib/src/xrc'], "Making xrc")

        # Install

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make'], 'install'], "Installing wxWindows")

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make'], '-Ccontrib/src/gizmos', 'install'],
         "Installing gizmos")

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make'], '-Ccontrib/src/ogl', 'install'],
         "Installing ogl")

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make'], '-Ccontrib/src/stc', 'install'], 
         "Installing stc")

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make'], '-Ccontrib/src/xrc', 'install'], 
         "Installing xrc")


        # wxPython

        if version == "debug":
            python = buildenv['python_d']
        else:
            python = buildenv['python']

        os.chdir("../wxPython")

        buildOptions = [
         python,
         'setup.py',
         'BUILD_OGL=0',
         'BUILD_GLCANVAS=0',
         'BUILD_BASE=build_%s' % version,
         'WX_CONFIG='+buildenv['root']+'/%s/bin/wx-config' % version,
         'build_ext',
         '--inplace',
        ]
        if version == "debug":
            buildOptions.append("--debug")
        if buildenv['os'] == "posix":
            buildOptions.append("WXPORT=gtk2")
            buildOptions.append("UNICODE=1")

        hardhatlib.executeCommand(buildenv, info['name'], buildOptions,
         "Building wxPython")

        installOptions = [
         python,
         'setup.py',
         'install',
         'BUILD_BASE=build_%s' % version,
        ]

        hardhatlib.executeCommand(buildenv, info['name'], installOptions,
         "Installing wxPython")


    # Windows

    if buildenv['os'] == 'win':

        os.chdir("build")
        os.chdir("msw")

        hardhatlib.executeCommand( buildenv, info['name'],
         [buildenv['compiler'], 
         "msw.sln",
         "/build",
         version.capitalize(),
         "/out",
         "output.txt"],
         "Building %s %s" % (info['name'], version),
         0, "output.txt")
         



def clean(buildenv):

    if buildenv['os'] == 'posix':

        if buildenv['version'] == 'release':

            buildDir=buildenv['root']+os.sep+'wxpython'+os.sep+'build_release'
            if os.access(buildDir, os.F_OK):
                hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
                 info['name'], 
                 "Removing temporary build directory: " + buildDir)
                hardhatlib.rmdir_recursive(buildDir)

        if buildenv['version'] == 'debug':

            buildDir = buildenv['root']+os.sep+'wxpython'+os.sep+'build_debug'
            if os.access(buildDir, os.F_OK):
                hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
                 info['name'], 
                 "Removing temporary build directory: " + buildDir)
                hardhatlib.rmdir_recursive(buildDir)


    if buildenv['os'] == 'osx':

        if buildenv['version'] == 'release':

            buildDir = buildenv['root']+os.sep+'wxpython'+os.sep+'build_release'
            if os.access(buildDir, os.F_OK):
                hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
                 info['name'], 
                 "Removing temporary build directory: " + buildDir)
                hardhatlib.rmdir_recursive(buildDir)

        if buildenv['version'] == 'debug':

            buildDir = buildenv['root']+os.sep+'wxpython'+os.sep+'build_debug'
            if os.access(buildDir, os.F_OK):
                hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
                 info['name'], 
                 "Removing temporary build directory: " + buildDir)
                hardhatlib.rmdir_recursive(buildDir)


    if buildenv['os'] == 'win':

        os.putenv('WXWIN', buildenv['root_dos'] + '\\wxpython')


        if buildenv['version'] == 'release':

            os.chdir("src")
            os.chdir("msw")
            hardhatlib.executeCommand( buildenv, info['name'],
             [buildenv['nmake'], '-f', 'makefile.vc', 'cleandll', 'FINAL=1'],
             "Cleaning wxWindows dll")
            hardhatlib.executeCommand( buildenv, info['name'],
             [buildenv['nmake'], '-f', 'makefile.vc', 'cleanall', 'FINAL=1'],
             "Cleaning wxWindows all")

        if buildenv['version'] == 'debug':

            os.chdir("src")
            os.chdir("msw")
            hardhatlib.executeCommand( buildenv, info['name'],
             [buildenv['nmake'], '-f', 'makefile.vc', 'cleandll', 'FINAL=0'],
             "Cleaning wxWindows dll")
            hardhatlib.executeCommand( buildenv, info['name'],
             [buildenv['nmake'], '-f', 'makefile.vc', 'cleanall', 'FINAL=0'],
             "Cleaning wxWindows all")


        os.chdir("..")
        os.chdir("..")
        os.chdir("wxPython")
        os.chdir("wxSWIG")
        hardhatlib.executeCommand( buildenv, info['name'],
         [buildenv['nmake'], '-f', 'makefile.vc', 'clean'],
         "Cleaning wxSWIG")


def run(buildenv):
    hardhatlib.log(buildenv, hardhatlib.HARDHAT_WARNING, info['name'], 
     "Nothing to run")

