/**
 * 偏离表编辑组件
 */
import React, { useState, useEffect } from 'react';
import { templateApi } from '../services/api';
import { 
  TableCellsIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

interface DeviationEditModalProps {
  projectId: number;
  technicalScores: any;
  isOpen: boolean;
  onClose: () => void;
  onSave: (mappings: any[]) => void;
}

interface DeviationItem {
  id: number;
  tender_requirement: string;
  bid_response: string;
  deviation_status: 'none' | 'positive' | 'negative';
  chapter_path: string;
  chapter_title: string;
  is_confirmed: boolean;
}

const DeviationEditModal: React.FC<DeviationEditModalProps> = ({
  projectId,
  technicalScores,
  isOpen,
  onClose,
  onSave,
}) => {
  const [loading, setLoading] = useState(false);
  const [deviations, setDeviations] = useState<DeviationItem[]>([]);
  const [editedItems, setEditedItems] = useState<Map<number, Partial<DeviationItem>>>(new Map());

  useEffect(() => {
    if (isOpen && projectId) {
      loadDeviationTable();
    }
  }, [isOpen, projectId]);

  const loadDeviationTable = async () => {
    try {
      setLoading(true);
      const response = await templateApi.getDeviationTable(projectId);
      setDeviations(response.data.deviations || []);
    } catch (err) {
      console.error('加载偏离表失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateDeviation = async () => {
    try {
      setLoading(true);
      const response = await templateApi.generateDeviationTable(projectId, technicalScores);
      setDeviations(response.data.deviations || []);
    } catch (err) {
      console.error('生成偏离表失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = (id: number, status: 'none' | 'positive' | 'negative') => {
    setEditedItems(prev => {
      const newMap = new Map(prev);
      const existing = newMap.get(id) || {};
      newMap.set(id, { ...existing, deviation_status: status, is_confirmed: status !== 'negative' });
      return newMap;
    });
  };

  const handleChapterChange = (id: number, chapterPath: string, chapterTitle: string) => {
    setEditedItems(prev => {
      const newMap = new Map(prev);
      const existing = newMap.get(id) || {};
      newMap.set(id, { ...existing, chapter_path: chapterPath, chapter_title: chapterTitle });
      return newMap;
    });
  };

  const handleResponseChange = (id: number, response: string) => {
    setEditedItems(prev => {
      const newMap = new Map(prev);
      const existing = newMap.get(id) || {};
      newMap.set(id, { ...existing, bid_response: response });
      return newMap;
    });
  };

  const handleSave = () => {
    const updatedDeviations = deviations.map(item => {
      const edits = editedItems.get(item.id);
      return edits ? { ...item, ...edits } : item;
    });
    onSave(updatedDeviations);
    onClose();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'none':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'positive':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'negative':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'none':
        return <CheckCircleIcon className="w-4 h-4 text-green-500" />;
      case 'positive':
        return <CheckCircleIcon className="w-4 h-4 text-blue-500" />;
      case 'negative':
        return <ExclamationTriangleIcon className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />
        
        <div className="relative inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-5xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="sm:flex sm:items-start">
              <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg leading-6 font-medium text-gray-900 flex items-center">
                    <TableCellsIcon className="w-5 h-5 mr-2" />
                    偏离表编辑
                  </h3>
                  <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>

                {deviations.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-gray-500 mb-4">尚未生成偏离表</p>
                    <button
                      onClick={handleGenerateDeviation}
                      disabled={loading}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400"
                    >
                      {loading ? '生成中...' : '生成偏离表'}
                    </button>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">序号</th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">招标要求</th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">投标响应</th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">偏离类型</th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">关联章节</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {deviations.map((item) => {
                          const edits = editedItems.get(item.id) || {};
                          const currentStatus = edits.deviation_status || item.deviation_status;
                          
                          return (
                            <tr key={item.id} className="hover:bg-gray-50">
                              <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                                {item.id}
                              </td>
                              <td className="px-3 py-2 text-sm text-gray-900 max-w-xs">
                                <div className="truncate" title={item.tender_requirement}>
                                  {item.tender_requirement}
                                </div>
                              </td>
                              <td className="px-3 py-2">
                                <textarea
                                  value={edits.bid_response || item.bid_response}
                                  onChange={(e) => handleResponseChange(item.id, e.target.value)}
                                  className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                  rows={2}
                                />
                              </td>
                              <td className="px-3 py-2 whitespace-nowrap">
                                <div className="flex items-center gap-1">
                                  <select
                                    value={currentStatus}
                                    onChange={(e) => handleStatusChange(item.id, e.target.value as any)}
                                    className={`text-xs font-medium rounded-full border-0 px-2 py-1 cursor-pointer focus:ring-2 ${getStatusColor(currentStatus)}`}
                                  >
                                    <option value="none">无偏离</option>
                                    <option value="positive">正偏离</option>
                                    <option value="negative">负偏离</option>
                                  </select>
                                  {getStatusIcon(currentStatus)}
                                </div>
                              </td>
                              <td className="px-3 py-2 text-sm">
                                <input
                                  type="text"
                                  value={edits.chapter_path !== undefined ? edits.chapter_path : item.chapter_path}
                                  onChange={(e) => handleChapterChange(item.id, e.target.value, item.chapter_title)}
                                  className="w-24 text-xs border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                  placeholder="章节号"
                                />
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
          
          <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              onClick={handleSave}
              disabled={loading}
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none sm:ml-3 sm:w-auto sm:text-sm disabled:bg-gray-400"
            >
              保存偏离表
            </button>
            <button
              onClick={onClose}
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
            >
              取消
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeviationEditModal;