import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import {
  DocumentArrowDownIcon,
  DocumentTextIcon,
  TableCellsIcon,
  CodeBracketIcon,
  GlobeAltIcon,
  PresentationChartBarIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  XMarkIcon,
  EyeIcon,
  TrashIcon,
  PlusIcon,
  AdjustmentsHorizontalIcon,
} from '@heroicons/react/24/outline';
import { useAppDispatch, useAppSelector } from '@/store';
import {
  selectIsExporting,
  selectExportProgress,
  selectCurrentExport,
  selectExportHistory,
  selectExportTemplates,
  selectAvailableFormats,
  selectExportOptions,
  startExport,
  cancelExport,
  updateExportOptions,
  addTemplate,
  useTemplate,
  removeFromHistory,
} from '@/store/slices/exportSlice';
import { selectSearchResults } from '@/store/slices/searchSlice';
import { ExportFormat } from '@/types';
import { format } from 'date-fns';

interface ExportPanelProps {
  className?: string;
}

export const ExportPanel: React.FC<ExportPanelProps> = ({ className = '' }) => {
  const dispatch = useAppDispatch();
  const isExporting = useAppSelector(selectIsExporting);
  const exportProgress = useAppSelector(selectExportProgress);
  const currentExport = useAppSelector(selectCurrentExport);
  const exportHistory = useAppSelector(selectExportHistory);
  const templates = useAppSelector(selectExportTemplates);
  const availableFormats = useAppSelector(selectAvailableFormats);
  const exportOptions = useAppSelector(selectExportOptions);
  const searchResults = useAppSelector(selectSearchResults);

  const [activeTab, setActiveTab] = useState<'export' | 'history' | 'templates'>('export');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');

  const formatIcons: Record<ExportFormat, React.ComponentType<{ className?: string }>> = {
    [ExportFormat.CSV]: TableCellsIcon,
    [ExportFormat.JSON]: CodeBracketIcon,
    [ExportFormat.PDF]: DocumentTextIcon,
    [ExportFormat.XLSX]: TableCellsIcon,
    [ExportFormat.HTML]: GlobeAltIcon,
    [ExportFormat.GRAPHML]: PresentationChartBarIcon,
    [ExportFormat.GEXF]: PresentationChartBarIcon,
  };

  const formatDescriptions: Record<ExportFormat, string> = {
    [ExportFormat.CSV]: 'Comma-separated values for spreadsheet applications',
    [ExportFormat.JSON]: 'JavaScript Object Notation for developers',
    [ExportFormat.PDF]: 'Portable Document Format for reports',
    [ExportFormat.XLSX]: 'Excel workbook with multiple sheets',
    [ExportFormat.HTML]: 'Web page format for browser viewing',
    [ExportFormat.GRAPHML]: 'Graph markup language for network analysis',
    [ExportFormat.GEXF]: 'Graph Exchange XML Format for Gephi',
  };

  // Handle export
  const handleExport = () => {
    if (!searchResults) return;

    const entityIds = searchResults.results.map(result => result.entity.id);
    
    dispatch(startExport({
      format: exportOptions.format,
      options: exportOptions,
      entityIds,
    }));
  };

  // Handle template selection
  const handleTemplateSelect = (templateId: string) => {
    if (templateId) {
      dispatch(useTemplate(templateId));
      setSelectedTemplate(templateId);
    }
  };

  // Handle save as template
  const handleSaveTemplate = () => {
    const templateName = prompt('Enter template name:');
    if (templateName) {
      dispatch(addTemplate({
        name: templateName,
        description: `Custom template for ${exportOptions.format} export`,
        format: exportOptions.format,
        options: exportOptions,
        isDefault: false,
      }));
    }
  };

  // Handle file download
  const handleDownload = (downloadUrl: string, fileName: string) => {
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const tabs = [
    { id: 'export', label: 'Export Data', icon: DocumentArrowDownIcon },
    { id: 'history', label: 'Export History', icon: ClockIcon },
    { id: 'templates', label: 'Templates', icon: AdjustmentsHorizontalIcon },
  ];

  return (
    <div className={`h-full flex flex-col bg-gray-50 dark:bg-gray-900 ${className}`}>
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Export & Reporting
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Export search results and generate reports
            </p>
          </div>

          <div className="flex items-center space-x-2">
            {currentExport && (
              <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                <span>Exporting... {exportProgress}%</span>
              </div>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="mt-4 border-b border-gray-200 dark:border-gray-700">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as typeof activeTab)}
                  className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <AnimatePresence mode="wait">
          {activeTab === 'export' && (
            <motion.div
              key="export"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              {!searchResults ? (
                <div className="text-center py-12">
                  <DocumentArrowDownIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">
                    No data to export
                  </h3>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    Perform a search to export results
                  </p>
                </div>
              ) : (
                <>
                  {/* Export options */}
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
                      Export Configuration
                    </h3>

                    {/* Format selection */}
                    <div className="mb-6">
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                        Export Format
                      </label>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {availableFormats.map((format) => {
                          const Icon = formatIcons[format];
                          const isSelected = exportOptions.format === format;
                          
                          return (
                            <button
                              key={format}
                              onClick={() => dispatch(updateExportOptions({ format }))}
                              className={`p-4 border rounded-lg text-left transition-colors ${
                                isSelected
                                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                              }`}
                            >
                              <div className="flex items-start space-x-3">
                                <Icon className="h-6 w-6 text-gray-400 mt-0.5" />
                                <div>
                                  <h4 className="font-medium text-gray-900 dark:text-gray-100 capitalize">
                                    {format}
                                  </h4>
                                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                    {formatDescriptions[format]}
                                  </p>
                                </div>
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {/* Data inclusion options */}
                    <div className="mb-6">
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                        Include in Export
                      </label>
                      <div className="space-y-3">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={exportOptions.includeGraph}
                            onChange={(e) => dispatch(updateExportOptions({ includeGraph: e.target.checked }))}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                            Network graph data
                          </span>
                        </label>
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={exportOptions.includeTimeline}
                            onChange={(e) => dispatch(updateExportOptions({ includeTimeline: e.target.checked }))}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                            Timeline events
                          </span>
                        </label>
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={exportOptions.includeRawData}
                            onChange={(e) => dispatch(updateExportOptions({ includeRawData: e.target.checked }))}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                            Raw data from all sources
                          </span>
                        </label>
                      </div>
                    </div>

                    {/* Advanced options */}
                    <div className="mb-6">
                      <button
                        onClick={() => setShowAdvanced(!showAdvanced)}
                        className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
                      >
                        <AdjustmentsHorizontalIcon className="h-4 w-4" />
                        <span>Advanced Options</span>
                      </button>

                      <AnimatePresence>
                        {showAdvanced && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="mt-4 space-y-4"
                          >
                            {/* Confidence threshold */}
                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Minimum Confidence: {Math.round(exportOptions.confidenceThreshold * 100)}%
                              </label>
                              <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.1"
                                value={exportOptions.confidenceThreshold}
                                onChange={(e) => dispatch(updateExportOptions({ 
                                  confidenceThreshold: parseFloat(e.target.value) 
                                }))}
                                className="w-full"
                              />
                            </div>

                            {/* Max items */}
                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Maximum Items (optional)
                              </label>
                              <input
                                type="number"
                                placeholder="No limit"
                                value={exportOptions.maxItems || ''}
                                onChange={(e) => dispatch(updateExportOptions({ 
                                  maxItems: e.target.value ? parseInt(e.target.value) : undefined 
                                }))}
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                              />
                            </div>

                            {/* Date range */}
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                  Start Date (optional)
                                </label>
                                <input
                                  type="date"
                                  value={exportOptions.dateRange?.start?.toISOString().split('T')[0] || ''}
                                  onChange={(e) => dispatch(updateExportOptions({
                                    dateRange: {
                                      ...exportOptions.dateRange,
                                      start: e.target.value ? new Date(e.target.value) : undefined,
                                    },
                                  }))}
                                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                                />
                              </div>
                              <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                  End Date (optional)
                                </label>
                                <input
                                  type="date"
                                  value={exportOptions.dateRange?.end?.toISOString().split('T')[0] || ''}
                                  onChange={(e) => dispatch(updateExportOptions({
                                    dateRange: {
                                      ...exportOptions.dateRange,
                                      end: e.target.value ? new Date(e.target.value) : undefined,
                                    },
                                  }))}
                                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                                />
                              </div>
                            </div>

                            {/* Redact sensitive data */}
                            <label className="flex items-center">
                              <input
                                type="checkbox"
                                checked={exportOptions.redactSensitive}
                                onChange={(e) => dispatch(updateExportOptions({ redactSensitive: e.target.checked }))}
                                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                              />
                              <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                                Redact sensitive information (emails, phone numbers, addresses)
                              </span>
                            </label>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>

                    {/* Template selection */}
                    <div className="mb-6">
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                        Templates
                      </label>
                      <div className="flex items-center space-x-2">
                        <select
                          value={selectedTemplate}
                          onChange={(e) => handleTemplateSelect(e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                        >
                          <option value="">Select a template</option>
                          {templates.map((template) => (
                            <option key={template.id} value={template.id}>
                              {template.name}
                            </option>
                          ))}
                        </select>
                        <button
                          onClick={handleSaveTemplate}
                          className="flex items-center space-x-1 px-3 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                        >
                          <PlusIcon className="h-4 w-4" />
                          <span>Save as Template</span>
                        </button>
                      </div>
                    </div>

                    {/* Export button */}
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {searchResults.results.length} entities will be exported
                      </div>
                      <button
                        onClick={handleExport}
                        disabled={isExporting || !searchResults}
                        className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isExporting ? (
                          <>
                            <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                            <span>Exporting...</span>
                          </>
                        ) : (
                          <>
                            <DocumentArrowDownIcon className="h-4 w-4" />
                            <span>Export Data</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </>
              )}
            </motion.div>
          )}

          {activeTab === 'history' && (
            <motion.div
              key="history"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-4"
            >
              {exportHistory.length === 0 ? (
                <div className="text-center py-12">
                  <ClockIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">
                    No export history
                  </h3>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    Your exported files will appear here
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {exportHistory.map((item) => (
                    <div
                      key={item.id}
                      className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-start space-x-3">
                          <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                            {React.createElement(formatIcons[item.format], { 
                              className: "h-5 w-5 text-gray-600 dark:text-gray-400" 
                            })}
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900 dark:text-gray-100">
                              {item.fileName}
                            </h4>
                            <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500 dark:text-gray-400">
                              <span>{item.entityCount} entities</span>
                              <span>•</span>
                              <span>{format(item.createdAt, 'MMM dd, yyyy HH:mm')}</span>
                              <span>•</span>
                              <span className="capitalize">{item.format}</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2">
                          {item.isExpired ? (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400">
                              <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
                              Expired
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                              <CheckCircleIcon className="h-3 w-3 mr-1" />
                              Available
                            </span>
                          )}

                          <div className="flex items-center space-x-1">
                            <button
                              onClick={() => handleDownload(item.downloadUrl, item.fileName)}
                              disabled={item.isExpired}
                              className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-50"
                              title="Download"
                            >
                              <DocumentArrowDownIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => dispatch(removeFromHistory(item.id))}
                              className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                              title="Remove from history"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      </div>

                      {item.size && (
                        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                          Size: {(item.size / 1024 / 1024).toFixed(2)} MB
                          {item.expiresAt && (
                            <span> • Expires {format(item.expiresAt, 'MMM dd, yyyy')}</span>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'templates' && (
            <motion.div
              key="templates"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-4"
            >
              {templates.length === 0 ? (
                <div className="text-center py-12">
                  <AdjustmentsHorizontalIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">
                    No templates saved
                  </h3>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    Create templates to quickly export data with preferred settings
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {templates.map((template) => (
                    <div
                      key={template.id}
                      className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-start space-x-3">
                          <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                            {React.createElement(formatIcons[template.format], { 
                              className: "h-5 w-5 text-gray-600 dark:text-gray-400" 
                            })}
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900 dark:text-gray-100">
                              {template.name}
                            </h4>
                            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                              {template.description}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                        <div>Format: {template.format.toUpperCase()}</div>
                        <div>
                          Created: {format(template.createdAt, 'MMM dd, yyyy')}
                        </div>
                        {template.lastUsed && (
                          <div>
                            Last used: {format(template.lastUsed, 'MMM dd, yyyy')}
                          </div>
                        )}
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleTemplateSelect(template.id)}
                          className="flex-1 px-3 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                        >
                          Use Template
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ExportPanel;