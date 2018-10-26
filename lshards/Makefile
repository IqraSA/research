SRC		= src
DOC		= doc
RSL		= results


all: 		test3


test2:
		mpirun -np 8 python $(SRC)/test.py

test3:
		mpirun -np 16 python3.6 $(SRC)/test.py


doc:
		@mkdir -p $(DOC)
		doxygen $(DOC)/Doxyfile.in


clean:
		$(RM) -rf $(DOC)/*/* $(SRC)/*.pyc $(RSL)/*


.PHONY:		test doc clean


