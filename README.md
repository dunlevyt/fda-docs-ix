
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

To-Do
-----
* Add useful PDF document info and metadata as properties and relations in Neo4j
* Create a more useful index in ES

Blockers
--------
* Neo4j River Plugin install had numerous dependency issues on install
* Neo4j River Plugin lacking documentation
* Automated index created by Neo4j River Plugin appears to have limited use as configured

