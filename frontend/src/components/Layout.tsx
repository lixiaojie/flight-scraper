import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Plane, BarChart3, Settings, LogOut, Home } from 'lucide-react';

const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const onLogout = () => {
    logout();
    navigate('/login');
  };

  const linkBase =
    'inline-flex items-center px-3 py-2 rounded-md text-sm font-medium';
  const linkInactive = 'text-gray-600 hover:text-gray-900 hover:bg-gray-100';
  const linkActive = 'text-blue-700 bg-blue-50';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 全局导航 */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center gap-6">
              <div className="flex items-center">
                <Plane className="h-7 w-7 text-blue-600" />
                <span className="ml-2 text-lg font-bold text-gray-900">
                  航班信息抓取系统
                </span>
              </div>
              <div className="hidden md:flex items-center gap-1">
                <NavLink
                  to="/dashboard"
                  className={({ isActive }) =>
                    `${linkBase} ${isActive ? linkActive : linkInactive}`
                  }
                >
                  <Home className="h-4 w-4 mr-1" /> 仪表板
                </NavLink>
                <NavLink
                  to="/task-records"
                  className={({ isActive }) =>
                    `${linkBase} ${isActive ? linkActive : linkInactive}`
                  }
                >
                  <BarChart3 className="h-4 w-4 mr-1" /> 任务记录
                </NavLink>
                <NavLink
                  to="/flight-results"
                  className={({ isActive }) =>
                    `${linkBase} ${isActive ? linkActive : linkInactive}`
                  }
                >
                  <Plane className="h-4 w-4 mr-1" /> 航班结果
                </NavLink>
                <NavLink
                  to="/system"
                  className={({ isActive }) =>
                    `${linkBase} ${isActive ? linkActive : linkInactive}`
                  }
                >
                  <Settings className="h-4 w-4 mr-1" /> 系统控制
                </NavLink>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-600 hidden sm:inline">
                欢迎, {user?.username}
              </span>
              <button
                onClick={onLogout}
                className="inline-flex items-center px-3 py-2 rounded-md text-sm border hover:bg-gray-50"
              >
                <LogOut className="h-4 w-4 mr-1" /> 退出
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* 页面内容 */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
