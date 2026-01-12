import React from 'react';
import { useSelector } from 'react-redux';
import { ChevronRightIcon, HomeIcon } from '@heroicons/react/24/outline';
import { selectBreadcrumbs } from '@/store/slices/uiSlice';
import { useAppSelector } from '@/store';

export const Breadcrumbs: React.FC = () => {
  const breadcrumbs = useSelector(selectBreadcrumbs);

  if (breadcrumbs.length <= 1) {
    return (
      <div className="flex items-center space-x-2">
        <HomeIcon className="h-4 w-4 text-gray-400" />
        <span className="text-sm text-gray-600 dark:text-gray-400">Dashboard</span>
      </div>
    );
  }

  return (
    <nav className="flex" aria-label="Breadcrumb">
      <ol className="flex items-center space-x-2">
        {breadcrumbs.map((breadcrumb, index) => (
          <li key={breadcrumb.path} className="flex items-center">
            {index > 0 && (
              <ChevronRightIcon className="h-4 w-4 text-gray-400 mx-2" />
            )}
            {index === breadcrumbs.length - 1 ? (
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {breadcrumb.label}
              </span>
            ) : (
              <a
                href={breadcrumb.path}
                className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
              >
                {breadcrumb.label}
              </a>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
};