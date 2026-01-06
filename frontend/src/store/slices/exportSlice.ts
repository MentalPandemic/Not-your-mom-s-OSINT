import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ExportOptions, ExportFormat } from '@/types';

interface ExportState {
  isExporting: boolean;
  exportProgress: number;
  currentExport: {
    id: string;
    format: ExportFormat;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    fileName?: string;
    downloadUrl?: string;
    error?: string;
  } | null;
  exportHistory: ExportHistoryItem[];
  templates: ExportTemplate[];
  recentExports: string[];
  availableFormats: ExportFormat[];
  exportOptions: ExportOptions;
  customFields: string[];
  defaultOptions: ExportOptions;
}

interface ExportHistoryItem {
  id: string;
  format: ExportFormat;
  fileName: string;
  createdAt: Date;
  size?: number;
  downloadUrl: string;
  isExpired: boolean;
  expiresAt?: Date;
  entityCount: number;
  confidenceThreshold: number;
  filters: Record<string, any>;
}

interface ExportTemplate {
  id: string;
  name: string;
  description: string;
  format: ExportFormat;
  options: ExportOptions;
  isDefault: boolean;
  createdAt: Date;
  lastUsed?: Date;
}

const initialState: ExportState = {
  isExporting: false,
  exportProgress: 0,
  currentExport: null,
  exportHistory: [],
  templates: [],
  recentExports: [],
  availableFormats: [
    ExportFormat.CSV,
    ExportFormat.JSON,
    ExportFormat.PDF,
    ExportFormat.XLSX,
    ExportFormat.HTML,
    ExportFormat.GRAPHML,
    ExportFormat.GEXF,
  ],
  exportOptions: {
    format: ExportFormat.JSON,
    includeGraph: true,
    includeTimeline: true,
    includeRawData: true,
    confidenceThreshold: 0.7,
    redactSensitive: false,
  },
  customFields: [],
  defaultOptions: {
    format: ExportFormat.JSON,
    includeGraph: true,
    includeTimeline: true,
    includeRawData: true,
    confidenceThreshold: 0.7,
    redactSensitive: false,
  },
};

