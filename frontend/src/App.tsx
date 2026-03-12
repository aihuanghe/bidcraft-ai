/**
 * 主应用组件
 */
import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import {
  HomeIcon,
  DocumentTextIcon,
  FolderIcon,
  Cog6ToothIcon,
  ArrowUpTrayIcon,
  ChevronDownIcon,
  DocumentDuplicateIcon,
  BuildingOffice2Icon
} from '@heroicons/react/24/outline';
import { useAppState } from './hooks/useAppState';
import ConfigPanel from './components/ConfigPanel';
import ModelConfigPanel from './components/ModelConfigPanel';
import DocumentAnalysis from './pages/DocumentAnalysis';
import OutlineEdit from './pages/OutlineEdit';
import ContentEdit from './pages/ContentEdit';
import Dashboard from './pages/Dashboard';
import Materials from './pages/Materials';
import Templates from './pages/Templates';

const navigation = [
  { name: '首页', href: '/', icon: HomeIcon },
  { name: '标书工作台', href: '/dashboard', icon: DocumentTextIcon },
  { name: '企业素材库', href: '/materials', icon: FolderIcon },
  { name: '模板管理', href: '/templates', icon: DocumentDuplicateIcon },
];

function AppLayout() {
  const location = useLocation();
  const [showSettings, setShowSettings] = useState(false);
  const [activeSettingsTab, setActiveSettingsTab] = useState<'basic' | 'model'>('basic');
  
  const {
    state,
    updateConfig,
    updateStep,
    updateFileContent,
    updateAnalysisResults,
    updateOutline,
    updateSelectedChapter,
  } = useAppState();

  const steps = ['标书解析', '目录编辑', '正文编辑'];

  const renderCurrentPage = () => {
    switch (location.pathname) {
      case '/':
        return (
          <div className="flex h-full">
            {activeSettingsTab === 'basic' ? (
              <ConfigPanel
                config={state.config}
                onConfigChange={updateConfig}
              />
            ) : (
              <ModelConfigPanel />
            )}
            
            <div className="flex-1 flex flex-col">
              <div className="bg-white shadow-sm px-6">
                <div className="flex gap-1 py-4">
                  {steps.map((step, index) => (
                    <div
                      key={step}
                      className={`flex items-center ${
                        index <= state.currentStep ? 'text-blue-600' : 'text-gray-400'
                      }`}
                    >
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                          index === state.currentStep
                            ? 'bg-blue-600 text-white'
                            : index < state.currentStep
                            ? 'bg-blue-100 text-blue-600'
                            : 'bg-gray-100 text-gray-400'
                        }`}
                      >
                        {index < state.currentStep ? '✓' : index + 1}
                      </div>
                      <span className="ml-2 font-medium">{step}</span>
                      {index < steps.length - 1 && (
                        <ChevronDownIcon className="w-4 h-4 mx-2 rotate-[-90deg]" />
                      )}
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="flex-1 p-6 overflow-y-auto">
                {state.currentStep === 0 && (
                  <DocumentAnalysis
                    fileContent={state.fileContent}
                    projectOverview={state.projectOverview}
                    techRequirements={state.techRequirements}
                    onFileUpload={updateFileContent}
                    onAnalysisComplete={updateAnalysisResults}
                  />
                )}
                {state.currentStep === 1 && (
                  <OutlineEdit
                    projectOverview={state.projectOverview}
                    techRequirements={state.techRequirements}
                    outlineData={state.outlineData}
                    onOutlineGenerated={updateOutline}
                  />
                )}
                {state.currentStep === 2 && (
                  <ContentEdit
                    outlineData={state.outlineData}
                    selectedChapter={state.selectedChapter}
                    onChapterSelect={updateSelectedChapter}
                  />
                )}
              </div>
              
              <div className="bg-white border-t border-gray-200 px-6 py-4">
                <div className="flex justify-between">
                  <button
                    onClick={() => updateStep(Math.max(0, state.currentStep - 1))}
                    disabled={state.currentStep === 0}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed"
                  >
                    上一步
                  </button>
                  <button
                    onClick={() => updateStep(Math.min(steps.length - 1, state.currentStep + 1))}
                    disabled={state.currentStep === steps.length - 1}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    下一步
                  </button>
                </div>
              </div>
            </div>
          </div>
        );
      
      case '/dashboard':
        return <Dashboard />;
      
      case '/materials':
        return <Materials />;
      
      case '/templates':
        return <Templates />;
      
      default:
        return <Navigate to="/" replace />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* 左侧导航 */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <BuildingOffice2Icon className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="text-lg font-bold text-gray-900">易标AI</h1>
              <p className="text-xs text-gray-500">智能标书助手</p>
            </div>
          </div>
        </div>
        
        <nav className="flex-1 p-4 space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium ${
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <item.icon className="w-5 h-5" />
                {item.name}
              </Link>
            );
          })}
        </nav>
        
        <div className="p-4 border-t border-gray-200">
          <button
            onClick={() => setShowSettings(true)}
            className="flex items-center gap-3 px-3 py-2 w-full rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-100"
          >
            <Cog6ToothIcon className="w-5 h-5" />
            系统设置
          </button>
        </div>
      </div>
      
      {/* 主内容 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {renderCurrentPage()}
      </div>
      
      {/* 设置弹窗 */}
      {showSettings && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-4xl h-[80vh] flex overflow-hidden">
            {/* 设置侧边栏 */}
            <div className="w-48 border-r border-gray-200 p-4">
              <h2 className="text-lg font-semibold mb-4">系统设置</h2>
              <nav className="space-y-1">
                <button
                  onClick={() => setActiveSettingsTab('basic')}
                  className={`flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm ${
                    activeSettingsTab === 'basic'
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <Cog6ToothIcon className="w-5 h-5" />
                  基本配置
                </button>
                <button
                  onClick={() => setActiveSettingsTab('model')}
                  className={`flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm ${
                    activeSettingsTab === 'model'
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <DocumentDuplicateIcon className="w-5 h-5" />
                  模型配置
                </button>
              </nav>
            </div>
            
            {/* 设置内容 */}
            <div className="flex-1 overflow-hidden">
              <div className="h-full overflow-y-auto">
                {activeSettingsTab === 'basic' ? (
                  <ConfigPanel
                    config={state.config}
                    onConfigChange={updateConfig}
                  />
                ) : (
                  <ModelConfigPanel />
                )}
              </div>
            </div>
            
            <button
              onClick={() => setShowSettings(false)}
              className="absolute top-4 right-4 p-2 hover:bg-gray-100 rounded"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/*" element={<AppLayout />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
