# geospatial-pdf-parser

Code to parse geospatial pdfs from python

Built on top of [pdfminer](https://github.com/pdfminer/pdfminer.six)

Adds rudimentary PDF Layers( Optional Content ) support on top of pdfminer

The main goal of this code is to be able to parse Geospatial PDFs created by ESRI ArcMap,
If it manages to do anything else( or even the above mentioned goal ), it is just your good fortune :)


How to identify a geospatial PDF?
 * use ogrinfo from osgeo GDAL toolset, if a NEATLINE shows up in the output to `ogringo <pdf_filename>` it is a geospatial pdf
 * Look at document properties.. if the `Content Creator` or `Application` metadata fields point to `ESRI ArcMap`,
   there is a good chance it is a Geospatial PDF


Tools that helped:
http://brendandahl.github.io/pdf.js.utils/browser/

Learnings:
I do not like the PDF

This is a WIP
