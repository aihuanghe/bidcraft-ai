import React, { useState, useCallback, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import { 
  ChevronRightIcon, 
  ChevronDownIcon, 
  PlusIcon, 
  TrashIcon,
  DocumentArrowDownIcon,
  SparklesIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';
import { outlineApi, templateApi, documentApi } from '../services/api';
import { OutlineItem, OutlineData, GenerationProgress } from '../types';

interface DashboardProps {
  projectId?: number;
}

const Dashboard: React.FC<DashboardProps> = ({ projectId }) => {
  const [outline, setOutline] = useState<OutlineItem[]>([]);
  const [selectedChapter, setSelectedChapter] = useState<string | null>(null);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [editorContent, setEditorContent] = useState<string>('');
  const [progress, setProgress] = useState<GenerationProgress>({
    total_chapters: 0,
    completed_chapters: 0,
    status: 'idle'
  });
  const [generating, setGenerating] = useState(false);
  const [templateName, setTemplateName] = useState<string>('默认模板');

  const toggleExpand = (id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) return;

    const items = Array.from(outline);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);
    setOutline(items);
  };

  const addChapter = (parentId?: string) => {
    const newChapter: OutlineItem = {
      id: `new-${Date.now()}`,
      title: '新章节',
      description: '',
      children: []
    };

    if (parentId) {
      const addToParent = (items: OutlineItem[]): OutlineItem[] => {
        return items.map(item => {
          if (item.id === parentId) {
            return { ...item, children: [...(item.children || []), newChapter] };
          }
          if (item.children) {
            return { ...item, children: addToParent(item.children) };
          }
          return item;
        });
      };
      setOutline(addToParent(outline));
    } else {
      setOutline([...outline, newChapter]);
    }
  };

  const deleteChapter = (id: string) => {
    const deleteFromList = (items: OutlineItem[]): OutlineItem[] => {
      return items.filter(item => item.id !== id).map(item => {
        if (item.children) {
          return { ...item, children: deleteFromList(item.children) };
        }
        return item;
      });
    };
    setOutline(deleteFromList(outline));
  };

  const updateChapter = (id: string, updates: Partial<OutlineItem>) => {
    const updateInList = (items: OutlineItem[]): OutlineItem[] => {
      return items.map(item => {
        if (item.id === id) {
          return { ...item, ...updates };
        }
        if (item.children) {
          return { ...item, children: updateInList(item.children) };
        }
        return item;
      });
    };
    setOutline(updateInList(outline));
  };

  const generateContent = async (chapterId?: string) => {
    setGenerating(true);
    setProgress({
      total_chapters: chapterId ? 1 : outline.length,
      completed_chapters: 0,
      status: 'generating'
    });

    try {
      if (chapterId) {
        const response = await templateApi.generateContentStream(
          projectId || 1,
          { id: chapterId },
          { overview: '', requirements: '' }
        );
        
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        
        if (reader) {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));
                  if (data.chunk) {
                    setEditorContent(prev => prev + data.chunk);
                  } else if (data.completed) {
                    setProgress(prev => ({
                      ...prev,
                      completed_chapters: prev.completed_chapters + 1,
                      status: 'completed'
                    }));
                  }
                } catch {}
              }
            }
          }
        }
      } else {
        for (let i = 0; i < outline.length; i++) {
          setProgress(prev => ({ ...prev, current_chapter: outline[i].title }));
          
          const response = await templateApi.generateContentStream(
            projectId || 1,
            outline[i],
            { overview: '', requirements: '' }
          );
          
          const reader = response.body?.getReader();
          const decoder = new TextDecoder();
          let content = '';
          
          if (reader) {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              
              const chunk = decoder.decode(value);
              const lines = chunk.split('\n');
              
              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  try {
                    const data = JSON.parse(line.slice(6));
                    if (data.chunk) {
                      content += data.chunk;
                    }
                  } catch {}
                }
              }
            }
          }
          
          updateChapter(outline[i].id, { content });
          setProgress(prev => ({
            ...prev,
            completed_chapters: prev.completed_chapters + 1
          }));
        }
        
        setProgress(prev => ({ ...prev, status: 'completed' }));
      }
    } catch (error) {
      console.error('生成内容失败:', error);
      setProgress(prev => ({ ...prev, status: 'failed', error: String(error) }));
    } finally {
      setGenerating(false);
    }
  };

  const exportDocument = async (format: 'docx' | 'pdf' = 'docx') => {
    try {
      const response = await templateApi.exportDocument(projectId || 1, format);
      const blob = new Blob([response.data], { 
        type: format === 'docx' ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' : 'application/pdf' 
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `标书_${new Date().toISOString().slice(0, 10)}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('导出失败:', error);
    }
  };

  const renderOutlineItem = (item: OutlineItem, level: number, index: number) => {
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedIds.has(item.id);
    const isSelected = selectedChapter === item.id;

    return (
      <Draggable key={item.id} draggableId={item.id} index={index}>
        {(provided) => (
          <div
            ref={provided.innerRef}
            {...provided.draggableProps}
            className={`mb-1 ${level > 0 ? 'ml-4' : ''}`}
          >
            <div
              className={`flex items-center gap-1 p-2 rounded cursor-pointer ${
                isSelected ? 'bg-blue-100 border-l-2 border-blue-500' : 'hover:bg-gray-100'
              }`}
              onClick={() => {
                setSelectedChapter(item.id);
                setEditorContent(item.content || '');
              }}
            >
              <div {...provided.dragHandleProps} className="cursor-grab">
                <ChevronRightIcon className="w-4 h-4 text-gray-400" />
              </div>
              
              {hasChildren ? (
                <button onClick={(e) => { e.stopPropagation(); toggleExpand(item.id); }}>
                  {isExpanded ? (
                    <ChevronDownIcon className="w-4 h-4 text-gray-500" />
                  ) : (
                    <ChevronRightIcon className="w-4 h-4 text-gray-500" />
                  )}
                </button>
              ) : (
                <span className="w-4" />
              )}
              
              <input
                value={item.title}
                onChange={(e) => updateChapter(item.id, { title: e.target.value })}
                onClick={(e) => e.stopPropagation()}
                className="flex-1 bg-transparent border-none focus:outline-none text-sm"
              />
              
              <button
                onClick={(e) => { e.stopPropagation(); addChapter(item.id); }}
                className="p-1 hover:bg-gray-200 rounded"
                title="添加子章节"
              >
                <PlusIcon className="w-4 h-4 text-gray-500" />
              </button>
              
              <button
                onClick={(e) => { e.stopPropagation(); deleteChapter(item.id); }}
                className="p-1 hover:bg-red-100 rounded"
                title="删除章节"
              >
                <TrashIcon className="w-4 h-4 text-red-500" />
              </button>
            </div>
            
            {hasChildren && isExpanded && (
              <Droppable droppableId={item.id} type="nested">
                {(provided) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    className="mt-1"
                  >
                    {item.children!.map((child, idx) => 
                      renderOutlineItem(child, level + 1, idx)
                    )}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            )}
          </div>
        )}
      </Draggable>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* 顶部工具栏 */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold">标书工作台</h2>
          
          <select
            value={templateName}
            onChange={(e) => setTemplateName(e.target.value)}
            className="border border-gray-300 rounded px-3 py-1.5 text-sm"
          >
            <option value="默认模板">默认模板</option>
            <option value="技术标">技术标</option>
            <option value="商务标">商务标</option>
          </select>
          
          <button
            onClick={() => generateContent()}
            disabled={generating}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            <SparklesIcon className="w-5 h-5" />
            {generating ? '生成中...' : 'AI生成全文'}
          </button>
          
          <button
            onClick={() => selectedChapter && generateContent(selectedChapter)}
            disabled={generating || !selectedChapter}
            className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
          >
            生成选中章节
          </button>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => exportDocument('docx')}
            className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded hover:bg-gray-50"
          >
            <DocumentArrowDownIcon className="w-5 h-5" />
            导出Word
          </button>
        </div>
      </div>

      {/* 三栏布局 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧：大纲树 */}
        <div className="w-72 border-r border-gray-200 bg-white flex flex-col">
          <div className="p-3 border-b border-gray-200 flex items-center justify-between">
            <span className="font-medium">大纲结构</span>
            <button
              onClick={() => addChapter()}
              className="p-1 hover:bg-gray-100 rounded"
              title="添加章节"
            >
              <PlusIcon className="w-5 h-5 text-blue-600" />
            </button>
          </div>
          
          <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="outline">
              {(provided) => (
                <div
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  className="flex-1 overflow-y-auto p-2"
                >
                  {outline.map((item, index) => renderOutlineItem(item, 0, index))}
                  {provided.placeholder}
                  
                  {outline.length === 0 && (
                    <div className="text-center text-gray-400 py-8">
                      点击上方 + 添加章节
                    </div>
                  )}
                </div>
              )}
            </Droppable>
          </DragDropContext>
        </div>

        {/* 中间：富文本编辑器 */}
        <div className="flex-1 flex flex-col bg-white">
          <ReactQuill
            theme="snow"
            value={editorContent}
            onChange={setEditorContent}
            modules={{
              toolbar: [
                [{ 'header': [1, 2, 3, false] }],
                ['bold', 'italic', 'underline', 'strike'],
                [{ 'list': 'ordered' }, { 'list': 'bullet' }],
                [{ 'indent': '-1' }, { 'indent': '+1' }],
                ['link', 'image'],
                ['clean']
              ]
            }}
            className="flex-1"
          />
        </div>

        {/* 右侧：占位符面板 */}
        <div className="w-80 border-l border-gray-200 bg-gray-50 p-4 overflow-y-auto">
          <h3 className="font-medium mb-4">占位符填充</h3>
          
          <div className="space-y-3">
            <div className="bg-white p-3 rounded shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">占位符类型</span>
              </div>
              <div className="flex gap-2">
                <button className="flex-1 py-2 text-sm bg-blue-100 text-blue-700 rounded">
                  手动填充
                </button>
                <button className="flex-1 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50">
                  RAG自动
                </button>
              </div>
            </div>
            
            <div className="bg-white p-3 rounded shadow-sm">
              <label className="block text-sm font-medium mb-2">搜索企业素材</label>
              <input
                type="text"
                placeholder="输入关键词搜索..."
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
              />
            </div>
            
            <div className="text-center text-gray-400 py-4">
              选择章节后显示相关占位符
            </div>
          </div>
        </div>
      </div>

      {/* 底部状态栏 */}
      <div className="bg-white border-t border-gray-200 px-4 py-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {generating && (
              <>
                <div className="flex items-center gap-2">
                  <ClockIcon className="w-4 h-4 text-blue-500" />
                  <span className="text-sm">
                    正在生成: {progress.current_chapter || '-'}
                  </span>
                </div>
                <div className="w-48 h-2 bg-gray-200 rounded overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all"
                    style={{ width: `${(progress.completed_chapters / progress.total_chapters) * 100}%` }}
                  />
                </div>
                <span className="text-sm text-gray-500">
                  {progress.completed_chapters}/{progress.total_chapters}
                </span>
              </>
            )}
            
            {progress.status === 'completed' && (
              <div className="flex items-center gap-2 text-green-600">
                <CheckCircleIcon className="w-5 h-5" />
                <span className="text-sm">生成完成</span>
              </div>
            )}
            
            {progress.status === 'failed' && (
              <div className="flex items-center gap-2 text-red-600">
                <ExclamationCircleIcon className="w-5 h-5" />
                <span className="text-sm">生成失败</span>
              </div>
            )}
          </div>
          
          <div className="text-sm text-gray-500">
            Token消耗: {progress.tokens_used?.toLocaleString() || 0}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
