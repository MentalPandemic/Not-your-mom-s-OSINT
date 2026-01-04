import React, { useState } from 'react';
import { FiX, FiMail, FiPhone, FiMapPin, FiBriefcase, FiGlobe, FiGithub, FiTwitter, FiLinkedin } from 'react-icons/fi';
import { useAppSelector } from '../hooks/useAppSelector';
import { useAppDispatch } from '../hooks/useAppDispatch';
import { setSelectedNode } from '../store/graphSlice';
import { toggleDetailsPanel } from '../store/uiSlice';
import { formatConfidence, formatDate } from '../utils/formatters';
import clsx from 'clsx';

const IdentityProfile: React.FC = () => {
  const dispatch = useAppDispatch();
  const { selectedNode } = useAppSelector(state => state.graph);
  const [activeSection, setActiveSection] = useState('basic');

  if (!selectedNode) return null;

  const identity = selectedNode.data;

  const sections = [
    { id: 'basic', label: 'Basic Info' },
    { id: 'social', label: 'Social Media' },
    { id: 'employment', label: 'Employment' },
    { id: 'education', label: 'Education' },
    { id: 'relationships', label: 'Relationships' },
    { id: 'activity', label: 'Activity' },
  ];

  const getPlatformIcon = (platform: string) => {
    switch (platform.toLowerCase()) {
      case 'github':
        return <FiGithub />;
      case 'twitter':
        return <FiTwitter />;
      case 'linkedin':
        return <FiLinkedin />;
      default:
        return <FiGlobe />;
    }
  };

  return (
    <div className="h-full overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-white dark:bg-dark-800 border-b border-gray-200 dark:border-dark-700 p-4 z-10">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            {identity.avatar ? (
              <img
                src={identity.avatar}
                alt={identity.name || 'Profile'}
                className="w-12 h-12 rounded-full"
              />
            ) : (
              <div className="w-12 h-12 rounded-full bg-primary-600 flex items-center justify-center text-white font-semibold text-lg">
                {(identity.name || identity.username || 'U')[0].toUpperCase()}
              </div>
            )}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {identity.name || identity.username || 'Unknown'}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Confidence: {formatConfidence(identity.confidenceScore || 0.5)}
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              dispatch(setSelectedNode(null));
              dispatch(toggleDetailsPanel());
            }}
            className="p-1 hover:bg-gray-100 dark:hover:bg-dark-700 rounded"
          >
            <FiX size={20} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 overflow-x-auto">
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={clsx(
                'px-3 py-1.5 text-sm font-medium rounded-lg whitespace-nowrap transition-colors',
                activeSection === section.id
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-700'
              )}
            >
              {section.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {activeSection === 'basic' && (
          <div className="space-y-4">
            {identity.email && (
              <InfoItem
                icon={<FiMail />}
                label="Email"
                value={identity.email}
              />
            )}
            {identity.phone && (
              <InfoItem
                icon={<FiPhone />}
                label="Phone"
                value={identity.phone}
              />
            )}
            {identity.location && (
              <InfoItem
                icon={<FiMapPin />}
                label="Location"
                value={identity.location}
              />
            )}
            {identity.company && (
              <InfoItem
                icon={<FiBriefcase />}
                label="Company"
                value={identity.company}
              />
            )}
            {identity.lastUpdated && (
              <InfoItem
                icon={<FiGlobe />}
                label="Last Updated"
                value={formatDate(identity.lastUpdated)}
              />
            )}
          </div>
        )}

        {activeSection === 'social' && (
          <div className="space-y-3">
            {identity.profiles && identity.profiles.length > 0 ? (
              identity.profiles.map((profile: any, index: number) => (
                <div
                  key={index}
                  className="p-3 bg-gray-50 dark:bg-dark-700 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-600 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      {getPlatformIcon(profile.platform)}
                      <span className="font-medium text-gray-900 dark:text-white">
                        {profile.platform}
                      </span>
                    </div>
                    {profile.verified && (
                      <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded">
                        Verified
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-700 dark:text-gray-300 mb-1">
                    @{profile.username}
                  </p>
                  {profile.url && (
                    <a
                      href={profile.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-primary-600 dark:text-primary-400 hover:underline"
                    >
                      View Profile
                    </a>
                  )}
                  {profile.bio && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                      {profile.bio}
                    </p>
                  )}
                </div>
              ))
            ) : (
              <p className="text-gray-500 dark:text-gray-400 text-sm">
                No social media profiles found
              </p>
            )}
          </div>
        )}

        {activeSection === 'employment' && (
          <div className="space-y-3">
            {identity.employment && identity.employment.length > 0 ? (
              identity.employment.map((job: any, index: number) => (
                <div
                  key={index}
                  className="p-3 bg-gray-50 dark:bg-dark-700 rounded-lg"
                >
                  <h4 className="font-medium text-gray-900 dark:text-white">
                    {job.title}
                  </h4>
                  <p className="text-sm text-gray-700 dark:text-gray-300">
                    {job.company}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    {job.startDate || 'Unknown'} - {job.current ? 'Present' : (job.endDate || 'Unknown')}
                  </p>
                  {job.location && (
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      {job.location}
                    </p>
                  )}
                </div>
              ))
            ) : (
              <p className="text-gray-500 dark:text-gray-400 text-sm">
                No employment history found
              </p>
            )}
          </div>
        )}

        {activeSection === 'education' && (
          <div className="space-y-3">
            {identity.education && identity.education.length > 0 ? (
              identity.education.map((edu: any, index: number) => (
                <div
                  key={index}
                  className="p-3 bg-gray-50 dark:bg-dark-700 rounded-lg"
                >
                  <h4 className="font-medium text-gray-900 dark:text-white">
                    {edu.institution}
                  </h4>
                  {edu.degree && (
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      {edu.degree} {edu.field ? `in ${edu.field}` : ''}
                    </p>
                  )}
                  {(edu.startDate || edu.endDate) && (
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      {edu.startDate || 'Unknown'} - {edu.endDate || 'Unknown'}
                    </p>
                  )}
                </div>
              ))
            ) : (
              <p className="text-gray-500 dark:text-gray-400 text-sm">
                No education history found
              </p>
            )}
          </div>
        )}

        {activeSection === 'relationships' && (
          <div className="space-y-3">
            {identity.relationships && identity.relationships.length > 0 ? (
              identity.relationships.map((rel: any, index: number) => (
                <div
                  key={index}
                  className="p-3 bg-gray-50 dark:bg-dark-700 rounded-lg"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">
                        {rel.relatedTo}
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                        {rel.type}
                      </p>
                    </div>
                    <span className="text-xs text-gray-500">
                      {formatConfidence(rel.confidence)}
                    </span>
                  </div>
                  {rel.description && (
                    <p className="text-sm text-gray-700 dark:text-gray-300 mt-2">
                      {rel.description}
                    </p>
                  )}
                </div>
              ))
            ) : (
              <p className="text-gray-500 dark:text-gray-400 text-sm">
                No relationships found
              </p>
            )}
          </div>
        )}

        {activeSection === 'activity' && (
          <div className="space-y-3">
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              Activity timeline will be displayed here
            </p>
          </div>
        )}

        {/* Data Sources */}
        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-dark-700">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
            Data Sources
          </h4>
          <div className="space-y-2">
            {identity.sources && identity.sources.length > 0 ? (
              identity.sources.map((source: any, index: number) => (
                <div
                  key={index}
                  className="text-sm text-gray-600 dark:text-gray-400 flex items-center justify-between"
                >
                  <span>{source.name}</span>
                  <span className="text-xs">{formatConfidence(source.confidence)}</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                No sources available
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const InfoItem: React.FC<{ icon: React.ReactNode; label: string; value: string }> = ({
  icon,
  label,
  value,
}) => (
  <div className="flex items-start space-x-3">
    <div className="text-gray-500 dark:text-gray-400 mt-0.5">{icon}</div>
    <div className="flex-1">
      <p className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</p>
      <p className="text-sm text-gray-900 dark:text-white">{value}</p>
    </div>
  </div>
);

export default IdentityProfile;
