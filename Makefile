dyncode_filename='lodel/leapi/dyncode.py'

all: doc refresh_dyn

doc: cleandoc
	doxygen

# Test em update ( examples/em_test.pickle )
em_test:
	python3 em_test.py

refresh_dyn: clean_dyn em_test
	python3 scripts/refreshdyn.py examples/em_test.pickle $(dyncode_filename)
	

.PHONY: clean clean_dyn cleandoc cleanpyc

clean: clean_dyn cleandoc cleanpyc

cleanpyc:
	-find ./ |grep -E "\.pyc$$" |xargs rm -f 2>/dev/null
cleanpycache:
	-find ./ -type d |grep '__pycache__' | xargs rmdir -f 2>/dev/null

cleandoc:
	-rm -R doc/html doc/doxygen_sqlite3.db

clean_dyn:
	-rm $(dyncode_filename)
	
