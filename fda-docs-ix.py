# -*- coding: utf-8 -*-
import urllib2
import re
import StringIO
import base64
from HTMLParser import HTMLParser
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdftypes import resolve1
from xmp import xmp_to_dict
from neo4jrestclient.client import GraphDatabase
from neo4jrestclient import client
from elasticsearch import Elasticsearch
from elasticsearch.client import IndicesClient


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
    authors = None
    keywords = None
    es_cluster = [{'host': 'localhost', 'port': 9200}]
    es = None
    es_ixc = None

    def __init__(self):
        self.db = GraphDatabase(self.db_path)
        self.pdf_documents = self.db.labels.create("PDFDocument")
        self.authors = self.db.labels.create("Author")
        self.keywords = self.db.labels.create("Keyword")
        self.es = Elasticsearch(self.es_cluster)
        self.es_ixc = IndicesClient(self.es)
        self.es_ixc.create(
            index="pdf_documents",
            body={
                'mappings': {
                    'pdf': {
                        'properties': {
                            'url': {'type': "string"},
                            'pdf_file': {'type': "attachment"}
                        }
                    }
                }
            }
        )

    def createNodesAndIx(self, doc_url, doc_info, doc_metadata, doc_data):
        check_for = lambda n, d: d[n] if (n in d) else ''
        author = check_for('Author', doc_info[0])
        if author is not '':
            author_node = self.authorExists(author)
            if author_node is None:
                author_node = self.createAuthor(author)
        if check_for('pdf', doc_metadata) is not '':
            keywords = check_for('Keywords', doc_metadata['pdf'])
        else:
            keywords = ''
        if keywords is not '':
            keyword_nodes = []
            for keyword in map(lambda x: x.strip(" '\""), keywords.split(",")):
                keyword_node = self.keywordExists(keyword)
                if keyword_node is None:
                    keyword_node = self.createKeyword(keyword)
                keyword_nodes.append(keyword_node)
        pdf_node = self.db.nodes.create(
            url=doc_url,
            info=repr(doc_info),
            metadata=repr(doc_metadata),
            title=check_for('Title', doc_info[0])
        )
        self.pdf_documents.add(pdf_node)
        if author is not '':
            pdf_node.relationships.create("AUTHORED_BY", author_node)
        if keywords is not '':
            for keyword_node in keyword_nodes:
                pdf_node.relationships.create("HAS_KEYWORD", keyword_node)
        self.es.create(
                index="pdf_documents",
                doc_type="pdf",
                id=pdf_node.id,
                body={
                    'url': doc_url,
                    'pdf_file': base64.b64encode(doc_data.getvalue())
                }
            )

    def authorExists(self, author):
        r = self.db.query(
            'match (a:Author) where a.name = "' + author + '" return a',
            returns=(client.Node)
        )
        return r[0][0] if (len(r) > 0) else None

    def createAuthor(self, author):
        an_author = self.db.nodes.create(name=author)
        self.authors.add(an_author)
        return an_author

    def keywordExists(self, keyword):
        r = self.db.query(
            'match (k:Keyword) where k.name = "' + keyword + '" return k',
            returns=(client.Node)
        )
        return r[0][0] if (len(r) > 0) else None

    def createKeyword(self, keyword):
        a_keyword = self.db.nodes.create(name=keyword)
        self.keywords.add(a_keyword)
        return a_keyword


# Get PDF doc links from the base URL
fdaBaseUrl = 'http://www.fda.gov'

response = urllib2.urlopen(
    fdaBaseUrl +
        '/ForConsumers/ByAudience/ForWomen/FreePublications/ucm116718.htm'
)
html = response.read()
parser = htmlPdfLinkParser()
parser.feed(html)

# Download PDF docs and import into Neo4j and ES
di = pdfDocInfo()
fd = fileDownloader()
graph = pdfGraph()

for link in parser.links:
#for link in parser.links[:3]:
    a_url = fdaBaseUrl + link
    a_pdf = fd.getFile(a_url)
    if a_pdf is not None:
        di.proc(a_pdf)
        graph.createNodesAndIx(a_url, di.info, di.metadata, a_pdf)
        a_pdf.close()
