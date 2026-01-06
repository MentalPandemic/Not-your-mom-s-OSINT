import React, { useState, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import {
  UserIcon,
  EnvelopeIcon,
  DevicePhoneMobileIcon,
  MapPinIcon,
  BuildingOfficeIcon,
  GlobeAltIcon,
  CalendarIcon,
  ClockIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  LinkIcon,
  ShareIcon,
  BookmarkIcon,
  DocumentTextIcon,
  ChartBarIcon,
  EyeIcon,
  CameraIcon,
  StarIcon,
  StarIcon as StarOutlineIcon,
} from '@heroicons/react/24/outline';
import { useAppDispatch } from '@/store';
import { setRightPanelOpen } from '@/store/slices/uiSlice';
import { EntityType, Identity, SocialProfile } from '@/types';
import { formatDistanceToNow, format } from 'date-fns';

interface IdentityProfileProps {
  entityId: string;
  className?: string;
}

export const IdentityProfile: React.FC<IdentityProfileProps> = ({ 
  entityId, 
  className = '' 
}) => {
  const dispatch = useAppDispatch();
  const [activeTab, setActiveTab] = useState('overview');
  const [isStarred, setIsStarred] = useState(false);

  // Mock identity data - in real implementation, this would come from API
  const identity = useMemo((): Identity => ({
    id: entityId,
    type: 'identity' as EntityType,
    createdAt: new Date('2023-01-15'),
    updatedAt: new Date('2024-01-10'),
    confidence: 0.87,
    sources: ['LinkedIn', 'Twitter', 'Public Records'],
    primaryName: 'John Smith',
    aliases: ['Johnny Smith', 'J. Smith', 'Johnathan Smith'],
    emails: ['john.smith@email.com', 'jsmith@company.com'],
    phones: ['+1-555-0123', '+1-555-0124'],
    addresses: [
      {
        id: 'addr-1',
        type: 'address' as any,
        createdAt: new Date('2023-01-15'),
        updatedAt: new Date('2024-01-10'),
        confidence: 0.92,
        sources: ['Public Records'],
        street: '123 Main Street',
        city: 'San Francisco',
        state: 'CA',
        country: 'USA',
        postalCode: '94102',
        isPOBox: false,
        isCurrent: true,
      }
    ],
    dateOfBirth: new Date('1985-06-15'),
    socialMedia: [
      {
        id: 'social-1',
        type: 'social' as any,
        createdAt: new Date('2023-01-15'),
        updatedAt: new Date('2024-01-10'),
        confidence: 0.94,
        sources: ['Twitter API'],
        platform: 'twitter' as any,
        username: 'johnsmith_dev',
        displayName: 'John Smith',
        profileUrl: 'https://twitter.com/johnsmith_dev',
        avatarUrl: 'https://example.com/avatar.jpg',
        bio: 'Software Developer | Tech Enthusiast | Coffee Lover',
        followers: 1247,
        following: 543,
        posts: 2847,
        verified: false,
        joinedDate: new Date('2019-03-20'),
        lastActive: new Date('2024-01-09'),
        location: 'San Francisco, CA',
        website: 'https://johnsmith.dev',
      }
    ],
    employment: [
      {
        company: 'TechCorp Inc.',
        position: 'Senior Software Engineer',
        startDate: new Date('2021-03-01'),
        endDate: new Date('2024-01-01'),
        isCurrent: false,
        description: 'Led development of microservices architecture',
        website: 'https://techcorp.com',
      },
      {
        company: 'StartupXYZ',
        position: 'Lead Developer',
        startDate: new Date('2024-01-15'),
        endDate: undefined,
        isCurrent: true,
        description: 'Building next-generation AI tools',
      }
    ],
    education: [
      {
        institution: 'University of California, Berkeley',
        degree: 'Bachelor of Science',
        field: 'Computer Science',
        startDate: new Date('2015-09-01'),
        endDate: new Date('2019-05-15'),
        isCurrent: false,
        description: 'Graduated Magna Cum Laude',
      }
    ],
    profiles: [
      {
        platform: 'LinkedIn',
        profileUrl: 'https://linkedin.com/in/johnsmith',
        displayName: 'John Smith',
        bio: 'Senior Software Engineer with 5+ years experience',
        avatarUrl: 'https://example.com/linkedin-avatar.jpg',
      }
    ]
  }), [entityId]);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: InformationCircleIcon },
    { id: 'social', label: 'Social Media', icon: GlobeAltIcon },
    { id: 'professional', label: 'Professional', icon: BuildingOfficeIcon },
    { id: 'education', label: 'Education', icon: DocumentTextIcon },
    { id: 'locations', label: 'Locations', icon: MapPinIcon },
    { id: 'timeline', label: 'Timeline', icon: CalendarIcon },
    { id: 'relationships', label: 'Relationships', icon: LinkIcon },
    { id: 'analysis', label: 'Analysis', icon: ChartBarIcon },
  ];

  const renderConfidenceIndicator = (confidence: number) => {
    const percentage = Math.round(confidence * 100);
    let colorClass = '';
    let label = '';
    
    if (confidence >= 0.9) {
      colorClass = 'text-green-600 bg-green-100';
      label = 'Very High';
    } else if (confidence >= 0.8) {
      colorClass = 'text-blue-600 bg-blue-100';
      label = 'High';
    } else if (confidence >= 0.6) {
      colorClass = 'text-yellow-600 bg-yellow-100';
      label = 'Medium';
    } else {
      colorClass = 'text-red-600 bg-red-100';
      label = 'Low';
    }

    return (
      <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${colorClass}`}>
        <CheckCircleIcon className="h-4 w-4 mr-1" />
        {percentage}% • {label}
      </div>
    );
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Basic Information */}
      <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
          Basic Information
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Primary Name
            </label>
            <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {identity.primaryName}
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Date of Birth
            </label>
            <p className="text-gray-900 dark:text-gray-100">
              {format(identity.dateOfBirth!, 'MMMM dd, yyyy')}
              <span className="text-sm text-gray-500 ml-2">
                ({Math.floor((Date.now() - identity.dateOfBirth!.getTime()) / (365.25 * 24 * 60 * 60 * 1000)} years old)
              </span>
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Confidence Score
            </label>
            {renderConfidenceIndicator(identity.confidence)}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Data Sources
            </label>
            <div className="flex flex-wrap gap-1">
              {identity.sources.map((source, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                >
                  {source}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Contact Information */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
          Contact Information
        </h3>
        <div className="space-y-4">
          {identity.emails && identity.emails.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                Email Addresses
              </label>
              <div className="space-y-2">
                {identity.emails.map((email, index) => (
                  <div key={index} className="flex items-center space-x-3 p-2 bg-gray-50 dark:bg-gray-900 rounded">
                    <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                    <span className="text-gray-900 dark:text-gray-100">{email}</span>
                    <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded-full">verified</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {identity.phones && identity.phones.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                Phone Numbers
              </label>
              <div className="space-y-2">
                {identity.phones.map((phone, index) => (
                  <div key={index} className="flex items-center space-x-3 p-2 bg-gray-50 dark:bg-gray-900 rounded">
                    <DevicePhoneMobileIcon className="h-5 w-5 text-gray-400" />
                    <span className="text-gray-900 dark:text-gray-100">{phone}</span>
                    <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded-full">mobile</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Aliases */}
      {identity.aliases && identity.aliases.length > 0 && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
            Known Aliases
          </h3>
          <div className="flex flex-wrap gap-2">
            {identity.aliases.map((alias, index) => (
              <span
                key={index}
                className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
              >
                {alias}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Data Quality Indicators */}
      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
        <div className="flex items-start space-x-3">
          <ShieldCheckIcon className="h-6 w-6 text-yellow-600 dark:text-yellow-400 mt-1" />
          <div>
            <h3 className="text-lg font-medium text-yellow-800 dark:text-yellow-200 mb-2">
              Data Quality Assessment
            </h3>
            <div className="space-y-2 text-sm text-yellow-700 dark:text-yellow-300">
              <p>• Data last verified: {formatDistanceToNow(identity.updatedAt, { addSuffix: true })}</p>
              <p>• Multiple data sources confirm identity</p>
              <p>• Cross-referenced with public records</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderSocialMedia = () => (
    <div className="space-y-6">
      {identity.socialMedia?.map((social) => (
        <div key={social.id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <div className="flex items-start space-x-4">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">
                {social.platform.charAt(0).toUpperCase()}
              </span>
            </div>
            
            <div className="flex-1">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                  {social.displayName}
                </h3>
                {renderConfidenceIndicator(social.confidence)}
              </div>
              
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                @{social.username}
              </p>
              
              {social.bio && (
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  {social.bio}
                </p>
              )}
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Followers</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {social.followers?.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Following</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {social.following?.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Posts</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {social.posts?.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Verified</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {social.verified ? 'Yes' : 'No'}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                {social.location && (
                  <span className="flex items-center space-x-1">
                    <MapPinIcon className="h-4 w-4" />
                    <span>{social.location}</span>
                  </span>
                )}
                {social.website && (
                  <a 
                    href={social.website} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex items-center space-x-1 hover:text-blue-600"
                  >
                    <GlobeAltIcon className="h-4 w-4" />
                    <span>Website</span>
                  </a>
                )}
              </div>
              
              <div className="mt-4 flex items-center space-x-2">
                <a
                  href={social.profileUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  <EyeIcon className="h-4 w-4 mr-1" />
                  View Profile
                </a>
                <button className="inline-flex items-center px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700">
                  <ShareIcon className="h-4 w-4 mr-1" />
                  Share
                </button>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  const renderProfessional = () => (
    <div className="space-y-6">
      {identity.employment?.map((job, index) => (
        <div key={index} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-blue-600 rounded-lg flex items-center justify-center">
                <BuildingOfficeIcon className="h-6 w-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                  {job.position}
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  {job.company}
                </p>
              </div>
            </div>
            {job.isCurrent && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300">
                Current
              </span>
            )}
          </div>
          
          <div className="space-y-2 text-sm text-gray-500 dark:text-gray-400 mb-4">
            <span>
              {format(job.startDate, 'MMM yyyy')} - {job.endDate ? format(job.endDate, 'MMM yyyy') : 'Present'}
            </span>
            <span className="block">
              {Math.floor((Date.now() - job.startDate.getTime()) / (365.25 * 24 * 60 * 60 * 1000)} years duration
            </span>
          </div>
          
          {job.description && (
            <p className="text-gray-700 dark:text-gray-300 mb-4">
              {job.description}
            </p>
          )}
          
          {job.website && (
            <a
              href={job.website}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center text-blue-600 hover:text-blue-800"
            >
              <GlobeAltIcon className="h-4 w-4 mr-1" />
              Company Website
            </a>
          )}
        </div>
      ))}
    </div>
  );

  const renderEducation = () => (
    <div className="space-y-6">
      {identity.education?.map((edu, index) => (
        <div key={index} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <div className="flex items-start space-x-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg flex items-center justify-center">
              <DocumentTextIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                {edu.degree}
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                {edu.field}
              </p>
              <p className="text-gray-500 dark:text-gray-500">
                {edu.institution}
              </p>
            </div>
          </div>
          
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            {format(edu.startDate, 'MMM yyyy')} - {format(edu.endDate, 'MMM yyyy')}
          </div>
          
          {edu.description && (
            <p className="text-gray-700 dark:text-gray-300">
              {edu.description}
            </p>
          )}
        </div>
      ))}
    </div>
  );

  const renderLocations = () => (
    <div className="space-y-6">
      {identity.addresses?.map((address, index) => (
        <div key={index} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <MapPinIcon className="h-6 w-6 text-gray-400" />
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                  {address.street}
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  {address.city}, {address.state} {address.postalCode}
                </p>
                <p className="text-gray-500 dark:text-gray-500">
                  {address.country}
                </p>
              </div>
            </div>
            <div className="flex flex-col space-y-2">
              {address.isCurrent && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300">
                  Current
                </span>
              )}
              {renderConfidenceIndicator(address.confidence)}
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverview();
      case 'social':
        return renderSocialMedia();
      case 'professional':
        return renderProfessional();
      case 'education':
        return renderEducation();
      case 'locations':
        return renderLocations();
      case 'timeline':
        return <div className="text-center py-8 text-gray-500">Timeline content would be implemented here</div>;
      case 'relationships':
        return <div className="text-center py-8 text-gray-500">Relationships content would be implemented here</div>;
      case 'analysis':
        return <div className="text-center py-8 text-gray-500">Analysis content would be implemented here</div>;
      default:
        return renderOverview();
    }
  };

  return (
    <div className={`h-full flex flex-col bg-gray-50 dark:bg-gray-900 ${className}`}>
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-4">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <UserIcon className="h-10 w-10 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-3 mb-2">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {identity.primaryName}
                </h1>
                <button
                  onClick={() => setIsStarred(!isStarred)}
                  className="p-1 text-gray-400 hover:text-yellow-500"
                >
                  {isStarred ? (
                    <StarIcon className="h-6 w-6 text-yellow-500 fill-current" />
                  ) : (
                    <StarOutlineIcon className="h-6 w-6" />
                  )}
                </button>
              </div>
              <p className="text-gray-600 dark:text-gray-400 mb-2">
                ID: {identity.id}
              </p>
              <div className="flex items-center space-x-4">
                {renderConfidenceIndicator(identity.confidence)}
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  Last updated {formatDistanceToNow(identity.updatedAt, { addSuffix: true })}
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsStarred(!isStarred)}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              title="Bookmark"
            >
              <BookmarkIcon className="h-5 w-5" />
            </button>
            <button className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" title="Share">
              <ShareIcon className="h-5 w-5" />
            </button>
            <button className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" title="Export">
              <DocumentTextIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <nav className="px-6 flex space-x-8 overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
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

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
          >
            {renderContent()}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};

export default IdentityProfile;