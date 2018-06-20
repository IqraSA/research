SRC		= src
DOC		= doc
RSL		= results


all: 		test


test:
		python $(SRC)/test.py


doc:
		@mkdir -p $(DOC)
		doxygen $(DOC)/Doxyfile.in


clean:
		$(RM) -rf $(DOC)/*/* $(SRC)/*.pyc $(RSL)/*


.PHONY:		test doc clean


