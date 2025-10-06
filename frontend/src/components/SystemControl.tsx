import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Play, Square, RefreshCw, Settings, Server, Smartphone, Database } from 'lucide-react';

interface SystemStatus {
  web: 'running' | 'stopped' | 'unknown';
  frontend: 'running' | 'stopped' | 'unknown';
  appium: 'running' | 'stopped' | 'unknown';
  android: 'running' | 'stopped' | 'unknown';
}

const SystemControl: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus>({
    web: 'unknown',
    frontend: 'unknown',
    appium: 'unknown',
    android: 'unknown'
  });
  const [loading, setLoading] = useState(false);

  // 检查系统状态
  const checkSystemStatus = async () => {
    setLoading(true);
    try {
      // 检查Web服务
      const webResponse = await fetch('http://localhost:8000/health');
      setStatus(prev => ({ ...prev, web: webResponse.ok ? 'running' : 'stopped' }));
      
      // 检查Appium服务
      const appiumResponse = await fetch('http://localhost:4723/status');
      setStatus(prev => ({ ...prev, appium: appiumResponse.ok ? 'running' : 'stopped' }));
      
      // 检查Android设备
      const androidResponse = await fetch('http://localhost:8000/api/android/status');
      setStatus(prev => ({ ...prev, android: androidResponse.ok ? 'running' : 'stopped' }));
      
      // 前端服务状态
      setStatus(prev => ({ ...prev, frontend: 'running' }));
      
    } catch (error) {
      console.error('检查系统状态失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 启动系统服务
  const startSystem = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/system/start', {
        method: 'POST'
      });
      
      if (response.ok) {
        alert('系统启动命令已发送');
        setTimeout(checkSystemStatus, 5000); // 5秒后检查状态
      } else {
        alert('系统启动失败');
      }
    } catch (error) {
      console.error('启动系统失败:', error);
      alert('启动系统失败');
    } finally {
      setLoading(false);
    }
  };

  // 停止系统服务
  const stopSystem = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/system/stop', {
        method: 'POST'
      });
      
      if (response.ok) {
        alert('系统停止命令已发送');
        setTimeout(checkSystemStatus, 3000); // 3秒后检查状态
      } else {
        alert('系统停止失败');
      }
    } catch (error) {
      console.error('停止系统失败:', error);
      alert('停止系统失败');
    } finally {
      setLoading(false);
    }
  };

  // 运行抓取任务
  const runScraper = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/scraper/run', {
        method: 'POST'
      });
      
      if (response.ok) {
        alert('抓取任务已启动');
      } else {
        alert('抓取任务启动失败');
      }
    } catch (error) {
      console.error('运行抓取任务失败:', error);
      alert('运行抓取任务失败');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (serviceStatus: string) => {
    switch (serviceStatus) {
      case 'running':
        return <Badge className="bg-green-100 text-green-800">运行中</Badge>;
      case 'stopped':
        return <Badge className="bg-red-100 text-red-800">已停止</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">未知</Badge>;
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">系统控制面板</h1>
        <p className="text-gray-600">管理和监控航班抓取系统服务</p>
      </div>

      {/* 系统状态 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Server className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Web服务</p>
                <div className="flex items-center gap-2">
                  <p className="text-lg font-bold text-gray-900">localhost:8000</p>
                  {getStatusBadge(status.web)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Database className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">前端服务</p>
                <div className="flex items-center gap-2">
                  <p className="text-lg font-bold text-gray-900">localhost:3000</p>
                  {getStatusBadge(status.frontend)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Settings className="h-8 w-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Appium服务</p>
                <div className="flex items-center gap-2">
                  <p className="text-lg font-bold text-gray-900">localhost:4723</p>
                  {getStatusBadge(status.appium)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Smartphone className="h-8 w-8 text-orange-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Android设备</p>
                <div className="flex items-center gap-2">
                  <p className="text-lg font-bold text-gray-900">模拟器</p>
                  {getStatusBadge(status.android)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 控制按钮 */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Settings className="h-5 w-5 mr-2" />
            系统控制
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <Button 
              onClick={checkSystemStatus} 
              disabled={loading}
              className="flex items-center"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              检查状态
            </Button>

            <Button 
              onClick={startSystem} 
              disabled={loading}
              variant="default"
              className="flex items-center"
            >
              <Play className="h-4 w-4 mr-2" />
              启动系统
            </Button>

            <Button 
              onClick={stopSystem} 
              disabled={loading}
              variant="destructive"
              className="flex items-center"
            >
              <Square className="h-4 w-4 mr-2" />
              停止系统
            </Button>

            <Button 
              onClick={runScraper} 
              disabled={loading || status.web !== 'running' || status.appium !== 'running'}
              variant="outline"
              className="flex items-center"
            >
              <Play className="h-4 w-4 mr-2" />
              运行抓取
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 快速操作 */}
      <Card>
        <CardHeader>
          <CardTitle>快速操作</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h3 className="font-semibold">Docker Compose 操作</h3>
              <div className="space-y-2">
                <Button 
                  variant="outline" 
                  className="w-full justify-start"
                  onClick={() => window.open('http://localhost:8000/docs', '_blank')}
                >
                  📚 API文档
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full justify-start"
                  onClick={() => window.open('http://localhost:3000', '_blank')}
                >
                  🌐 前端界面
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full justify-start"
                  onClick={() => window.open('http://localhost:4723/inspector', '_blank')}
                >
                  🔍 Appium Inspector
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <h3 className="font-semibold">系统管理</h3>
              <div className="space-y-2">
                <Button 
                  variant="outline" 
                  className="w-full justify-start"
                  onClick={() => window.open('/task-records', '_self')}
                >
                  📋 任务记录
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full justify-start"
                  onClick={() => window.open('/flight-results', '_self')}
                >
                  ✈️ 航班结果
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full justify-start"
                  onClick={() => window.open('/settings', '_self')}
                >
                  ⚙️ 系统设置
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SystemControl;