const exportSlice = createSlice({
  name: 'export',
  initialState,
  reducers: {
    startExport: (state, action: PayloadAction<{
      format: ExportFormat;
      options: ExportOptions;
      entityIds: string[];
    }>) => {
      const { format, options, entityIds } = action.payload;
      const exportId = `export-${Date.now()}`;
      
      state.currentExport = {
        id: exportId,
        format,
        status: 'pending',
        progress: 0,
      };
      state.isExporting = true;
      state.exportProgress = 0;
    },
    
    updateExportProgress: (state, action: PayloadAction<number>) => {
      if (state.currentExport) {
        state.currentExport.progress = action.payload;
        state.exportProgress = action.payload;
        
        if (action.payload >= 100) {
          state.currentExport.status = 'completed';
          state.isExporting = false;
        }
      }
    },
    
    setExportStatus: (state, action: PayloadAction<'pending' | 'processing' | 'completed' | 'failed'>) => {
      if (state.currentExport) {
        state.currentExport.status = action.payload;
        
        if (action.payload === 'completed') {
          state.isExporting = false;
          state.exportProgress = 100;
        } else if (action.payload === 'failed') {
          state.isExporting = false;
          state.exportProgress = 0;
        }
      }
    },
    
    setExportFileInfo: (state, action: PayloadAction<{
      fileName: string;
      downloadUrl: string;
      size?: number;
    }>) => {
      if (state.currentExport) {
        state.currentExport.fileName = action.payload.fileName;
        state.currentExport.downloadUrl = action.payload.downloadUrl;
        
        // Add to history
        const historyItem: ExportHistoryItem = {
          id: state.currentExport.id,
          format: state.currentExport.format,
          fileName: action.payload.fileName,
          createdAt: new Date(),
          downloadUrl: action.payload.downloadUrl,
          size: action.payload.size,
          isExpired: false,
          expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7 days
          entityCount: 0, // This would be set by the actual export
          confidenceThreshold: state.exportOptions.confidenceThreshold,
          filters: state.exportOptions,
        };
        
        state.exportHistory.unshift(historyItem);
        state.recentExports.unshift(action.payload.fileName);
        
        // Keep only last 100 exports
        state.exportHistory = state.exportHistory.slice(0, 100);
        state.recentExports = state.recentExports.slice(0, 20);
        
        // Reset current export
        state.currentExport = null;
        state.exportProgress = 0;
        state.isExporting = false;
      }
    },
    
    setExportError: (state, action: PayloadAction<string>) => {
      if (state.currentExport) {
        state.currentExport.status = 'failed';
        state.currentExport.error = action.payload;
        state.isExporting = false;
        state.exportProgress = 0;
      }
    },
    
    cancelExport: (state) => {
      state.currentExport = null;
      state.isExporting = false;
      state.exportProgress = 0;
    },
    
    updateExportOptions: (state, action: PayloadAction<Partial<ExportOptions>>) => {
      state.exportOptions = { ...state.exportOptions, ...action.payload };
    },
    
    resetExportOptions: (state) => {
      state.exportOptions = { ...state.defaultOptions };
    },
    
    addTemplate: (state, action: PayloadAction<Omit<ExportTemplate, 'id' | 'createdAt'>>) => {
      const template: ExportTemplate = {
        ...action.payload,
        id: `template-${Date.now()}`,
        createdAt: new Date(),
      };
      state.templates.push(template);
    },
    
    updateTemplate: (state, action: PayloadAction<{ id: string; updates: Partial<ExportTemplate> }>) => {
      const { id, updates } = action.payload;
      const templateIndex = state.templates.findIndex(t => t.id === id);
      if (templateIndex !== -1) {
        state.templates[templateIndex] = { ...state.templates[templateIndex], ...updates };
      }
    },
    
    deleteTemplate: (state, action: PayloadAction<string>) => {
      state.templates = state.templates.filter(t => t.id !== action.payload);
    },
    
    useTemplate: (state, action: PayloadAction<string>) => {
      const template = state.templates.find(t => t.id === action.payload);
      if (template) {
        state.exportOptions = { ...template.options };
        // Update last used
        const templateIndex = state.templates.findIndex(t => t.id === action.payload);
        if (templateIndex !== -1) {
          state.templates[templateIndex].lastUsed = new Date();
        }
      }
    },
    
    removeFromHistory: (state, action: PayloadAction<string>) => {
      state.exportHistory = state.exportHistory.filter(item => item.id !== action.payload);
    },
    
    clearHistory: (state) => {
      state.exportHistory = [];
      state.recentExports = [];
    },
    
    markAsExpired: (state, action: PayloadAction<string>) => {
      const item = state.exportHistory.find(item => item.id === action.payload);
      if (item) {
        item.isExpired = true;
      }
    },
    
    addCustomField: (state, action: PayloadAction<string>) => {
      if (!state.customFields.includes(action.payload)) {
        state.customFields.push(action.payload);
      }
    },
    
    removeCustomField: (state, action: PayloadAction<string>) => {
      state.customFields = state.customFields.filter(field => field !== action.payload);
    },
    
    setCustomFields: (state, action: PayloadAction<string[]>) => {
      state.customFields = action.payload;
    },
    
    // Export validation
    validateExportOptions: (state, action: PayloadAction<ExportOptions>) => {
      const options = action.payload;
      const errors: string[] = [];
      
      if (!Object.values(ExportFormat).includes(options.format)) {
        errors.push('Invalid export format');
      }
      
      if (options.confidenceThreshold < 0 || options.confidenceThreshold > 1) {
        errors.push('Confidence threshold must be between 0 and 1');
      }
      
      if (options.maxItems && options.maxItems < 1) {
        errors.push('Max items must be at least 1');
      }
      
      // This would typically be handled by a separate validation service
      return errors;
    },
    
    // Batch export operations
    startBatchExport: (state, action: PayloadAction<{
      exportRequests: Array<{
        format: ExportFormat;
        options: ExportOptions;
        entityIds: string[];
      }>;
    }>) => {
      // This would handle multiple exports at once
      state.isExporting = true;
      state.exportProgress = 0;
    },
    
    updateBatchProgress: (state, action: PayloadAction<{
      current: number;
      total: number;
    }>) => {
      const { current, total } = action.payload;
      state.exportProgress = (current / total) * 100;
    },
    
    completeBatchExport: (state, action: PayloadAction<{
      results: Array<{
        format: ExportFormat;
        fileName: string;
        downloadUrl: string;
        size?: number;
      }>;
    }>) => {
      const { results } = action.payload;
      
      results.forEach(result => {
        const historyItem: ExportHistoryItem = {
          id: `export-${Date.now()}-${Math.random()}`,
          format: result.format,
          fileName: result.fileName,
          createdAt: new Date(),
          downloadUrl: result.downloadUrl,
          size: result.size,
          isExpired: false,
          expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
          entityCount: 0,
          confidenceThreshold: state.exportOptions.confidenceThreshold,
          filters: state.exportOptions,
        };
        
        state.exportHistory.unshift(historyItem);
      });
      
      state.isExporting = false;
      state.exportProgress = 100;
    },
  },
});

export const {
  startExport,
  updateExportProgress,
  setExportStatus,
  setExportFileInfo,
  setExportError,
  cancelExport,
  updateExportOptions,
  resetExportOptions,
  addTemplate,
  updateTemplate,
  deleteTemplate,
  useTemplate,
  removeFromHistory,
  clearHistory,
  markAsExpired,
  addCustomField,
  removeCustomField,
  setCustomFields,
  validateExportOptions,
  startBatchExport,
  updateBatchProgress,
  completeBatchExport,
} = exportSlice.actions;

export default exportSlice.reducer;

// Selectors
export const selectIsExporting = (state: { export: ExportState }) => state.export.isExporting;
export const selectExportProgress = (state: { export: ExportState }) => state.export.exportProgress;
export const selectCurrentExport = (state: { export: ExportState }) => state.export.currentExport;
export const selectExportHistory = (state: { export: ExportState }) => state.export.exportHistory;
export const selectExportTemplates = (state: { export: ExportState }) => state.export.templates;
export const selectRecentExports = (state: { export: ExportState }) => state.export.recentExports;
export const selectAvailableFormats = (state: { export: ExportState }) => state.export.availableFormats;
export const selectExportOptions = (state: { export: ExportState }) => state.export.exportOptions;
export const selectCustomFields = (state: { export: ExportState }) => state.export.customFields;
export const selectDefaultOptions = (state: { export: ExportState }) => state.export.defaultOptions;