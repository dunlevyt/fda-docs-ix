
Goals
-----
* Retrieve PDF documents from http://www.fda.gov/ForConsumers/ByAudience/ForWomen/FreePublications/ucm116718.htm
* Extract document info and metadata
* Create nodes in Neo4j
* Create index on ElasticSearch (ES)

Dependencies Used
-----------------
* Neo4j 2.0
* Elasticsearch 0.90.9
* Neo4j River Plugin 0.90.9.0


Execution
---------
* line 65, 'db_path' is the url of the Neo4j database
* line 70, 'es_cluster' are the connection parameters for the elasticsearch cluster
* line 185, 'fda_base_url' is the http host of the source of pdf documents
* line 188, the path and document to parse for links to pdf documents
* python fda-docs-ix.py

Results
-------
* Neo4j browser: http://localhost:7474/browser/
 * match (n) return n;
 * The default graph in the Neo4j browser can be seen here: <neo_screenshot.png>
 * Keyword query:
 * match q(d:PDFDocument)-[r:HAS_KEYWORD]->(k:Keyword) where k.name='menopause' return d.title, d.url;
 * Results can be seen here <neo_keyword_query.png>
* Kibana dashboard:
 * Querying for the same keyword against the document index: <kibana_screenshot.png>

Conclusion
----------
* Successfully extracted document metadata and created graph results in neo4j
* Successfully created full text index of pdf documents in Elasticsearch
* Successfully utilized Kibana dashboard for ad-hoc searches

