# -*- coding: utf-8 -*-

import json
import logging
from odoo import models, api
from opensearchpy import OpenSearch, exceptions as opensearch_exceptions

_logger = logging.getLogger(__name__)


class NBSOpenSearchService(models.AbstractModel):
    _name = 'nbs.opensearch.service'
    _description = 'OpenSearch Integration Service'
    
    def _get_client(self):
        """Get OpenSearch client"""
        config = self.env['ir.config_parameter'].sudo()
        host = config.get_param('opensearch.host', 'opensearch')
        port = int(config.get_param('opensearch.port', '9200'))
        
        client = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            http_auth=None,  # No auth in development
            use_ssl=False,
            verify_certs=False,
            ssl_show_warn=False,
            timeout=30
        )
        
        return client
    
    @api.model
    def create_index(self):
        """Create OpenSearch index with proper mappings"""
        client = self._get_client()
        index_name = 'nbs_documents'
        
        # Check if index exists
        if client.indices.exists(index=index_name):
            _logger.info(f"OpenSearch index '{index_name}' already exists")
            return True
        
        # Index mapping with Arabic/English support
        mapping = {
            "settings": {
                "analysis": {
                    "analyzer": {
                        "arabic_english": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                                "arabic_normalization",
                                "asciifolding"
                            ]
                        }
                    }
                },
                "index": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                }
            },
            "mappings": {
                "properties": {
                    "document_id": {"type": "integer"},
                    "title": {
                        "type": "text",
                        "analyzer": "arabic_english",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "content": {
                        "type": "text",
                        "analyzer": "arabic_english"
                    },
                    "pages": {
                        "type": "nested",
                        "properties": {
                            "page_number": {"type": "integer"},
                            "text": {
                                "type": "text",
                                "analyzer": "arabic_english"
                            }
                        }
                    },
                    "department": {"type": "keyword"},
                    "department_id": {"type": "integer"},
                    "document_type": {"type": "keyword"},
                    "document_type_id": {"type": "integer"},
                    "tags": {"type": "keyword"},
                    "barcode": {"type": "keyword"},
                    "po_number": {"type": "keyword"},
                    "bl_number": {"type": "keyword"},
                    "container_number": {"type": "keyword"},
                    "invoice_number": {"type": "keyword"},
                    "envoy_number": {"type": "keyword"},
                    "confidentiality_level": {"type": "keyword"},
                    "upload_date": {"type": "date"},
                    "uploader": {"type": "keyword"},
                    "uploader_id": {"type": "integer"},
                    "state": {"type": "keyword"},
                    "version_number": {"type": "integer"},
                }
            }
        }
        
        try:
            client.indices.create(index=index_name, body=mapping)
            _logger.info(f"OpenSearch index '{index_name}' created successfully")
            return True
        except opensearch_exceptions.RequestError as e:
            _logger.error(f"Failed to create OpenSearch index: {e}")
            return False
    
    def _index_document(self, document_id):
        """Index document by ID (wrapper for async calls)"""
        try:
            document = self.env['nbs.document'].sudo().browse(document_id)
            if document.exists():
                return self.index_document(document)
            return False
        except Exception as e:
            _logger.warning(f'Failed to index document {document_id}: {str(e)}')
            return False
    
    @api.model
    def index_document(self, document):
        """Index a document in OpenSearch"""
        if not document:
            return False
        
        client = self._get_client()
        index_name = 'nbs_documents'
        
        version = document.current_version_id
        
        # Build document data
        doc_data = {
            'document_id': document.id,
            'title': document.name,
            'content': version.extracted_text or '',
            'department': document.department_id.code,
            'department_id': document.department_id.id,
            'document_type': document.document_type_id.code,
            'document_type_id': document.document_type_id.id,
            'tags': [tag.name for tag in document.tag_ids],
            'barcode': document.barcode,
            'po_number': document.po_number or '',
            'bl_number': document.bl_number or '',
            'container_number': document.container_number or '',
            'invoice_number': document.invoice_number or '',
            'envoy_number': document.envoy_number or '',
            'confidentiality_level': document.confidentiality_level,
            'upload_date': document.upload_date.isoformat() if document.upload_date else None,
            'uploader': document.uploader_id.name,
            'uploader_id': document.uploader_id.id,
            'state': document.state,
            'version_number': version.version_number,
        }
        
        # Add per-page text
        pages = version.get_extracted_pages()
        if pages:
            doc_data['pages'] = pages
        
        try:
            client.index(
                index=index_name,
                id=document.id,
                body=doc_data,
                refresh=True
            )
            _logger.info(f"Document {document.id} indexed successfully")
            return True
        except Exception as e:
            _logger.error(f"Failed to index document {document.id}: {e}")
            return False
    
    @api.model
    def search_documents(self, query, filters=None, fuzzy=True, page=1, per_page=20):
        """
        Search documents with highlight
        
        Args:
            query: Search query string
            filters: Dict of filters (department_ids, document_type_ids, date_from, etc.)
            fuzzy: Enable fuzzy search
            page: Page number (1-indexed)
            per_page: Results per page
        
        Returns:
            Dict with results, pagination, and timing info
        """
        client = self._get_client()
        index_name = 'nbs_documents'
        filters = filters or {}
        
        # Build query
        must_queries = []
        filter_queries = []
        
        # Main search query
        if query:
            must_queries.append({
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "content", "pages.text"],
                    "fuzziness": "AUTO" if fuzzy else 0,
                    "operator": "or"
                }
            })
        else:
            must_queries.append({"match_all": {}})
        
        # Filters
        if filters.get('department_ids'):
            filter_queries.append({
                "terms": {"department_id": filters['department_ids']}
            })
        
        if filters.get('document_type_ids'):
            filter_queries.append({
                "terms": {"document_type_id": filters['document_type_ids']}
            })
        
        if filters.get('date_from'):
            filter_queries.append({
                "range": {"upload_date": {"gte": filters['date_from']}}
            })
        
        if filters.get('date_to'):
            filter_queries.append({
                "range": {"upload_date": {"lte": filters['date_to']}}
            })
        
        if filters.get('confidentiality_levels'):
            filter_queries.append({
                "terms": {"confidentiality_level": filters['confidentiality_levels']}
            })
        
        if filters.get('tags'):
            filter_queries.append({
                "terms": {"tags": filters['tags']}
            })
        
        # Only active documents by default
        if filters.get('state'):
            filter_queries.append({"term": {"state": filters['state']}})
        else:
            filter_queries.append({"term": {"state": "active"}})
        
        # Build full query
        search_body = {
            "from": (page - 1) * per_page,
            "size": per_page,
            "query": {
                "bool": {
                    "must": must_queries,
                    "filter": filter_queries
                }
            },
            "highlight": {
                "fields": {
                    "title": {
                        "pre_tags": ["<mark>"],
                        "post_tags": ["</mark>"],
                        "number_of_fragments": 0
                    },
                    "content": {
                        "pre_tags": ["<mark>"],
                        "post_tags": ["</mark>"],
                        "fragment_size": 150,
                        "number_of_fragments": 3
                    },
                    "pages.text": {
                        "pre_tags": ["<mark>"],
                        "post_tags": ["</mark>"],
                        "fragment_size": 150,
                        "number_of_fragments": 3
                    }
                },
                "require_field_match": False
            },
            "sort": [
                {"_score": {"order": "desc"}},
                {"upload_date": {"order": "desc"}}
            ]
        }
        
        try:
            response = client.search(index=index_name, body=search_body)
            
            # Process results
            results = []
            for hit in response['hits']['hits']:
                result = {
                    'document_id': hit['_source']['document_id'],
                    'title': hit['_source']['title'],
                    'barcode': hit['_source']['barcode'],
                    'score': hit['_score'],
                    'department': hit['_source']['department'],
                    'document_type': hit['_source']['document_type'],
                    'upload_date': hit['_source']['upload_date'],
                    'uploader': hit['_source']['uploader'],
                }
                
                # Add highlights
                if 'highlight' in hit:
                    result['highlights'] = {}
                    if 'title' in hit['highlight']:
                        result['highlights']['title'] = hit['highlight']['title']
                    if 'content' in hit['highlight']:
                        result['highlights']['content'] = hit['highlight']['content']
                    if 'pages.text' in hit['highlight']:
                        result['highlights']['pages'] = hit['highlight']['pages.text']
                
                results.append(result)
            
            return {
                'results': results,
                'total': response['hits']['total']['value'],
                'page': page,
                'per_page': per_page,
                'took_ms': response['took']
            }
        
        except Exception as e:
            _logger.error(f"Search failed: {e}")
            return {
                'results': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'error': str(e)
            }
    
    @api.model
    def search_by_barcode(self, barcode):
        """Search document by barcode"""
        client = self._get_client()
        index_name = 'nbs_documents'
        
        try:
            response = client.search(
                index=index_name,
                body={
                    "query": {
                        "term": {"barcode": barcode}
                    }
                }
            )
            
            if response['hits']['total']['value'] > 0:
                hit = response['hits']['hits'][0]
                return {
                    'found': True,
                    'document_id': hit['_source']['document_id']
                }
            else:
                return {'found': False}
        
        except Exception as e:
            _logger.error(f"Barcode search failed: {e}")
            return {'found': False, 'error': str(e)}
    
    @api.model
    def delete_document(self, document_id):
        """Remove document from index"""
        client = self._get_client()
        index_name = 'nbs_documents'
        
        try:
            client.delete(index=index_name, id=document_id)
            _logger.info(f"Document {document_id} removed from index")
            return True
        except opensearch_exceptions.NotFoundError:
            _logger.warning(f"Document {document_id} not found in index")
            return False
        except Exception as e:
            _logger.error(f"Failed to delete document from index: {e}")
            return False

