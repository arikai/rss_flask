REPORTDIR = ./report
LABNAME = 6_progtech
TEXFILE = $(LABNAME)_report.tex
PDFFILE = $(LABNAME)_report.pdf



report: $(PDFFILE)
	zathura $(REPORTDIR)/$(PDFFILE) &

$(PDFFILE): $(REPORTDIR)/$(TEXFILE) 
	cd $(REPORTDIR) && xelatex -shell-escape $(TEXFILE) && cd -

.PHONY: report
