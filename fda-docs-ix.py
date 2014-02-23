# -*- coding: utf-8 -*-
import urllib2
import re
import StringIO
from HTMLParser import HTMLParser
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdftypes import resolve1
from xmp import xmp_to_dict
from neo4jrestclient.client import GraphDatabase
#from elasticsearch import Elasticsearch


class pdfDocInfo():
    """Extract PDF document info and metadata"""

    info = None
    metadata = None
    raw_doc = None

    def proc(self, pdfFp):
        parser = PDFParser(pdfFp)
        doc = PDFDocument(parser)
        parser.set_document(doc)
        doc.initialize()
        self.info = doc.info
        if 'Metadata' in doc.catalog:
            self.metadata = xmp_to_dict(
                resolve1(doc.catalog['Metadata']).get_data()
            )
        self.raw_doc = pdfFp.getvalue()


class fileDownloader():
    def getFile(self, url):
        try:
            response = urllib2.urlopen(url)
            return StringIO.StringIO(response.read())
        except:
            return None


class htmlPdfLinkParser(HTMLParser):
    """Get PDF links from HTML"""

    links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for nv in attrs:
                if nv[0] == 'href' and re.search('.*\.pdf$', nv[1]) is not None:
                    self.links.append(nv[1])


class pdfGraph():
    """Create and manage the PDF graph"""

    db_path = "http://localhost:7474/db/data/"
    db = None
    pdf_documents = None

    def __init__(self):
        self.db = GraphDatabase(self.db_path)
        self.pdf_documents = self.db.labels.create("PDFDocument")

    def createNode(self, doc_url, doc_info, doc_metadata):
        a_node = self.db.nodes.create(
            url=doc_url,
            info=repr(doc_info),
            metadata=repr(doc_metadata)
        )
        self.pdf_documents.add(a_node)


# Get PDF doc links from the base URL
fdaBaseUrl = 'http://www.fda.gov'

response = urllib2.urlopen(
    fdaBaseUrl +
        '/ForConsumers/ByAudience/ForWomen/FreePublications/ucm116718.htm'
)
html = response.read()
parser = htmlPdfLinkParser()
parser.feed(html)

# Download PDF docs and import into Neo4j
di = pdfDocInfo()
fd = fileDownloader()
graph = pdfGraph()

for link in parser.links:
    a_url = fdaBaseUrl + link
    aPdf = fd.getFile(a_url)
    if aPdf is not None:
        di.proc(aPdf)
        aPdf.close()
        graph.createNode(a_url, di.info, di.metadata)

# Create the ES index
#    (using https://github.com/sksamuel/elasticsearch-river-neo4j)
#
#curl -XPUT 'http://localhost:9200/_river/neo_pdfdocuments/_meta' -d
#  '{
#    "type": "neo4j",
#    "neo4j": {
#        "uri": "http://localhost:7474/db/data",
#        "labels": ["PDFDocument"],
#        "interval": 1000
#        },
#    "index": {
#        "name": "neo_pdfdocuments",
#        "type": "neo_pdfdocuments"}
#   }'
