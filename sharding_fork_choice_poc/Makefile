SRC		= src
DOC		= doc


all: 		test


test:
		python $(SRC)/test.py


doc:
		@mkdir -p $(DOC)
		doxygen $(DOC)/Doxyfile.in


clean:
		$(RM) -rf $(DOC)/*/*


.PHONY:		test doc clean


