"""Export functionality for username enumeration results"""
import json
import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import Response
from fastapi.responses import StreamingResponse


class ExportFormat:
    """Supported export formats"""
    JSON = "json"
    CSV = "csv"


class ResultExporter:
    """Export username enumeration results to various formats"""
    
    def __init__(self):
        pass
    
    async def export_to_json(
        self,
        results: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Export results to JSON format
        
        Args:
            results: List of search results
            metadata: Optional metadata to include in export
            
        Returns:
            JSON string
        """
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_results": len(results),
            "results": results
        }
        
        if metadata:
            export_data["metadata"] = metadata
        
        return json.dumps(export_data, indent=2, default=str)
    
    async def export_to_csv(
        self,
        results: List[Dict[str, Any]],
        include_metadata: bool = False
    ) -> str:
        """
        Export results to CSV format
        
        Args:
            results: List of search results
            include_metadata: Whether to include metadata columns
            
        Returns:
            CSV string
        """
        if not results:
            return ""
        
        output = io.StringIO()
        
        # Determine columns
        base_columns = ['username', 'platform', 'profile_url', 'confidence', 
                       'match_type', 'discovered_at']
        
        if include_metadata:
            # Get all unique metadata keys
            metadata_keys = set()
            for result in results:
                if 'metadata' in result and result['metadata']:
                    metadata_keys.update(result['metadata'].keys())
            columns = base_columns + list(metadata_keys)
        else:
            columns = base_columns
        
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        
        for result in results:
            row = {
                'username': result.get('username', ''),
                'platform': result.get('platform', ''),
                'profile_url': result.get('profile_url', ''),
                'confidence': result.get('confidence', 0),
                'match_type': result.get('match_type', ''),
                'discovered_at': result.get('discovered_at', '')
            }
            
            # Add metadata if requested
            if include_metadata and 'metadata' in result:
                row.update(result['metadata'])
            
            writer.writerow(row)
        
        return output.getvalue()
    
    async def export_identity_chain(
        self,
        chain_data: Dict[str, Any],
        format: str = ExportFormat.JSON
    ) -> str:
        """
        Export identity chain to specified format
        
        Args:
            chain_data: Identity chain data with nodes and relationships
            format: Export format (json or csv)
            
        Returns:
            Exported data string
        """
        if format == ExportFormat.JSON:
            export_data = {
                "export_timestamp": datetime.utcnow().isoformat(),
                "chain_length": chain_data.get('chain_length', 0),
                "nodes": chain_data.get('nodes', []),
                "relationships": chain_data.get('relationships', [])
            }
            return json.dumps(export_data, indent=2, default=str)
        
        elif format == ExportFormat.CSV:
            # Export nodes
            nodes_csv = self._export_nodes_to_csv(chain_data.get('nodes', []))
            
            # Export relationships
            relationships_csv = self._export_relationships_to_csv(
                chain_data.get('relationships', [])
            )
            
            # Combine with separator
            return f"# NODES\n{nodes_csv}\n\n# RELATIONSHIPS\n{relationships_csv}"
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_nodes_to_csv(self, nodes: List[Dict[str, Any]]) -> str:
        """Export nodes to CSV"""
        output = io.StringIO()
        
        columns = ['id', 'type', 'value', 'platform', 'confidence']
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        
        for node in nodes:
            writer.writerow(node)
        
        return output.getvalue()
    
    def _export_relationships_to_csv(self, relationships: List[Dict[str, Any]]) -> str:
        """Export relationships to CSV"""
        output = io.StringIO()
        
        columns = ['source_id', 'target_id', 'relationship_type', 
                   'confidence', 'discovered_at']
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        
        for rel in relationships:
            writer.writerow(rel)
        
        return output.getvalue()
    
    async def create_json_response(
        self,
        results: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
        filename: str = "results.json"
    ) -> Response:
        """
        Create FastAPI response for JSON export
        
        Args:
            results: Results to export
            metadata: Optional metadata
            filename: Filename for download
            
        Returns:
            FastAPI Response object
        """
        json_data = await self.export_to_json(results, metadata)
        
        return Response(
            content=json_data,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    
    async def create_csv_response(
        self,
        results: List[Dict[str, Any]],
        include_metadata: bool = False,
        filename: str = "results.csv"
    ) -> Response:
        """
        Create FastAPI response for CSV export
        
        Args:
            results: Results to export
            include_metadata: Whether to include metadata
            filename: Filename for download
            
        Returns:
            FastAPI Response object
        """
        csv_data = await self.export_to_csv(results, include_metadata)
        
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    
    async def create_identity_chain_response(
        self,
        chain_data: Dict[str, Any],
        format: str = ExportFormat.JSON,
        filename: str = "identity_chain"
    ) -> Response:
        """
        Create FastAPI response for identity chain export
        
        Args:
            chain_data: Identity chain data
            format: Export format
            filename: Filename (without extension)
            
        Returns:
            FastAPI Response object
        """
        data = await self.export_identity_chain(chain_data, format)
        
        if format == ExportFormat.JSON:
            media_type = "application/json"
            ext = "json"
        else:
            media_type = "text/csv"
            ext = "csv"
        
        return Response(
            content=data,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}.{ext}"'
            }
        )


def get_exporter() -> ResultExporter:
    """Get singleton exporter instance"""
    return ResultExporter()
