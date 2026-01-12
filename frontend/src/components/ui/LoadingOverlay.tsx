import React from 'react';
import { useSelector } from 'react-redux';
import { motion } from 'framer-motion';
import { selectLoading } from '@/store/slices/uiSlice';

export const LoadingOverlay: React.FC = () => {
  const loading = useSelector(selectLoading);

  const isLoading = loading.global || loading.search || loading.graph || loading.export;

  if (!isLoading) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.8, opacity: 0 }}
        className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-xl"
      >
        <div className="flex items-center space-x-4">
          <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
          <div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
              Loading...
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Please wait while we process your request
            </p>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};