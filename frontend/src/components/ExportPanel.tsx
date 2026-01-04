import React, { useState } from 'react';
import { FiDownload, FiFileText, FiFile } from 'react-icons/fi';
import { useAppSelector } from '../hooks/useAppSelector';
import { exportToCSV, exportToJSON, exportToPDF, exportToExcel, exportToHTML } from '../utils/exportUtils';
import toast from 'react-hot-toast';
import clsx from 'clsx';

const ExportPanel: React.FC = () => {
  const { results } = useAppSelector(state => state.search);
  const { selectedNode } = useAppSelector(state => state.graph);
  const [format, setFormat] = useState<'csv' | 'json' | 'pdf' | 'xlsx' | 'html'>('json');
  const [template, setTemplate] = useState<'standard' | 'executive' | 'detailed'>('standard');
  const [includeGraph, setIncludeGraph] = useState(true);
  const [includeTimeline, setIncludeTimeline] = useState(true);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.5);

  const handleExport = () => {
    try {
      if (!selectedNode && results.length === 0) {
        toast.error('No data to export');
        return;
      }

      const dataToExport = selectedNode ? selectedNode.data : { results };

      switch (format) {
        case 'csv':
          exportToCSV(Array.isArray(dataToExport) ? dataToExport : [dataToExport], 'osint-export.csv');
          break;
        case 'json':
          exportToJSON(dataToExport, 'osint-export.json');
          break;
        case 'pdf':
          if (selectedNode?.data) {
            exportToPDF(selectedNode.data, { format: 'pdf', template });
          }
          break;
        case 'xlsx':
          exportToExcel(Array.isArray(dataToExport) ? dataToExport : [dataToExport], 'osint-export.xlsx');
          break;
        case 'html':
          if (selectedNode?.data) {
            exportToHTML(selectedNode.data);
          }
          break;
      }

      toast.success('Export completed successfully');
    } catch (error) {
      toast.error('Export failed');
      console.error(error);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Export Data
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Export your OSINT data in various formats
        </p>
      </div>

      <div className="bg-white dark:bg-dark-800 rounded-lg shadow p-6 space-y-6">
        {/* Export Format */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Export Format
          </label>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {(['json', 'csv', 'xlsx', 'pdf', 'html'] as const).map((fmt) => (
              <button
                key={fmt}
                onClick={() => setFormat(fmt)}
                className={clsx(
                  'p-4 rounded-lg border-2 transition-all',
                  format === fmt
                    ? 'border-primary-600 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-gray-200 dark:border-dark-600 hover:border-gray-300 dark:hover:border-dark-500'
                )}
              >
                <FiFile className="mx-auto mb-2" size={24} />
                <div className="text-center text-sm font-medium uppercase">
                  {fmt}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Report Template (for PDF/HTML) */}
        {(format === 'pdf' || format === 'html') && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Report Template
            </label>
            <div className="grid grid-cols-3 gap-3">
              {(['standard', 'executive', 'detailed'] as const).map((tmpl) => (
                <button
                  key={tmpl}
                  onClick={() => setTemplate(tmpl)}
                  className={clsx(
                    'px-4 py-3 rounded-lg border-2 transition-all capitalize',
                    template === tmpl
                      ? 'border-primary-600 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-dark-600 hover:border-gray-300 dark:hover:border-dark-500'
                  )}
                >
                  {tmpl}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Export Options */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Export Options
          </label>
          <div className="space-y-3">
            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={includeGraph}
                onChange={(e) => setIncludeGraph(e.target.checked)}
                className="rounded text-primary-600 focus:ring-primary-500"
              />
              <span className="text-gray-700 dark:text-gray-300">
                Include relationship graph
              </span>
            </label>
            
            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={includeTimeline}
                onChange={(e) => setIncludeTimeline(e.target.checked)}
                className="rounded text-primary-600 focus:ring-primary-500"
              />
              <span className="text-gray-700 dark:text-gray-300">
                Include activity timeline
              </span>
            </label>
          </div>
        </div>

        {/* Confidence Threshold */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Minimum Confidence Score: {Math.round(confidenceThreshold * 100)}%
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={confidenceThreshold * 100}
            onChange={(e) => setConfidenceThreshold(parseInt(e.target.value) / 100)}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
            <span>0%</span>
            <span>50%</span>
            <span>100%</span>
          </div>
        </div>

        {/* Export Button */}
        <div className="pt-4 border-t border-gray-200 dark:border-dark-700">
          <button
            onClick={handleExport}
            disabled={!selectedNode && results.length === 0}
            className={clsx(
              'w-full px-6 py-3 rounded-lg font-medium flex items-center justify-center space-x-2 transition-colors',
              selectedNode || results.length > 0
                ? 'bg-primary-600 hover:bg-primary-700 text-white'
                : 'bg-gray-300 dark:bg-dark-600 cursor-not-allowed text-gray-500'
            )}
          >
            <FiDownload size={20} />
            <span>Export Data</span>
          </button>
        </div>

        {/* Export History */}
        <div className="pt-4 border-t border-gray-200 dark:border-dark-700">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
            Recent Exports
          </h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-dark-700 rounded-lg">
              <div className="flex items-center space-x-3">
                <FiFileText className="text-gray-500" />
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    osint-export.json
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    Exported 2 minutes ago
                  </p>
                </div>
              </div>
              <button className="text-primary-600 dark:text-primary-400 text-sm hover:underline">
                Download
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExportPanel;
