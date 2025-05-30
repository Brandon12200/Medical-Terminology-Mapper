import type { MappingResponse } from '../types';

export const exportToCSV = (data: MappingResponse | MappingResponse[], filename: string) => {
  const dataArray = Array.isArray(data) ? data : [data];
  
  // Create CSV header
  const headers = ['Term', 'System', 'Code', 'Display', 'Confidence', 'Match Type'];
  const csvContent = [headers.join(',')];
  
  // Add data rows
  dataArray.forEach(result => {
    result.mappings.forEach(mapping => {
      const row = [
        `"${result.term}"`,
        mapping.system,
        mapping.code,
        `"${mapping.display}"`,
        mapping.confidence.toFixed(3),
        mapping.match_type || ''
      ];
      csvContent.push(row.join(','));
    });
  });
  
  // Create blob and download
  const blob = new Blob([csvContent.join('\n')], { type: 'text/csv;charset=utf-8;' });
  downloadBlob(blob, filename);
};

export const exportToJSON = (data: MappingResponse | MappingResponse[], filename: string) => {
  const jsonContent = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonContent], { type: 'application/json' });
  downloadBlob(blob, filename);
};

const downloadBlob = (blob: Blob, filename: string) => {
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  // Clean up
  URL.revokeObjectURL(url);
};