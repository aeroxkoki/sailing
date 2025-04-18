import React from 'react';
import { useRouter } from 'next/router';
import Card from '../common/Card';
import Badge from '../common/Badge';

export interface Session {
  id: string;
  name: string;
  description?: string;
  date: string | number | Date;
  duration?: number; // in seconds
  distance?: number; // in meters
  location?: string;
  avgWindSpeed?: number; // in knots
  avgBoatSpeed?: number; // in knots
  projectId?: string;
  tags?: string[];
  dataType?: 'gps' | 'wind' | 'combined';
  status?: 'raw' | 'processed' | 'analyzed';
}

interface SessionCardProps {
  session: Session;
  onClick?: (session: Session) => void;
  showProjectBadge?: boolean;
  className?: string;
}

const SessionCard: React.FC<SessionCardProps> = ({
  session,
  onClick,
  showProjectBadge = false,
  className = '',
}) => {
  const router = useRouter();
  const {
    id,
    name,
    description,
    date,
    duration,
    distance,
    location,
    avgWindSpeed,
    avgBoatSpeed,
    projectId,
    tags,
    dataType,
    status,
  } = session;

  // Format date
  const formattedDate = new Date(date).toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

  // Format time
  const formattedTime = new Date(date).toLocaleTimeString('ja-JP', {
    hour: '2-digit',
    minute: '2-digit',
  });

  // Format duration
  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours > 0 ? `${hours}時間 ` : ''}${minutes}分`;
  };

  // Format distance
  const formatDistance = (meters: number) => {
    if (meters >= 1000) {
      return `${(meters / 1000).toFixed(2)} km`;
    }
    return `${meters.toFixed(0)} m`;
  };

  // Handle click
  const handleClick = () => {
    if (onClick) {
      onClick(session);
    } else {
      router.push(`/sessions/${id}`);
    }
  };

  // Get data type badge variant
  const getDataTypeBadge = () => {
    switch (dataType) {
      case 'gps':
        return { variant: 'primary', label: 'GPS' };
      case 'wind':
        return { variant: 'warning', label: '風向風速' };
      case 'combined':
        return { variant: 'success', label: '複合データ' };
      default:
        return { variant: 'default', label: 'データ' };
    }
  };

  // Get status badge variant
  const getStatusBadge = () => {
    switch (status) {
      case 'raw':
        return { variant: 'default', label: '生データ' };
      case 'processed':
        return { variant: 'primary', label: '処理済み' };
      case 'analyzed':
        return { variant: 'success', label: '分析済み' };
      default:
        return { variant: 'default', label: '' };
    }
  };

  const dataTypeBadge = getDataTypeBadge();
  const statusBadge = getStatusBadge();

  return (
    <Card
      hoverable
      className={`h-full ${className}`}
      onClick={handleClick}
    >
      <div className="flex flex-col h-full">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-lg font-medium text-gray-900 mr-2">{name}</h3>
          <div className="flex flex-col gap-1">
            <Badge variant={dataTypeBadge.variant as any} size="sm">
              {dataTypeBadge.label}
            </Badge>
            {status && (
              <Badge variant={statusBadge.variant as any} size="sm">
                {statusBadge.label}
              </Badge>
            )}
          </div>
        </div>
        
        <div className="mb-3 text-sm text-gray-600">
          <div className="flex items-center">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="h-4 w-4 mr-1 text-gray-500" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" 
              />
            </svg>
            {formattedDate} {formattedTime}
          </div>
          
          {location && (
            <div className="flex items-center mt-1">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                className="h-4 w-4 mr-1 text-gray-500" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" 
                />
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" 
                />
              </svg>
              {location}
            </div>
          )}
        </div>
        
        {description && (
          <p className="text-gray-600 text-sm mb-3 line-clamp-2">
            {description}
          </p>
        )}

        <div className="mt-auto">
          <div className="grid grid-cols-2 gap-2 mb-3">
            {duration !== undefined && (
              <div className="bg-gray-50 p-2 rounded text-sm">
                <div className="text-gray-500 text-xs">セッション時間</div>
                <div className="font-medium">{formatDuration(duration)}</div>
              </div>
            )}
            
            {distance !== undefined && (
              <div className="bg-gray-50 p-2 rounded text-sm">
                <div className="text-gray-500 text-xs">距離</div>
                <div className="font-medium">{formatDistance(distance)}</div>
              </div>
            )}
            
            {avgWindSpeed !== undefined && (
              <div className="bg-gray-50 p-2 rounded text-sm">
                <div className="text-gray-500 text-xs">平均風速</div>
                <div className="font-medium">{avgWindSpeed.toFixed(1)} kts</div>
              </div>
            )}
            
            {avgBoatSpeed !== undefined && (
              <div className="bg-gray-50 p-2 rounded text-sm">
                <div className="text-gray-500 text-xs">平均艇速</div>
                <div className="font-medium">{avgBoatSpeed.toFixed(1)} kts</div>
              </div>
            )}
          </div>
          
          <div className="flex flex-wrap gap-1 mb-2">
            {showProjectBadge && projectId && (
              <Badge variant="primary" size="sm" className="mr-1">
                プロジェクト
              </Badge>
            )}
            
            {tags && tags.length > 0 && tags.map((tag) => (
              <Badge key={tag} variant="default" size="sm" className="bg-gray-100 text-gray-700">
                {tag}
              </Badge>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
};

export default SessionCard;