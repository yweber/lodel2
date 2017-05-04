# 
# This file is part of Lodel 2 (https://github.com/OpenEdition)
#
# Copyright (C) 2015-2017 Cléo UMS-3287
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


dyncode = None

##@page lodel2_start Lodel2 boot mechanism
#
# @par Lodel2 boot sequence
# see @ref install/loader.py
# 1. lodel package is imported
# 2. settings are started 
# 3. plugins are pre-loaded from conf to load plugins configuration specs
# 4. settings are loaded from conf and checked
# 3. plugins are loaded (hooks are registered etc)
# 4. "lodel2_bootstraped" hooks are called
# 5. "lodel2_loader_main" hooks are called (if runned from loader.py as main executable)
#

##@page lodel2_instance_admin Lodel2 instance administration
#
#@section lodel2_instance_adm_tools Tools
#
#@subsection lodel2_instance_makefile Makefile
#
#The Makefile allows to run automated without arguments such as :
#- refresh the dynamic code using conf + EM (target **dyncode**)
#- update databases (target **init_db**)
#- refresh plugins list (target **refresh_plugins**)
#
#@subsection lodel2_instance_adm_scripts lodel_admin.py scripts
#
#In all instances you find a symlink named lodel_admin.py . This script
#contains the code run by @ref lodel2_instance_makefile "Makefile targets"
#and a main function that allows to run it as a CLI script.
#
#@par Script help
#<pre>
#usage: lodel_admin.py [-h] [-L] [ACTION] [OPTIONS [OPTIONS ...]]
#
#Lodel2 script runner
#
#positional arguments:
#  ACTION              One of the following actions : discover-plugin [...]
#  OPTIONS             Action options. Use lodel_admin.py ACTION -h to have
#                      help on a specific action
#
#optional arguments:
#  -h, --help          show this help message and exit
#  -L, --list-actions  List available actions
#</pre>
#
#@par Script customization
#
#See @ref lodel2_script_doc "Lodel2 scripting"
#
#

##@defgroup lodel2_deployment Diffusion and deployment

##@page lodel2_autotools Lodel2 and autotools integration
#@ingroup lodel2_deployment
#
#Autotools provide a way to distribute a software on Posix platforms.
#
#@section lodel2_autotools_howto Howto use them
#
#Basically you have to run :
#- <code>./bootstrap.sh</code> to generate the configure script( run 
#approximatly <code>aclocal; autoconf; automake</code> or 
#<code>autoreconf</code> )
#- <code>./configure</code> to generate Makefile s
#- <code>make</code> to build lodel2 (actually to generate lodel/buildconf.py
#from @ref lodel/buildconf.py.in )
#
#Here is a list of most usefull targets provided by lodel2's Makefile :
#- automake targets
# - **all** compile the sources (don't do a lot for a script langage)
# - **clean** delete compiled files (don't do a lot for a script langage)
# - **distclean** enhanced comportment compared to default (delete compiled 
#files and generated binary). Here it deletes everything generated by
#<code>./bootstrap.sh && ./configure && make</code>
# - **install** Install lodel2 (for the moment copy the lodel dir in 
#the good path (configurable when running ./configure ) )
# - **uninstall** Remove installed files
#- lodel2 specific targets 
# - **tests**, **check** and **checks** are aliases for running tests
# - **doc** generate the doxygen documentation
# - **em_test** refresh the example/em_test.pickle file using em_test.py
# - **dyncode** generate a dyncode.py file using lefactory in
#lodel/leapi/dyncode.py
#
#@section lodel2_autotools_why Why using autotools
#
#Python has a lot of packaging and distributing solutions, but none of them
#is as convinent, complete, portable as GNU autotools. For example setup.py 
#with distutils has no uninstall target; pip, wheel, easy-install etc brokes 
#totally your distribution packaging/upgrade system etc.
#
#Autotools are portable, integrated by debian packaging system ( see 
#checkinstall) and can support multi langages.
#
#@section lodel2_autotools_whatfor For doing what
#
#Autotools are here to allow distributing and installing Lodel2 on 
#Posix OS. 
#
#The distribution mechanisms handles dependencies checking (NO AUTO INSTALL
#WITH BINARY BLOBS !!!), compiling .py files to pyc and pyo, and copy all files
#in the good directories (python libs, doc, scripts etc)
#
#@section lodel2_autotools_how How autotools are integrated
#
#What we call autotools is in fact a lot of software. In our case we use only
#both of them : 
#<a href="https://www.gnu.org/software/autoconf/autoconf.html#documentation">
#autoconf</a> and 
#<a href="https://www.gnu.org/software/automake/#documentation">automake</a>
#
#A python file is generated ( lodel/buildconf.py from 
#@ref lodel/buildconf.py.in) containing various informations gathered during
#the build process (for example the presence of pymongo or the precense of
#the dependency needed by webui etc.)
#
#@subsection lodel2_autoconf Autoconf
#
#Autoconf job is to handle configure.ac file and generated the configure
#script.
#
#@par Configure script
#The configure script job is to check all dependencies fetch all
#path etc. And when runned it generates all Makefile from the Makefile.in files
#(see @ref lodel2_automake "below" )
#
#@par Autoconf macros
#We use both macro family :
#- <a href="https://www.gnu.org/software/automake/manual/html_node/Python.html">
#default autoconf python macro</a>
#- <a href="https://www.gnu.org/software/pyconfigure/manual/">
#pyconfigure autoconf macros</a>
#@see lodel2_autotools_problems
#
#@subsection lodel2_automake Automake
#
#Automake job is to transform the Makefile.am files into Makefile.in files.
#It handles all target creation for build, clean, install, uninstall etc.
#
#@section lodel2_autotools_problems Encontered problems
#
#@ref lodel2_autoconf "Autoconf" use macro "written in m4" (not sure if m4
#is the macro langage). We use two macros sources : automake default python 
#support & pyconfigure automake macros.
#
#Those macros are broken with python3 (see 
#<a href="https://bugs.launchpad.net/ubuntu/+source/python3-defaults/+bug/1408092">
#the python3 sysconfig bug with debian OS</a> ). There is patched version of 
#these macro in the m4 directory (and the associated patches : 
#@ref m4/python.m4.patch "for automake python macros patch" and 
#@ref m4/python_pyconfigure.m4.patch "for pyconfigure python macros patch")

##@file m4/python.m4.patch
#@ingroup lodel2_deployment
#@brief Patch of automake python macro to solve a bug in pythondir retrieval 
#on debian
#@see https://bugs.launchpad.net/ubuntu/+source/python3-defaults/+bug/1408092

##@file m4/python_pyconfigure.m4.patch
#@ingroup lodel2_deployment
#@brief Patch to solve a bug in pyconfigure ac macros in pythondir retrieval 
#on debian
#@see https://bugs.launchpad.net/ubuntu/+source/python3-defaults/+bug/1408092

##@file m4/python.m4
#@ingroup lodel2_deployment
#@brief Automake macro for python (patched version)
#@see m4/python.m4.patch


##@file m4/python_pyconfigure.m4
#@brief Pyconfigure automake macro (patched version)
#@see m4/python_pyconfigure.m4.patch

##@file configure.ac
#@brief configure script model for autoconf
#@ingroup lodel2_deployment

##@file Makefile.am
#@brief Makefile model for autotools
#@ingroup lodel2_deployment

##@file lodel/Makefile.am
#@brief Makefile model for autotools
#@ingroup lodel2_deployment

