import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { 
  Plane, 
  BarChart3, 
  Settings, 
  Database, 
  Server, 
  Smartphone,
  Activity,
  Play,
  Loader2
} from 'lucide-react';

const Dashboard: React.FC = () => {
  const [isCreatingTask, setIsCreatingTask] = useState(false);
  const navigate = useNavigate();

  const createTask = async () => {
    try {
      setIsCreatingTask(true);
      const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: '12306', task_type: 'flight_scraper' })
      });
      if (response.ok) {
        // 跳转到任务记录页面查看新任务
        navigate('/task-records');
      }
    } catch (error) {
      console.error('新建任务失败:', error);
    } finally {
      setIsCreatingTask(false);
    }
  };

  return (
    <div>
      {/* 主要内容 */}
      <div>
        <div>
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">仪表板</h1>
            <p className="mt-2 text-gray-600">
              管理和监控航班信息抓取系统
            </p>
          </div>

          {/* 快速操作 */}
          <div className="mb-8">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Play className="h-5 w-5 mr-2 text-green-600" />
                  快速操作
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex gap-4">
                  <Button 
                    onClick={createTask} 
                    disabled={isCreatingTask}
                    className="flex items-center"
                  >
                    {isCreatingTask ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4 mr-2" />
                    )}
                    {isCreatingTask ? '创建中...' : '新建抓取任务'}
                  </Button>
                  <Link to="/task-records">
                    <Button variant="outline" className="flex items-center">
                      <BarChart3 className="h-4 w-4 mr-2" />
                      查看任务记录
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 功能卡片 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Plane className="h-5 w-5 mr-2 text-blue-600" />
                  航班结果
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  查看和管理抓取的航班信息
                </p>
                <Link to="/flight-results">
                  <Button className="w-full">
                    查看航班结果
                  </Button>
                </Link>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2 text-green-600" />
                  任务记录
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  查看抓取任务的执行记录
                </p>
                <Link to="/task-records">
                  <Button className="w-full">
                    查看任务记录
                  </Button>
                </Link>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Settings className="h-5 w-5 mr-2 text-purple-600" />
                  系统控制
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  管理和监控系统服务
                </p>
                <Link to="/system">
                  <Button className="w-full">
                    系统控制
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>

          {/* 系统状态 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>系统状态</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Server className="h-5 w-5 mr-2 text-blue-600" />
                      <span>后端API</span>
                    </div>
                    <span className="text-green-600 font-medium">运行中</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Database className="h-5 w-5 mr-2 text-green-600" />
                      <span>数据库</span>
                    </div>
                    <span className="text-green-600 font-medium">正常</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Smartphone className="h-5 w-5 mr-2 text-purple-600" />
                      <span>Appium服务</span>
                    </div>
                    <span className="text-green-600 font-medium">运行中</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Activity className="h-5 w-5 mr-2 text-orange-600" />
                      <span>Android模拟器</span>
                    </div>
                    <span className="text-green-600 font-medium">运行中</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>快速操作</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Link to="/flight-results" className="block">
                    <Button variant="outline" className="w-full justify-start">
                      <Plane className="h-4 w-4 mr-2" />
                      查看航班结果
                    </Button>
                  </Link>
                  <Link to="/task-records" className="block">
                    <Button variant="outline" className="w-full justify-start">
                      <BarChart3 className="h-4 w-4 mr-2" />
                      查看任务记录
                    </Button>
                  </Link>
                  <Link to="/system" className="block">
                    <Button variant="outline" className="w-full justify-start">
                      <Settings className="h-4 w-4 mr-2" />
                      系统控制
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
