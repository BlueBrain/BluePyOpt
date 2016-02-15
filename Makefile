all: install
install:
	pip install . --upgrade
doc: install
	pip install sphinx sphinx-autobuild
	cd docs; $(MAKE) clean; $(MAKE) html
doc_upload: doc
	cd docs/build/html && \
	touch .nojekyll && \
	git init . && \
	git add . && \
	git commit -m "Updating docs" && \
	git push "git@github.com:BlueBrain/BluePyOpt.git" master:gh-pages --force && \
	rm -rf .git	
docopen: doc
	open docs/build/html/index.html
docpdf: install
	pip install sphinx sphinx-autobuild
	cd docs; $(MAKE) clean; $(MAKE) latexpdf
test: install
	pip install nose
	# TODO create one big test for this
	nosetests -s -v -x -w bluepyopt/tests/
	# cd examples/l5pc; nrnivmodl mechanisms;  	
	# nosetests -s -v -x -w examples/tests/
example: install
	cd examples/simplecell && \
	python ./opt_simplecell.py
l5pc_start: install
	cd examples/l5pc && \
	nrnivmodl mechanisms && \
	python ./opt_l5pc.py --start
l5pc_cont: install
	cd examples/l5pc && \
	nrnivmodl mechanisms && \
	python ./opt_l5pc.py --continue_cp
l5pc_analyse: install
	cd examples/l5pc && \
	nrnivmodl mechanisms && \
	python ./opt_l5pc.py --analyse
